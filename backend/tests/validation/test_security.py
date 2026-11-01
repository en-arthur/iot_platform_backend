from app.validation.security import SecurityValidator


def test_security_detects_plaintext_mqtt():
    validator = SecurityValidator()
    spec = {
        "security": {"fields": {"tls_enabled": {"value": False}}},
        "cloud_backend": {"fields": {"broker_port": {"value": 1883}}},
        "connectivity": {"fields": {}},
        "updates": {"fields": {}},
    }
    issues = validator.validate(spec)
    tls_warnings = [i for i in issues if "tls" in i.message.lower()]
    assert len(tls_warnings) >= 1
    assert tls_warnings[0].severity == "warning"


def test_security_detects_hardcoded_secret():
    validator = SecurityValidator()
    spec = {
        "security": {"fields": {"tls_enabled": {"value": True}}},
        "cloud_backend": {"fields": {"broker_port": {"value": 8883}}},
        "connectivity": {
            "fields": {
                # HARDCODED PLAINTEXT PASSWORD
                "wifi_password": {"value": "MySuperSecretPassword123!"}
            }
        },
        "updates": {"fields": {}},
    }
    issues = validator.validate(spec)
    secret_errors = [i for i in issues if "hardcoded" in i.message.lower()]
    assert len(secret_errors) == 1
    assert secret_errors[0].severity == "error"
    assert secret_errors[0].field_path == "connectivity.wifi_password"


def test_security_detects_ota_without_rollback():
    validator = SecurityValidator()
    spec = {
        "security": {"fields": {"tls_enabled": {"value": True}}},
        "cloud_backend": {"fields": {"broker_port": {"value": 8883}}},
        "connectivity": {"fields": {"wifi_password": {"value": "ENV_WIFI_PASSWORD"}}},
        "updates": {
            "fields": {
                "ota_enabled": {"value": True},
                "rollback_on_failed_boot": {"value": False},
            }
        },
    }
    issues = validator.validate(spec)
    rollback_errors = [i for i in issues if "rollback" in i.message.lower()]
    assert len(rollback_errors) == 1
    assert rollback_errors[0].severity == "error"
