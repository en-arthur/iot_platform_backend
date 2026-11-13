from typing import Any, Dict, List, Optional
from app.models.library import Board, DriverBlock, Pattern, Peripheral

# =============================================================================
# VERIFIED SEED DATA
# Facts (pins, voltages, addresses) come strictly from this verified library.
# =============================================================================

SEED_BOARDS: List[Board] = [
    Board(
        id="esp32-s3-devkitc-1",
        name="ESP32-S3 DevKitC-1",
        vendor="Espressif",
        mcu="ESP32-S3 (Xtensa Dual-core 32-bit LX7)",
        status="tested",
        platform="espressif32",
        pio_board="esp32-s3-devkitc-1",
        framework="arduino",
        env_name="esp32s3",
        connectivity="wifi",
        pin_naming="GPIO",
        binary_ext=".bin",
        upload_protocol="esptool",
        specs={
            "flash_mb": 8.0,
            "psram_mb": 2.0,
            "clock_mhz": 240,
            "operating_voltage_v": 3.3,
            "wifi": "802.11 b/g/n (2.4 GHz)",
            "ble": "Bluetooth 5.0 (BLE)",
            "usb": "Native USB OTG & USB-to-UART",
        },
        pin_map={
            "GPIO0": {
                "name": "GPIO0",
                "capabilities": ["BOOT", "RTC"],
                "is_bootstrapping": True,
                "description": "Strapping pin (LOW for bootloader flash mode)",
            },
            "GPIO1": {"name": "GPIO1", "capabilities": ["ADC", "RTC", "GPIO"]},
            "GPIO2": {"name": "GPIO2", "capabilities": ["ADC", "RTC", "GPIO"]},
            "GPIO4": {"name": "GPIO4", "capabilities": ["I2C_SDA", "GPIO", "ADC"]},
            "GPIO5": {"name": "GPIO5", "capabilities": ["I2C_SCL", "GPIO", "ADC"]},
            "GPIO6": {"name": "GPIO6", "capabilities": ["SPI_SCK", "GPIO"]},
            "GPIO7": {"name": "GPIO7", "capabilities": ["SPI_MOSI", "GPIO"]},
            "GPIO8": {"name": "GPIO8", "capabilities": ["SPI_MISO", "GPIO"]},
            "GPIO9": {"name": "GPIO9", "capabilities": ["RELAY_OUT", "GPIO"]},
            "GPIO10": {"name": "GPIO10", "capabilities": ["BUTTON_IN", "GPIO"]},
            "GPIO18": {"name": "GPIO18", "capabilities": ["USB_D-"], "is_reserved": True},
            "GPIO19": {"name": "GPIO19", "capabilities": ["USB_D+"], "is_reserved": True},
            "GPIO21": {"name": "GPIO21", "capabilities": ["UART_RX", "GPIO"]},
            "GPIO43": {"name": "GPIO43", "capabilities": ["UART_TX", "GPIO"]},
            "GPIO45": {
                "name": "GPIO45",
                "capabilities": ["STRAPPING"],
                "is_bootstrapping": True,
                "description": "Strapping pin for VDD_SPI voltage selection",
            },
            "GPIO46": {
                "name": "GPIO46",
                "capabilities": ["STRAPPING"],
                "is_bootstrapping": True,
                "description": "Strapping pin for ROM code print logging",
            },
        },
        tested_notes="Verified in physical HIL loop with ESP-IDF v5.2 on ESP32-S3-WROOM-1.",
    ),
    Board(
        id="raspberry-pi-pico-w",
        name="Raspberry Pi Pico W",
        vendor="Raspberry Pi",
        mcu="RP2040 Dual ARM Cortex-M0+",
        status="draft",
        # PlatformIO's raspberrypi platform ships `pico` and
        # `nanorp2040connect` only; the W variant needs a custom board
        # definition (PICO_BOARD=pico_w) before this entry can be promoted.
        platform="raspberrypi",
        pio_board="rpipicow",
        framework="arduino",
        env_name="pico",
        connectivity="wifi",
        pin_naming="GP",
        binary_ext=".uf2",
        upload_protocol="uf2",
        specs={
            "flash_mb": 2.0,
            "psram_mb": 0.0,
            "clock_mhz": 133,
            "operating_voltage_v": 3.3,
            "wifi": "CYW43439 802.11n",
            "ble": "Bluetooth 5.2",
            "usb": "Micro-USB 1.1",
        },
        pin_map={
            "GP0": {"name": "GP0", "capabilities": ["UART0_TX", "I2C0_SDA", "GPIO"]},
            "GP1": {"name": "GP1", "capabilities": ["UART0_RX", "I2C0_SCL", "GPIO"]},
            "GP4": {"name": "GP4", "capabilities": ["I2C0_SDA", "SPI0_RX", "GPIO"]},
            "GP5": {"name": "GP5", "capabilities": ["I2C0_SCL", "SPI0_CSn", "GPIO"]},
        },
        tested_notes="Draft: PlatformIO's raspberrypi platform has no Pico W board definition yet; a custom board JSON is required before verification can pass.",
    ),
]

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
