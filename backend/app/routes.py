from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select
from datetime import datetime
import os
import json
import hashlib
import time
import uuid
from typing import Dict, Any, Optional

from eth_utils import keccak

from .database import get_session
from .config import settings
from .schemas import (
    HealthResponse,
    AuthNonceRequest,
    AuthNonceResponse,
    AuthVerifyRequest,
    AuthVerifyResponse,
    DailyPromptResponse,
    UserResponse,
    UserUpdateRequest,
    CheckinRequest,
    CheckinResponse,
    TxConfirmRequest,
    TxConfirmResponse,
    ProofApprovalRequest,
    ProofApprovalResponse,
    ProofCompensationRequest,
    ProofCompensationResponse,
    NftConfirmRequest,
    NftConfirmResponse,
    ProgressResponse,
    ReportResponse,
    MetadataResponse,
    DailySnapshotResponse,
    HomeSnapshotResponse,
    MilestoneMintRequest,
    MilestoneMintResponse,
    AiReflectionRequest,
    AiReflectionResponse,
    GenerateNftRequest,
    GenerateNftResponse,
)
from .models import (
    UserProgress,
    DailyLog,
    ProofApproval,
    ProofCompensation,
)
from .services.tasks import get_task_by_day_index
from .services.time import date_key_for_timezone, diff_days, date_key_for_day_index
from .graph.agent import create_agent
from .services.reflection import PROMPT_VERSION, generate_reflection
from .services.checkpoint import SQLiteGraphCheckpointer
from .services.nft_image import generate_nft_image
from .services.auth import (
    AuthenticationError,
    authenticate_bearer_token,
    create_wallet_challenge,
    verify_wallet_signature,
)
from .services.chain import (
    ChainVerificationError,
    ChainVerifier,
    get_chain_verifier,
)
from .services.proof_approval import (
    ProofApprovalError,
    create_or_get_approval,
    eligible_streak,
    effective_proof_hash,
    invalidate_pending_approvals,
    is_log_eligible,
)
from spoon_ai.graph.types import Command, StateSnapshot

router = APIRouter()


def _http_error(status: int, code: str, message: str, details: Optional[dict] = None):
    raise HTTPException(status_code=status, detail={"error": {"code": code, "message": message, "details": details or {}}})


def _lower_address(addr: str) -> str:
    return addr.strip().lower()


def _require_address(addr: str) -> str:
    if not addr or not addr.startswith("0x") or len(addr) != 42:
        _http_error(400, "INVALID_ARGUMENT", "invalid address")
    return _lower_address(addr)


def _authorize_address(
    address: str,
    authorization: str | None,
    session: Session,
) -> None:
    if settings.demo_mode:
        return
    try:
        authenticated_address = authenticate_bearer_token(
            session,
            authorization,
        )
    except AuthenticationError as exc:
        _http_error(401, "AUTH_REQUIRED", str(exc))
    if authenticated_address != address:
        _http_error(
            403,
            "ADDRESS_FORBIDDEN",
            "wallet session is bound to a different address",
        )


def _authorize_session(
    authorization: str | None,
    session: Session,
) -> Optional[str]:
    if settings.demo_mode:
        return None
    try:
        return authenticate_bearer_token(session, authorization)
    except AuthenticationError as exc:
        _http_error(401, "AUTH_REQUIRED", str(exc))


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
        "proofStatus": log.proof_status,
        "effectiveProofHash": effective_proof_hash(log),
        "status": log.status,
        "txHash": log.tx_hash,
        "dayNftTxHash": log.day_nft_tx_hash,
        "createdAt": log.created_at.isoformat() + "Z",
    }


def _token_id_for_milestone(address: str, milestone_id: int) -> int:
    addr_bytes = bytes.fromhex(address[2:])
    packed = addr_bytes + bytes([milestone_id])
    return int.from_bytes(keccak(packed), "big")


