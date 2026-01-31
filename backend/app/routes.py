from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
import json
from typing import Dict, Any, Optional

from eth_utils import keccak

from .database import get_session
from .config import settings
from .schemas import (
    HealthResponse,
    DailyPromptResponse,
    UserResponse,
    UserUpdateRequest,
    CheckinRequest,
    CheckinResponse,
    TxConfirmRequest,
    TxConfirmResponse,
    ProgressResponse,
    ReportResponse,
    SbtConfirmRequest,
    SbtConfirmResponse,
    MetadataResponse,
    DailySnapshotResponse,
    HomeSnapshotResponse,
    MilestoneMintRequest,
    MilestoneMintResponse,
)
from .models import UserProgress, DailyLog
from .services.tasks import get_task_by_day_index
from .services.time import date_key_for_timezone, diff_days, date_key_for_day_index
from .graph.agent import create_agent

router = APIRouter()


def _http_error(status: int, code: str, message: str, details: Optional[dict] = None):
    raise HTTPException(status_code=status, detail={"error": {"code": code, "message": message, "details": details or {}}})


def _lower_address(addr: str) -> str:
    return addr.strip().lower()


def _require_address(addr: str) -> str:
    if not addr or not addr.startswith("0x") or len(addr) != 42:
        _http_error(400, "INVALID_ARGUMENT", "invalid address")
    return _lower_address(addr)


def _default_milestones() -> Dict[str, Optional[str]]:
    return {"1": None, "2": None, "3": None}


def _demo_start_date_key(timezone: str) -> str:
    return settings.demo_start_date_key or date_key_for_timezone(timezone)


def _ensure_milestones(progress: UserProgress, session: Optional[Session] = None) -> Dict[str, Optional[str]]:
    changed = False
    if not isinstance(progress.milestones, dict):
        progress.milestones = {}
        changed = True
    for key in ("1", "2", "3"):
        if key not in progress.milestones:
            progress.milestones[key] = None
            changed = True
    if changed and session:
        session.add(progress)
        session.commit()
    return progress.milestones


def _parse_reflection(value: Any) -> Dict[str, str]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {"note": "", "next": ""}
    return {"note": "", "next": ""}


def _log_to_response(log: DailyLog) -> Dict[str, Any]:
    return {
        "id": log.id,
        "address": log.address,
        "challengeId": log.challenge_id,
        "dayIndex": log.day_index,
        "dateKey": log.date_key,
        "normalizedText": log.normalized_text or "",
        "reflection": _parse_reflection(log.reflection),
        "saltHex": log.salt_hex,
        "proofHash": log.proof_hash,
        "status": log.status,
        "txHash": log.tx_hash,
        "daySbtTxHash": log.day_sbt_tx_hash,
        "createdAt": log.created_at.isoformat() + "Z",
    }


def _token_id_for_day(address: str, day_index: int) -> int:
    addr_bytes = bytes.fromhex(address[2:])
    packed = addr_bytes + bytes([day_index])
    return int.from_bytes(keccak(packed), "big")


def _token_id_for_final(address: str) -> int:
    addr_bytes = bytes.fromhex(address[2:])
    packed = addr_bytes + bytes([99])
    return int.from_bytes(keccak(packed), "big")


def _parse_token_id(token_id: str) -> int:
    token_id = token_id.strip()
    if token_id.startswith("0x"):
        return int(token_id, 16)
    return int(token_id)


async def _invoke_graph(state: Dict[str, Any]):
    agent = create_agent()
    return await agent.graph.invoke(state)


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "version": settings.version}


@router.get("/dailyPrompt", response_model=DailyPromptResponse)
def daily_prompt(dayIndex: int, timezone: str = settings.default_timezone):
    if dayIndex < 1 or dayIndex > 28:
        _http_error(400, "INVALID_ARGUMENT", "dayIndex must be between 1 and 28")
    task = get_task_by_day_index(dayIndex)
    return {
        "challengeId": settings.challenge_id,
        "dayIndex": dayIndex,
        "title": task["title"],
        "instruction": task["instruction"],
        "hint": task.get("hint"),
    }


@router.get("/user", response_model=UserResponse)
def get_user(address: str, session: Session = Depends(get_session)):
    address = _require_address(address)
    user = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if not user:
        _http_error(404, "NOT_FOUND", "user not found")
    return {
        "address": user.address,
        "displayName": user.display_name,
        "avatarUrl": user.avatar_url,
        "timezone": user.timezone,
        "challengeId": user.challenge_id,
        "createdAt": user.created_at.isoformat() + "Z",
        "updatedAt": user.updated_at.isoformat() + "Z",
    }


