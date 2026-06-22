import json
import uuid
from typing import Dict, Any
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from ..config import settings
from ..services.tasks import get_task_by_day_index
from ..services.crypto import normalize_text, sha256_hex, generate_salt_hex, compute_proof_hash
from ..services.reflection import (
    fallback_reflection,
    request_reflection_candidate_with_metadata,
    validate_reflection,
)
from ..services.reflection_safety import (
    CRISIS_REFLECTION,
    assess_input_risk,
    assess_input_quality,
)
from ..services.time import date_key_for_timezone, diff_days
from ..services.report import generate_report_text
from ..models import DailyLog, UserProgress


def _ensure_progress(db: Session, address: str, timezone: str, date_key: str, start_date_key_override: str | None = None) -> UserProgress:
    progress = db.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if not progress:
        progress = UserProgress(
            address=address,
            timezone=timezone,
            challenge_id=settings.challenge_id,
            start_date_key=start_date_key_override or date_key,
            streak=0,
            milestones={"1": None, "2": None, "3": None},
        )
        db.add(progress)
    milestones = progress.milestones if isinstance(progress.milestones, dict) else {}
    normalized_milestones = dict(milestones)
    for key in ("1", "2", "3"):
        normalized_milestones.setdefault(key, None)
    if normalized_milestones != progress.milestones:
        progress.milestones = normalized_milestones
        db.add(progress)
    return progress


async def daily_prompt_node(state: Dict[str, Any]) -> Dict[str, Any]:
    flow = state.get("flow", "checkin")
    if flow != "checkin":
        return {}

    db: Session = state.get("db")
    address = state.get("address")
    date_key = state.get("dateKey")
    challenge_id = state.get("challengeId", settings.challenge_id)
    if db and address and date_key:
        log = db.exec(
            select(DailyLog).where(
                DailyLog.address == address,
                DailyLog.challenge_id == challenge_id,
                DailyLog.date_key == date_key,
            )
        ).first()
        if log:
            return {"alreadyCheckedIn": True, "logId": log.id}

    day_index = state.get("dayIndex")
    if day_index is None:
        return {}
    task = get_task_by_day_index(int(day_index))
    return {"task": task, "alreadyCheckedIn": False}


async def user_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
    text = state.get("text") or ""
    normalized = normalize_text(text)
    image_url = state.get("imageUrl")
    image_desc = None
    if image_url:
        image_desc = "TODO: image OCR not implemented in MVP"
    return {"normalizedText": normalized, "imageDesc": image_desc}


async def risk_classify_node(state: Dict[str, Any]) -> Dict[str, Any]:
    assessment = await assess_input_risk(state.get("normalizedText", ""))
    return {
        "riskLevel": assessment.level,
        "riskReasons": assessment.reasons,
        "riskConfidence": assessment.confidence,
    }


async def crisis_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "outcome": "crisis_redirected",
        "reflection": CRISIS_REFLECTION,
        "responseMessage": "当前输入已进入安全分流，不会生成打卡记录或链上 Proof。",
    }


async def input_quality_node(state: Dict[str, Any]) -> Dict[str, Any]:
    assessment = assess_input_quality(state.get("normalizedText", ""))
    return {
        "inputDecision": assessment.decision,
        "inputReasons": assessment.reasons,
        "responseMessage": assessment.message,
    }


async def clarification_response_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "outcome": "clarify",
        "responseMessage": state.get("responseMessage"),
    }


async def rejected_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "outcome": "rejected",
        "responseMessage": state.get("responseMessage"),
    }


async def reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    task = state.get("task", {})
    normalized = state.get("normalizedText", "")
    try:
        candidate = await request_reflection_candidate_with_metadata(
            task,
            normalized,
        )
        return {
            "rawReflection": candidate.raw,
            "modelAttempts": candidate.attempts,
            "generationError": None,
        }
    except Exception as exc:
        return {
            "rawReflection": "",
            "modelAttempts": getattr(exc, "attempts", 1),
            "generationError": type(exc).__name__,
            "fallbackReason": "model_unavailable",
        }


