import uuid

from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from backend.app.config import settings
from backend.app.database import get_session
from backend.app.main import app
from backend.app.models import (
    DailyLog,
    ProofApproval,
    ProofCompensation,
    UserProgress,
)
from backend.app.services.proof_approval import _approval_message


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


def test_persisted_safe_checkin_receives_one_active_short_lived_approval(
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

    validator = Account.create()
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(
        settings,
        "proof_approval_private_key",
        validator.key.hex(),
        raising=False,
    )
    monkeypatch.setattr(settings, "proof_approval_ttl_seconds", 300, raising=False)
    monkeypatch.setattr(
        settings,
        "proof_registry_address",
        "0x9999999999999999999999999999999999999999",
    )
    app.dependency_overrides[get_session] = get_test_session
    account = Account.create()
    address = account.address.lower()
    note = (
        "你把今天完成的动作和遇到的阻力都记录得很具体，这条记录已经通过输入与输出安全检查。"
        "上链批准只证明这条本地打卡经过了当前规则，并不证明现实世界任务的真实性。"
        "批准需要短期有效并绑定当前钱包、日期和 Proof，避免被复制到其他请求。"
    )
    next_step = "现在用五分钟确认今天最想保留的一条记录。"

    async def fake_ask(self, messages, system_msg=None):
        return f'{{"note":"{note}","next":"{next_step}"}}'

    monkeypatch.setattr("backend.app.services.reflection.ChatBot.ask", fake_ask)
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
                "text": "今天完成了计划中的第一步。",
            },
        )
        assert checkin.status_code == 200
        log = checkin.json()["log"]

        first = client.post(
            "/proof/approval",
            headers=headers,
            json={"address": address, "logId": log["id"]},
        )
        assert first.status_code == 200
        approval = first.json()
        assert approval["approvalId"].startswith("0x")
        assert len(approval["approvalId"]) == 66
        assert approval["signature"].startswith("0x")
        assert approval["proofHash"] == log["proofHash"]
        assert approval["deadline"] > 0
        recovered = Account.recover_message(
            _approval_message(
                address=address,
                day_index=log["dayIndex"],
                proof_hash=approval["proofHash"],
                deadline=approval["deadline"],
                approval_id=approval["approvalId"],
            ),
            signature=approval["signature"],
        )
        assert recovered.lower() == validator.address.lower()

        second = client.post(
            "/proof/approval",
            headers=headers,
            json={"address": address, "logId": log["id"]},
        )
        assert second.status_code == 200
        assert second.json()["approvalId"] == approval["approvalId"]
        assert second.json()["signature"] == approval["signature"]
    finally:
        app.dependency_overrides.clear()


def _seed_progress_and_logs(
    engine,
    *,
    address: str,
    count: int,
) -> list[DailyLog]:
    logs = []
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
            log = DailyLog(
                id=str(uuid.uuid4()),
                address=address,
                challenge_id=settings.challenge_id,
                day_index=day,
                date_key=f"2026-06-{day:02d}",
                normalized_text=f"day {day}",
                reflection={"note": "note", "next": "next"},
                salt_hex=f"0x{day:02x}",
                proof_hash="0x" + f"{day:02x}" * 32,
                status="CREATED",
            )
            session.add(log)
            logs.append(log)
        session.commit()
        for log in logs:
            session.refresh(log)
            session.expunge(log)
    return logs


