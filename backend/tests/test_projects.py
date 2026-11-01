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
