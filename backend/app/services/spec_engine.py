from typing import Any, Dict, List, Optional, Set, Tuple
from app.models.project import ProjectCreate
from app.models.spec import (
    ProjectSpec,
    SpecDiff,
    SpecDiffItem,
    SpecField,
    SpecFieldState,
    SpecFieldSource,
)

# Cross-section dependency mapping rule table
DEPENDENCY_RULES: Dict[str, List[str]] = {
    "hardware.board_id": ["peripherals", "verification", "power"],
    "hardware.mcu_clock_mhz": ["behavior", "verification"],
    "hardware.power_source": ["hardware", "behavior"],
    "peripherals.bme280_sda_pin": ["peripherals", "verification"],
    "peripherals.bme280_scl_pin": ["peripherals", "verification"],
    "peripherals.fan_relay_pin": ["peripherals", "behavior", "verification"],
    "peripherals.manual_override_button_pin": ["peripherals", "behavior", "verification"],
    "data_model.metrics": ["cloud_backend", "interface"],
    "cloud_backend.protocol": ["connectivity", "security"],
    "interface.interface_type": ["interface", "behavior"],
}


class SpecEngine:
    """Core Spec Engine responsible for 12-section model lifecycle, field states,
    cross-section dependency mapping, provenance tracking, and structured diffs.
    """

    @staticmethod
    def create_default_spec(project_input: ProjectCreate, user_name: str = "Hardware Engineer") -> Dict[str, Any]:
        """Synthesizes the initial 12-section specification single source of truth."""
        spec = {
            "metadata": {
                "title": "1. Project Metadata",
                "fields": {
                    "project_name": {
                        "value": project_input.name,
                        "state": "confirmed",
                        "source": "user",
                    },
                    "description": {
                        "value": project_input.description or "",
                        "state": "confirmed",
                        "source": "user",
                    },
                    "target_deployment_date": {
                        "value": None,
                        "state": "open",  # Open blocking field
                        "source": "user",
                        "override_reason": "Deployment target deadline required before production confirmation.",
                    },
                    "author": {
                        "value": user_name,
                        "state": "confirmed",
                        "source": "user",
                    },
                },
            },
            "hardware": {
                "title": "2. Hardware Platform & Power",
                "fields": {
                    "board_id": {
                        "value": project_input.board_id,
                        "state": "confirmed",
                        "source": "library",
                    },
                    "mcu_clock_mhz": {
                        "value": 240,
                        "state": "defaulted",
                        "source": "library",
                    },
                    "power_source": {
                        "value": "LiPo Battery (3.7V) + Solar Harvester",
                        "state": "confirmed",
                        "source": "user",
                    },
                    "deep_sleep_enabled": {
                        "value": True,
                        "state": "inferred",
                        "source": "ai",
                    },
                    "deep_sleep_interval_seconds": {
                        "value": 60,
                        "state": "confirmed",
                        "source": "user",
                    },
                },
            },
            "peripherals": {
                "title": "3. Peripherals & Pin Multiplexing",
                "fields": {
                    "bme280_sda_pin": {
                        "value": "GPIO4",
                        "state": "confirmed",
                        "source": "user",
                    },
                    "bme280_scl_pin": {
                        "value": "GPIO5",
                        "state": "confirmed",
                        "source": "user",
                    },
                    "bme280_i2c_addr": {
                        "value": "0x76",
                        "state": "defaulted",
                        "source": "library",
                    },
                    "fan_relay_pin": {
                        "value": "GPIO9",
                        "state": "confirmed",
                        "source": "user",
                    },
                    "button_pin": {
                        "value": "GPIO10",
                        "state": "confirmed",
                        "source": "user",
                    },
                },
            },
            "behavior": {
                "title": "4. Runtime Behavior & State Machine",
                "fields": {
                    "telemetry_sampling_rate_hz": {
                        "value": 0.0167,  # Once every 60 seconds
                        "state": "confirmed",
                        "source": "user",
                    },
                    "high_temperature_threshold_c": {
                        "value": 30.0,
                        "state": "confirmed",
                        "source": "user",
                    },
                    "urgent_alert_threshold_c": {
                        "value": 35.0,
                        "state": "confirmed",
                        "source": "user",
                    },
                    "declared_commands": {
                        "value": ["TRIGGER_FAN_FORCE_ON", "TRIGGER_FAN_FORCE_OFF", "REBOOT_NODE"],
                        "state": "confirmed",
                        "source": "user",
                    },
                },
            },
            "data_model": {
                "title": "5. Telemetry & Data Model",
                "fields": {
                    "metrics": {
                        "value": [
                            {"name": "temperature_c", "type": "float", "unit": "°C"},
                            {"name": "relative_humidity_pct", "type": "float", "unit": "%"},
                            {"name": "barometric_pressure_hpa", "type": "float", "unit": "hPa"},
                            {"name": "battery_voltage_v", "type": "float", "unit": "V"},
                        ],
                        "state": "confirmed",
                        "source": "user",
                    },
                    "serialization_format": {
                        "value": "json",
                        "state": "defaulted",
                        "source": "platform_default",
                    },
                },
            },
            "connectivity": {
                "title": "6. Connectivity & Protocols",
                "fields": {
                    "primary_protocol": {
                        "value": "MQTT",
                        "state": "confirmed",
                        "source": "user",
                    },
                    "wifi_ssid": {
                        "value": "ENV_WIFI_SSID",
                        "state": "defaulted",
                        "source": "platform_default",
                    },
                    "wifi_password": {
                        "value": "ENV_WIFI_PASSWORD",
                        "state": "defaulted",
                        "source": "platform_default",
                    },
                },
            },
            "cloud_backend": {
                "title": "7. Cloud Backend & Telemetry Ingestion",
                "fields": {
                    "broker_host": {
                        "value": "mqtt.cloud.iot-builder.io",
                        "state": "defaulted",
                        "source": "platform_default",
                    },
                    "broker_port": {
                        "value": 8883,
                        "state": "defaulted",
                        "source": "platform_default",
                    },
                    "telemetry_topic": {
                        "value": "devices/{{device_id}}/telemetry",
                        "state": "defaulted",
                        "source": "platform_default",
                    },
                    "commands_topic": {
                        "value": "devices/{{device_id}}/commands",
                        "state": "defaulted",
                        "source": "platform_default",
                    },
                },
            },
            "interface": {
                "title": "8. Web/App Interface & Dashboards",
                "fields": {
                    "interface_type": {
                        "value": project_input.interface_type,
                        "state": "confirmed",
                        "source": "user",
                    },
                    "widgets": {
                        "value": [
                            {"id": "temp_gauge", "type": "gauge", "metric": "temperature_c"},
                            {"id": "humidity_chart", "type": "timeseries", "metric": "relative_humidity_pct"},
                            {"id": "fan_switch", "type": "toggle", "command": "TRIGGER_FAN_FORCE_ON"},
                        ],
                        "state": "confirmed",
                        "source": "user",
                    },
                },
            },
            "security": {
                "title": "9. Device Security & Identity",
                "fields": {
                    "tls_enabled": {
                        "value": True,
                        "state": "confirmed",
                        "source": "platform_default",
                    },
                    "device_auth_method": {
                        "value": "per_device_token",
                        "state": "confirmed",
                        "source": "platform_default",
                    },
                },
            },
            "updates": {
                "title": "10. Updates & Lifecycle (OTA)",
                "fields": {
                    "ota_enabled": {
                        "value": True,
                        "state": "confirmed",
                        "source": "platform_default",
                    },
                    "rollback_on_failed_boot": {
                        "value": True,
                        "state": "defaulted",
                        "source": "platform_default",
                    },
                },
            },
            "verification": {
                "title": "11. Verification Contracts & Pinout Rules",
                "fields": {
                    "zero_pinout_collision_rule": {
                        "value": True,
                        "state": "confirmed",
                        "source": "platform_default",
                    },
                    "voltage_compatibility_rule": {
                        "value": True,
                        "state": "confirmed",
                        "source": "platform_default",
                    },
                },
            },
            "provenance": {
                "title": "12. Audit Provenance & Export Gate",
                "fields": {
                    "library_overrides": {
                        "value": [],
                        "state": "confirmed",
                        "source": "platform_default",
                    },
                    "audit_chain_intact": {
                        "value": True,
                        "state": "confirmed",
                        "source": "platform_default",
                    },
                },
            },
        }
        return spec

    @staticmethod
    def patch_field(
        spec_data: Dict[str, Any],
        path: str,
        value: Any,
        state: SpecFieldState = "confirmed",
        override_reason: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Applies a patch to a single field by dot-path and returns affected sections."""
        parts = path.split(".", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid field path '{path}'. Must be 'section.field'")

        section_key, field_key = parts
        if section_key not in spec_data:
            raise ValueError(f"Section '{section_key}' not found in spec")

        section = spec_data[section_key]
        if "fields" not in section:
            section["fields"] = {}

        current_field = section["fields"].get(field_key, {})
        source: SpecFieldSource = "user"

        # Record provenance if this is overriding a library default
        if current_field.get("source") in ("library", "from_library") and override_reason:
            overrides = spec_data.get("provenance", {}).get("fields", {}).get("library_overrides", {})
            if "value" in overrides and isinstance(overrides["value"], list):
                overrides["value"].append(
                    {
                        "path": path,
                        "previous": current_field.get("value"),
                        "overridden_to": value,
                        "reason": override_reason,
                    }
                )

        section["fields"][field_key] = {
            "value": value,
            "state": state,
            "source": source,
            "override_reason": override_reason or current_field.get("override_reason"),
        }

        # Resolve cross-section dependencies
        affected_sections = DEPENDENCY_RULES.get(path, [section_key])
        return spec_data, affected_sections

    @staticmethod
    def compute_diff(spec_a: Dict[str, Any], spec_b: Dict[str, Any], version_a: int, version_b: int) -> SpecDiff:
        """Computes structured field-by-field diff between two spec versions."""
        changes: List[SpecDiffItem] = []

        all_sections = set(spec_a.keys()).union(set(spec_b.keys()))
        for sec_key in sorted(all_sections):
            fields_a = spec_a.get(sec_key, {}).get("fields", {})
            fields_b = spec_b.get(sec_key, {}).get("fields", {})

            all_field_keys = set(fields_a.keys()).union(set(fields_b.keys()))
            for f_key in sorted(all_field_keys):
                f_a = fields_a.get(f_key, {})
                f_b = fields_b.get(f_key, {})

                val_a = f_a.get("value")
                val_b = f_b.get("value")

                if val_a != val_b:
                    changes.append(
                        SpecDiffItem(
                            path=f"{sec_key}.{f_key}",
                            old=val_a,
                            new=val_b,
                            reason=f_b.get("override_reason"),
                        )
                    )

        return SpecDiff(version_a=version_a, version_b=version_b, changes=changes)

    @staticmethod
    def get_open_blocking_fields(spec_data: Dict[str, Any]) -> List[str]:
        """Finds all fields with state=='open' that block spec confirmation."""
        open_fields: List[str] = []
        for sec_key, sec in spec_data.items():
            if not isinstance(sec, dict):
                continue
            for f_key, field in sec.get("fields", {}).items():
                if isinstance(field, dict) and field.get("state") == "open":
                    open_fields.append(f"{sec_key}.{f_key}")
        return open_fields
