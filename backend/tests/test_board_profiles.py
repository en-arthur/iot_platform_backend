import pytest

from app.codegen.firmware_generator import ArduinoFirmwareGenerator
from app.core.exceptions import ValidationError
from app.db.repositories.library_repo import library_repo
from app.models.project import ProjectCreate
from app.services.spec_engine import SpecEngine

# Byte-for-byte output of the generator before the board record refactor. This
# guards the "no behavior change" promise: existing ESP32-S3 projects must keep
# producing exactly the same platformio.ini.
ESP32_S3_PLATFORMIO_INI = (
    "; PlatformIO Project Configuration for Arduino Framework\n"
    "; Target: esp32-s3-devkitc-1\n"
    "; Single-source-of-truth project spec v1.0\n"
    "\n"
    "[platformio]\n"
    "default_envs = esp32s3\n"
    "\n"
    "[env:esp32s3]\n"
    "platform = espressif32\n"
    "board = esp32-s3-devkitc-1\n"
    "framework = arduino\n"
    "monitor_speed = 115200\n"
    "\n"
    "; The build machine already has these libraries installed, so the build needs\n"
    "; no internet access. To build this folder on your own computer, install them\n"
    "; once with:\n"
    ';   pio pkg install -l "knolleary/PubSubClient@2.8.0"\n'
    ';                   -l "adafruit/Adafruit BME280 Library@2.3.0"\n'
    ';                   -l "adafruit/Adafruit Unified Sensor@1.1.15"\n'
    ';                   -l "bblanchon/ArduinoJson@7.4.3"\n'
    "lib_extra_dirs = /opt/platformio/lib\n"
    "\n"
    "# USER CODE BEGIN PLATFORMIO_CONFIG\n"
    "# Optional custom build flags or extra libraries\n"
    "# USER CODE END PLATFORMIO_CONFIG\n"
)


def _spec(board_id: str):
    return SpecEngine.create_default_spec(
        ProjectCreate(
            name="Profile Node",
            description="Goal: monitor soil moisture.",
            board_id=board_id,
            interface_type="web app",
        )
    )


def _platformio_ini(board_id: str) -> str:
    files = ArduinoFirmwareGenerator.generate("proj-profile", 1, _spec(board_id))
    return next(f for f in files if f.path == "firmware/platformio.ini").content


def test_catalog_entries_declare_a_build_recipe():
    problems = library_repo.validate_catalog()
    assert problems == [], "\n".join(problems)


def test_catalog_offers_thirty_boards_people_actually_buy():
    boards = library_repo.list_boards()
    assert len(boards) == 30
    ids = [b.id for b in boards]
    assert len(set(ids)) == len(ids)
    # Every offered board must run on a platform the build image has.
    assert {b.platform for b in boards} <= {"espressif32", "espressif8266"}


def test_every_offered_board_has_usable_default_pins():
    for board in library_repo.list_boards():
        assert len(board.pin_map) > 5, board.id
        for role in ("i2c_sda", "i2c_scl", "relay", "button"):
            label = board.default_pins.get(role)
            assert label, f"{board.id} has no default {role}"
            key = board.resolve_pin(label)
            assert key is not None, f"{board.id}: {role}={label} is not in the pin map"
            pin = board.pin_map[key]
            assert not pin.is_reserved, f"{board.id}: {role} points at reserved {label}"
            assert pin.gpio is not None


def test_every_offered_board_generates_firmware():
    for board in library_repo.list_boards():
        files = ArduinoFirmwareGenerator.generate("proj-catalog", 1, _spec(board.id))
        paths = {f.path for f in files}
        assert "firmware/src/main.cpp" in paths, board.id
        ini = next(f.content for f in files if f.path == "firmware/platformio.ini")
        assert f"board = {board.pio_board}" in ini, board.id
        assert "lib_deps" not in ini, board.id


def test_esp32_s3_platformio_ini_is_unchanged():
    assert _platformio_ini("esp32-s3-devkitc-1") == ESP32_S3_PLATFORMIO_INI


