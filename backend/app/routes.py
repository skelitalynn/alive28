from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime

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
)
from .models import UserProgress, DailyLog
from .services.tasks import get_task_by_day_index
from .services.time import date_key_for_timezone, diff_days
from .graph.agent import create_agent
import json

router = APIRouter()


def _lower_address(addr: str) -> str:
    return addr.strip().lower()


def _require_address(addr: str) -> str:
    if not addr or not addr.startswith("0x") or len(addr) != 42:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_ARGUMENT", "message": "invalid address", "details": {}}})
    return _lower_address(addr)


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "version": settings.version}


@router.get("/dailyPrompt", response_model=DailyPromptResponse)
def daily_prompt(dayIndex: int, timezone: str = settings.default_timezone):
    if dayIndex < 1 or dayIndex > 28:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_ARGUMENT", "message": "dayIndex must be between 1 and 28", "details": {}}})
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
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "user not found", "details": {}}})
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
            badges_minted={"7": False, "14": False, "28": False},
        )
    else:
        user.display_name = payload.displayName
        user.avatar_url = payload.avatarUrl
        # timezone is fixed once challenge starts (MVP)
    user.updated_at = datetime.utcnow()
    session.add(user)
    session.commit()
    return {"ok": True}


@router.post("/checkin", response_model=CheckinResponse)
async def checkin(payload: CheckinRequest, session: Session = Depends(get_session)):
    address = _require_address(payload.address)
    timezone = payload.timezone or settings.default_timezone
    date_key = date_key_for_timezone(timezone)
    if not payload.text and not payload.imageUrl:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_ARGUMENT", "message": "text or imageUrl required", "details": {}}})

    existing_log = session.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == settings.challenge_id,
            DailyLog.date_key == date_key,
        )
    ).first()

    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if not progress:
        progress = UserProgress(
            address=address,
            timezone=timezone,
            challenge_id=settings.challenge_id,
            start_date_key=date_key,
            streak=0,
            badges_minted={"7": False, "14": False, "28": False},
        )
        session.add(progress)
        session.commit()

    day_index = diff_days(progress.start_date_key, date_key) + 1
    if day_index < 1:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_ARGUMENT", "message": "dayIndex must be >= 1", "details": {}}})
    if day_index > 28:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_ARGUMENT", "message": "challenge completed", "details": {}}})

    if existing_log:
        return {
            "logId": existing_log.id,
            "challengeId": existing_log.challenge_id,
            "dateKey": existing_log.date_key,
            "dayIndex": existing_log.day_index,
            "reflection": existing_log.reflection,
            "proofHash": existing_log.proof_hash,
            "streak": progress.streak,
            "milestoneEligible": 28 if progress.streak >= 28 else 14 if progress.streak >= 14 else 7 if progress.streak >= 7 else 0,
            "alreadyCheckedIn": True,
        }

    agent = create_agent()
    graph_state = {
        "db": session,
        "flow": "checkin",
        "address": address,
        "timezone": timezone,
        "challengeId": settings.challenge_id,
        "dateKey": date_key,
        "dayIndex": day_index,
        "text": payload.text,
        "imageUrl": payload.imageUrl,
    }
    # GraphAgent in spoon_ai.agents.graph_agent takes initial_state via instance field
    agent.initial_state = graph_state
    output = await agent.run()
    data = json.loads(output)
    return data


@router.post("/tx/confirm", response_model=TxConfirmResponse)
async def tx_confirm(payload: TxConfirmRequest, session: Session = Depends(get_session)):
    address = _require_address(payload.address)
    log = session.exec(select(DailyLog).where(DailyLog.id == payload.logId)).first()
    if not log:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "logId not found", "details": {}}})
    if log.tx_hash:
        raise HTTPException(status_code=409, detail={"error": {"code": "CONFLICT", "message": "txHash already set", "details": {}}})
    agent = create_agent()
    agent.initial_state = {
        "db": session,
        "flow": "tx_confirm",
        "address": address,
        "logId": payload.logId,
        "txHash": payload.txHash,
        "chainId": payload.chainId,
        "contractAddress": payload.contractAddress,
    }
    await agent.run()
    return {"ok": True}


@router.get("/progress", response_model=ProgressResponse)
def progress(address: str, challengeId: int = settings.challenge_id, session: Session = Depends(get_session)):
    address = _require_address(address)
    progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
    if not progress:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "user not found", "details": {}}})

    logs = session.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == challengeId,
        )
    ).all()
    completed_days = [l.day_index for l in logs]
    today_key = date_key_for_timezone(progress.timezone)
    today_checked = any(l.date_key == today_key for l in logs)

    return {
        "address": progress.address,
        "challengeId": challengeId,
        "timezone": progress.timezone,
        "streak": progress.streak,
        "lastDateKey": progress.last_date_key,
        "todayCheckedIn": today_checked,
        "completedDays": completed_days,
        "milestonesEligible": {
            "eligible7": progress.streak >= 7,
            "eligible14": progress.streak >= 14,
            "eligible28": progress.streak >= 28,
        },
        "badgesMinted": {
            "minted7": bool(progress.badges_minted.get("7")) if progress.badges_minted else False,
            "minted14": bool(progress.badges_minted.get("14")) if progress.badges_minted else False,
            "minted28": bool(progress.badges_minted.get("28")) if progress.badges_minted else False,
        },
    }


@router.get("/report", response_model=ReportResponse)
async def report(address: str, range: str, challengeId: int = settings.challenge_id, session: Session = Depends(get_session)):
    address = _require_address(address)
    if range not in ("week", "final"):
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_ARGUMENT", "message": "range must be week or final", "details": {}}})
    flow = "report_week" if range == "week" else "report_final"
    agent = create_agent()
    agent.initial_state = {
        "db": session,
        "flow": flow,
        "address": address,
        "challengeId": challengeId,
    }
    output = await agent.run()
    data = json.loads(output)
    return data
