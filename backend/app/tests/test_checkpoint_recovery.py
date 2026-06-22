from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select

from backend.app.database import get_session
from backend.app.config import settings
from backend.app.main import app
from backend.app.models import DailyLog, GraphCheckpoint, UserProgress


def test_retry_resumes_from_persistent_checkpoint_without_repeating_reflection(
    monkeypatch,
):
    monkeypatch.setattr(settings, "demo_mode", True)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    note = (
        "你把今天真正完成的部分写得很具体，也看见了中途停顿之后仍然继续行动的过程。"
        "这份记录不需要证明你始终保持高效率，它更重要的价值是保留一次重新开始的证据。"
        "接下来只要延续已经启动的节奏，不需要再扩大今天的目标。"
    )
    next_step = "现在用五分钟整理明天开始时需要的一样东西。"
    model_calls = 0

    async def fake_ask(self, messages, system_msg=None):
        nonlocal model_calls
        model_calls += 1
        return f'{{"note":"{note}","next":"{next_step}"}}'

    monkeypatch.setattr("backend.app.services.reflection.ChatBot.ask", fake_ask)

    original_commit = Session.commit
    persistence_failed = False

    def fail_first_log_commit(self):
        nonlocal persistence_failed
        if not persistence_failed and any(isinstance(obj, DailyLog) for obj in self.new):
            persistence_failed = True
            raise RuntimeError("simulated database outage")
        return original_commit(self)

    monkeypatch.setattr(Session, "commit", fail_first_log_commit)
    client = TestClient(app, raise_server_exceptions=False)
    payload = {
        "checkinId": "recovery-checkin-001",
        "address": "0x8181818181818181818181818181818181818181",
        "dayIndex": 1,
        "timezone": "Asia/Shanghai",
        "text": "今天中途停顿了一次，但后来还是完成了原定的一小部分。",
    }

    try:
        first = client.post("/checkin", json=payload)
        assert first.status_code == 500

        with Session(engine) as session:
            assert session.exec(select(DailyLog)).all() == []
            assert session.exec(select(UserProgress)).all() == []

        second = client.post("/checkin", json=payload)
        assert second.status_code == 200
        body = second.json()
        assert body["outcome"] == "accepted"
        assert body["checkinId"] == payload["checkinId"]
        assert body["recovered"] is True
        assert body["execution"]["promptVersion"] == "reflection-v2"
        assert body["execution"]["nodeDurationsMs"]["Reflection"] >= 0
        assert body["execution"]["nodeAttempts"]["ProgressUpdate"] == 2
        assert body["execution"]["lastError"]["node"] == "ProgressUpdate"
        assert model_calls == 1

        with Session(engine) as session:
            logs = session.exec(select(DailyLog)).all()
            progress = session.exec(select(UserProgress)).all()
            checkpoints = session.exec(select(GraphCheckpoint)).all()
            assert len(logs) == 1
            assert len(progress) == 1
            assert progress[0].streak == 1
            assert len(checkpoints) == 1
            assert checkpoints[0].checkpoint_metadata["status"] == "completed"
            assert "text" not in checkpoints[0].state_values
            assert "normalizedText" not in checkpoints[0].state_values
            assert "proofHash" not in checkpoints[0].state_values
    finally:
        app.dependency_overrides.clear()


def test_checkin_reports_transient_model_attempts(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    note = (
        "你已经把今天遇到的阻力和仍然完成的动作写得很清楚，这让记录有了可以回看的事实。"
        "短暂的服务等待不会改变这次行动本身的价值，也不需要因此重新提交或扩大目标。"
        "保留已经完成的一小步，然后把注意力放回下一个可控制的动作即可。"
    )
    next_step = "现在用五分钟写下明天最先开始的一件小事。"
    model_calls = 0

    async def fake_ask(self, messages, system_msg=None):
        nonlocal model_calls
        model_calls += 1
        if model_calls == 1:
            raise TimeoutError("temporary timeout")
        return f'{{"note":"{note}","next":"{next_step}"}}'

    monkeypatch.setattr("backend.app.services.reflection.ChatBot.ask", fake_ask)
    client = TestClient(app)

    try:
        response = client.post(
            "/checkin",
            json={
                "checkinId": "observable-checkin-001",
                "address": "0x8282828282828282828282828282828282828282",
                "dayIndex": 1,
                "timezone": "Asia/Shanghai",
                "text": "今天遇到了一点阻力，但我还是完成了计划中的第一步。",
            },
        )

        assert response.status_code == 200
        execution = response.json()["execution"]
        assert execution["modelAttempts"] == 2
        assert execution["repairAttempts"] == 0
        assert execution["fallbackReason"] is None
    finally:
        app.dependency_overrides.clear()


def test_incomplete_checkin_id_cannot_resume_with_different_input(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    note = (
        "你已经把今天完成的动作和当时的感受写得足够具体，这次记录可以形成稳定的恢复边界。"
        "如果执行中途失败，同一个标识只能继续原来的输入，不能被另一段内容覆盖。"
        "这样可以避免反馈、Proof 和最终日志属于不同请求。"
    )
    next_step = "现在用五分钟确认这次记录中最重要的一句话。"

    async def fake_ask(self, messages, system_msg=None):
        return f'{{"note":"{note}","next":"{next_step}"}}'

    monkeypatch.setattr("backend.app.services.reflection.ChatBot.ask", fake_ask)
    original_commit = Session.commit
    persistence_failed = False

    def fail_first_log_commit(self):
        nonlocal persistence_failed
        if not persistence_failed and any(isinstance(obj, DailyLog) for obj in self.new):
            persistence_failed = True
            raise RuntimeError("simulated database outage")
        return original_commit(self)

    monkeypatch.setattr(Session, "commit", fail_first_log_commit)
    client = TestClient(app, raise_server_exceptions=False)
    payload = {
        "checkinId": "conflicting-checkin-001",
        "address": "0x8383838383838383838383838383838383838383",
        "dayIndex": 1,
        "timezone": "Asia/Shanghai",
        "text": "今天完成了计划中的第一步。",
    }

    try:
        first = client.post("/checkin", json=payload)
        assert first.status_code == 500

        conflict = client.post(
            "/checkin",
            json={**payload, "text": "这是另一份不同的输入。"},
        )
        assert conflict.status_code == 409
        assert (
            conflict.json()["detail"]["error"]["code"]
            == "CHECKIN_ID_CONFLICT"
        )

        with Session(engine) as session:
            assert session.exec(select(DailyLog)).all() == []
            assert session.exec(select(UserProgress)).all() == []
    finally:
        app.dependency_overrides.clear()
