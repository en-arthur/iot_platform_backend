def test_list_proposals(client):
    headers = {"Authorization": "Bearer mock-user-alice"}
    res = client.get("/api/v1/projects/proj-greenhouse-01/proposals", headers=headers)
    assert res.status_code == 200
    proposals = res.json()
    assert len(proposals) >= 1
    assert proposals[0]["proposal_id"] == "prop-fix-pin-conflict"
    assert proposals[0]["status"] == "pending"


def test_approve_proposal_applies_changes_and_mints_version(client):
    headers = {"Authorization": "Bearer mock-user-alice"}
    # 1. Approve proposal
    res = client.post(
        "/api/v1/projects/proj-greenhouse-01/proposals/prop-fix-pin-conflict/approve",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "approved"
    assert data["new_version"] >= 2

    # 2. Verify spec was mutated by the approved proposal
    spec_res = client.get("/api/v1/projects/proj-greenhouse-01/spec", headers=headers)
    assert spec_res.status_code == 200
    spec = spec_res.json()
    # Button was remapped to GPIO10
    assert spec["peripherals"]["fields"]["button_pin"]["value"] == "GPIO10"
    assert spec["metadata"]["fields"]["target_deployment_date"]["value"] == "2026-12-01"


def test_reject_proposal(client):
    headers = {"Authorization": "Bearer mock-user-alice"}
    # Create a new project with its own proposal to reject
    p_res = client.post(
        "/api/v1/projects", json={"name": "Reject Demo", "board_id": "esp32-s3-devkitc-1"}, headers=headers
    )
    p_id = p_res.json()["id"]

    # Trigger chat to generate a proposal
    chat_res = client.post(
        f"/api/v1/projects/{p_id}/chat",
        json={"prompt": "Please fix any pin conflicts."},
        headers=headers,
    )
    assert chat_res.status_code == 200

    # Get generated proposal
    prop_list = client.get(f"/api/v1/projects/{p_id}/proposals", headers=headers).json()
    assert len(prop_list) >= 1
    prop_id = prop_list[0]["proposal_id"]

    # Reject proposal
    reject_res = client.post(
        f"/api/v1/projects/{p_id}/proposals/{prop_id}/reject",
        headers=headers,
    )
    assert reject_res.status_code == 200
    r_data = reject_res.json()
    assert r_data["success"] is True
    assert r_data["status"] == "rejected"
