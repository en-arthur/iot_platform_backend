from typing import Any, Dict, List, Optional

from app.db.repositories.board_catalog import SEED_BOARDS
from app.models.library import (
    Board,
    DriverBlock,
    Pattern,
    Peripheral,
)


SEED_PERIPHERALS: List[Peripheral] = [
    Peripheral(
        id="bme280",
        name="BME280 Environmental Sensor",
        category="Sensors",
        interface="I2C",
        default_address="0x76",
        operating_voltage_v=3.3,
        pins_required=["SDA", "SCL", "3V3", "GND"],
        status="tested",
        description="Measures temperature (-40 to +85°C), relative humidity (0-100%), and barometric pressure (300-1100 hPa).",
        datasheet_url="https://www.bosch-sensortec.com/products/environmental-sensors/humidity-sensors-bme280/",
    ),
    Peripheral(
        id="relay-module-5v",
        name="1-Channel 5V Relay Module (Optocoupled)",
        category="Actuators",
        interface="Digital Output",
        operating_voltage_v=5.0,
        pins_required=["IN", "VCC", "GND"],
        status="tested",
        description="High-current relay switch for driving AC appliances, irrigation valves, heaters, or fans.",
    ),
    Peripheral(
        id="push-button",
        name="Momentary Tactile Push Button",
        category="Inputs",
        interface="Digital Input",
        operating_voltage_v=3.3,
        pins_required=["SIG", "GND"],
        status="tested",
        description="Active-low user input push button with internal MCU pull-up resistor support.",
    ),
    Peripheral(
        id="ssd1306-oled",
        name="SSD1306 0.96 inch I2C OLED Display",
        category="Displays",
        interface="I2C",
        default_address="0x3C",
        operating_voltage_v=3.3,
        pins_required=["SDA", "SCL", "3V3", "GND"],
        status="tested",
        description="128x64 monochrome graphic OLED display for telemetry metrics and diagnostics.",
    ),
]

SEED_PATTERNS: List[Pattern] = [
    Pattern(
        id="periodic-sampling",
        name="Periodic Sampling Loop",
        category="Sampling",
        description="Wakes periodically via FreeRTOS timer, samples all sensors, publishes telemetry to MQTT, and yields CPU.",
        template_slots=["sampling_interval_seconds", "telemetry_topic", "publish_qos"],
        status="tested",
    ),
    Pattern(
        id="deep-sleep-sampling",
        name="Deep-Sleep Duty Cycle",
        category="Power",
        description="Ultra-low power cycle: powers up from deep sleep, performs rapid sensor burst, publishes payload, and enters RTC deep sleep.",
        template_slots=["deep_sleep_interval_seconds", "wakeup_pin", "early_shutdown_v"],
        status="tested",
    ),
    Pattern(
        id="offline-buffering",
        name="Offline Ring Buffer",
        category="Lifecycle",
        description="Buffers telemetry readings to non-volatile flash (NVS/LittleFS) during broker disconnects, flushing in FIFO order upon reconnect.",
        template_slots=["max_buffer_records", "storage_partition"],
        status="tested",
    ),
    Pattern(
        id="ota-rollback",
        name="OTA Updates with Health Rollback",
        category="Lifecycle",
        description="Dual-partition OTA with self-test verification window; automatically rolls back if boot verification fails.",
        template_slots=["ota_url", "validation_timeout_seconds"],
        status="tested",
    ),
]


class LibraryRepository:
    """Provides access to verified hardware boards, peripherals, and architectural patterns."""

    def __init__(self):
        self._boards = {b.id: b for b in SEED_BOARDS}
        self._peripherals = {p.id: p for p in SEED_PERIPHERALS}
        self._patterns = {pt.id: pt for pt in SEED_PATTERNS}

    def list_boards(self, include_all: bool = False) -> List[Board]:
        """Lists boards. Returns tested boards by default, or all if include_all is True."""
        if include_all:
            return list(self._boards.values())
        return [b for b in self._boards.values() if b.status == "tested"]

    def get_board(self, board_id: str) -> Optional[Board]:
        return self._boards.get(board_id)

    def build_profile(self, board_id: str) -> Optional[Dict[str, Any]]:
        """PlatformIO build recipe for a board, or None if it is unknown.

        Code generation, the sandbox and the artifact lookup all read the board
        record through this method so a board id alone is never enough to
        silently produce firmware for a different target.
        """
        board = self.get_board(board_id)
        if not board:
            return None
        return {
            "board_id": board.id,
            "platform": board.platform,
            "board": board.pio_board,
            "framework": board.framework,
            "env": board.env_name,
            "binary_ext": board.binary_ext,
            "upload_protocol": board.upload_protocol,
            "connectivity": board.connectivity,
        }

    def validate_catalog(self) -> List[str]:
        """Return a list of problems with the hardware catalog (empty is good).

        Every entry must declare its build recipe explicitly. Pydantic defaults
        exist for backwards compatibility, so an omitted field would otherwise
        inherit ESP32 values without anyone noticing.
        """
        problems: List[str] = []
        built_in = {
            "platform",
            "pio_board",
            "env_name",
            "connectivity",
            "pin_naming",
            "binary_ext",
            "upload_protocol",
        }
        seen: set = set()

        for board in self._boards.values():
            if board.id in seen:
                problems.append(f"{board.id}: duplicate board id")
            seen.add(board.id)

            missing = sorted(built_in - board.model_fields_set)
            if missing:
                problems.append(
                    f"{board.id}: build recipe missing explicit {', '.join(missing)}"
                )

            if not board.pio_board.strip():
                problems.append(f"{board.id}: empty PlatformIO board id")

            if not board.env_name.replace("_", "").isalnum():
                problems.append(
                    f"{board.id}: env name '{board.env_name}' is not a valid identifier"
                )

            if "flash_mb" not in board.specs.model_fields_set:
                problems.append(f"{board.id}: flash_mb must be declared explicitly")

            # Pin maps must be resolvable and unique, otherwise code generation
            # silently emits one pin twice or an unusable number.
            gpio_numbers: Dict[int, str] = {}
            for key, pin in board.pin_map.items():
                if pin.gpio is None:
                    problems.append(f"{board.id}: pin '{key}' has no GPIO number")
                    continue
                other = gpio_numbers.get(pin.gpio)
                if other is not None:
                    problems.append(
                        f"{board.id}: pins '{other}' and '{key}' both claim GPIO{pin.gpio}"
                    )
                gpio_numbers[pin.gpio] = key

            for role, label in board.default_pins.items():
                if board.resolve_pin(label) is None:
                    problems.append(
                        f"{board.id}: default pin '{role}' = '{label}' is not in the pin map"
                    )

        return problems

    def list_peripherals(self, query: Optional[str] = None) -> List[Peripheral]:
        """Filters peripherals by name, category, or interface query."""
        results = list(self._peripherals.values())
        if not query:
            return results

        q = query.lower().strip()
        return [
            p
            for p in results
            if q in p.name.lower() or q in p.category.lower() or q in p.interface.lower()
        ]

    def get_peripheral(self, peripheral_id: str) -> Optional[Peripheral]:
        return self._peripherals.get(peripheral_id)

    def list_patterns(self) -> List[Pattern]:
        return list(self._patterns.values())


library_repo = LibraryRepository()