@router.post("/user", response_model=dict)
def update_user(payload: UserUpdateRequest, session: Session = Depends(get_session)):
    address = _require_address(payload.address)
    user = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if not user:
        date_key = date_key_for_timezone(payload.timezone)
        user = UserProgress(
            address=address,
            display_name=payload.displayName,
            avatar_url=payload.avatarUrl,
            timezone=payload.timezone,
            challenge_id=settings.challenge_id,
            start_date_key=date_key,
            streak=0,
            day_mint_count=0,
            final_minted=False,
            milestones=_default_milestones(),
        )
    else:
        user.display_name = payload.displayName
        user.avatar_url = payload.avatarUrl
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    return {"ok": True}


@router.get("/homeSnapshot", response_model=HomeSnapshotResponse)
def home_snapshot(address: str, session: Session = Depends(get_session)):
    address = _require_address(address)
    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    timezone = progress.timezone if progress else settings.default_timezone
    if settings.demo_mode:
        start_date_key = progress.start_date_key if progress and progress.start_date_key else _demo_start_date_key(timezone)
        day_btn_target = progress.last_day_index or 1 if progress else 1
        day_btn_target = min(28, max(1, day_btn_target))
        today_key = date_key_for_day_index(start_date_key, day_btn_target)
    else:
        today_key = date_key_for_timezone(timezone)
        start_date_key = progress.start_date_key if progress else today_key
        day_btn_target = 1
        if start_date_key:
            day_btn_target = diff_days(start_date_key, today_key) + 1
            day_btn_target = min(28, max(1, day_btn_target))
    day_btn_label = f"Day {day_btn_target}"
    return {
        "dayBtnLabel": day_btn_label,
        "dayBtnTarget": day_btn_target,
        "startDateKey": start_date_key,
        "todayDateKey": today_key,
    }


@router.get("/dailySnapshot", response_model=DailySnapshotResponse)
def daily_snapshot(address: str, dayIndex: int, session: Session = Depends(get_session)):
    address = _require_address(address)
    if dayIndex < 1 or dayIndex > 28:
        _http_error(400, "INVALID_ARGUMENT", "dayIndex must be between 1 and 28")
    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    timezone = progress.timezone if progress else settings.default_timezone
    if settings.demo_mode:
        start_date_key = progress.start_date_key if progress and progress.start_date_key else _demo_start_date_key(timezone)
        date_key = date_key_for_day_index(start_date_key, dayIndex)
    else:
        date_key = date_key_for_timezone(timezone)
    task = get_task_by_day_index(dayIndex)
    log = session.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == settings.challenge_id,
            DailyLog.date_key == date_key,
        )
    ).first()
    return {
        "dateKey": date_key,
        "task": {
            "dayIndex": dayIndex,
            "title": task["title"],
            "instruction": task["instruction"],
            "hint": task.get("hint"),
        },
        "log": _log_to_response(log) if log else None,
        "alreadyCheckedIn": bool(log),
    }


@router.post("/checkin", response_model=CheckinResponse)
async def checkin(payload: CheckinRequest, session: Session = Depends(get_session)):
    address = _require_address(payload.address)
    if payload.dayIndex < 1 or payload.dayIndex > 28:
        _http_error(400, "INVALID_ARGUMENT", "dayIndex must be between 1 and 28")
    if payload.text is None and not payload.imageUrl:
        _http_error(400, "INVALID_ARGUMENT", "text or imageUrl required")

    timezone = payload.timezone or settings.default_timezone
    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    start_date_key = None
    if settings.demo_mode:
        start_date_key = progress.start_date_key if progress and progress.start_date_key else _demo_start_date_key(timezone)
        date_key = date_key_for_day_index(start_date_key, payload.dayIndex)
    else:
        date_key = date_key_for_timezone(timezone)

    state = {
        "db": session,
        "flow": "checkin",
        "address": address,
        "timezone": timezone,
        "challengeId": settings.challenge_id,
        "dateKey": date_key,
        "dayIndex": payload.dayIndex,
        "text": payload.text,
        "imageUrl": payload.imageUrl,
    }
    if start_date_key:
        state["startDateKey"] = start_date_key
    result = await _invoke_graph(state)
    log_id = result.get("logId")
    if not log_id:
        log = session.exec(
            select(DailyLog).where(
                DailyLog.address == address,
                DailyLog.challenge_id == settings.challenge_id,
                DailyLog.date_key == date_key,
            )
        ).first()
    else:
        log = session.exec(select(DailyLog).where(DailyLog.id == log_id)).first()
    if not log:
        _http_error(500, "INTERNAL", "failed to create log")
    return {
        "log": _log_to_response(log),
        "alreadyCheckedIn": bool(result.get("alreadyCheckedIn")),
    }


