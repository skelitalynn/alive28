from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from backend.app.config import settings
from backend.app.database import get_session
from backend.app.main import app
from backend.app.models import DailyLog, ProofApproval
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


def test_authenticated_daily_completion_loop_updates_one_log_and_progress(
    monkeypatch,
):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    class AcceptingVerifier:
        def verify_proof_submission(self, **kwargs):
            assert kwargs["address"] == address
            assert kwargs["day_index"] == 1
            assert kwargs["proof_hash"] == proof_hash
            assert kwargs["approval_id"] == approval_id
            return VerifiedReceipt(block_number=101)

        def verify_day_mint(self, **kwargs):
            assert kwargs["address"] == address
            assert kwargs["day_index"] == 1
            return VerifiedReceipt(block_number=102)

    validator = Account.create()
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(
        settings,
        "proof_approval_private_key",
        validator.key.hex(),
    )
    monkeypatch.setattr(
        settings,
        "proof_registry_address",
        "0x9999999999999999999999999999999999999999",
    )
    monkeypatch.setattr(
        settings,
        "restart_badge_address",
        "0x8888888888888888888888888888888888888888",
    )
    app.dependency_overrides[get_session] = get_test_session
    app.dependency_overrides[get_chain_verifier] = lambda: AcceptingVerifier()

    note = (
        "你已经把今天完成的一小步记录得很清楚，这条记录可以进入后续确认流程。"
        "链上操作只确认该日志的哈希与钱包事件，不替代对现实行为的判断。"
        "完成后可以从进度页看到同一条记录的确认状态。"
    )
    next_step = "现在用五分钟整理明天开始时需要的一样东西。"

    async def fake_ask(self, messages, system_msg=None):
        return f'{{"note":"{note}","next":"{next_step}"}}'

    monkeypatch.setattr("backend.app.services.reflection.ChatBot.ask", fake_ask)
    account = Account.create()
    address = account.address.lower()
    proof_hash = ""
    approval_id = ""
    client = TestClient(app)

    try:
        headers = _authenticate(client, account)
        checkin = client.post(
            "/checkin",
            headers=headers,
            json={
                "address": address,
                "dayIndex": 1,
                "timezone": "Asia/Shanghai",
                "text": "今天完成了计划中的第一步，也记录了遇到的阻力。",
            },
        )
        assert checkin.status_code == 200
        log = checkin.json()["log"]
        proof_hash = log["proofHash"]

        approval_response = client.post(
            "/proof/approval",
            headers=headers,
            json={"address": address, "logId": log["id"]},
        )
        assert approval_response.status_code == 200
        approval = approval_response.json()
        approval_id = approval["approvalId"]
        assert approval["dayIndex"] == 1

        proof_tx = "0x" + "ab" * 32
        proof_confirmation = client.post(
            "/tx/confirm",
            headers=headers,
            json={
                "logId": log["id"],
                "address": address,
                "txHash": proof_tx,
                "chainId": settings.chain_id,
                "contractAddress": settings.proof_registry_address,
                "approvalId": approval_id,
            },
        )
        assert proof_confirmation.status_code == 200
        confirmed_log = proof_confirmation.json()["log"]
        assert confirmed_log["id"] == log["id"]
        assert confirmed_log["status"] == "SUBMITTED"
        assert confirmed_log["txHash"] == proof_tx

        day_tx = "0x" + "cd" * 32
        day_confirmation = client.post(
            "/nft/confirm",
            headers=headers,
            json={
                "address": address,
                "type": "DAY",
                "logId": log["id"],
                "txHash": day_tx,
                "chainId": settings.chain_id,
                "contractAddress": settings.restart_badge_address,
            },
        )
        assert day_confirmation.status_code == 200
        completed_log = day_confirmation.json()["log"]
        assert completed_log["id"] == log["id"]
        assert completed_log["dayNftTxHash"] == day_tx

        progress = client.get(
            f"/progress?address={address}",
            headers=headers,
        )
        assert progress.status_code == 200
        body = progress.json()
        assert body["completedDays"] == [1]
        assert body["dayMintCount"] == 1
        assert body["shouldMintDay"] is False

        with Session(engine) as session:
            logs = session.exec(select(DailyLog)).all()
            assert len(logs) == 1
            assert logs[0].id == log["id"]
            assert logs[0].tx_hash == proof_tx
            assert logs[0].day_nft_tx_hash == day_tx
            stored_approval = session.exec(
                select(ProofApproval).where(
                    ProofApproval.approval_id == approval_id
                )
            ).one()
            assert stored_approval.used_at is not None
            assert stored_approval.tx_hash == proof_tx
    finally:
        app.dependency_overrides.clear()
