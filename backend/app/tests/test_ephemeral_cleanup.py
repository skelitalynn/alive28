import uuid
from datetime import datetime, timedelta

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from backend.app.models import (
    DailyLog,
    GraphCheckpoint,
    ProofApproval,
    WalletChallenge,
    WalletSession,
)
from backend.app.services.cleanup import cleanup_ephemeral_records


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _checkpoint(
    *,
    thread_id: str,
    status: str,
    created_at: datetime,
) -> GraphCheckpoint:
    return GraphCheckpoint(
        thread_id=thread_id,
        checkpoint_id=str(uuid.uuid4()),
        state_values={"address": "0x" + "11" * 20},
        next_nodes=[] if status == "completed" else ["Reflection"],
        config_data={"configurable": {"thread_id": thread_id}},
        checkpoint_metadata={"status": status},
        created_at=created_at,
    )


def test_cleanup_dry_run_reports_candidates_without_mutating_data():
    engine = _engine()
    now = datetime(2026, 6, 22, 12, 0, 0)
    with Session(engine) as session:
        session.add(
            WalletChallenge(
                id=str(uuid.uuid4()),
                address="0x" + "11" * 20,
                nonce="expired",
                message="expired",
                expires_at=now - timedelta(seconds=1),
                created_at=now - timedelta(minutes=10),
            )
        )
        session.add(
            WalletSession(
                id=str(uuid.uuid4()),
                address="0x" + "11" * 20,
                token_hash="a" * 64,
                expires_at=now - timedelta(seconds=1),
                created_at=now - timedelta(days=2),
            )
        )
        session.add(
            ProofApproval(
                id=str(uuid.uuid4()),
                approval_id="0x" + "12" * 32,
                log_id=str(uuid.uuid4()),
                address="0x" + "11" * 20,
                day_index=1,
                proof_hash="0x" + "13" * 32,
                deadline=int(now.timestamp()) - 1,
                signature="0x" + "14" * 65,
                created_at=now - timedelta(hours=1),
            )
        )
        session.add(
            _checkpoint(
                thread_id="old-completed",
                status="completed",
                created_at=now - timedelta(days=8),
            )
        )
        session.commit()

        result = cleanup_ephemeral_records(
            session,
            now=now,
            completed_checkpoint_retention_seconds=7 * 86400,
            incomplete_checkpoint_retention_seconds=30 * 86400,
            dry_run=True,
        )

        assert result.model_dump() == {
            "walletChallenges": 1,
            "walletSessions": 1,
            "proofApprovals": 1,
            "graphCheckpoints": 1,
            "total": 4,
            "dryRun": True,
        }
        assert len(session.exec(select(WalletChallenge)).all()) == 1
        assert len(session.exec(select(WalletSession)).all()) == 1
        assert len(session.exec(select(ProofApproval)).all()) == 1
        assert len(session.exec(select(GraphCheckpoint)).all()) == 1


def test_cleanup_preserves_active_and_audit_records_and_is_idempotent():
    engine = _engine()
    now = datetime(2026, 6, 22, 12, 0, 0)
    address = "0x" + "22" * 20
    log = DailyLog(
        id=str(uuid.uuid4()),
        address=address,
        challenge_id=1,
        day_index=1,
        date_key="2026-06-22",
        normalized_text="kept business record",
        reflection={"note": "note", "next": "next"},
        salt_hex="0x01",
        proof_hash="0x" + "20" * 32,
        status="SUBMITTED",
    )
    with Session(engine) as session:
        session.add(log)
        session.add_all(
            [
                WalletChallenge(
                    id=str(uuid.uuid4()),
                    address=address,
                    nonce="expired",
                    message="expired",
                    expires_at=now - timedelta(seconds=1),
                    created_at=now - timedelta(minutes=10),
                ),
                WalletChallenge(
                    id=str(uuid.uuid4()),
                    address=address,
                    nonce="active",
                    message="active",
                    expires_at=now + timedelta(minutes=5),
                    created_at=now,
                ),
                WalletSession(
                    id=str(uuid.uuid4()),
                    address=address,
                    token_hash="b" * 64,
                    expires_at=now + timedelta(days=1),
                    revoked_at=now - timedelta(seconds=1),
                    created_at=now - timedelta(days=1),
                ),
                WalletSession(
                    id=str(uuid.uuid4()),
                    address=address,
                    token_hash="c" * 64,
                    expires_at=now + timedelta(days=1),
                    created_at=now,
                ),
                ProofApproval(
                    id=str(uuid.uuid4()),
                    approval_id="0x" + "21" * 32,
                    log_id=log.id,
                    address=address,
                    day_index=1,
                    proof_hash=log.proof_hash,
                    deadline=int(now.timestamp()) - 1,
                    signature="0x" + "22" * 65,
                    created_at=now - timedelta(hours=1),
                ),
                ProofApproval(
                    id=str(uuid.uuid4()),
                    approval_id="0x" + "23" * 32,
                    log_id=log.id,
                    address=address,
                    day_index=1,
                    proof_hash=log.proof_hash,
                    deadline=int(now.timestamp()) - 1,
                    signature="0x" + "24" * 65,
                    tx_hash="0x" + "25" * 32,
                    used_at=now - timedelta(minutes=30),
                    created_at=now - timedelta(hours=1),
                ),
                _checkpoint(
                    thread_id="old-completed",
                    status="completed",
                    created_at=now - timedelta(days=8),
                ),
                _checkpoint(
                    thread_id="recent-completed",
                    status="completed",
                    created_at=now - timedelta(days=6),
                ),
                _checkpoint(
                    thread_id="old-incomplete",
                    status="failed",
                    created_at=now - timedelta(days=31),
                ),
                _checkpoint(
                    thread_id="recent-incomplete",
                    status="failed",
                    created_at=now - timedelta(days=29),
                ),
            ]
        )
        session.commit()

        result = cleanup_ephemeral_records(
            session,
            now=now,
            completed_checkpoint_retention_seconds=7 * 86400,
            incomplete_checkpoint_retention_seconds=30 * 86400,
        )

        assert result.walletChallenges == 1
        assert result.walletSessions == 1
        assert result.proofApprovals == 1
        assert result.graphCheckpoints == 2
        assert result.total == 5
        assert result.dryRun is False

        assert [row.nonce for row in session.exec(select(WalletChallenge)).all()] == [
            "active"
        ]
        assert [row.token_hash for row in session.exec(select(WalletSession)).all()] == [
            "c" * 64
        ]
        approvals = session.exec(select(ProofApproval)).all()
        assert len(approvals) == 1
        assert approvals[0].used_at is not None
        checkpoints = session.exec(select(GraphCheckpoint)).all()
        assert {row.thread_id for row in checkpoints} == {
            "recent-completed",
            "recent-incomplete",
        }
        assert session.get(DailyLog, log.id) is not None

        second = cleanup_ephemeral_records(
            session,
            now=now,
            completed_checkpoint_retention_seconds=7 * 86400,
            incomplete_checkpoint_retention_seconds=30 * 86400,
        )
        assert second.total == 0