async def validate_reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("generationError"):
        return {
            "reflectionValid": False,
            "validationErrors": ["model_unavailable"],
        }

    validation = validate_reflection(state.get("rawReflection", ""))
    if validation.valid:
        return {
            "reflection": validation.reflection.model_dump(),
            "reflectionValid": True,
            "validationErrors": [],
        }
    return {
        "reflectionValid": False,
        "validationErrors": validation.errors,
    }


async def repair_reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    repair_attempts = int(state.get("repairAttempts") or 0) + 1
    try:
        candidate = await request_reflection_candidate_with_metadata(
            state.get("task", {}),
            state.get("normalizedText", ""),
            invalid_output=state.get("rawReflection", ""),
            validation_errors=state.get("validationErrors", []),
        )
        return {
            "rawReflection": candidate.raw,
            "modelAttempts": int(state.get("modelAttempts") or 0)
            + candidate.attempts,
            "repairAttempts": repair_attempts,
            "generationError": None,
        }
    except Exception as exc:
        return {
            "rawReflection": "",
            "modelAttempts": int(state.get("modelAttempts") or 0)
            + getattr(exc, "attempts", 1),
            "repairAttempts": repair_attempts,
            "generationError": type(exc).__name__,
            "fallbackReason": "invalid_output",
        }


async def fallback_reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    reason = state.get("fallbackReason")
    if not reason:
        reason = "model_unavailable" if state.get("generationError") else "invalid_output"
    return {
        "reflection": fallback_reflection(reason),
        "fallbackReason": reason,
    }


async def proof_builder_node(state: Dict[str, Any]) -> Dict[str, Any]:
    date_key = state.get("dateKey")
    normalized = state.get("normalizedText", "")
    salt_hex = generate_salt_hex()
    proof_hash = compute_proof_hash(date_key, normalized, salt_hex)
    input_hash = sha256_hex(normalized) if normalized else None
    return {"saltHex": salt_hex, "proofHash": proof_hash, "inputHash": input_hash}


async def onchain_submit_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "submitHint": {
            "method": "submitProof",
            "params": [state.get("dayIndex"), state.get("proofHash")],
            "contract": state.get("contractAddress"),
        }
    }


async def tx_confirm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    db: Session = state["db"]
    log_id = state.get("logId")
    tx_hash = state.get("txHash")
    chain_id = state.get("chainId")
    contract_address = state.get("contractAddress")
    block_number = state.get("blockNumber")
    if not log_id:
        return {"txStatus": "CREATED"}

    log = db.exec(select(DailyLog).where(DailyLog.id == log_id)).first()
    if log and tx_hash and not log.tx_hash:
        log.tx_hash = tx_hash
        log.chain_id = chain_id
        log.contract_address = contract_address
        log.block_number = block_number
        log.status = "SUBMITTED"
        db.add(log)
        db.commit()
    return {"txStatus": "SUBMITTED" if tx_hash else "CREATED"}


