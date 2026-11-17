import pytest
from app.db.repositories.audit_repo import audit_repo
from app.db.repositories.project_repo import project_repo


def test_health_observability(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "components" in data
    components = data["components"]
    # Components report configuration, not a guessed pass.
    for name in ("database", "mqtt_broker", "e2b_sandbox", "cloud_service"):
        assert name in components
    assert components["database"] in ("operational", "memory")
    assert components["e2b_sandbox"] in ("configured", "not_configured")


def test_cors_allows_local_dev_origins_even_when_env_lists_only_prod(
    client, monkeypatch
):
    """A local frontend must be able to call the deployed API.

    Render's env var lists only the deployed origin, so the settings layer has
    to add the localhost dev origins itself.
    """
    from app.core.config import settings

    monkeypatch.setattr(
        settings, "BACKEND_CORS_ORIGINS", ["https://iot-platform-sepia.vercel.app"]
    )
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://127.0.0.1:3000" in settings.CORS_ORIGINS
    assert "https://iot-platform-sepia.vercel.app" in settings.CORS_ORIGINS

    response = client.options(
        "/api/v1/library/boards",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:3000"
    )


def test_rate_limit_headers(client, create_test_token):
    token = create_test_token()
    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers


def test_payload_too_large_rejection(client):
    # Send a request with Content-Length simulating oversized body > 10MB
    headers = {"Content-Length": str(15 * 1024 * 1024)}
    response = client.post(
        "/api/v1/projects/proj-greenhouse-01/spec/fields",
        data=b"huge payload",
        headers=headers,
    )
    assert response.status_code == 413
    assert "Payload Too Large" in response.text


def test_audit_log_tracking_across_lifecycle(client, create_test_token):
    token = create_test_token()
    project_id = "proj-greenhouse-01"

    # 1. Provision a device to generate audit entry
    client.post(
        f"/api/v1/projects/{project_id}/devices",
        json={"name": "Audit Test Node"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 2. Query audit logs endpoint
    res = client.get(
        f"/api/v1/projects/{project_id}/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    actions = [item["action"] for item in data["items"]]
    assert "DEVICE_PROVISION" in actions

    # Verify audit payload and actor
    provision_entry = [i for i in data["items"] if i["action"] == "DEVICE_PROVISION"][-1]
    assert provision_entry["user_id"] == "test-user-uuid-1"
    assert provision_entry["project_id"] == project_id
    assert "device_id" in provision_entry["payload"]
