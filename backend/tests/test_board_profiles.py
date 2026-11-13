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
    "lib_deps =\n"
    "    knolleary/PubSubClient@^2.8\n"
    "    adafruit/Adafruit BME280 Library@^2.2.2\n"
    "    adafruit/Adafruit Unified Sensor@^1.1.9\n"
    "    bblanchon/ArduinoJson@^7.0.0\n"
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
