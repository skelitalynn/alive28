import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from backend.app.models import DailyLog
from backend.app.services.crypto import compute_proof_hash
from backend.app.services.time import diff_days
import uuid


def test_proof_hash_deterministic():
    date_key = "2026-01-29"
    normalized = "hello"
    salt = "0xabc123"
    h1 = compute_proof_hash(date_key, normalized, salt)
    h2 = compute_proof_hash(date_key, normalized, salt)
    assert h1 == h2
    assert h1.startswith("0x") and len(h1) == 66


def test_day_index_calc():
    assert diff_days("2026-01-01", "2026-01-01") + 1 == 1
    assert diff_days("2026-01-01", "2026-01-02") + 1 == 2


def test_dailylog_idempotent_unique():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        log = DailyLog(
            id=str(uuid.uuid4()),
            address="0xabc",
            challenge_id=1,
            day_index=1,
            date_key="2026-01-29",
            reflection={"note": "n", "next": "x"},
            salt_hex="0x1",
            proof_hash="0x" + "0" * 64,
            status="CREATED",
        )
        session.add(log)
        session.commit()

        dup = DailyLog(
            id=str(uuid.uuid4()),
            address="0xabc",
            challenge_id=1,
            day_index=1,
            date_key="2026-01-29",
            reflection={"note": "n", "next": "x"},
            salt_hex="0x2",
            proof_hash="0x" + "1" * 64,
            status="CREATED",
        )
        session.add(dup)
        with pytest.raises(Exception):
            session.commit()
