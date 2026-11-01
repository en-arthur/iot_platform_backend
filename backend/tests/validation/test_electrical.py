from app.db.repositories.library_repo import library_repo
from app.validation.electrical import ElectricalValidator


def test_electrical_detects_pin_collision():
    validator = ElectricalValidator()
    # Both BME280 SDA and Button assigned to GPIO4
    spec = {
        "peripherals": {
            "fields": {
                "bme280_sda_pin": {"value": "GPIO4", "state": "confirmed"},
                "button_pin": {"value": "GPIO4", "state": "confirmed"},
                "fan_relay_pin": {"value": "GPIO9", "state": "confirmed"},
            }
        }
    }
    issues = validator.validate(spec)
    collisions = [i for i in issues if i.layer == "electrical" and i.severity == "error"]
    assert len(collisions) >= 2
    paths = [i.field_path for i in collisions]
    assert "peripherals.bme280_sda_pin" in paths
    assert "peripherals.button_pin" in paths
    assert "Pin collision on GPIO4" in collisions[0].message


def test_electrical_detects_reserved_pin_assignment():
    validator = ElectricalValidator()
    board = library_repo.get_board("esp32-s3-devkitc-1")

    # GPIO18 is reserved for Native USB D-
    spec = {
        "peripherals": {
            "fields": {
                "sensor_sda": {"value": "GPIO18", "state": "confirmed"},
            }
        }
    }
    issues = validator.validate(spec, board=board)
    reserved_errors = [i for i in issues if "reserved" in i.message.lower()]
    assert len(reserved_errors) == 1
    assert reserved_errors[0].severity == "error"
    assert reserved_errors[0].field_path == "peripherals.sensor_sda"


def test_electrical_detects_i2c_address_clash():
    validator = ElectricalValidator()
    spec = {
        "peripherals": {
            "fields": {
                "sensor1_i2c_addr": {"value": "0x76", "state": "confirmed"},
                "sensor2_i2c_addr": {"value": "0x76", "state": "confirmed"},
            }
        }
    }
    issues = validator.validate(spec)
    i2c_errors = [i for i in issues if "i2c bus address clash" in i.message.lower()]
    assert len(i2c_errors) == 2
