import pytest
from app.db.repositories.device_repo import device_repo
from app.db.repositories.project_repo import project_repo


def test_device_provisioning(client, create_test_token):
    token = create_test_token()
    payload = {"name": "Greenhouse Temp Sensor 02"}
    response = client.post(
        "/api/v1/projects/proj-greenhouse-01/devices",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "device_id" in data
    assert data["name"] == "Greenhouse Temp Sensor 02"
    # Secret is returned ONCE
    assert "secret" in data
    assert data["secret"].startswith("dsec_")
    assert "devices/" in data["telemetry_topic"]
    assert "devices/" in data["command_topic"]

    # Verify that listing devices does NOT leak the secret
    list_res = client.get(
        "/api/v1/projects/proj-greenhouse-01/devices",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_res.status_code == 200
    devices = list_res.json()
    created = [d for d in devices if d["device_id"] == data["device_id"]][0]
    assert "secret" not in created
    assert created["status"] == "provisioned"


def test_dispatch_undeclared_command_rejected(client, create_test_token):
    token = create_test_token()
    # Attempting to dispatch an undeclared command must fail with 422/400 ValidationError
    payload = {
        "command": "UNDECLARED_DANGEROUS_ACTION",
        "params": {"voltage": 999},
    }
    response = client.post(
        "/api/v1/devices/dev-greenhouse-01/commands",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code in (400, 422)
    assert "not declared" in response.text.lower()


def test_dispatch_declared_command_success(client, create_test_token, monkeypatch):
    token = create_test_token()

    async def fake_publish(topic, payload, **kwargs):
        return True

    monkeypatch.setattr(
        "app.db.repositories.device_repo.mqtt_service.publish", fake_publish
    )
    payload = {
        "command": "TRIGGER_FAN_FORCE_ON",
        "params": {"speed": 100},
    }
    response = client.post(
        "/api/v1/devices/dev-greenhouse-01/commands",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "dispatched"
    assert data["command"] == "TRIGGER_FAN_FORCE_ON"


def test_dispatch_queues_when_broker_unavailable(client, create_test_token, monkeypatch):
    token = create_test_token()

    async def fake_publish(topic, payload, **kwargs):
        return False

    monkeypatch.setattr(
        "app.db.repositories.device_repo.mqtt_service.publish", fake_publish
    )
    response = client.post(
        "/api/v1/devices/dev-greenhouse-01/commands",
        json={"command": "TRIGGER_FAN_FORCE_ON", "params": {}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "queued"


def test_telemetry_ingestion_and_threshold_alert(client, create_test_token):
    token = create_test_token()
    # Send normal reading
    normal_payload = {"temperature_c": 22.5, "humidity_pct": 55.0}
    res1 = client.post(
        "/api/v1/devices/dev-greenhouse-01/telemetry",
        json=normal_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200

    # Send critical temperature reading > 35.0 C
    critical_payload = {"temperature_c": 38.2, "humidity_pct": 50.0}
    res2 = client.post(
        "/api/v1/devices/dev-greenhouse-01/telemetry",
        json=critical_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 200

    # Check alerts endpoint
    alerts_res = client.get(
        "/api/v1/devices/dev-greenhouse-01/alerts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    crit_alerts = [a for a in alerts if a["severity"] == "critical" and a["metric"] == "temperature_c"]
    assert len(crit_alerts) > 0
    assert crit_alerts[0]["current_value"] == 38.2


def test_project_deployment(client, create_test_token):
    token = create_test_token()
    # Confirm project first if needed
    project = project_repo.get_project("proj-greenhouse-01", "test-user-uuid-1")
    project.lifecycle = "verified"

    response = client.post(
        "/api/v1/projects/proj-greenhouse-01/deploy",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "wc-app-proj-greenhouse-01" in data["cloud_service_app_id"]
    assert project.lifecycle == "deployed"

    # Verify querying deployment status
    status_res = client.get(
        "/api/v1/projects/proj-greenhouse-01/deployment",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert status_res.status_code == 200
    assert status_res.json()["deployment_id"] == data["deployment_id"]
