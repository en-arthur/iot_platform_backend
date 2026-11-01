from app.models.library import Board, BoardSpecs
from app.validation.resource import ResourceValidator


def test_resource_detects_insufficient_flash_for_ota():
    validator = ResourceValidator()
    # 2MB board with dual-partition OTA enabled
    board = Board(
        id="small-mcu",
        name="Small MCU",
        vendor="Test",
        mcu="Cortex-M0+",
        specs=BoardSpecs(flash_mb=2.0),
        pin_map={},
    )
    spec = {
        "hardware": {"fields": {}},
        "updates": {
            "fields": {
                "ota_enabled": {"value": True}
            }
        },
    }
    issues = validator.validate(spec, board=board)
    flash_issues = [i for i in issues if "flash" in i.message.lower()]
    assert len(flash_issues) == 1
    assert flash_issues[0].severity == "error"
    assert "requires at least 4MB flash" in flash_issues[0].message


def test_resource_warns_on_battery_without_sleep():
    validator = ResourceValidator()
    spec = {
        "hardware": {
            "fields": {
                "power_source": {"value": "LiPo Battery (3.7V)"},
                "deep_sleep_enabled": {"value": False},
            }
        },
        "updates": {"fields": {"ota_enabled": {"value": False}}},
    }
    issues = validator.validate(spec)
    sleep_warnings = [i for i in issues if "deep sleep disabled" in i.message.lower()]
    assert len(sleep_warnings) == 1
    assert sleep_warnings[0].severity == "warning"
