import uuid

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import keccak
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from backend.app.config import settings
from backend.app.database import get_session
from backend.app.main import app
from backend.app.models import DailyLog, UserProgress
from backend.app.services.chain import VerifiedReceipt, get_chain_verifier


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


def _seed_days(engine, address: str, count: int) -> None:
    with Session(engine) as session:
        session.add(
            UserProgress(
                address=address,
                timezone="Asia/Shanghai",
                challenge_id=settings.challenge_id,
                start_date_key="2026-06-01",
                streak=count,
                last_date_key=f"2026-06-{count:02d}",
                last_day_index=count,
                milestones={"1": None, "2": None, "3": None},
            )
        )
        for day in range(1, count + 1):
            session.add(
                DailyLog(
                    id=str(uuid.uuid4()),
                    address=address,
                    challenge_id=settings.challenge_id,
                    day_index=day,
                    date_key=f"2026-06-{day:02d}",
                    normalized_text=f"day {day}",
                    reflection={"note": "note", "next": "next"},
                    salt_hex=f"0x{day:02x}",
                    proof_hash="0x" + f"{day:02x}" * 32,
                    status="SUBMITTED",
                )
            )
        session.commit()


def test_milestone_prepare_and_confirm_use_one_canonical_token_id(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    account = Account.create()
    address = account.address.lower()
    expected_token_id = int.from_bytes(
        keccak(bytes.fromhex(address[2:]) + bytes([1])),
        "big",
    )

    class AcceptingVerifier:
        def verify_milestone_mint(self, **kwargs):
            assert kwargs["address"] == address
            assert kwargs["token_id"] == expected_token_id
            return VerifiedReceipt(block_number=777)

    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(
        settings,
        "milestone_nft_address",
        "0x7777777777777777777777777777777777777777",
    )
    monkeypatch.setattr(
        settings,
        "milestone_base_uri",
        "https://api.alive28.test/metadata/",
    )
    app.dependency_overrides[get_session] = get_test_session
    app.dependency_overrides[get_chain_verifier] = lambda: AcceptingVerifier()
    _seed_days(engine, address, 7)
    client = TestClient(app)

    try:
        headers = _authenticate(client, account)
        first = client.post(
            "/milestone/prepare",
            headers=headers,
            json={"address": address, "milestoneId": 1},
        )
        assert first.status_code == 200
        preparation = first.json()
        assert preparation == {
            "milestoneId": 1,
            "requiredDays": 7,
            "completedDays": 7,
            "tokenId": str(expected_token_id),
            "tokenUri": (
                f"https://api.alive28.test/metadata/{expected_token_id}.json"
            ),
        }

        second = client.post(
            "/milestone/prepare",
            headers=headers,
            json={"address": address, "milestoneId": 1},
        )
        assert second.json() == preparation

        confirmed = client.post(
            "/milestone/mint",
            headers=headers,
            json={
                "address": address,
                "milestoneId": 1,
                "txHash": "0x" + "ab" * 32,
                "chainId": settings.chain_id,
                "contractAddress": settings.milestone_nft_address,
            },
        )
        assert confirmed.status_code == 200
        assert confirmed.json()["milestones"]["1"] == "0x" + "ab" * 32
    finally:
        app.dependency_overrides.clear()


def test_milestone_prepare_rejects_ineligible_user(monkeypatch):
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
    _seed_days(engine, address, 6)
    client = TestClient(app)

    try:
        headers = _authenticate(client, account)
        response = client.post(
            "/milestone/prepare",
            headers=headers,
            json={"address": address, "milestoneId": 1},
        )
        assert response.status_code == 400
        error = response.json()["detail"]["error"]
        assert error["code"] == "NEED_MORE_DAYS"
        assert error["details"] == {"required": 7, "completed": 6}
    finally:
        app.dependency_overrides.clear()