def test_revoke_is_append_only_and_removes_progress_and_milestone_eligibility(
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

    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(
        settings,
        "proof_approval_private_key",
        Account.create().key.hex(),
    )
    monkeypatch.setattr(
        settings,
        "proof_registry_address",
        "0x9999999999999999999999999999999999999999",
    )
    app.dependency_overrides[get_session] = get_test_session
    account = Account.create()
    address = account.address.lower()
    logs = _seed_progress_and_logs(engine, address=address, count=7)
    client = TestClient(app)

    try:
        headers = _authenticate(client, account)
        approval = client.post(
            "/proof/approval",
            headers=headers,
            json={"address": address, "logId": logs[0].id},
        )
        assert approval.status_code == 200

        revoked = client.post(
            "/proof/compensate",
            headers=headers,
            json={
                "address": address,
                "logId": logs[0].id,
                "action": "revoke",
                "reason": "The persisted record was later found to be invalid.",
            },
        )
        assert revoked.status_code == 200
        assert revoked.json()["action"] == "REVOKE"

        with Session(engine) as session:
            stored = session.get(DailyLog, logs[0].id)
            assert stored.proof_status == "REVOKED"
            stored.tx_hash = "0x" + "ab" * 32
            session.add(stored)
            session.commit()

        repeated = client.post(
            "/proof/compensate",
            headers=headers,
            json={
                "address": address,
                "logId": logs[0].id,
                "action": "revoke",
                "reason": "Do not duplicate compensation records.",
            },
        )
        assert repeated.status_code == 409

        progress = client.get(
            f"/progress?address={address}",
            headers=headers,
        )
        assert progress.status_code == 200
        assert 1 not in progress.json()["completedDays"]
        assert progress.json()["streak"] == 6

        milestone = client.post(
            "/milestone/mint",
            headers=headers,
            json={
                "address": address,
                "milestoneId": 1,
                "txHash": "0x" + "cd" * 32,
                "chainId": settings.chain_id,
                "contractAddress": settings.milestone_nft_address,
            },
        )
        assert milestone.status_code == 400
        assert milestone.json()["detail"]["error"]["code"] == "NEED_MORE_DAYS"

        with Session(engine) as session:
            audits = session.exec(select(ProofCompensation)).all()
            approvals = session.exec(select(ProofApproval)).all()
            stored = session.get(DailyLog, logs[0].id)
            assert len(audits) == 1
            assert audits[0].previous_proof_hash == logs[0].proof_hash
            assert approvals[0].invalidated_at is not None
            assert stored.tx_hash == "0x" + "ab" * 32
    finally:
        app.dependency_overrides.clear()


def test_supersede_is_post_chain_compensation_not_a_new_approval(
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

    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(
        settings,
        "proof_approval_private_key",
        Account.create().key.hex(),
    )
    monkeypatch.setattr(
        settings,
        "proof_registry_address",
        "0x9999999999999999999999999999999999999999",
    )
    app.dependency_overrides[get_session] = get_test_session
    account = Account.create()
    address = account.address.lower()
    log = _seed_progress_and_logs(engine, address=address, count=1)[0]
    replacement_hash = "0x" + "fe" * 32
    client = TestClient(app)

    try:
        headers = _authenticate(client, account)
        premature = client.post(
            "/proof/compensate",
            headers=headers,
            json={
                "address": address,
                "logId": log.id,
                "action": "supersede",
                "reason": "A pending proof should be corrected before submission.",
                "replacementProofHash": replacement_hash,
            },
        )
        assert premature.status_code == 409
        assert (
            premature.json()["detail"]["error"]["code"]
            == "PROOF_NOT_SUBMITTED"
        )

        with Session(engine) as session:
            stored = session.get(DailyLog, log.id)
            stored.tx_hash = "0x" + "ab" * 32
            session.add(stored)
            session.commit()

        compensated = client.post(
            "/proof/compensate",
            headers=headers,
            json={
                "address": address,
                "logId": log.id,
                "action": "supersede",
                "reason": "Replace the pending proof with the corrected digest.",
                "replacementProofHash": replacement_hash,
            },
        )
        assert compensated.status_code == 200
        assert compensated.json()["replacementProofHash"] == replacement_hash

        new_approval = client.post(
            "/proof/approval",
            headers=headers,
            json={"address": address, "logId": log.id},
        )
        assert new_approval.status_code == 409
        assert (
            new_approval.json()["detail"]["error"]["code"]
            == "PROOF_NOT_ACTIVE"
        )

        progress = client.get(
            f"/progress?address={address}",
            headers=headers,
        )
        assert progress.status_code == 200
        assert progress.json()["completedDays"] == [1]

        with Session(engine) as session:
            audits = session.exec(select(ProofCompensation)).all()
            stored = session.get(DailyLog, log.id)
            assert len(audits) == 1
            assert audits[0].previous_proof_hash == log.proof_hash
            assert audits[0].replacement_proof_hash == replacement_hash
            assert stored.proof_status == "SUPERSEDED"
            assert stored.effective_proof_hash == replacement_hash
            assert stored.tx_hash == "0x" + "ab" * 32
    finally:
        app.dependency_overrides.clear()