@router.post("/tx/confirm", response_model=TxConfirmResponse)
async def tx_confirm(payload: TxConfirmRequest, session: Session = Depends(get_session)):
    address = _require_address(payload.address)
    log = session.exec(select(DailyLog).where(DailyLog.id == payload.logId)).first()
    if not log:
        _http_error(404, "NOT_FOUND", "logId not found")
    if log.tx_hash:
        return {"ok": True}
    state = {
        "db": session,
        "flow": "tx_confirm",
        "address": address,
        "logId": payload.logId,
        "txHash": payload.txHash,
        "chainId": payload.chainId,
        "contractAddress": payload.contractAddress,
    }
    await _invoke_graph(state)
    return {"ok": True}


@router.post("/sbt/confirm", response_model=SbtConfirmResponse)
def sbt_confirm(payload: SbtConfirmRequest, session: Session = Depends(get_session)):
    address = _require_address(payload.address)
    sbt_type = payload.type.upper()
    if sbt_type not in ("DAY", "FINAL"):
        _http_error(400, "INVALID_ARGUMENT", "type must be DAY or FINAL")

    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if not progress:
        _http_error(404, "NOT_FOUND", "user not found")
    _ensure_milestones(progress, session)

    if sbt_type == "DAY":
        if payload.dayIndex is None or payload.dayIndex < 1 or payload.dayIndex > 28:
            _http_error(400, "INVALID_ARGUMENT", "dayIndex must be between 1 and 28")
        log = session.exec(
            select(DailyLog).where(
                DailyLog.address == address,
                DailyLog.challenge_id == settings.challenge_id,
                DailyLog.day_index == payload.dayIndex,
            ).order_by(DailyLog.date_key.desc())
        ).first()
        if not log:
            _http_error(404, "NOT_FOUND", "daily log not found for dayIndex")
        if log.day_sbt_tx_hash:
            return {"ok": True}
        log.day_sbt_tx_hash = payload.txHash
        log.chain_id = payload.chainId
        log.contract_address = payload.contractAddress
        if progress.day_mint_count < 28:
            progress.day_mint_count += 1
        progress.updated_at = datetime.utcnow()
        session.add(log)
        session.add(progress)
        session.commit()
        return {"ok": True}

    if progress.final_minted:
        return {"ok": True}
    progress.final_minted = True
    progress.final_sbt_tx_hash = payload.txHash
    progress.updated_at = datetime.utcnow()
    session.add(progress)
    session.commit()
    return {"ok": True}


@router.post("/milestone/mint", response_model=MilestoneMintResponse)
def milestone_mint(payload: MilestoneMintRequest, session: Session = Depends(get_session)):
    address = _require_address(payload.address)
    milestone_id = payload.milestoneId
    if milestone_id not in (1, 2, 3):
        _http_error(400, "INVALID_ARGUMENT", "milestoneId must be 1, 2 or 3")

    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if not progress:
        _http_error(404, "NOT_FOUND", "user not found")
    milestones = _ensure_milestones(progress, session)

    if milestones.get(str(milestone_id)):
        return {"ok": True, "milestones": milestones}

    logs = session.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == settings.challenge_id,
        )
    ).all()
    completed_days = {l.day_index for l in logs}
    completed_count = len(completed_days)
    required = 7 if milestone_id == 1 else 14 if milestone_id == 2 else 28

    if completed_count < required:
        _http_error(400, "NEED_MORE_DAYS", f"need {required}", {"required": required, "completed": completed_count})

    milestones[str(milestone_id)] = payload.txHash
    progress.milestones = milestones
    progress.updated_at = datetime.utcnow()
    session.add(progress)
    session.commit()
    return {"ok": True, "milestones": milestones}


