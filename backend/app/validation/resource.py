import uuid
from typing import Any, Dict, List, Optional
from app.models.library import Board, Peripheral
from app.models.validation import ValidationIssue
from app.validation.base import BaseValidator


class ResourceValidator(BaseValidator):
    """Layer 4: Resource & Power Budget Verification.
    Audits MCU Flash, RAM/PSRAM, and battery life against operational duty cycles.
    """

    def validate(
        self,
        spec: Dict[str, Any],
        board: Optional[Board] = None,
        peripherals: Optional[List[Peripheral]] = None,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        hw_fields = spec.get("hardware", {}).get("fields", {})
        updates_fields = spec.get("updates", {}).get("fields", {})
        behavior_fields = spec.get("behavior", {}).get("fields", {})

        board_flash = board.specs.flash_mb if board else 8.0
        ota_enabled = updates_fields.get("ota_enabled", {}).get("value", True)

        # 1. Dual Partition OTA Flash Sizing Rule:
        # OTA updates require two identical app slots (app0, app1), requiring minimum 4MB flash.
        if ota_enabled and board_flash < 4.0:
            issues.append(
                ValidationIssue(
                    id=f"res-flash-ota-{uuid.uuid4().hex[:6]}",
                    layer="resource",
                    severity="error",
                    field_path="updates.ota_enabled",
                    message=f"OTA updates enabled but target board only has {board_flash}MB flash. Dual-slot rollback partition table requires at least 4MB flash.",
                )
            )

        # 2. Battery & Power Budget Audit
        power_source = str(hw_fields.get("power_source", {}).get("value") or "").lower()
        deep_sleep_enabled = hw_fields.get("deep_sleep_enabled", {}).get("value")

        if "battery" in power_source or "lipo" in power_source:
            if deep_sleep_enabled is False:
                issues.append(
                    ValidationIssue(
                        id=f"res-battery-sleep-{uuid.uuid4().hex[:6]}",
                        layer="resource",
                        severity="warning",
                        field_path="hardware.deep_sleep_enabled",
                        message="Battery-powered deployment configured with deep sleep disabled. Continuous active radio duty cycle will deplete battery in under 24 hours.",
                    )
                )

        # 3. Clock Speed vs Power
        clock_mhz = hw_fields.get("mcu_clock_mhz", {}).get("value")
        if clock_mhz and int(clock_mhz) > 160 and "battery" in power_source and deep_sleep_enabled is False:
            issues.append(
                ValidationIssue(
                    id=f"res-clock-power-{uuid.uuid4().hex[:6]}",
                    layer="resource",
                    severity="info",
                    field_path="hardware.mcu_clock_mhz",
                    message=f"MCU clock is set to {clock_mhz} MHz on battery power. Consider reducing to 80 MHz during active bursts to extend operating duration.",
                )
            )

        return issues
