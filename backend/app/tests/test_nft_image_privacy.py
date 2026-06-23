import uuid

from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from backend.app.config import settings
from backend.app.database import get_session
from backend.app.main import app
from backend.app.models import DailyLog


def _authenticate(client: TestClient, account) -> dict[str, str]:
    address = account.address.lower()
    challenge = client.post("/auth/nonce", json={"address": address})
    signature = Account.sign_message(
        encode_defunct(text=challenge.json()["message"]),
        account.key,
    ).signature.hex()
    verified = client.post(
        "/auth/verify",
        json={"address": address, "signature": signature},
    )
    return {"Authorization": f"Bearer {verified.json()['token']}"}


def _seed_log(engine, *, address: str, proof_status: str = "ACTIVE") -> DailyLog:
    log = DailyLog(
        id=str(uuid.uuid4()),
        address=address,
        challenge_id=settings.challenge_id,
        day_index=1,
        date_key="2026-06-23",
        normalized_text="PRIVATE_DIARY_SENTINEL 今天发生了不应外发的事情",
        reflection={
            "note": "PRIVATE_REFLECTION_SENTINEL",
            "next": "PRIVATE_NEXT_SENTINEL",
        },
        salt_hex="0xprivate",
        proof_hash="0x" + "12" * 32,
        proof_status=proof_status,
        status="CREATED",
    )
    with Session(engine) as session:
        session.add(log)
        session.commit()
        session.refresh(log)
        session.expunge(log)
    return log


def test_nft_prompt_uses_only_public_task_metadata(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(settings, "demo_mode", False)
    app.dependency_overrides[get_session] = get_test_session
    account = Account.create()
    address = account.address.lower()
    log = _seed_log(engine, address=address)
    captured_prompts: list[str] = []

    def fake_pollinations(prompt: str):
        captured_prompts.append(prompt)
        return "data:image/png;base64,c2FmZQ=="

    monkeypatch.setattr(
        "backend.app.services.nft_image._pollinations_image",
        fake_pollinations,
    )
    client = TestClient(app)

    try:
        unauthenticated = client.post(
            "/ai/generate-nft",
            json={"address": address, "logId": log.id},
        )
        assert unauthenticated.status_code == 401

        headers = _authenticate(client, account)
        response = client.post(
            "/ai/generate-nft",
            headers=headers,
            json={"address": address, "logId": log.id},
        )
        assert response.status_code == 200
        assert response.json()["image"] == "data:image/png;base64,c2FmZQ=="
        assert len(captured_prompts) == 1

        prompt = captured_prompts[0]
        assert "Day 1 of 28" in prompt
        assert "PRIVATE_DIARY_SENTINEL" not in prompt
        assert "PRIVATE_REFLECTION_SENTINEL" not in prompt
        assert "PRIVATE_NEXT_SENTINEL" not in prompt
        assert address not in prompt
        assert log.proof_hash not in prompt

        legacy_prompt_injection = client.post(
            "/ai/generate-nft",
            headers=headers,
            json={
                "address": address,
                "logId": log.id,
                "userText": "CLIENT_SECRET",
            },
        )
        assert legacy_prompt_injection.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_nft_generation_rejects_unowned_and_revoked_logs(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    monkeypatch.setattr(settings, "demo_mode", False)
    app.dependency_overrides[get_session] = get_test_session
    owner = Account.create()
    other = Account.create()
    active_log = _seed_log(engine, address=owner.address.lower())
    revoked_log = _seed_log(
        engine,
        address=other.address.lower(),
        proof_status="REVOKED",
    )
    client = TestClient(app)

    try:
        other_headers = _authenticate(client, other)
        unowned = client.post(
            "/ai/generate-nft",
            headers=other_headers,
            json={"address": other.address.lower(), "logId": active_log.id},
        )
        assert unowned.status_code == 403

        revoked = client.post(
            "/ai/generate-nft",
            headers=other_headers,
            json={"address": other.address.lower(), "logId": revoked_log.id},
        )
        assert revoked.status_code == 409
        assert revoked.json()["detail"]["error"]["code"] == "PROOF_REVOKED"
    finally:
        app.dependency_overrides.clear()
