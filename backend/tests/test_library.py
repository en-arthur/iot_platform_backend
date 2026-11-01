def test_list_boards_default_tested_only(client):
    response = client.get("/api/v1/library/boards")
    assert response.status_code == 200
    boards = response.json()
    assert len(boards) >= 1
    board_ids = [b["id"] for b in boards]
    assert "esp32-s3-devkitc-1" in board_ids
    # By default, draft/untested boards are omitted
    assert "raspberry-pi-pico-w" not in board_ids


def test_list_boards_include_untested(client):
    response = client.get("/api/v1/library/boards?include_untested=true")
    assert response.status_code == 200
    boards = response.json()
    board_ids = [b["id"] for b in boards]
    assert "esp32-s3-devkitc-1" in board_ids
    assert "raspberry-pi-pico-w" in board_ids


def test_get_board_by_id(client):
    response = client.get("/api/v1/library/boards/esp32-s3-devkitc-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "esp32-s3-devkitc-1"
    assert data["vendor"] == "Espressif"
    assert data["specs"]["clock_mhz"] == 240
    assert "GPIO4" in data["pin_map"]
    assert "I2C_SDA" in data["pin_map"]["GPIO4"]["capabilities"]
    assert data["pin_map"]["GPIO0"]["is_bootstrapping"] is True


def test_get_board_not_found(client):
    response = client.get("/api/v1/library/boards/non-existent-board")
    assert response.status_code == 404
    assert "not found" in response.text.lower()


def test_list_peripherals(client):
    response = client.get("/api/v1/library/peripherals")
    assert response.status_code == 200
    peripherals = response.json()
    assert len(peripherals) >= 4
    ids = [p["id"] for p in peripherals]
    assert "bme280" in ids
    assert "relay-module-5v" in ids


def test_filter_peripherals_query(client):
    response = client.get("/api/v1/library/peripherals?query=sensor")
    assert response.status_code == 200
    results = response.json()
    for item in results:
        assert (
            "sensor" in item["name"].lower()
            or "sensor" in item["category"].lower()
            or "sensor" in item["description"].lower()
        )


def test_get_peripheral_by_id(client):
    response = client.get("/api/v1/library/peripherals/bme280")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "bme280"
    assert data["interface"] == "I2C"
    assert data["default_address"] == "0x76"
    assert "SDA" in data["pins_required"]
    assert "SCL" in data["pins_required"]


def test_get_peripheral_not_found(client):
    response = client.get("/api/v1/library/peripherals/non-existent-sensor")
    assert response.status_code == 404


def test_list_patterns(client):
    response = client.get("/api/v1/library/patterns")
    assert response.status_code == 200
    patterns = response.json()
    pattern_ids = [p["id"] for p in patterns]
    assert "periodic-sampling" in pattern_ids
    assert "deep-sleep-sampling" in pattern_ids
    assert "offline-buffering" in pattern_ids
    assert "ota-rollback" in pattern_ids
