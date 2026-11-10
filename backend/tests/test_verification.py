import pytest
from app.agents.debug_agent import DebugAgent
from app.db.repositories.proposal_repo import proposal_repo
from app.db.repositories.verification_repo import verification_repo


def test_get_verification_run_demo(client, create_test_token):
    token = create_test_token()
    response = client.get(
        "/api/v1/runs/run-greenhouse-01",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "run-greenhouse-01"
    assert data["status"] == "passed"
    assert data["sandbox_provider"] == "e2b"
    assert "PlatformIO" in data["logs"]
    assert data["selftest_results"]["wifi_connected"] is True


def test_trigger_verification_run(client, create_test_token):
    token = create_test_token()
    response = client.post(
        "/api/v1/projects/proj-greenhouse-01/verify",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["status"] == "running"
    assert "e2b" in data["message"].lower()


def test_stream_verification_logs(client, create_test_token):
    token = create_test_token()
    response = client.get(
        "/api/v1/runs/run-greenhouse-01/stream",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    content = response.text
    assert "event: status" in content
    assert "event: done" in content


def test_download_firmware_binary(client, create_test_token):
    token = create_test_token()
    response = client.get(
        "/api/v1/runs/run-greenhouse-01/firmware",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert len(response.content) > 0


def test_submit_selftest_success(client, create_test_token):
    token = create_test_token()
    # Create a fresh run
    run = verification_repo.create_run("proj-greenhouse-01", "test-user-uuid-1")

    payload = {
        "results": {
            "wifi_connected": True,
            "bme280_ack": True,
            "fan_relay_switched": True,
        }
    }
    response = client.post(
        f"/api/v1/runs/{run.run_id}/selftest",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "passed"
    assert "SELF-TEST PASSED" in data["logs"]


def test_submit_selftest_failure_triggers_debug_agent(client, create_test_token):
    token = create_test_token()
    run = verification_repo.create_run("proj-greenhouse-01", "test-user-uuid-1")

    payload = {
        "results": {
            "wifi_connected": True,
            "bme280_ack": False,  # BME280 sensor not detected
        }
    }
    response = client.post(
        f"/api/v1/runs/{run.run_id}/selftest",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"
    assert "SELF-TEST FAILED" in data["logs"]

    # Debug agent should have created an automated spec proposal
    proposals = proposal_repo.list_proposals("proj-greenhouse-01")
    hardware_proposals = [p for p in proposals if "bme280" in p.title.lower() or "hardware" in p.title.lower()]
    assert len(hardware_proposals) > 0


@pytest.mark.asyncio
async def test_debug_agent_compiler_error_analysis():
    stderr_sample = "error: 'D4' was not declared in this scope; did you mean 'GPIO4'?"
    proposal = DebugAgent.analyze_compiler_error("proj-greenhouse-01", stderr_sample)
    assert proposal is not None
    assert "compiler" in proposal.title.lower() or "fix" in proposal.title.lower()
    assert len(proposal.suggested_changes) > 0