async def progress_update_node(state: Dict[str, Any]) -> Dict[str, Any]:
    db: Session = state["db"]
    flow = state.get("flow", "checkin")
    address = state.get("address")
    challenge_id = state.get("challengeId", settings.challenge_id)
    timezone = state.get("timezone") or settings.default_timezone
    date_key = state.get("dateKey") or date_key_for_timezone(timezone)

    if not address:
        return {}

    start_date_key_override = state.get("startDateKey")
    progress = _ensure_progress(db, address, timezone, date_key, start_date_key_override)

    log = None
    already_checked_in = False

    if flow == "checkin":
        with db.no_autoflush:
            log = db.exec(
                select(DailyLog).where(
                    DailyLog.address == address,
                    DailyLog.challenge_id == challenge_id,
                    DailyLog.date_key == date_key,
                )
            ).first()
        already_checked_in = bool(log)

        if not log:
            day_index = state.get("dayIndex")
            reflection = state.get("reflection")
            salt_hex = state.get("saltHex")
            proof_hash = state.get("proofHash")
            input_hash = state.get("inputHash")
            normalized_text = state.get("normalizedText")
            if day_index is None or not proof_hash:
                return {}

            log = DailyLog(
                id=str(uuid.uuid4()),
                address=address,
                challenge_id=challenge_id,
                day_index=day_index,
                date_key=date_key,
                input_hash=input_hash,
                normalized_text=normalized_text,
                reflection=reflection,
                salt_hex=salt_hex,
                proof_hash=proof_hash,
                status="CREATED",
            )
            if progress.last_date_key and progress.last_date_key != date_key:
                delta = diff_days(progress.last_date_key, date_key)
                if delta == 1:
                    progress.streak = (progress.streak or 0) + 1
                else:
                    progress.streak = 1
            elif not progress.last_date_key:
                progress.streak = 1

            progress.last_date_key = date_key
            progress.last_day_index = log.day_index
            progress.updated_at = datetime.utcnow()
            db.add(log)
            db.add(progress)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                log = db.exec(
                    select(DailyLog).where(
                        DailyLog.address == address,
                        DailyLog.challenge_id == challenge_id,
                        DailyLog.date_key == date_key,
                    )
                ).first()
                progress = db.exec(
                    select(UserProgress).where(UserProgress.address == address)
                ).first()
                if not log or not progress:
                    raise
                already_checked_in = True
            except Exception:
                db.rollback()
                raise
        else:
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise
    else:
        log = db.exec(
            select(DailyLog).where(
                DailyLog.address == address,
                DailyLog.challenge_id == challenge_id,
                DailyLog.date_key == date_key,
            )
        ).first()
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    logs = db.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == challenge_id,
        )
    ).all()
    completed_days = sorted({l.day_index for l in logs})

    today_checked_in = bool(log)
    milestones = progress.milestones or {"1": None, "2": None, "3": None}

    return {
        "logId": log.id if log else None,
        "streak": progress.streak or 0,
        "completedDays": completed_days,
        "todayCheckedIn": today_checked_in,
        "dateKey": date_key,
        "startDateKey": progress.start_date_key,
        "milestones": milestones,
        "alreadyCheckedIn": already_checked_in,
    }


async def badge_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    completed_days = set(state.get("completedDays") or [])
    milestones = state.get("milestones") or {"1": None, "2": None, "3": None}
    eligible = []
    if milestones.get("1") is None and all(day in completed_days for day in range(1, 8)):
        eligible.append(1)
    if milestones.get("2") is None and all(day in completed_days for day in range(1, 15)):
        eligible.append(2)
    if milestones.get("3") is None and all(day in completed_days for day in range(1, 29)):
        eligible.append(3)
    return {
        "eligibleMilestones": eligible,
        "alreadyCheckedIn": state.get("alreadyCheckedIn", False),
    }


def _report_payload(logs: list, title: str, range_value: str) -> Dict[str, Any]:
    total = len(logs)
    streak = 0
    chart_by_day = [0] * 28
    for log in logs:
        if 1 <= log.day_index <= 28:
            chart_by_day[log.day_index - 1] += 1
    if total == 0:
        report_text = "你还没有打卡记录。先去 Daily 页写一句话。"
    elif range_value == "final":
        report_text = f"你累计记录了 {total} 天。结营建议：挑一条你最想保留的‘边界’，把它写成一句固定句，接下来每周读一遍。"
    else:
        report_text = f"这段时间你记录了 {total} 天。你的节奏更像‘先做一小步再往下走’。如果要继续：每天只保留一句最关键的句子。"
    recent_logs = list(reversed(logs[-6:]))
    return {
        "title": title,
        "reportText": report_text,
        "recentLogs": recent_logs,
        "chartByDay": chart_by_day,
        "range": range_value,
        "streak": streak,
    }


async def weekly_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    db: Session = state["db"]
    address = state.get("address")
    challenge_id = state.get("challengeId", settings.challenge_id)
    logs = db.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == challenge_id,
        ).order_by(DailyLog.date_key)
    ).all()
    range_logs = logs[-7:] if logs else []
    payload = _report_payload(range_logs, "周报（模拟）", "week")
    if range_logs:
        payload["reportText"] = await generate_report_text(range_logs, "week")
    return payload


async def final_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    db: Session = state["db"]
    address = state.get("address")
    challenge_id = state.get("challengeId", settings.challenge_id)
    logs = db.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == challenge_id,
        ).order_by(DailyLog.date_key)
    ).all()
    payload = _report_payload(logs, "结营报告（模拟）", "final")
    if logs:
        payload["reportText"] = await generate_report_text(logs, "final")
    return payload
