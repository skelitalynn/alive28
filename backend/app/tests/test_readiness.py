from eth_account import Account
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_demo_health_is_ready_without_chain_configuration(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    monkeypatch.setattr(settings, "rpc_url", "")
    monkeypatch.setattr(settings, "proof_registry_address", ZERO_ADDRESS)
    monkeypatch.setattr(settings, "restart_badge_address", ZERO_ADDRESS)
    monkeypatch.setattr(settings, "milestone_nft_address", ZERO_ADDRESS)
    monkeypatch.setattr(settings, "milestone_base_uri", "https://api.YOUR_DOMAIN/metadata/")
    monkeypatch.setattr(settings, "proof_approval_private_key", "")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mode"] == "demo"
    assert body["ready"] is True
    assert body["blockingIssues"] == []


def test_non_demo_health_reports_blocking_configuration_issues(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "rpc_url", "")
    monkeypatch.setattr(settings, "proof_registry_address", ZERO_ADDRESS)
    monkeypatch.setattr(settings, "restart_badge_address", ZERO_ADDRESS)
    monkeypatch.setattr(settings, "milestone_nft_address", ZERO_ADDRESS)
    monkeypatch.setattr(settings, "milestone_base_uri", "https://api.YOUR_DOMAIN/metadata/")
    monkeypatch.setattr(settings, "proof_approval_private_key", "your_validator_private_key")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["mode"] == "production"
    assert body["ready"] is False
    assert body["checks"] == {
        "rpcUrl": False,
        "proofRegistryAddress": False,
        "restartBadgeAddress": False,
        "milestoneNftAddress": False,
        "milestoneBaseUri": False,
        "proofApprovalPrivateKey": False,
    }
    assert {issue["code"] for issue in body["blockingIssues"]} == {
        "RPC_URL_MISSING",
        "PROOF_REGISTRY_ADDRESS_MISSING",
        "RESTART_BADGE_ADDRESS_MISSING",
        "MILESTONE_NFT_ADDRESS_MISSING",
        "MILESTONE_BASE_URI_MISSING",
        "PROOF_APPROVAL_PRIVATE_KEY_MISSING",
    }


def test_non_demo_health_is_ready_when_required_configuration_is_present(
    monkeypatch,
):
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "rpc_url", "https://rpc.example")
    monkeypatch.setattr(
        settings,
        "proof_registry_address",
        "0x1111111111111111111111111111111111111111",
    )
    monkeypatch.setattr(
        settings,
        "restart_badge_address",
        "0x2222222222222222222222222222222222222222",
    )
    monkeypatch.setattr(
        settings,
        "milestone_nft_address",
        "0x3333333333333333333333333333333333333333",
    )
    monkeypatch.setattr(settings, "milestone_base_uri", "https://metadata.example/")
    monkeypatch.setattr(settings, "proof_approval_private_key", Account.create().key.hex())

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["mode"] == "production"
    assert body["ready"] is True
    assert all(body["checks"].values())
    assert body["blockingIssues"] == []
