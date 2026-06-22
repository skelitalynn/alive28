from __future__ import annotations

from datetime import datetime, timedelta, timezone

from pydantic import BaseModel
from sqlalchemy import or_
from sqlmodel import Session, select

from ..config import settings
from ..models import (
    GraphCheckpoint,
    ProofApproval,
    WalletChallenge,
    WalletSession,
)


class CleanupResult(BaseModel):
    walletChallenges: int
    walletSessions: int
    proofApprovals: int
    graphCheckpoints: int
    total: int
    dryRun: bool


def _unix_timestamp(value: datetime) -> int:
    normalized = (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )
    return int(normalized.timestamp())


def cleanup_ephemeral_records(
    session: Session,
    *,
    now: datetime | None = None,
    completed_checkpoint_retention_seconds: int | None = None,
    incomplete_checkpoint_retention_seconds: int | None = None,
    dry_run: bool = False,
) -> CleanupResult:
    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    completed_retention = (
        settings.checkpoint_completed_retention_seconds
        if completed_checkpoint_retention_seconds is None
        else completed_checkpoint_retention_seconds
    )
    incomplete_retention = (
        settings.checkpoint_incomplete_retention_seconds
        if incomplete_checkpoint_retention_seconds is None
        else incomplete_checkpoint_retention_seconds
    )
    if completed_retention < 0 or incomplete_retention < 0:
        raise ValueError("checkpoint retention seconds cannot be negative")

    challenges = session.exec(
        select(WalletChallenge).where(WalletChallenge.expires_at <= now)
    ).all()
    sessions = session.exec(
        select(WalletSession).where(
            or_(
                WalletSession.expires_at <= now,
                WalletSession.revoked_at.is_not(None),
            )
        )
    ).all()
    approvals = session.exec(
        select(ProofApproval).where(
            ProofApproval.used_at.is_(None),
            ProofApproval.deadline < _unix_timestamp(now),
        )
    ).all()

    completed_cutoff = now - timedelta(seconds=completed_retention)
    incomplete_cutoff = now - timedelta(seconds=incomplete_retention)
    checkpoints = session.exec(select(GraphCheckpoint)).all()
    expired_checkpoints = []
    for checkpoint in checkpoints:
        metadata = checkpoint.checkpoint_metadata or {}
        is_completed = metadata.get("status") == "completed"
        cutoff = completed_cutoff if is_completed else incomplete_cutoff
        if checkpoint.created_at <= cutoff:
            expired_checkpoints.append(checkpoint)

    result = CleanupResult(
        walletChallenges=len(challenges),
        walletSessions=len(sessions),
        proofApprovals=len(approvals),
        graphCheckpoints=len(expired_checkpoints),
        total=(
            len(challenges)
            + len(sessions)
            + len(approvals)
            + len(expired_checkpoints)
        ),
        dryRun=dry_run,
    )
    if dry_run:
        return result

    try:
        for row in [
            *challenges,
            *sessions,
            *approvals,
            *expired_checkpoints,
        ]:
            session.delete(row)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return result
