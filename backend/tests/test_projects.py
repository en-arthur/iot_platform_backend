def test_create_project_and_get_spec(client):
    headers = {"Authorization": "Bearer mock-user-alice"}
    create_payload = {
        "name": "Solar Soil Monitor",
        "description": "Capacitive moisture array with ESP32-S3",
        "board_id": "esp32-s3-devkitc-1",
        "interface_type": "web app",
    }
    res = client.post("/api/v1/projects", json=create_payload, headers=headers)
    assert res.status_code == 201
    project = res.json()
    assert project["name"] == "Solar Soil Monitor"
    assert project["lifecycle"] == "draft"
    assert project["version"] == 1
    project_id = project["id"]

    # Retrieve spec
    spec_res = client.get(f"/api/v1/projects/{project_id}/spec", headers=headers)
    assert spec_res.status_code == 200
    spec = spec_res.json()
    assert "metadata" in spec
    assert "hardware" in spec
    assert "peripherals" in spec
    assert "behavior" in spec
    assert "data_model" in spec
    assert "connectivity" in spec
    assert "cloud_backend" in spec
    assert "interface" in spec
    assert "security" in spec
    assert "updates" in spec
    assert "verification" in spec
    assert "provenance" in spec


def test_confirm_gate_blocks_on_open_fields(client):
    headers = {"Authorization": "Bearer mock-user-bob"}
    create_payload = {"name": "Test Node", "board_id": "esp32-s3-devkitc-1"}
    p_res = client.post("/api/v1/projects", json=create_payload, headers=headers)
    project_id = p_res.json()["id"]

    # Initial spec has metadata.target_deployment_date open
    confirm_res = client.post(f"/api/v1/projects/{project_id}/spec/confirm", headers=headers)
    assert confirm_res.status_code == 409
    err = confirm_res.json()
    assert "Cannot confirm spec" in err["message"]
    assert len(err["reasons"]) > 0


def test_patch_field_and_successful_confirm(client):
    headers = {"Authorization": "Bearer mock-user-charlie"}
    create_payload = {"name": "Smart Valve", "board_id": "esp32-s3-devkitc-1"}
    p_res = client.post("/api/v1/projects", json=create_payload, headers=headers)
    project_id = p_res.json()["id"]

    # Patch the open field to confirmed
    patch_payload = [
        {
            "path": "metadata.target_deployment_date",
            "value": "2026-12-01",
            "state": "confirmed",
            "override_reason": "Verified deadline with lead engineer.",
        }
    ]
    patch_res = client.patch(
        f"/api/v1/projects/{project_id}/spec/fields", json=patch_payload, headers=headers
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert (
        data["spec"]["metadata"]["fields"]["target_deployment_date"]["state"] == "confirmed"
    )

    # Now confirmation succeeds
    confirm_res = client.post(f"/api/v1/projects/{project_id}/spec/confirm", headers=headers)
    assert confirm_res.status_code == 200
    c_data = confirm_res.json()
    assert c_data["success"] is True
    assert c_data["lifecycle"] == "confirmed"
    assert c_data["version"] == 2

    # Check version history and diff
    versions_res = client.get(f"/api/v1/projects/{project_id}/versions", headers=headers)
    assert versions_res.status_code == 200
    versions = versions_res.json()
    assert len(versions) == 2

    # Check diff between v1 and v2
    diff_res = client.get(f"/api/v1/projects/{project_id}/versions/1/diff/2", headers=headers)
    assert diff_res.status_code == 200
    diff = diff_res.json()
    assert len(diff["changes"]) >= 1
    paths = [ch["path"] for ch in diff["changes"]]
    assert "metadata.target_deployment_date" in paths


def test_cross_user_isolation(client):
    user_a = {"Authorization": "Bearer mock-user-user-a"}
    user_b = {"Authorization": "Bearer mock-user-user-b"}

    create_payload = {"name": "Secret Device", "board_id": "esp32-s3-devkitc-1"}
    p_res = client.post("/api/v1/projects", json=create_payload, headers=user_a)
    project_id = p_res.json()["id"]

    # User B attempting to read user A's project is forbidden
    res = client.get(f"/api/v1/projects/{project_id}", headers=user_b)
    assert res.status_code in (403, 404)


def test_validate_spec_endpoint_and_pin_conflict_gate(client):
    headers = {"Authorization": "Bearer mock-user-dan"}
    create_payload = {"name": "Collision Test Node", "board_id": "esp32-s3-devkitc-1"}
    p_res = client.post("/api/v1/projects", json=create_payload, headers=headers)
    project_id = p_res.json()["id"]

    # First validate: open field target_deployment_date is flagged
    val_res = client.post(f"/api/v1/projects/{project_id}/spec/validate", headers=headers)
    assert val_res.status_code == 200
    issues = val_res.json()
    assert any(i["layer"] == "completeness" and i["severity"] == "error" for i in issues)

    # Patch open field, but introduce an electrical pin collision (GPIO4 shared)
    patch_payload = [
        {"path": "metadata.target_deployment_date", "value": "2026-12-01", "state": "confirmed"},
        {"path": "peripherals.bme280_sda_pin", "value": "GPIO4", "state": "confirmed"},
        {"path": "peripherals.button_pin", "value": "GPIO4", "state": "confirmed"},
    ]
    client.patch(f"/api/v1/projects/{project_id}/spec/fields", json=patch_payload, headers=headers)

    # Validate again: pin collision is flagged
    val_res2 = client.post(f"/api/v1/projects/{project_id}/spec/validate", headers=headers)
    assert val_res2.status_code == 200
    issues2 = val_res2.json()
    electrical_errors = [i for i in issues2 if i["layer"] == "electrical" and i["severity"] == "error"]
    assert len(electrical_errors) >= 2

    # Confirmation MUST be blocked by electrical error
    confirm_res = client.post(f"/api/v1/projects/{project_id}/spec/confirm", headers=headers)
    assert confirm_res.status_code == 409
    assert "error-level issue(s) require resolution" in confirm_res.json()["message"]



def test_behavior_draft_falls_back_to_template(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    headers = {"Authorization": "Bearer mock-user-alice"}
    payload = {
        "name": "Greenhouse Monitor",
        "goal": "Keep soil moisture between 35% and 60% and alert on dry spells.",
        "board_id": "esp32-s3-devkitc-1",
        "peripherals": ["capacitive_soil_moisture", "sht31"],
        "custom_peripherals": ["solenoid valve"],
        "interface_type": "web app",
    }
    res = client.post("/api/v1/projects/behavior-draft", json=payload, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "template"
    text = body["behavior"]
    assert "esp32-s3-devkitc-1" in text
    assert "capacitive_soil_moisture" in text
    assert "solenoid valve" in text
    assert "Keep soil moisture between 35% and 60%" in text


def test_behavior_draft_requires_auth(client):
    res = client.post("/api/v1/projects/behavior-draft", json={"name": "x"})
    assert res.status_code == 401