def test_pico_profile_uses_its_own_platform_not_esp32():
    ini = _platformio_ini("raspberry-pi-pico-w")
    assert "default_envs = pico" in ini
    assert "[env:pico]" in ini
    assert "platform = raspberrypi" in ini
    assert "board = rpipicow" in ini
    assert "espressif32" not in ini
    assert "esp32-s3-devkitc-1" not in ini.replace("; Target: raspberry-pi-pico-w", "")


def test_unknown_board_is_rejected_by_the_generator():
    with pytest.raises(ValidationError):
        ArduinoFirmwareGenerator.generate("proj-profile", 1, _spec("not-a-board"))


def test_create_project_rejects_unknown_board(client):
    response = client.post(
        "/api/v1/projects",
        json={"name": "Bad Board Node", "board_id": "not-a-board"},
        headers={"Authorization": "Bearer mock-user-profile"},
    )
    assert response.status_code == 422
    assert "hardware library" in response.text


def test_library_api_exposes_the_build_recipe(client):
    response = client.get("/api/v1/library/boards/esp32-s3-devkitc-1")
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "espressif32"
    assert data["pio_board"] == "esp32-s3-devkitc-1"
    assert data["env_name"] == "esp32s3"
    assert data["connectivity"] == "wifi"
    assert data["pin_naming"] == "GPIO"

NODEMCU_PLATFORMIO_INI_HEADER = """; PlatformIO Project Configuration for Arduino Framework
; Target: nodemcuv2
; Single-source-of-truth project spec v1.0

[platformio]
default_envs = nodemcuv2

[env:nodemcuv2]
platform = espressif8266
board = nodemcuv2
framework = arduino
monitor_speed = 115200
"""


def test_nodemcu_uses_the_esp8266_platform():
    ini = _platformio_ini("nodemcuv2")
    assert ini.startswith(NODEMCU_PLATFORMIO_INI_HEADER)
    assert "espressif32" not in ini


def test_spec_pin_defaults_come_from_the_board():
    esp = _spec("esp32-s3-devkitc-1")
    node = _spec("nodemcuv2")
    esp_fields = esp["peripherals"]["fields"]
    node_fields = node["peripherals"]["fields"]
    assert esp_fields["bme280_sda_pin"]["value"] == "GPIO4"
    assert node_fields["bme280_sda_pin"]["value"] == "D2"
    assert node_fields["bme280_scl_pin"]["value"] == "D1"
    assert node_fields["fan_relay_pin"]["value"] == "D5"
    assert node_fields["button_pin"]["value"] == "D6"
    assert node["hardware"]["fields"]["mcu_clock_mhz"]["value"] == 80


def test_generated_config_uses_resolved_gpio_numbers():
    files = {
        f.path: f.content
        for f in ArduinoFirmwareGenerator.generate("proj-profile", 1, _spec("nodemcuv2"))
    }
    config = files["firmware/include/config.h"]
    assert "#define PIN_I2C_SDA         4  // D2" in config
    assert "#define PIN_I2C_SCL         5  // D1" in config
    assert "#define PIN_FAN_RELAY       14  // D5" in config
    assert "#define PIN_MANUAL_BUTTON   12  // D6" in config
    assert "#define PLATFORM_CONNECTIVITY   \"wifi\"" in config


def test_nodemcu_firmware_includes_the_esp8266_stack_and_guards_deep_sleep():
    files = {
        f.path: f.content
        for f in ArduinoFirmwareGenerator.generate("proj-profile", 1, _spec("nodemcuv2"))
    }
    main = files["firmware/src/main.cpp"]
    assert "#include <ESP8266WiFi.h>" in main
    assert "#if defined(ESP32)" in main
    assert "ESP.deepSleep" in main
    # The ESP32-only sleep API must not be called outside its guard.
    guard_start = main.index("#if defined(ESP32)")
    esptool_call = main.index("esp_sleep_enable_timer_wakeup")
    esp8266_branch = main.index("#elif defined(ESP8266)")
    assert guard_start < esptool_call < esp8266_branch


def test_unresolvable_pin_is_rejected_with_the_board_pin_list():
    spec = _spec("nodemcuv2")
    spec["peripherals"]["fields"]["bme280_sda_pin"]["value"] = "GPIO99"
    with pytest.raises(ValidationError) as exc:
        ArduinoFirmwareGenerator.generate("proj-profile", 1, spec)
    message = str(exc.value)
    assert "GPIO99" in message
    assert "NodeMCU" in message
    assert "D2" in message


