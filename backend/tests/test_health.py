def test_root_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time-MS" in response.headers


def test_api_v1_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_health_does_not_claim_an_unconfigured_sandbox(client, monkeypatch):
    """Health reports configuration, so a missing E2B key is visible."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "E2B_API_KEY", None)
    data = client.get("/health").json()
    assert data["components"]["e2b_sandbox"] == "not_configured"