@router.get("/progress", response_model=ProgressResponse)
async def progress(address: str, session: Session = Depends(get_session)):
    address = _require_address(address)
    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    timezone = progress.timezone if progress else settings.default_timezone

    start_date_key = None
    date_key = None
    if settings.demo_mode:
        start_date_key = progress.start_date_key if progress and progress.start_date_key else _demo_start_date_key(timezone)
        day_for_demo = progress.last_day_index or 1 if progress else 1
        day_for_demo = min(28, max(1, day_for_demo))
        date_key = date_key_for_day_index(start_date_key, day_for_demo)

    state = {
        "db": session,
        "flow": "progress",
        "address": address,
        "challengeId": settings.challenge_id,
        "timezone": timezone,
    }
    if start_date_key:
        state["startDateKey"] = start_date_key
    if date_key:
        state["dateKey"] = date_key
    result = await _invoke_graph(state)

    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if not progress:
        _http_error(404, "NOT_FOUND", "user not found")
    milestones = _ensure_milestones(progress, session)

    return {
        "dateKey": result.get("dateKey") or date_key_for_timezone(progress.timezone),
        "streak": result.get("streak", progress.streak or 0),
        "dayMintCount": result.get("dayMintCount", progress.day_mint_count),
        "completedDays": result.get("completedDays", []),
        "shouldMintDay": result.get("shouldMintDay", False),
        "mintableDayIndex": result.get("mintableDayIndex"),
        "shouldComposeFinal": result.get("shouldComposeFinal", False),
        "finalMinted": result.get("finalMinted", progress.final_minted),
        "finalSbtTxHash": progress.final_sbt_tx_hash,
        "milestones": milestones,
        "startDateKey": progress.start_date_key,
    }


@router.get("/metadata/{token_id}.json", response_model=MetadataResponse)
def metadata(token_id: str, session: Session = Depends(get_session)):
    try:
        token_int = _parse_token_id(token_id)
    except Exception:
        _http_error(400, "INVALID_ARGUMENT", "invalid tokenId")

    users = session.exec(select(UserProgress)).all()
    for user in users:
        if _token_id_for_final(user.address) == token_int:
            return {
                "name": "Alive28 - Final",
                "description": "Alive28 final soulbound badge for completing 28 days.",
                "image": "https://YOUR_DOMAIN/static/final.png",
                "attributes": [
                    {"trait_type": "Type", "value": "FinalSBT"},
                    {"trait_type": "Days", "value": 28},
                    {"trait_type": "Challenge", "value": "Alive28"},
                ],
            }

    logs = session.exec(select(DailyLog)).all()
    for log in logs:
        if _token_id_for_day(log.address, log.day_index) == token_int:
            return {
                "name": f"Alive28 - Day {log.day_index}",
                "description": "Alive28 daily check-in soulbound badge.",
                "image": "https://YOUR_DOMAIN/static/day.png",
                "attributes": [
                    {"trait_type": "Type", "value": "DaySBT"},
                    {"trait_type": "DayIndex", "value": log.day_index},
                    {"trait_type": "Challenge", "value": "Alive28"},
                ],
            }

    return {
        "name": f"Alive28 - Badge {token_id}",
        "description": "Alive28 soulbound badge.",
        "image": "https://YOUR_DOMAIN/static/day.png",
        "attributes": [
            {"trait_type": "Type", "value": "DaySBT"},
            {"trait_type": "DayIndex", "value": 0},
            {"trait_type": "Challenge", "value": "Alive28"},
        ],
    }


@router.get("/report", response_model=ReportResponse)
async def report(address: str, range: str, session: Session = Depends(get_session)):
    address = _require_address(address)
    if range not in ("week", "final"):
        _http_error(400, "INVALID_ARGUMENT", "range must be week or final")

    flow = "report_week" if range == "week" else "report_final"
    state = {
        "db": session,
        "flow": flow,
        "address": address,
        "challengeId": settings.challenge_id,
    }
    result = await _invoke_graph(state)

    recent_logs = result.get("recentLogs", [])
    if recent_logs and isinstance(recent_logs[0], DailyLog):
        recent_logs = [_log_to_response(l) for l in recent_logs]
    elif recent_logs:
        recent_logs = [_log_to_response(l) if isinstance(l, DailyLog) else l for l in recent_logs]

    return {
        "title": result.get("title", "周报（模拟）" if range == "week" else "结营报告（模拟）"),
        "reportText": result.get("reportText", ""),
        "recentLogs": recent_logs,
        "chartByDay": result.get("chartByDay", []),
        "range": range,
    }
