import re
import uuid
from typing import Any, Dict, List, Optional
from app.models.library import Board, Peripheral
from app.models.validation import ValidationIssue
from app.validation.base import BaseValidator

# Labels that unambiguously mean a physical pin, even when the field name does
# not end in "_pin". Used to catch typos instead of ignoring them.
_PIN_LABEL = re.compile(r"^(GPIO\d+|GP\d+|IO\d+|D\d+|A0)$", re.IGNORECASE)


class ElectricalValidator(BaseValidator):
    """Layer 2: Electrical & Silicon Verification.
    Catches pin multiplexing collisions, strapping pin misuse, voltage incompatibilities,
    and bus address clashes before firmware touches physical silicon.
    """

    def validate(
        self,
        spec: Dict[str, Any],
        board: Optional[Board] = None,
        peripherals: Optional[List[Peripheral]] = None,
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        periph_fields = spec.get("peripherals", {}).get("fields", {})

        # 1. Physical Pin Multiplexing Collision Check
        # Pin labels are resolved through the board's pin map first, so "D2"
        # and "GPIO4" on a NodeMCU are the same physical pin, and a label the
        # board does not have is an error instead of being silently ignored.
        used_pins: Dict[str, List[str]] = {}  # { "GPIO4": ["peripherals.bme280_sda_pin"] }

        for f_key, f_data in periph_fields.items():
            if not isinstance(f_data, dict):
                continue
            val = str(f_data.get("value") or "").strip()
            if not val:
                continue

            if board is not None:
                key = board.resolve_pin(val)
                if key is None:
                    # A field that is not a pin (protocol, address, ...) is
                    # ignored; a pin-shaped value the board lacks is an error.
                    if "pin" in f_key or _PIN_LABEL.match(val):
                        issues.append(
                            ValidationIssue(
                                id=f"elec-unknown-pin-{uuid.uuid4().hex[:6]}",
                                layer="electrical",
                                severity="error",
                                field_path=f"peripherals.{f_key}",
                                message=f"Pin '{val}' does not exist on {board.name}. Choose a pin from the board pin map.",
                            )
                        )
                    continue
            else:
                # Without a board we cannot resolve aliases; keep the legacy
                # heuristic so validation still works for board-less specs.
                if not (val.startswith("GPIO") or val.startswith("GP")):
                    continue
                key = val

            used_pins.setdefault(key, []).append(f"peripherals.{f_key}")

        for pin_name, paths in used_pins.items():
            if len(paths) > 1:
                # Collision error!
                for p in paths:
                    conflicts = [x for x in paths if x != p]
                    issues.append(
                        ValidationIssue(
                            id=f"elec-pin-conflict-{uuid.uuid4().hex[:6]}",
                            layer="electrical",
                            severity="error",
                            field_path=p,
                            message=f"Pin collision on {pin_name}: Shared with {', '.join(conflicts)}. Pins must be uniquely allocated.",
                        )
                    )

        # 2. Board Pin Map Constraints (Bootstrapping, Reserved, PSRAM pins)
        if board and board.pin_map:
            for pin_name, paths in used_pins.items():
                pin_info = board.pin_map.get(pin_name)
                if not pin_info:
                    continue

                if pin_info.is_reserved:
                    for p in paths:
                        issues.append(
                            ValidationIssue(
                                id=f"elec-reserved-pin-{uuid.uuid4().hex[:6]}",
                                layer="electrical",
                                severity="error",
                                field_path=p,
                                message=f"Pin {pin_name} is reserved for board native hardware ({', '.join(pin_info.capabilities)}) and cannot be assigned to peripherals.",
                            )
                        )

                if pin_info.is_bootstrapping:
                    for p in paths:
                        issues.append(
                            ValidationIssue(
                                id=f"elec-strap-pin-{uuid.uuid4().hex[:6]}",
                                layer="electrical",
                                severity="warning",
                                field_path=p,
                                message=f"Pin {pin_name} is an MCU bootstrapping pin: {pin_info.description or 'State at boot dictates chip reset/bootloader mode'}.",
                            )
                        )

                if "PSRAM" in pin_info.capabilities:
                    for p in paths:
                        issues.append(
                            ValidationIssue(
                                id=f"elec-psram-pin-{uuid.uuid4().hex[:6]}",
                                layer="electrical",
                                severity="warning",
                                field_path=p,
                                message=f"Pin {pin_name}: {pin_info.description or 'May be consumed by PSRAM.'}",
                            )
                        )

        # 3. Voltage Level Mismatch Check
        board_logic_v = board.specs.operating_voltage_v if board else 3.3
        if peripherals:
            for p in peripherals:
                if p.operating_voltage_v > board_logic_v:
                    issues.append(
                        ValidationIssue(
                            id=f"elec-voltage-{uuid.uuid4().hex[:6]}",
                            layer="electrical",
                            severity="warning",
                            field_path=f"peripherals.{p.id}",
                            message=f"Peripheral '{p.name}' operates at {p.operating_voltage_v}V while MCU logic is {board_logic_v}V. Requires bidirectional logic level shifter.",
                        )
                    )

        # 4. Bus Address Clashes (I2C)
        i2c_addresses: Dict[str, List[str]] = {}
        for f_key, f_data in periph_fields.items():
            if "i2c_addr" in f_key or "address" in f_key:
                addr = str(f_data.get("value") or "").lower()
                if addr:
                    i2c_addresses.setdefault(addr, []).append(f"peripherals.{f_key}")

        for addr, paths in i2c_addresses.items():
            if len(paths) > 1:
                for p in paths:
                    issues.append(
                        ValidationIssue(
                            id=f"elec-i2c-addr-{uuid.uuid4().hex[:6]}",
                            layer="electrical",
                            severity="error",
                            field_path=p,
                            message=f"I2C bus address clash: Address '{addr}' is claimed by multiple peripherals ({', '.join(paths)}).",
                        )
                    )

        return issues
