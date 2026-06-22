from __future__ import annotations

import secrets
import time
import uuid
from datetime import datetime, timezone

from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import keccak
from sqlmodel import Session, select

from ..config import settings
from ..models import DailyLog, ProofApproval


class ProofApprovalError(Exception):
    pass


def effective_proof_hash(log: DailyLog) -> str:
    return log.effective_proof_hash or log.proof_hash


def is_log_eligible(log: DailyLog) -> bool:
    return log.proof_status != "REVOKED"


def eligible_streak(logs: list[DailyLog]) -> int:
    completed_days = {
        log.day_index for log in logs if is_log_eligible(log)
    }
    if not completed_days:
        return 0
    streak = 0
    day = max(completed_days)
    while day in completed_days:
        streak += 1
        day -= 1
    return streak


def _approval_message(
    *,
    address: str,
    day_index: int,
    proof_hash: str,
    deadline: int,
    approval_id: str,
):
    payload_hash = keccak(
        encode(
            [
                "address",
                "uint256",
                "address",
                "uint16",
                "bytes32",
                "uint64",
                "bytes32",
            ],
            [
                settings.proof_registry_address,
                settings.chain_id,
                address,
                day_index,
                bytes.fromhex(proof_hash.removeprefix("0x")),
                deadline,
                bytes.fromhex(approval_id.removeprefix("0x")),
            ],
        )
    )
    return encode_defunct(hexstr=payload_hash.hex())


def create_or_get_approval(
    session: Session,
    log: DailyLog,
    *,
    now: datetime | None = None,
) -> ProofApproval:
    if now is None:
        now_timestamp = int(time.time())
    else:
        timestamp_source = (
            now.replace(tzinfo=timezone.utc)
            if now.tzinfo is None
            else now
        )
        now_timestamp = int(timestamp_source.timestamp())
    proof_hash = effective_proof_hash(log)
    existing = session.exec(
        select(ProofApproval).where(
            ProofApproval.log_id == log.id,
            ProofApproval.proof_hash == proof_hash,
            ProofApproval.used_at.is_(None),
            ProofApproval.invalidated_at.is_(None),
            ProofApproval.deadline >= now_timestamp,
        ).order_by(ProofApproval.created_at.desc())
    ).first()
    if existing:
        return existing

    if not settings.proof_approval_private_key:
        raise ProofApprovalError("PROOF_APPROVAL_PRIVATE_KEY is not configured")
    if (
        settings.proof_registry_address.lower()
        == "0x0000000000000000000000000000000000000000"
    ):
        raise ProofApprovalError("PROOF_REGISTRY_ADDRESS is not configured")

    approval_id = f"0x{secrets.token_hex(32)}"
    deadline = now_timestamp + settings.proof_approval_ttl_seconds
    message = _approval_message(
        address=log.address,
        day_index=log.day_index,
        proof_hash=proof_hash,
        deadline=deadline,
        approval_id=approval_id,
    )
    raw_signature = Account.sign_message(
        message,
        settings.proof_approval_private_key,
    ).signature.hex()
    signature = (
        raw_signature
        if raw_signature.startswith("0x")
        else f"0x{raw_signature}"
    )
    approval = ProofApproval(
        id=str(uuid.uuid4()),
        approval_id=approval_id,
        log_id=log.id,
        address=log.address,
        day_index=log.day_index,
        proof_hash=proof_hash,
        deadline=deadline,
        signature=signature,
    )
    session.add(approval)
    return approval


def invalidate_pending_approvals(
    session: Session,
    log_id: str,
    *,
    now: datetime | None = None,
) -> None:
    invalidated_at = now or datetime.utcnow()
    approvals = session.exec(
        select(ProofApproval).where(
            ProofApproval.log_id == log_id,
            ProofApproval.used_at.is_(None),
            ProofApproval.invalidated_at.is_(None),
        )
    ).all()
    for approval in approvals:
        approval.invalidated_at = invalidated_at
        session.add(approval)
