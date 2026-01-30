import json
import uuid
from typing import Dict, Any
from sqlmodel import Session, select

from spoon_ai.graph import Command

from ..services.tasks import get_task_by_day_index
from ..services.crypto import normalize_text, sha256_hex, generate_salt_hex, compute_proof_hash
from ..services.reflection import generate_reflection
from ..services.report import build_report
from ..models import DailyLog, UserProgress


async def daily_prompt_node(state: Dict[str, Any]) -> Command | Dict[str, Any]:
    flow = state.get("flow", "checkin")
    if flow == "tx_confirm":
        return Command(goto="TxConfirm")
    if flow == "report_week":
        return Command(goto="WeeklyReport")
    if flow == "report_final":
        return Command(goto="FinalReport")

    day_index = state.get("dayIndex")
    task = get_task_by_day_index(int(day_index))
    return {"task": task}


async def user_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
    text = state.get("text") or ""
    normalized = normalize_text(text)
    image_url = state.get("imageUrl")
    image_desc = None
    if image_url:
        image_desc = "TODO: image OCR not implemented in MVP"
    return {"normalizedText": normalized, "imageDesc": image_desc}


async def reflection_node(state: Dict[str, Any]) -> Dict[str, Any]:
    task = state.get("task", {})
    normalized = state.get("normalizedText", "")
    reflection = await generate_reflection(task, normalized)
    return {"reflection": reflection}


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
            "contract": state.get("contractAddress")
        }
    }


async def tx_confirm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    db: Session = state["db"]
    log_id = state.get("logId")
    tx_hash = state.get("txHash")
    chain_id = state.get("chainId")
    contract_address = state.get("contractAddress")
    if not log_id:
        return {"txStatus": "CREATED"}

    log = db.exec(select(DailyLog).where(DailyLog.id == log_id)).first()
    if log and tx_hash and not log.tx_hash:
        log.tx_hash = tx_hash
        log.chain_id = chain_id
        log.contract_address = contract_address
        log.status = "SUBMITTED"
        db.add(log)
        db.commit()
    return {"txStatus": "SUBMITTED" if tx_hash else "CREATED"}


async def progress_update_node(state: Dict[str, Any]) -> Dict[str, Any]:
    db: Session = state["db"]
    address = state.get("address")
    challenge_id = state.get("challengeId")
    date_key = state.get("dateKey")
    day_index = state.get("dayIndex")
    reflection = state.get("reflection")
    salt_hex = state.get("saltHex")
    proof_hash = state.get("proofHash")
    input_hash = state.get("inputHash")
    normalized_text = state.get("normalizedText")
    if not date_key or not proof_hash:
        return {}

    log = db.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == challenge_id,
            DailyLog.date_key == date_key,
        )
    ).first()

    if not log:
        log = DailyLog(
            id=str(uuid.uuid4()),
            address=address,
            challenge_id=challenge_id,
            day_index=day_index,
            date_key=date_key,
            input_hash=input_hash,
            normalized_text=normalized_text,
            reflection=reflection,
            salt=salt_hex,
            proof_hash=proof_hash,
            status="CREATED",
        )
        db.add(log)
        db.commit()
    else:
        # First wins: keep original
        pass

    progress = db.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if progress:
        if progress.last_date_key and progress.last_date_key != date_key:
            from datetime import date as _date
            last = _date.fromisoformat(progress.last_date_key)
            current = _date.fromisoformat(date_key)
            if (current - last).days == 1:
                progress.streak = (progress.streak or 0) + 1
            else:
                progress.streak = 1
        elif not progress.last_date_key:
            progress.streak = 1
        progress.last_date_key = date_key
        progress.last_day_index = day_index
        progress.updated_at = __import__("datetime").datetime.utcnow()
        db.add(progress)
        db.commit()

    completed_logs = db.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == challenge_id,
        )
    ).all()
    completed_days = [r.day_index for r in completed_logs]

    milestone = 0
    if progress and progress.streak >= 28:
        milestone = 28
    elif progress and progress.streak >= 14:
        milestone = 14
    elif progress and progress.streak >= 7:
        milestone = 7

    badges = progress.badges_minted if progress else {}
    return {
        "logId": log.id,
        "streak": progress.streak if progress else 1,
        "completedDays": completed_days,
        "milestoneEligible": milestone,
        "badgesMinted": badges,
    }


async def badge_check_node(state: Dict[str, Any]) -> Dict[str, Any]:
    streak = state.get("streak", 0)
    badges = state.get("badgesMinted", {}) or {}
    should_mint = False
    badge_type = None
    if streak >= 28 and not badges.get("28"):
        should_mint = True
        badge_type = "Restart Completed"
    elif streak >= 14 and not badges.get("14"):
        should_mint = True
        badge_type = "Restart Halfway"
    elif streak >= 7 and not badges.get("7"):
        should_mint = True
        badge_type = "Restart Week 1"

    output = {
        "logId": state.get("logId"),
        "challengeId": state.get("challengeId"),
        "dateKey": state.get("dateKey"),
        "dayIndex": state.get("dayIndex"),
        "reflection": state.get("reflection"),
        "proofHash": state.get("proofHash"),
        "streak": state.get("streak"),
        "milestoneEligible": state.get("milestoneEligible"),
        "alreadyCheckedIn": state.get("alreadyCheckedIn", False),
    }
    return {"output": json.dumps(output, ensure_ascii=False)}


async def weekly_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    db: Session = state["db"]
    address = state.get("address")
    challenge_id = state.get("challengeId")
    logs = db.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == challenge_id,
        ).order_by(DailyLog.date_key)
    ).all()
    from_date = logs[-7].date_key if len(logs) >= 7 else (logs[0].date_key if logs else "")
    to_date = logs[-1].date_key if logs else ""
    report = build_report([{"date_key": l.date_key} for l in logs[-7:]], from_date, to_date)
    output = {
        "address": address,
        "challengeId": challenge_id,
        "range": "week",
        "from": from_date,
        "to": to_date,
        "reportText": report["reportText"],
        "chartData": report["chartData"],
    }
    return {"output": json.dumps(output, ensure_ascii=False)}


async def final_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    db: Session = state["db"]
    address = state.get("address")
    challenge_id = state.get("challengeId")
    logs = db.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == challenge_id,
        ).order_by(DailyLog.date_key)
    ).all()
    from_date = logs[0].date_key if logs else ""
    to_date = logs[-1].date_key if logs else ""
    report = build_report([{"date_key": l.date_key} for l in logs], from_date, to_date)
    output = {
        "address": address,
        "challengeId": challenge_id,
        "range": "final",
        "from": from_date,
        "to": to_date,
        "reportText": report["reportText"],
        "chartData": report["chartData"],
    }
    return {"output": json.dumps(output, ensure_ascii=False)}