def _parse_token_id(token_id: str) -> int:
    token_id = token_id.strip()
    if token_id.startswith("0x"):
        return int(token_id, 16)
    return int(token_id)


def _default_checkin_id(
    address: str,
    challenge_id: int,
    date_key: str,
    day_index: int,
    request_fingerprint: str,
) -> str:
    identity = (
        f"alive28:{challenge_id}:{address}:{date_key}:{day_index}:"
        f"{request_fingerprint}"
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, identity))


def _request_fingerprint(
    address: str,
    challenge_id: int,
    date_key: str,
    day_index: int,
    text: str | None,
    image_url: str | None,
) -> str:
    payload = json.dumps(
        {
            "address": address,
            "challengeId": challenge_id,
            "dateKey": date_key,
            "dayIndex": day_index,
            "text": text,
            "imageUrl": image_url,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _checkin_execution(result: Dict[str, Any]) -> Dict[str, Any]:
    last_error = result.get("lastError")
    public_error = None
    if isinstance(last_error, dict):
        public_error = {
            "node": last_error.get("node", "unknown"),
            "type": last_error.get("type", "ExecutionError"),
            "message": "node execution failed",
        }
    return {
        "promptVersion": result.get("promptVersion", PROMPT_VERSION),
        "modelProvider": result.get("modelProvider", settings.llm_provider),
        "modelName": result.get("modelName", settings.llm_model),
        "modelAttempts": int(result.get("modelAttempts") or 0),
        "repairAttempts": int(result.get("repairAttempts") or 0),
        "fallbackReason": result.get("fallbackReason"),
        "nodeDurationsMs": result.get("nodeDurationsMs") or {},
        "nodeAttempts": result.get("nodeAttempts") or {},
        "lastError": public_error,
    }


def _require_proof_hash(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if (
        not normalized.startswith("0x")
        or len(normalized) != 66
        or any(char not in "0123456789abcdef" for char in normalized[2:])
    ):
        _http_error(400, "INVALID_ARGUMENT", "invalid bytes32 proof hash")
    return normalized


def _compact_completed_state(result: Dict[str, Any]) -> Dict[str, Any]:
    compact = dict(result)
    for sensitive_or_transient in (
        "db",
        "text",
        "normalizedText",
        "imageUrl",
        "imageDesc",
        "rawReflection",
        "saltHex",
        "inputHash",
        "proofHash",
        "task",
    ):
        compact.pop(sensitive_or_transient, None)
    return compact


async def _invoke_graph(
    state: Dict[str, Any],
    *,
    checkpointer: SQLiteGraphCheckpointer | None = None,
    thread_id: str | None = None,
    resume: bool = False,
):
    agent = create_agent(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
    initial_state: Dict[str, Any] | Command = state
    if resume:
        initial_state = Command(resume={"db": state["db"], "recovered": True})
    try:
        result = await agent.graph.invoke(initial_state, config=config)
    except Exception as exc:
        if checkpointer and thread_id:
            latest = checkpointer.get_checkpoint(thread_id)
            if latest:
                failed_node = getattr(exc, "node", None)
                if not failed_node and latest.next:
                    failed_node = latest.next[0]
                values = dict(latest.values)
                attempts = dict(values.get("nodeAttempts") or {})
                if failed_node:
                    attempts[failed_node] = int(attempts.get(failed_node, 0)) + 1
                root_error = exc
                while root_error.__cause__ is not None:
                    root_error = root_error.__cause__
                values["nodeAttempts"] = attempts
                values["lastError"] = {
                    "node": failed_node or "unknown",
                    "type": type(root_error).__name__,
                    "message": str(root_error)[:300],
                }
                checkpointer.save_checkpoint(
                    thread_id,
                    StateSnapshot(
                        values=values,
                        next=(failed_node,) if failed_node else latest.next,
                        config=config,
                        metadata={
                            "status": "failed",
                            "node": failed_node,
                        },
                        created_at=datetime.utcnow(),
                    ),
                )
        raise
    if checkpointer and thread_id:
        checkpointer.clear_thread(thread_id)
        checkpointer.save_checkpoint(
            thread_id,
            StateSnapshot(
                values=_compact_completed_state(result),
                next=(),
                config=config,
                metadata={"status": "completed", "node": None},
                created_at=datetime.utcnow(),
            ),
        )
    return result


@router.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "version": settings.version, "demo_mode": settings.demo_mode}


@router.post("/auth/nonce", response_model=AuthNonceResponse)
def auth_nonce(
    payload: AuthNonceRequest,
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    challenge = create_wallet_challenge(session, address)
    return {
        "message": challenge.message,
        "expiresAt": challenge.expires_at.isoformat() + "Z",
    }


@router.post("/auth/verify", response_model=AuthVerifyResponse)
def auth_verify(
    payload: AuthVerifyRequest,
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    try:
        token, wallet_session = verify_wallet_signature(
            session,
            address,
            payload.signature,
        )
    except AuthenticationError as exc:
        _http_error(401, "INVALID_SIGNATURE", str(exc))
    return {
        "token": token,
        "address": address,
        "expiresAt": wallet_session.expires_at.isoformat() + "Z",
    }


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
def get_user(
    address: str,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(address)
    _authorize_address(address, authorization, session)
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
def update_user(
    payload: UserUpdateRequest,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    _authorize_address(address, authorization, session)
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
def home_snapshot(
    address: str,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(address)
    _authorize_address(address, authorization, session)
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
def daily_snapshot(
    address: str,
    dayIndex: int,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(address)
    _authorize_address(address, authorization, session)
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
async def checkin(
    payload: CheckinRequest,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    _authorize_address(address, authorization, session)
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

    request_fingerprint = _request_fingerprint(
        address,
        settings.challenge_id,
        date_key,
        payload.dayIndex,
        payload.text,
        payload.imageUrl,
    )
    checkin_id = payload.checkinId or _default_checkin_id(
        address,
        settings.challenge_id,
        date_key,
        payload.dayIndex,
        request_fingerprint,
    )
    checkpointer = SQLiteGraphCheckpointer(session.get_bind())
    latest_checkpoint = checkpointer.get_checkpoint(checkin_id)
    completed_replay = bool(
        latest_checkpoint
        and latest_checkpoint.metadata.get("status") == "completed"
    )
    resume = bool(latest_checkpoint and not completed_replay)

    if latest_checkpoint:
        previous = latest_checkpoint.values
        same_identity = (
            previous.get("address") == address
            and previous.get("challengeId") == settings.challenge_id
            and previous.get("dateKey") == date_key
            and previous.get("dayIndex") == payload.dayIndex
        )
        if (
            not same_identity
            or previous.get("requestFingerprint") != request_fingerprint
        ):
            _http_error(
                409,
                "CHECKIN_ID_CONFLICT",
                "checkinId is already bound to a different request",
            )

    state = {
        "db": session,
        "flow": "checkin",
        "checkinId": checkin_id,
        "requestFingerprint": request_fingerprint,
        "recovered": False,
        "nodeDurationsMs": {},
        "nodeAttempts": {},
        "lastError": None,
        "promptVersion": PROMPT_VERSION,
        "modelProvider": settings.llm_provider,
        "modelName": settings.llm_model,
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
    if completed_replay:
        result = latest_checkpoint.values
    else:
        result = await _invoke_graph(
            state,
            checkpointer=checkpointer,
            thread_id=checkin_id,
            resume=resume,
        )
    outcome = result.get("outcome")
    if outcome in ("clarify", "rejected", "crisis_redirected"):
        return {
            "outcome": outcome,
            "log": None,
            "alreadyCheckedIn": False,
            "message": result.get("responseMessage"),
            "reflection": result.get("reflection"),
            "checkinId": checkin_id,
            "recovered": bool(result.get("recovered")),
            "execution": _checkin_execution(result),
        }
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
        "outcome": "already_checked_in"
        if completed_replay or result.get("alreadyCheckedIn")
        else "accepted",
        "log": _log_to_response(log),
        "alreadyCheckedIn": bool(
            completed_replay or result.get("alreadyCheckedIn")
        ),
        "message": None,
        "reflection": None,
        "checkinId": checkin_id,
        "recovered": bool(result.get("recovered")),
        "execution": _checkin_execution(result),
    }


@router.post("/tx/confirm", response_model=TxConfirmResponse)
async def tx_confirm(
    payload: TxConfirmRequest,
    authorization: Optional[str] = Header(default=None),
    verifier: ChainVerifier = Depends(get_chain_verifier),
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    _authorize_address(address, authorization, session)
    log = session.exec(select(DailyLog).where(DailyLog.id == payload.logId)).first()
    if not log:
        _http_error(404, "NOT_FOUND", "logId not found")
    if log.address != address:
        _http_error(403, "ADDRESS_FORBIDDEN", "log belongs to another address")
    if log.tx_hash:
        return {"ok": True}
    if log.proof_status != "ACTIVE":
        _http_error(
            409,
            "PROOF_NOT_ACTIVE",
            "only an active safety-approved proof can be confirmed",
        )
    verified = None
    approval = None
    if not settings.demo_mode:
        if not payload.approvalId:
            _http_error(400, "APPROVAL_REQUIRED", "approvalId is required")
        approval = session.exec(
            select(ProofApproval).where(
                ProofApproval.approval_id == payload.approvalId.lower(),
                ProofApproval.log_id == log.id,
                ProofApproval.address == address,
            )
        ).first()
        if (
            not approval
            or approval.proof_hash != effective_proof_hash(log)
            or approval.used_at is not None
            or approval.invalidated_at is not None
            or approval.deadline < int(time.time())
        ):
            _http_error(
                400,
                "INVALID_APPROVAL",
                "approval is missing, expired, consumed, or invalidated",
            )
        try:
            verified = verifier.verify_proof_submission(
                tx_hash=payload.txHash,
                address=address,
                chain_id=payload.chainId,
                contract_address=payload.contractAddress,
                day_index=log.day_index,
                proof_hash=effective_proof_hash(log),
                approval_id=approval.approval_id,
            )
        except ChainVerificationError as exc:
            _http_error(400, "INVALID_CHAIN_RECEIPT", str(exc))
    state = {
        "db": session,
        "flow": "tx_confirm",
        "address": address,
        "logId": payload.logId,
        "txHash": payload.txHash,
        "chainId": payload.chainId,
        "contractAddress": payload.contractAddress,
        "blockNumber": verified.block_number if verified else None,
        "approvalId": approval.approval_id if approval else None,
    }
    await _invoke_graph(state)
    return {"ok": True}


@router.post("/proof/approval", response_model=ProofApprovalResponse)
def proof_approval(
    payload: ProofApprovalRequest,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    _authorize_address(address, authorization, session)
    log = session.get(DailyLog, payload.logId)
    if not log:
        _http_error(404, "NOT_FOUND", "logId not found")
    if log.address != address:
        _http_error(403, "ADDRESS_FORBIDDEN", "log belongs to another address")
    if log.proof_status != "ACTIVE":
        _http_error(
            409,
            "PROOF_NOT_ACTIVE",
            "only the original active safety-approved proof can be approved",
        )
    if log.tx_hash:
        _http_error(409, "PROOF_ALREADY_SUBMITTED", "proof is already on-chain")
    try:
        approval = create_or_get_approval(session, log)
        session.commit()
        session.refresh(approval)
    except ProofApprovalError as exc:
        session.rollback()
        _http_error(503, "APPROVAL_UNAVAILABLE", str(exc))
    return {
        "approvalId": approval.approval_id,
        "deadline": approval.deadline,
        "signature": approval.signature,
        "proofHash": approval.proof_hash,
    }


@router.post("/proof/compensate", response_model=ProofCompensationResponse)
def compensate_proof(
    payload: ProofCompensationRequest,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    _authorize_address(address, authorization, session)
    log = session.get(DailyLog, payload.logId)
    if not log:
        _http_error(404, "NOT_FOUND", "logId not found")
    if log.address != address:
        _http_error(403, "ADDRESS_FORBIDDEN", "log belongs to another address")

    previous_hash = effective_proof_hash(log)
    replacement_hash = None
    if payload.action == "revoke":
        if log.proof_status == "REVOKED":
            _http_error(409, "PROOF_ALREADY_REVOKED", "proof is already revoked")
        log.proof_status = "REVOKED"
    else:
        if not log.tx_hash:
            _http_error(
                409,
                "PROOF_NOT_SUBMITTED",
                "supersede is a compensation for an already submitted proof",
            )
        replacement_hash = _require_proof_hash(payload.replacementProofHash)
        if replacement_hash == previous_hash:
            _http_error(
                400,
                "INVALID_ARGUMENT",
                "replacement proof must differ from current proof",
            )
        log.proof_status = "SUPERSEDED"
        log.effective_proof_hash = replacement_hash

    audit = ProofCompensation(
        id=str(uuid.uuid4()),
        log_id=log.id,
        address=address,
        action=payload.action.upper(),
        reason=payload.reason.strip(),
        previous_proof_hash=previous_hash,
        replacement_proof_hash=replacement_hash,
    )
    invalidate_pending_approvals(session, log.id)
    session.add(log)
    session.add(audit)
    progress = session.get(UserProgress, address)
    if progress:
        logs = session.exec(
            select(DailyLog).where(
                DailyLog.address == address,
                DailyLog.challenge_id == settings.challenge_id,
            )
        ).all()
        progress.streak = eligible_streak(logs)
        progress.updated_at = datetime.utcnow()
        session.add(progress)
    session.commit()
    session.refresh(audit)
    return {
        "id": audit.id,
        "logId": audit.log_id,
        "action": audit.action,
        "reason": audit.reason,
        "previousProofHash": audit.previous_proof_hash,
        "replacementProofHash": audit.replacement_proof_hash,
        "createdAt": audit.created_at.isoformat() + "Z",
    }


@router.post("/nft/confirm", response_model=NftConfirmResponse)
def nft_confirm(
    payload: NftConfirmRequest,
    authorization: Optional[str] = Header(default=None),
    verifier: ChainVerifier = Depends(get_chain_verifier),
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    _authorize_address(address, authorization, session)
    if payload.type == "DAY":
        if payload.dayIndex is None:
            _http_error(400, "INVALID_ARGUMENT", "dayIndex required for type=DAY")
        log = session.exec(
            select(DailyLog).where(
                DailyLog.address == address,
                DailyLog.challenge_id == settings.challenge_id,
                DailyLog.day_index == payload.dayIndex,
            )
        ).first()
        if not log:
            _http_error(404, "NOT_FOUND", "log not found for dayIndex")
        if not is_log_eligible(log):
            _http_error(409, "PROOF_REVOKED", "revoked proof cannot mint a day NFT")
        if log.day_nft_tx_hash:
            return {"ok": True}
        if not settings.demo_mode:
            try:
                verifier.verify_day_mint(
                    tx_hash=payload.txHash,
                    address=address,
                    chain_id=payload.chainId,
                    contract_address=payload.contractAddress,
                    day_index=payload.dayIndex,
                )
            except ChainVerificationError as exc:
                _http_error(400, "INVALID_CHAIN_RECEIPT", str(exc))
        log.day_nft_tx_hash = payload.txHash
        session.add(log)
        progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
        if progress:
            progress.day_mint_count = (progress.day_mint_count or 0) + 1
            progress.updated_at = datetime.utcnow()
            session.add(progress)
        session.commit()
    elif payload.type == "FINAL":
        progress = session.exec(select(UserProgress).where(UserProgress.address == address)).first()
        if not progress:
            _http_error(404, "NOT_FOUND", "user not found")
        if progress.final_nft_tx_hash:
            return {"ok": True}
        if not settings.demo_mode:
            try:
                verifier.verify_final_mint(
                    tx_hash=payload.txHash,
                    address=address,
                    chain_id=payload.chainId,
                    contract_address=payload.contractAddress,
                )
            except ChainVerificationError as exc:
                _http_error(400, "INVALID_CHAIN_RECEIPT", str(exc))
        progress.final_nft_tx_hash = payload.txHash
        progress.final_minted = True
        progress.updated_at = datetime.utcnow()
        session.add(progress)
        session.commit()
    else:
        _http_error(400, "INVALID_ARGUMENT", "type must be DAY or FINAL")
    return {"ok": True}


@router.post("/milestone/mint", response_model=MilestoneMintResponse)
def milestone_mint(
    payload: MilestoneMintRequest,
    authorization: Optional[str] = Header(default=None),
    verifier: ChainVerifier = Depends(get_chain_verifier),
    session: Session = Depends(get_session),
):
    address = _require_address(payload.address)
    _authorize_address(address, authorization, session)
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
    completed_days = {l.day_index for l in logs if is_log_eligible(l)}
    completed_count = len(completed_days)
    required = 7 if milestone_id == 1 else 14 if milestone_id == 2 else 28

    if completed_count < required:
        _http_error(400, "NEED_MORE_DAYS", f"need {required}", {"required": required, "completed": completed_count})

    if not settings.demo_mode:
        try:
            verifier.verify_milestone_mint(
                tx_hash=payload.txHash,
                address=address,
                chain_id=payload.chainId,
                contract_address=payload.contractAddress,
                token_id=_token_id_for_milestone(address, milestone_id),
            )
        except ChainVerificationError as exc:
            _http_error(400, "INVALID_CHAIN_RECEIPT", str(exc))

    milestones[str(milestone_id)] = payload.txHash
    progress.milestones = milestones
    progress.updated_at = datetime.utcnow()
    session.add(progress)
    session.commit()
    return {"ok": True, "milestones": milestones}


@router.get("/progress", response_model=ProgressResponse)
async def progress(
    address: str,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(address)
    _authorize_address(address, authorization, session)
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

    logs = session.exec(
        select(DailyLog).where(
            DailyLog.address == address,
            DailyLog.challenge_id == settings.challenge_id,
        )
    ).all()
    eligible_logs = [log for log in logs if is_log_eligible(log)]
    day_mint_count = sum(
        1 for log in eligible_logs if getattr(log, "day_nft_tx_hash", None)
    )
    mintable_day_index = None
    for d in range(1, 29):
        log_d = next((l for l in eligible_logs if l.day_index == d), None)
        if log_d and log_d.tx_hash and not getattr(log_d, "day_nft_tx_hash", None):
            mintable_day_index = d
            break
    should_mint_day = mintable_day_index is not None
    should_compose_final = (day_mint_count == 28) and not (progress.final_minted or progress.final_nft_tx_hash)

    return {
        "dateKey": result.get("dateKey") or date_key_for_timezone(progress.timezone),
        "streak": result.get("streak", progress.streak or 0),
        "dayMintCount": day_mint_count,
        "completedDays": result.get("completedDays", []),
        "shouldMintDay": should_mint_day,
        "mintableDayIndex": mintable_day_index,
        "shouldComposeFinal": should_compose_final,
        "finalMinted": bool(progress.final_minted or progress.final_nft_tx_hash),
        "finalNftTxHash": progress.final_nft_tx_hash,
        "milestones": milestones,
        "startDateKey": progress.start_date_key,
    }


@router.get("/metadata/{token_id}.json", response_model=MetadataResponse)
def metadata(token_id: str, session: Session = Depends(get_session)):
    try:
        token_int = _parse_token_id(token_id)
    except Exception:
        _http_error(400, "INVALID_ARGUMENT", "invalid tokenId")

    def _milestone_meta(milestone_id: int) -> Dict[str, Any]:
        if milestone_id == 1:
            return {
                "name": "Alive28 - Week1",
                "description": "Alive28 milestone NFT for completing 7 days.",
                "image": "https://YOUR_DOMAIN/static/week1.png",
                "attributes": [
                    {"trait_type": "Type", "value": "MilestoneNFT"},
                    {"trait_type": "Milestone", "value": "Week1"},
                    {"trait_type": "Days", "value": 7},
                    {"trait_type": "Challenge", "value": "Alive28"},
                ],
            }
        if milestone_id == 2:
            return {
                "name": "Alive28 - Week2",
                "description": "Alive28 milestone NFT for completing 14 days.",
                "image": "https://YOUR_DOMAIN/static/week2.png",
                "attributes": [
                    {"trait_type": "Type", "value": "MilestoneNFT"},
                    {"trait_type": "Milestone", "value": "Week2"},
                    {"trait_type": "Days", "value": 14},
                    {"trait_type": "Challenge", "value": "Alive28"},
                ],
            }
        return {
            "name": "Alive28 - Final",
            "description": "Alive28 milestone NFT for completing 28 days.",
            "image": "https://YOUR_DOMAIN/static/final.png",
            "attributes": [
                {"trait_type": "Type", "value": "MilestoneNFT"},
                {"trait_type": "Milestone", "value": "Final"},
                {"trait_type": "Days", "value": 28},
                {"trait_type": "Challenge", "value": "Alive28"},
            ],
        }

    users = session.exec(select(UserProgress)).all()
    for user in users:
        milestones = user.milestones or {}
        for milestone_id in (1, 2, 3):
            if milestones.get(str(milestone_id)) and _token_id_for_milestone(user.address, milestone_id) == token_int:
                return _milestone_meta(milestone_id)

    return {
        "name": f"Alive28 - Milestone {token_id}",
        "description": "Alive28 milestone NFT.",
        "image": "https://YOUR_DOMAIN/static/final.png",
        "attributes": [
            {"trait_type": "Type", "value": "MilestoneNFT"},
            {"trait_type": "Milestone", "value": "Unknown"},
            {"trait_type": "Days", "value": 0},
            {"trait_type": "Challenge", "value": "Alive28"},
        ],
    }


@router.post("/ai/reflection", response_model=AiReflectionResponse)
async def ai_reflection(
    payload: AiReflectionRequest,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    _authorize_session(authorization, session)
    if not payload.userText or not payload.task:
        _http_error(400, "INVALID_ARGUMENT", "userText and task are required")
    reflection = await generate_reflection(payload.task.model_dump(), payload.userText)
    return {"reflection": reflection}


@router.post("/ai/generate-nft", response_model=GenerateNftResponse)
def ai_generate_nft(
    payload: GenerateNftRequest,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    _authorize_session(authorization, session)
    if payload.userText is None or payload.dayIndex is None:
        _http_error(400, "INVALID_ARGUMENT", "userText and dayIndex are required")
    image = generate_nft_image(
        day_index=payload.dayIndex,
        task_title=payload.taskTitle or f"Day {payload.dayIndex}",
        user_text=payload.userText,
        reflection_note=payload.reflectionNote or "",
        reflection_next=payload.reflectionNext or "",
        gemini_api_key=os.getenv("GOOGLE_AI_API_KEY", ""),
    )
    return {
        "success": True,
        "image": image,
        "dayIndex": payload.dayIndex,
        "message": f"Day {payload.dayIndex} NFT generated",
    }


@router.get("/report", response_model=ReportResponse)
async def report(
    address: str,
    range: str,
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
):
    address = _require_address(address)
    _authorize_address(address, authorization, session)
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
