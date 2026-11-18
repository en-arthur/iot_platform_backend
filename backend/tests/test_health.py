def test_get_run_backfills_board_from_artifact_meta(client, monkeypatch):
    """After a restart the run row has no board; the stored artifact does."""
    from app.db import supabase_store
    from app.db.repositories.verification_repo import verification_repo

    run = verification_repo.create_run("proj-greenhouse-01", "test-user-uuid-1")
    run.board_id = None
    run.status = "passed"
    run.artifact_available = False

    meta = {
        "run_id": run.run_id,
        "project_id": run.project_id,
        "board_id": "nodemcuv2",
        "format": "esp-segments",
        "artifact_name": "firmware.bin",
        "total_bytes": 301216,
    }
    monkeypatch.setattr(
        supabase_store, "load_verification_artifact_meta", lambda run_id: meta
    )

    loaded = verification_repo.get_run(run.run_id, "test-user-uuid-1")

    assert loaded.board_id == "nodemcuv2"
    assert loaded.artifact_available is True
    assert loaded.artifact_size_bytes == 301216


def test_get_run_backfills_board_from_project_when_no_artifact(client):
    from app.db.repositories.verification_repo import verification_repo

    run = verification_repo.create_run("proj-greenhouse-01", "test-user-uuid-1")
    run.board_id = None

    loaded = verification_repo.get_run(run.run_id, "test-user-uuid-1")
    assert loaded.board_id == "esp32-s3-devkitc-1"


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

