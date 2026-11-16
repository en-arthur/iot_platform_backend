from typing import Any, Dict, List, Optional
from app.models.library import Board, BoardSpecs, DriverBlock, Pattern, Peripheral, PinCapability

# =============================================================================
# VERIFIED SEED DATA
# Facts (pins, voltages, addresses) come strictly from this verified library.
# Pin maps come from the vendor datasheets/module schematics and name every pin
# that is physically broken out on the board, plus the internal pins a user
# might type by mistake (marked reserved so they fail with a clear reason).
# =============================================================================


def _esp32_s3_devkitc1_pins() -> Dict[str, PinCapability]:
    """ESP32-S3-WROOM-1 pins broken out on the DevKitC-1 headers."""
    pins: Dict[str, PinCapability] = {}

    def add(gpio: int, capabilities: List[str], **kwargs: Any) -> None:
        pins[f"GPIO{gpio}"] = PinCapability(
            name=f"GPIO{gpio}",
            gpio=gpio,
            capabilities=capabilities,
            aliases=[str(gpio), f"IO{gpio}"],
            **kwargs,
        )

    # GPIO1-10: ADC1 channels 0-9, touch 1-10, RTC domain.
    for gpio in range(1, 11):
        add(gpio, [f"ADC1_CH{gpio - 1}", f"TOUCH{gpio}", "RTC", "GPIO"])
    # GPIO11-14: ADC2 channels 0-3, touch 11-14, RTC domain.
    for gpio in range(11, 15):
        add(gpio, [f"ADC2_CH{gpio - 11}", f"TOUCH{gpio}", "RTC", "GPIO"])

    add(
        0,
        ["BOOT", "RTC", "GPIO"],
        is_bootstrapping=True,
        description="Strapping pin: hold LOW at reset to enter the ROM download mode.",
    )
    add(15, ["ADC2_CH4", "XTAL_32K_P", "RTC", "GPIO"])
    add(16, ["ADC2_CH5", "XTAL_32K_N", "RTC", "GPIO"])
    add(17, ["ADC2_CH6", "UART1_TX", "RTC", "GPIO"])
    add(18, ["ADC2_CH7", "UART1_RX", "RTC", "GPIO"])
    # Native USB pins: wired to the USB connector on the DevKitC-1.
    add(
        19,
        ["ADC2_CH8", "USB_D-", "RTC"],
        is_reserved=True,
        description="Native USB D-; reserved by the on-board USB connector.",
    )
    add(
        20,
        ["ADC2_CH9", "USB_D+", "RTC"],
        is_reserved=True,
        description="Native USB D+; reserved by the on-board USB connector.",
    )
    add(21, ["RTC", "GPIO"])

    # Internal SPI0/1 flash bus (ESP32-S3-WROOM-1 datasheet, table 3).
    for gpio in range(26, 33):
        add(
            gpio,
            ["SPI_FLASH"],
            is_reserved=True,
            description="Internal SPI flash bus; not broken out on the DevKitC-1 headers.",
        )
    # GPIO33/34 are not bonded out on the WROOM-1 module.
    for gpio in (33, 34):
        add(
            gpio,
            ["NOT_BONDED"],
            is_reserved=True,
            description="Not bonded out on ESP32-S3-WROOM-1 modules.",
        )
    # GPIO35-37 are consumed by octal PSRAM on R8 variants (N8R8, N16R8...).
    for gpio in (35, 36, 37):
        add(
            gpio,
            ["PSRAM", "GPIO"],
            description=(
                "Free on quad-PSRAM modules (e.g. N8R2) but used by octal PSRAM "
                "on R8 variants. It is not in-flight configurable; verify the module."
            ),
        )

    add(38, ["GPIO"])
    for gpio, jtag in ((39, "MTCK"), (40, "MTDO"), (41, "MTDI"), (42, "MTMS")):
        add(gpio, ["JTAG", jtag, "GPIO"])
    add(43, ["UART0_TX", "GPIO"], description="UART0 TX, also the USB-serial TX line.")
    add(44, ["UART0_RX", "GPIO"], description="UART0 RX, also the USB-serial RX line.")
    add(
        45,
        ["STRAPPING", "GPIO"],
        is_bootstrapping=True,
        description="Strapping pin for VDD_SPI flash voltage selection; leave floating at boot.",
    )
    add(
        46,
        ["STRAPPING", "GPIO"],
        is_bootstrapping=True,
        description="Strapping pin for ROM message printing; leave floating at boot.",
    )
    add(47, ["GPIO"])
    add(48, ["GPIO"])
    return pins


