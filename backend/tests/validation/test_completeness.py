from app.validation.completeness import CompletenessValidator


def test_completeness_flags_open_fields():
    validator = CompletenessValidator()
    spec = {
        "metadata": {
            "fields": {
                "project_name": {"value": "Test Project", "state": "confirmed"},
                "target_date": {"value": None, "state": "open", "override_reason": "Deadline required"},
            }
        }
    }
    issues = validator.validate(spec)
    assert len(issues) == 1
    assert issues[0].layer == "completeness"
    assert issues[0].severity == "error"
    assert issues[0].field_path == "metadata.target_date"
    assert "Deadline required" in issues[0].message


def test_completeness_clean_when_all_confirmed():
    validator = CompletenessValidator()
    spec = {
        "metadata": {
            "fields": {
                "project_name": {"value": "Test Project", "state": "confirmed"},
                "target_date": {"value": "2026-12-01", "state": "confirmed"},
            }
        }
    }
    issues = validator.validate(spec)
    assert len(issues) == 0
