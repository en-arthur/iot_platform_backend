from app.validation.logical import LogicalValidator


def test_logical_detects_undeclared_widget_command():
    validator = LogicalValidator()
    spec = {
        "behavior": {
            "fields": {
                "declared_commands": {"value": ["TRIGGER_FAN_ON", "REBOOT"]}
            }
        },
        "data_model": {
            "fields": {
                "metrics": {"value": [{"name": "temperature_c", "type": "float"}]}
            }
        },
        "interface": {
            "fields": {
                "widgets": {
                    "value": [
                        # UNDECLARED COMMAND: TRIGGER_IRRIGATION_VALVE
                        {"id": "valve_switch", "type": "toggle", "command": "TRIGGER_IRRIGATION_VALVE"}
                    ]
                }
            }
        },
    }
    issues = validator.validate(spec)
    undeclared = [i for i in issues if "undeclared" in i.id or "declared in behavior" in i.message]
    assert len(undeclared) == 1
    assert undeclared[0].severity == "error"
    assert "TRIGGER_IRRIGATION_VALVE" in undeclared[0].message


def test_logical_detects_missing_widget_metric():
    validator = LogicalValidator()
    spec = {
        "behavior": {"fields": {}},
        "data_model": {
            "fields": {
                "metrics": {"value": [{"name": "temperature_c"}]}
            }
        },
        "interface": {
            "fields": {
                "widgets": {
                    # MISSING METRIC: soil_moisture_pct does not exist in data_model
                    "value": [{"id": "gauge_1", "type": "gauge", "metric": "soil_moisture_pct"}]
                }
            }
        },
    }
    issues = validator.validate(spec)
    missing = [i for i in issues if "missing-metric" in i.id or "does not exist in data_model" in i.message]
    assert len(missing) == 1
    assert missing[0].severity == "error"