def test_reserved_pin_is_rejected_by_the_generator():
    spec = _spec("esp32-s3-devkitc-1")
    spec["peripherals"]["fields"]["bme280_sda_pin"]["value"] = "GPIO19"
    with pytest.raises(ValidationError) as exc:
        ArduinoFirmwareGenerator.generate("proj-profile", 1, spec)
    assert "reserved" in str(exc.value)


def test_electrical_validator_rejects_unknown_pins():
    from app.db.repositories.library_repo import library_repo
    from app.validation.electrical import ElectricalValidator

    board = library_repo.get_board("nodemcuv2")
    spec = {"peripherals": {"fields": {"bme280_sda_pin": {"value": "GPIO99"}}}}
    issues = ElectricalValidator().validate(spec, board=board)
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "does not exist" in issues[0].message


def test_electrical_validator_catches_aliased_pin_collisions():
    from app.db.repositories.library_repo import library_repo
    from app.validation.electrical import ElectricalValidator

    board = library_repo.get_board("nodemcuv2")
    # D2 and GPIO4 are the same physical pin on a NodeMCU.
    spec = {
        "peripherals": {
            "fields": {
                "bme280_sda_pin": {"value": "D2"},
                "button_pin": {"value": "GPIO4"},
            }
        }
    }
    issues = ElectricalValidator().validate(spec, board=board)
    collisions = [i for i in issues if "collision" in i.message.lower()]
    assert len(collisions) == 2

def test_ethernet_board_switches_the_generated_transport():
    from app.db.repositories.library_repo import library_repo
    from app.models.library import Board, BoardSpecs

    board = Board(
        id="test-ethernet-node",
        name="Test Ethernet Node",
        vendor="Test",
        mcu="Test MCU",
        status="unverified",
        platform="atmelavr",
        pio_board="uno",
        env_name="uno",
        connectivity="ethernet",
        pin_naming="D",
        binary_ext=".hex",
        upload_protocol="avrdude",
        specs=BoardSpecs(flash_mb=32.0),
        pin_map={
            "D2": {"name": "D2", "gpio": 2, "capabilities": ["GPIO"]},
            "D3": {"name": "D3", "gpio": 3, "capabilities": ["GPIO"]},
            "D4": {"name": "D4", "gpio": 4, "capabilities": ["GPIO"]},
            "D5": {"name": "D5", "gpio": 5, "capabilities": ["GPIO"]},
        },
        default_pins={"i2c_sda": "D2", "i2c_scl": "D3", "relay": "D4", "button": "D5"},
    )
    library_repo._boards[board.id] = board
    try:
        assert library_repo.validate_catalog() == []
        files = {
            f.path: f.content
            for f in ArduinoFirmwareGenerator.generate(
                "proj-profile", 1, _spec(board.id)
            )
        }
        config = files["firmware/include/config.h"]
        main = files["firmware/src/main.cpp"]
        assert "#define PLATFORM_ETHERNET       1" in config
        assert "#define ETHERNET_CS_PIN         10" in config
        assert "#include <Ethernet.h>" in main
        assert "EthernetClient networkClient;" in main
        assert "Ethernet.begin(ETHERNET_MAC)" in main
    finally:
        del library_repo._boards[board.id]

def test_generate_rejects_an_unknown_pin_before_streaming(client):
    headers = {"Authorization": "Bearer mock-user-pin-preflight"}
    created = client.post(
        "/api/v1/projects",
        json={"name": "Pin Preflight Node", "board_id": "nodemcuv2"},
        headers=headers,
    )
    assert created.status_code == 201
    pid = created.json()["id"]
    try:
        patched = client.patch(
            f"/api/v1/projects/{pid}/spec/fields",
            json=[{"path": "peripherals.bme280_sda_pin", "value": "GPIO99"}],
            headers=headers,
        )
        assert patched.status_code == 200

        response = client.post(f"/api/v1/projects/{pid}/generate", headers=headers)
        assert response.status_code == 422
        assert "GPIO99" in response.text
    finally:
        client.delete(f"/api/v1/projects/{pid}", headers=headers)
