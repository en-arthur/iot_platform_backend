from app.codegen.protected_regions import ProtectedRegionManager
from app.db.repositories.files_repo import files_repo


def test_codegen_generate_arduino_firmware_and_cloud(client):
    headers = {"Authorization": "Bearer mock-user-alice"}
    project_id = "proj-greenhouse-01"

    # Trigger code generation via SSE endpoint
    gen_res = client.post(f"/api/v1/projects/{project_id}/generate", headers=headers)
    assert gen_res.status_code == 200
    assert "event: done" in gen_res.text

    # List generated files
    files_res = client.get(f"/api/v1/projects/{project_id}/files", headers=headers)
    assert files_res.status_code == 200
    file_list = files_res.json()
    paths = [f["path"] for f in file_list]

    # Verify Arduino firmware files exist
    assert "firmware/platformio.ini" in paths
    assert "firmware/include/config.h" in paths
    assert "firmware/src/main.cpp" in paths

    # Verify Cloud Backend files exist (with WorkersCraft CloudService integration)
    assert "cloud_backend/cloud_service_client.py" in paths
    assert "cloud_backend/mqtt_worker.py" in paths
    assert "cloud_backend/server.py" in paths

    # Verify Interface files exist
    assert "interface/src/App.jsx" in paths


def test_arduino_syntax_and_framework(client):
    headers = {"Authorization": "Bearer mock-user-alice"}
    project_id = "proj-greenhouse-01"

    # Inspect platformio.ini
    pio_res = client.get(
        f"/api/v1/projects/{project_id}/files/firmware/platformio.ini", headers=headers
    )
    assert pio_res.status_code == 200
    pio_content = pio_res.json()["content"]
    assert "framework = arduino" in pio_content
    assert "platform = espressif32" in pio_content

    # Inspect main.cpp
    main_res = client.get(
        f"/api/v1/projects/{project_id}/files/firmware/src/main.cpp", headers=headers
    )
    assert main_res.status_code == 200
    main_content = main_res.json()["content"]
    assert "#include <Arduino.h>" in main_content
    assert "void setup()" in main_content
    assert "void loop()" in main_content
    assert "Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);" in main_content


def test_protected_regions_preservation(client):
    headers = {"Authorization": "Bearer mock-user-alice"}
    project_id = "proj-greenhouse-01"

    # 1. Fetch main.cpp
    f_res = client.get(
        f"/api/v1/projects/{project_id}/files/firmware/src/main.cpp", headers=headers
    )
    orig_content = f_res.json()["content"]

    # 2. Add custom developer code inside USER CODE BEGIN SETUP
    custom_line = "    Serial.println(\"[CUSTOM LOG] Lead Hardware Engineer calibrated sensors.\");"
    edited_content = orig_content.replace(
        "/* USER CODE BEGIN SETUP */",
        f"/* USER CODE BEGIN SETUP */\n{custom_line}",
    )

    # 3. Save manual edit (PUT)
    put_res = client.put(
        f"/api/v1/projects/{project_id}/files/firmware/src/main.cpp",
        json={"content": edited_content},
        headers=headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["is_protected"] is True

    # 4. Re-generate project code
    client.post(f"/api/v1/projects/{project_id}/generate", headers=headers)

    # 5. Verify manual edit was preserved across regeneration!
    check_res = client.get(
        f"/api/v1/projects/{project_id}/files/firmware/src/main.cpp", headers=headers
    )
    preserved_content = check_res.json()["content"]
    assert "[CUSTOM LOG] Lead Hardware Engineer calibrated sensors." in preserved_content
