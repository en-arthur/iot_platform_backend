from typing import Any, Dict, List, Optional, Set, Tuple
from app.db.repositories.library_repo import library_repo
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
        # Pins and clock come from the selected board. Hardcoding ESP32 numbers
        # here is how a NodeMCU project used to arrive with GPIO9/GPIO10, which
        # are the ESP8266 flash bus.
        board = library_repo.get_board(project_input.board_id)
        defaults = board.default_pins if board else {}
        clock_mhz = board.specs.clock_mhz if board else 240

        peripherals_fields = SpecEngine._build_peripheral_fields(
            project_input.peripherals or [], project_input.custom_peripherals or [], defaults
        )

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
                        "value": clock_mhz,
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
                "fields": peripherals_fields,
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
    def _build_peripheral_fields(
        selected: List[str], custom: List[str], defaults: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build the Section 3 peripheral fields from the wizard's selection.

        An empty ``selected`` list keeps the reference BME280 + relay + button
        set, so the demo project and any caller that omits peripherals keep the
        pin defaults the rest of the platform (and the tests) rely on. A
        non-empty list only includes the parts the engineer actually picked, so
        code generation emits firmware for the hardware they chose.
        """
        use_defaults = not selected
        chosen = set(selected)
        fields: Dict[str, Any] = {}

        if use_defaults or "bme280" in chosen:
            fields["bme280_sda_pin"] = {
                "value": defaults.get("i2c_sda", "GPIO4"),
                "state": "confirmed",
                "source": "user",
            }
            fields["bme280_scl_pin"] = {
                "value": defaults.get("i2c_scl", "GPIO5"),
                "state": "confirmed",
                "source": "user",
            }
            fields["bme280_i2c_addr"] = {
                "value": "0x76",
                "state": "defaulted",
                "source": "library",
            }
        if use_defaults or "relay-module-5v" in chosen:
            fields["fan_relay_pin"] = {
                "value": defaults.get("relay", "GPIO9"),
                "state": "confirmed",
                "source": "user",
            }
        if use_defaults or "push-button" in chosen:
            fields["button_pin"] = {
                "value": defaults.get("button", "GPIO10"),
                "state": "confirmed",
                "source": "user",
            }
        if "ssd1306-oled" in chosen:
            fields["oled_display"] = {
                "value": 'SSD1306 0.96" I2C OLED',
                "state": "confirmed",
                "source": "user",
            }
        if custom:
            fields["custom_components"] = {
                "value": list(custom),
                "state": "confirmed",
                "source": "user",
            }
        return fields

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