def _esp8266_nodemcuv2_pins() -> Dict[str, PinCapability]:
    """NodeMCU v2 (ESP-12E) header labels mapped to ESP8266 GPIO numbers."""
    pins: Dict[str, PinCapability] = {}

    def add(
        key: str,
        gpio: int,
        capabilities: List[str],
        **kwargs: Any,
    ) -> None:
        pins[key] = PinCapability(
            name=key,
            gpio=gpio,
            capabilities=capabilities,
            aliases=[f"GPIO{gpio}", f"IO{gpio}", str(gpio)],
            **kwargs,
        )

    add("D0", 16, ["GPIO", "WAKE"], description="No interrupt, PWM or I2C support; wire to RST for deep-sleep wake.")
    add("D1", 5, ["I2C_SCL", "GPIO"])
    add("D2", 4, ["I2C_SDA", "GPIO"])
    add(
        "D3",
        0,
        ["BOOT", "GPIO"],
        is_bootstrapping=True,
        description="Must be HIGH at boot; the board has an external pull-up.",
    )
    add(
        "D4",
        2,
        ["LED_BUILTIN", "GPIO"],
        is_bootstrapping=True,
        description="On-board LED and boot strapping pin; must be HIGH at boot.",
    )
    add("D5", 14, ["SPI_SCK", "GPIO"])
    add("D6", 12, ["SPI_MISO", "GPIO"])
    add("D7", 13, ["SPI_MOSI", "GPIO"])
    add(
        "D8",
        15,
        ["SPI_CS", "GPIO"],
        is_bootstrapping=True,
        description="Must be LOW at boot; the board has an external pull-down.",
    )
    add("D9", 3, ["UART0_RX", "GPIO"], description="UART0 RX; shared with the USB-serial bridge.")
    add("D10", 1, ["UART0_TX", "GPIO"], description="UART0 TX; shared with the USB-serial bridge.")
    add("A0", 17, ["ADC", "TOUT"], description="10-bit ADC, 0-1.0 V range through the on-board divider.")

    # ESP-12E flash bus: GPIO6-11 are not available to the user.
    for key, gpio in (
        ("SD_CLK", 6),
        ("SD_D0", 7),
        ("SD_D1", 8),
        ("SD_D2", 9),
        ("SD_D3", 10),
        ("SD_CMD", 11),
    ):
        add(
            key,
            gpio,
            ["SPI_FLASH"],
            is_reserved=True,
            description="Internal SPI flash bus; not available on the NodeMCU headers.",
        )
    return pins


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
        specs=BoardSpecs(
            flash_mb=8.0,
            psram_mb=2.0,
            clock_mhz=240,
            operating_voltage_v=3.3,
            wifi="802.11 b/g/n (2.4 GHz)",
            ble="Bluetooth 5.0 (BLE)",
            usb="Native USB OTG & USB-to-UART",
        ),
        pin_map=_esp32_s3_devkitc1_pins(),
        default_pins={
            "i2c_sda": "GPIO4",
            "i2c_scl": "GPIO5",
            "relay": "GPIO9",
            "button": "GPIO10",
        },
        tested_notes="PlatformIO build recipe verified; pin map from the ESP32-S3-WROOM-1 datasheet and DevKitC-1 header layout.",
    ),
    Board(
        id="nodemcuv2",
        name="NodeMCU v2 (ESP8266 ESP-12E)",
        vendor="Espressif / NodeMCU",
        mcu="ESP8266EX (Xtensa L106, 80 MHz)",
        status="tested",
        platform="espressif8266",
        pio_board="nodemcuv2",
        framework="arduino",
        env_name="nodemcuv2",
        connectivity="wifi",
        pin_naming="D",
        binary_ext=".bin",
        upload_protocol="esptool",
        specs=BoardSpecs(
            flash_mb=4.0,
            psram_mb=0.0,
            clock_mhz=80,
            operating_voltage_v=3.3,
            wifi="802.11 b/g/n (2.4 GHz)",
            usb="Micro-USB (CP2102 USB-serial)",
        ),
        pin_map=_esp8266_nodemcuv2_pins(),
        default_pins={
            "i2c_sda": "D2",
            "i2c_scl": "D1",
            "relay": "D5",
            "button": "D6",
        },
        tested_notes="Second supported family: ESP8266 Arduino core via PlatformIO espressif8266. Pin labels follow the NodeMCU silkscreen.",
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
        specs=BoardSpecs(
            flash_mb=2.0,
            psram_mb=0.0,
            clock_mhz=133,
            operating_voltage_v=3.3,
            wifi="CYW43439 802.11n",
            ble="Bluetooth 5.2",
            usb="Micro-USB 1.1",
        ),
        pin_map={
            "GP0": {"name": "GP0", "gpio": 0, "capabilities": ["UART0_TX", "I2C0_SDA", "GPIO"], "aliases": ["GPIO0"]},
            "GP1": {"name": "GP1", "gpio": 1, "capabilities": ["UART0_RX", "I2C0_SCL", "GPIO"], "aliases": ["GPIO1"]},
            "GP4": {"name": "GP4", "gpio": 4, "capabilities": ["I2C0_SDA", "SPI0_RX", "GPIO"], "aliases": ["GPIO4"]},
            "GP5": {"name": "GP5", "gpio": 5, "capabilities": ["I2C0_SCL", "SPI0_CSn", "GPIO"], "aliases": ["GPIO5"]},
        },
        default_pins={
            "i2c_sda": "GP4",
            "i2c_scl": "GP5",
            "relay": "GP0",
            "button": "GP1",
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
