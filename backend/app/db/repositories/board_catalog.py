"""Board library used by the wizard, code generator and build preflight.

Every entry is a build recipe (PlatformIO platform/board/environment) plus a
conservative pin map. The map lists only pins that are physically broken out on
that board's headers, and marks flash, USB and strapping pins as reserved with a
reason, so generated code never ends up driving the flash bus or an unbonded
pin.

All boards here share the two platforms baked into the verification image
(``espressif32`` for ESP32/S2/S3/C3/C6 and ``espressif8266``), so every entry
can be compiled with outbound network access blocked.
"""

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from app.models.library import Board, BoardSpecs, PinCapability

ESP32_PLATFORM = "espressif32"
ESP8266_PLATFORM = "espressif8266"

WIFI_24 = "802.11 b/g/n (2.4 GHz)"
USB_UART = "USB-to-UART bridge (no native USB)"

# GPIO -> (capability, description, is_bootstrapping) for pins that must not be
# used by generated code. Kept per chip so a mistake fails with a real reason.
CHIP_RULES: Dict[str, Dict[str, Any]] = {
    "esp32": {
        "adc1": {
            36: "ADC1_CH0",
            37: "ADC1_CH1",
            38: "ADC1_CH2",
            39: "ADC1_CH3",
            32: "ADC1_CH4",
            33: "ADC1_CH5",
            34: "ADC1_CH6",
            35: "ADC1_CH7",
        },
        "adc2": {
            4: "ADC2_CH0",
            0: "ADC2_CH1",
            2: "ADC2_CH2",
            15: "ADC2_CH3",
            13: "ADC2_CH4",
            12: "ADC2_CH5",
            14: "ADC2_CH6",
            27: "ADC2_CH7",
            25: "ADC2_CH8",
            26: "ADC2_CH9",
        },
        "touch": {0, 2, 4, 12, 13, 14, 15, 27, 32, 33},
        "input_only": {34, 35, 36, 39},
        "boot": {0},
        "uart": {1: "UART0_TX", 3: "UART0_RX"},
        "reserved": {
            6: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False),
            7: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False),
            8: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False),
            9: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False),
            10: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False),
            11: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False),
            20: ("NOT_BONDED", "Not bonded out on ESP32-WROOM modules.", False),
            24: ("NOT_BONDED", "Not bonded out on ESP32-WROOM modules.", False),
        },
    },
    "esp32s2": {
        "adc1": {gpio: f"ADC1_CH{gpio - 1}" for gpio in range(1, 11)},
        "adc2": {gpio: f"ADC2_CH{gpio - 11}" for gpio in range(11, 21)},
        "touch": set(range(1, 15)),
        "input_only": {46},
        "boot": {0, 46},
        "uart": {43: "UART0_TX", 44: "UART0_RX"},
        "reserved": {
            19: ("USB_D-", "Native USB D-; reserved while the USB port is used.", False),
            20: ("USB_D+", "Native USB D+; reserved while the USB port is used.", False),
            22: ("NOT_BONDED", "Not bonded out on ESP32-S2 modules.", False),
            23: ("NOT_BONDED", "Not bonded out on ESP32-S2 modules.", False),
            24: ("NOT_BONDED", "Not bonded out on ESP32-S2 modules.", False),
            25: ("NOT_BONDED", "Not bonded out on ESP32-S2 modules.", False),
        },
    },
    "esp32s3": {
        "adc1": {gpio: f"ADC1_CH{gpio - 1}" for gpio in range(1, 11)},
        "adc2": {gpio: f"ADC2_CH{gpio - 11}" for gpio in range(11, 21)},
        "touch": set(range(1, 15)),
        "input_only": set(),
        "boot": {0, 45, 46},
        "uart": {43: "UART0_TX", 44: "UART0_RX"},
        "reserved": {
            **{
                gpio: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False)
                for gpio in range(26, 33)
            },
            19: ("USB_D-", "Native USB D-; reserved while the USB port is used.", False),
            20: ("USB_D+", "Native USB D+; reserved while the USB port is used.", False),
            33: ("NOT_BONDED", "Not bonded out on ESP32-S3-WROOM modules.", False),
            34: ("NOT_BONDED", "Not bonded out on ESP32-S3-WROOM modules.", False),
        },
    },
    "esp32c3": {
        "adc1": {0: "ADC1_CH0", 1: "ADC1_CH1", 2: "ADC1_CH2", 3: "ADC1_CH3", 4: "ADC1_CH4"},
        "adc2": {5: "ADC2_CH0"},
        "touch": set(),
        "input_only": set(),
        "boot": {2, 8, 9},
        "uart": {20: "UART0_RX", 21: "UART0_TX"},
        "reserved": {
            **{
                gpio: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False)
                for gpio in range(11, 18)
            },
            18: ("USB_D-", "Native USB D-; reserved while the USB port is used.", False),
            19: ("USB_D+", "Native USB D+; reserved while the USB port is used.", False),
        },
    },
    "esp32c6": {
        "adc1": {gpio: f"ADC1_CH{gpio}" for gpio in range(0, 7)},
        "adc2": {},
        "touch": set(),
        "input_only": set(),
        "boot": {4, 5, 8, 9, 15},
        "uart": {16: "UART0_TX", 17: "UART0_RX"},
        "reserved": {
            **{
                gpio: ("SPI_FLASH", "Internal SPI flash bus; not available on the headers.", False)
                for gpio in range(24, 31)
            },
            12: ("USB_D-", "Native USB D-; reserved while the USB port is used.", False),
            13: ("USB_D+", "Native USB D+; reserved while the USB port is used.", False),
        },
    },
}

# First choice wins; the next entry is used when the board does not break out
# that pin. SDA/SCL follow the usual Arduino defaults for each chip.
DEFAULT_ROLES: Dict[str, Dict[str, List[int]]] = {
    "esp32": {"sda": [21, 4], "scl": [22, 5], "relay": [5, 26, 12], "button": [4, 27, 13]},
    "esp32s3": {"sda": [4, 8], "scl": [5, 9], "relay": [9, 12], "button": [10, 11]},
    "esp32s2": {"sda": [33, 8], "scl": [34, 9], "relay": [5, 7], "button": [4, 6]},
    "esp32c3": {"sda": [4, 8], "scl": [5, 9], "relay": [6, 10], "button": [7, 3]},
    "esp32c6": {"sda": [4, 6], "scl": [5, 7], "relay": [10, 3], "button": [11, 2]},
    "esp8266": {"sda": [4, 5], "scl": [5, 4], "relay": [14, 12], "button": [12, 13]},
}


def _gpio_key(gpio: int) -> str:
    return f"GPIO{gpio}"


def _chip_pins(chip: str, exposed: Sequence[int]) -> Dict[str, PinCapability]:
    """Pin map for a board that labels its headers with GPIO numbers."""
    rules = CHIP_RULES[chip]
    pins: Dict[str, PinCapability] = {}

    for gpio in exposed:
        capabilities = ["GPIO"]
        if gpio in rules["adc1"]:
            capabilities.append(rules["adc1"][gpio])
        if gpio in rules["adc2"]:
            capabilities.append(rules["adc2"][gpio])
        if gpio in rules["touch"]:
            capabilities.append(f"TOUCH{gpio}")
        if gpio in rules["input_only"]:
            capabilities.append("INPUT_ONLY")
        if gpio in rules["uart"]:
            capabilities.append(rules["uart"][gpio])

        kwargs: Dict[str, Any] = {}
        if gpio in rules["boot"]:
            capabilities.insert(0, "BOOT")
            kwargs["is_bootstrapping"] = True
            kwargs["description"] = (
                "Strapping pin: its level at reset selects a boot mode. "
                "Avoid driving it at power-up."
            )
        key = _gpio_key(gpio)
        pins[key] = PinCapability(
            name=key,
            gpio=gpio,
            capabilities=capabilities,
            aliases=[str(gpio), f"IO{gpio}"],
            **kwargs,
        )

    for gpio, (capability, description, boot) in rules["reserved"].items():
        key = _gpio_key(gpio)
        pins[key] = PinCapability(
            name=key,
            gpio=gpio,
            capabilities=[capability],
            is_reserved=True,
            is_bootstrapping=boot,
            description=description,
            aliases=[str(gpio), f"IO{gpio}"],
        )
    return pins


def _esp8266_d_pins() -> Dict[str, PinCapability]:
    """NodeMCU / Wemos D1 mini silkscreen labels mapped to ESP8266 GPIOs."""
    pins: Dict[str, PinCapability] = {}

    def add(key: str, gpio: int, capabilities: List[str], **kwargs: Any) -> None:
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
    add("D3", 0, ["BOOT", "GPIO"], is_bootstrapping=True,
        description="Must be HIGH at boot; the board has an external pull-up.")
    add("D4", 2, ["LED_BUILTIN", "GPIO"], is_bootstrapping=True,
        description="On-board LED and boot strapping pin; must be HIGH at boot.")
    add("D5", 14, ["SPI_SCK", "GPIO"])
    add("D6", 12, ["SPI_MISO", "GPIO"])
    add("D7", 13, ["SPI_MOSI", "GPIO"])
    add("D8", 15, ["SPI_CS", "GPIO"], is_bootstrapping=True,
        description="Must be LOW at boot; the board has an external pull-down.")
    add("D9", 3, ["UART0_RX", "GPIO"], description="UART0 RX; shared with the USB-serial bridge.")
    add("D10", 1, ["UART0_TX", "GPIO"], description="UART0 TX; shared with the USB-serial bridge.")
    add("A0", 17, ["ADC", "TOUT"], description="10-bit ADC, 0-1.0 V range through the on-board divider.")

    for key, gpio in (
        ("SD_CLK", 6),
        ("SD_D0", 7),
        ("SD_D1", 8),
        ("SD_D2", 9),
        ("SD_D3", 10),
        ("SD_CMD", 11),
    ):
        add(key, gpio, ["SPI_FLASH"], is_reserved=True,
            description="Internal SPI flash bus; not available on the headers.")
    return pins


def _esp8266_gpio_pins(exposed: Sequence[int] = (0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16)) -> Dict[str, PinCapability]:
    """ESP8266 modules that label their pins with GPIO numbers."""
    pins: Dict[str, PinCapability] = {}

    def add(gpio: int, capabilities: List[str], **kwargs: Any) -> None:
        key = _gpio_key(gpio)
        pins[key] = PinCapability(
            name=key,
            gpio=gpio,
            capabilities=capabilities,
            aliases=[str(gpio), f"IO{gpio}"],
            **kwargs,
        )

    for gpio in exposed:
        capabilities = ["GPIO"]
        if gpio == 0:
            capabilities.insert(0, "BOOT")
            add(gpio, capabilities, is_bootstrapping=True,
                description="Must be HIGH at boot; pulled up on most modules.")
        elif gpio == 1:
            add(gpio, ["UART0_TX", "GPIO"], description="UART0 TX; shared with the USB-serial bridge.")
        elif gpio == 2:
            add(gpio, ["LED_BUILTIN", "GPIO"], is_bootstrapping=True,
                description="Must be HIGH at boot; drives the on-board LED.")
        elif gpio == 3:
            add(gpio, ["UART0_RX", "GPIO"], description="UART0 RX; shared with the USB-serial bridge.")
        elif gpio == 15:
            add(gpio, ["SPI_CS", "GPIO"], is_bootstrapping=True,
                description="Must be LOW at boot; the module has an external pull-down.")
        elif gpio == 16:
            add(gpio, ["GPIO", "WAKE"], description="No interrupt, PWM or I2C support.")
        elif gpio == 17:
            add(gpio, ["ADC", "TOUT"], description="10-bit ADC, 0-1.0 V range.")
        else:
            add(gpio, capabilities)

    for gpio in range(6, 12):
        add(gpio, ["SPI_FLASH"], is_reserved=True,
            description="Internal SPI flash bus; not available on the headers.")
    return pins


def _defaults(pins: Dict[str, PinCapability], chip: str) -> Dict[str, str]:
    """Pick the I2C/relay/button defaults from the pins the board really has."""
    role_names = {
        "sda": "i2c_sda",
        "scl": "i2c_scl",
        "relay": "relay",
        "button": "button",
    }
    defaults: Dict[str, str] = {}
    used: set = set()
    for role, preferred in DEFAULT_ROLES[chip].items():
        for gpio in preferred:
            match = next(
                (
                    key
                    for key, pin in pins.items()
                    if pin.gpio == gpio and not pin.is_reserved and key not in used
                ),
                None,
            )
            if match:
                defaults[role_names[role]] = match
                used.add(match)
                break
    return defaults


def _board(
    board_id: str,
    name: str,
    vendor: str,
    mcu: str,
    pio_board: str,
    env: str,
    chip: str,
    *,
    flash_mb: float,
    clock_mhz: int,
    exposed: Optional[Sequence[int]] = None,
    pins: Optional[Dict[str, PinCapability]] = None,
    psram_mb: float = 0.0,
    connectivity: str = "wifi",
    pin_naming: str = "GPIO",
    platform: str = ESP32_PLATFORM,
    ble: Optional[str] = None,
    usb: Optional[str] = USB_UART,
    notes: Optional[str] = None,
    defaults: Optional[Dict[str, str]] = None,
    status: str = "tested",
    binary_ext: str = ".bin",
    upload_protocol: str = "esptool",
) -> Board:
    pin_map = pins if pins is not None else _chip_pins(chip, exposed or ())
    return Board(
        id=board_id,
        name=name,
        vendor=vendor,
        mcu=mcu,
        status=status,
        platform=platform,
        pio_board=pio_board,
        framework="arduino",
        env_name=env,
        connectivity=connectivity,
        pin_naming=pin_naming,
        binary_ext=binary_ext,
        upload_protocol=upload_protocol,
        specs=BoardSpecs(
            flash_mb=flash_mb,
            psram_mb=psram_mb,
            clock_mhz=clock_mhz,
            operating_voltage_v=3.3,
            wifi=WIFI_24 if connectivity in ("wifi", "ethernet") else None,
            ble=ble,
            usb=usb,
        ),
        pin_map=pin_map,
        default_pins=defaults if defaults is not None else _defaults(pin_map, chip),
        tested_notes=notes,
    )


ESP32_30_PIN = (4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33)
ESP32_38_PIN = ESP32_30_PIN + (34, 35, 36, 39)
S3_DEVKIT = tuple(range(1, 19)) + (21,) + tuple(range(38, 49))
C3_DEVKIT = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 21)
C6_DEVKIT = tuple(range(0, 12)) + tuple(range(14, 24))
S2_DEVKIT = tuple(range(0, 19)) + (21,) + tuple(range(33, 47))


def _pico_pins() -> Dict[str, PinCapability]:
    """RP2040 GPIO0-28, used only by the draft Pico W entry."""
    pins: Dict[str, PinCapability] = {}
    for gpio in range(0, 29):
        key = f"GP{gpio}"
        pins[key] = PinCapability(
            name=key,
            gpio=gpio,
            capabilities=["GPIO", "ADC"] if gpio < 4 else ["GPIO"],
            aliases=[str(gpio), f"GPIO{gpio}"],
        )
    return pins


def _esp8266_boards() -> List[Board]:
    d_pins = _esp8266_d_pins()
    d_defaults = {"i2c_sda": "D2", "i2c_scl": "D1", "relay": "D5", "button": "D6"}
    module_notes = "ESP8266 Arduino core via PlatformIO espressif8266; pin labels follow the module silkscreen."

    return [
        _board(
            "nodemcuv2",
            "NodeMCU v2 (ESP8266 ESP-12E)",
            "Espressif / NodeMCU",
            "ESP8266EX (Xtensa L106, 80 MHz)",
            "nodemcuv2",
            "nodemcuv2",
            "esp8266",
            platform=ESP8266_PLATFORM,
            flash_mb=4.0,
            clock_mhz=80,
            pin_naming="D",
            pins=d_pins,
            defaults=d_defaults,
            usb="Micro-USB (CP2102 USB-serial)",
            notes="Second supported family: ESP8266 Arduino core via PlatformIO espressif8266. Pin labels follow the NodeMCU silkscreen.",
        ),
        _board(
            "d1_mini",
            "WEMOS D1 Mini (ESP8266)",
            "WEMOS",
            "ESP8266EX (Xtensa L106, 80 MHz)",
            "d1_mini",
            "d1mini",
            "esp8266",
            platform=ESP8266_PLATFORM,
            flash_mb=4.0,
            clock_mhz=80,
            pin_naming="D",
            pins=d_pins,
            defaults=d_defaults,
            usb="Micro-USB (CH340 USB-serial)",
            notes=module_notes,
        ),
        _board(
            "esp12e",
            "ESP-12E module (ESP8266)",
            "Espressif",
            "ESP8266EX (Xtensa L106, 80 MHz)",
            "esp12e",
            "esp12e",
            "esp8266",
            platform=ESP8266_PLATFORM,
            flash_mb=4.0,
            clock_mhz=80,
            pins=_esp8266_gpio_pins(),
            usb="None on the module; use a USB-serial adapter",
            notes="Bare ESP-12E module with GPIO-number labels.",
        ),
        _board(
            "huzzah",
            "Adafruit Feather HUZZAH ESP8266",
            "Adafruit",
            "ESP8266EX (Xtensa L106, 80 MHz)",
            "huzzah",
            "huzzah",
            "esp8266",
            platform=ESP8266_PLATFORM,
            flash_mb=4.0,
            clock_mhz=80,
            pins=_esp8266_gpio_pins((0, 2, 4, 5, 12, 13, 14, 15, 16)),
            usb="Micro-USB (CP2104 USB-serial)",
            notes=module_notes,
        ),
    ]


SEED_BOARDS: List[Board] = [
    # ---- ESP32 (classic Xtensa) -------------------------------------------
    _board(
        "esp32dev",
        "ESP32 DevKit V1 (30-pin)",
        "Espressif / DOIT",
        "ESP32 (Xtensa Dual-core 32-bit LX6)",
        "esp32dev",
        "esp32dev",
        "esp32",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=ESP32_30_PIN,
        ble="Bluetooth 4.2 (BLE)",
        notes="The most common cheap ESP32 devkit; 30-pin layout.",
    ),
    _board(
        "esp32doit-devkit-v1",
        "DOIT ESP32 DevKit V1",
        "DOIT",
        "ESP32 (Xtensa Dual-core 32-bit LX6)",
        "esp32doit-devkit-v1",
        "doit32",
        "esp32",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=ESP32_30_PIN,
        ble="Bluetooth 4.2 (BLE)",
        notes="DOIT variant of the 30-pin ESP32 devkit.",
    ),
    _board(
        "nodemcu-32s",
        "NodeMCU-32S",
        "Ai-Thinker",
        "ESP32 (Xtensa Dual-core 32-bit LX6)",
        "nodemcu-32s",
        "nodemcu32s",
        "esp32",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=ESP32_30_PIN,
        ble="Bluetooth 4.2 (BLE)",
        notes="ESP32-WROOM-32 in the NodeMCU form factor.",
    ),
    _board(
        "lolin32",
        "WEMOS LOLIN32",
        "WEMOS",
        "ESP32 (Xtensa Dual-core 32-bit LX6)",
        "lolin32",
        "lolin32",
        "esp32",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=ESP32_30_PIN,
        ble="Bluetooth 4.2 (BLE)",
        notes="WEMOS ESP32 board with a JST battery connector.",
    ),
    _board(
        "wemos_d1_mini32",
        "WEMOS D1 Mini ESP32",
        "WEMOS",
        "ESP32 (Xtensa Dual-core 32-bit LX6)",
        "wemos_d1_mini32",
        "d1mini32",
        "esp32",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=ESP32_30_PIN,
        ble="Bluetooth 4.2 (BLE)",
        notes="ESP32 in the small D1 mini footprint.",
    ),
    _board(
        "featheresp32",
        "Adafruit Feather ESP32",
        "Adafruit",
        "ESP32 (Xtensa Dual-core 32-bit LX6)",
        "featheresp32",
        "feather32",
        "esp32",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=ESP32_38_PIN,
        ble="Bluetooth 4.2 (BLE)",
        notes="Feather form factor with a LiPo charger.",
    ),
    _board(
        "az-delivery-devkit-v4",
        "AZ-Delivery ESP32 DevKit C V4",
        "AZ-Delivery",
        "ESP32 (Xtensa Dual-core 32-bit LX6)",
        "az-delivery-devkit-v4",
        "az32",
        "esp32",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=ESP32_38_PIN,
        ble="Bluetooth 4.2 (BLE)",
        notes="38-pin ESP32 devkit, popular in Europe.",
    ),
    _board(
        "esp32cam",
        "ESP32-CAM (AI-Thinker)",
        "AI-Thinker",
        "ESP32 (Xtensa Dual-core 32-bit LX6)",
        "esp32cam",
        "esp32cam",
        "esp32",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=(4, 12, 13, 14, 15, 16),
        ble="Bluetooth 4.2 (BLE)",
        usb="None on the board; use a USB-serial adapter",
        defaults={
            "i2c_sda": "GPIO14",
            "i2c_scl": "GPIO15",
            "relay": "GPIO12",
            "button": "GPIO13",
        },
        notes="Only the pins on the camera header are exposed; they double as camera/SD lines, so leave the camera disconnected when you use them.",
    ),
    # ---- ESP32-S3 ----------------------------------------------------------
    _board(
        "esp32-s3-devkitc-1",
        "ESP32-S3 DevKitC-1",
        "Espressif",
        "ESP32-S3 (Xtensa Dual-core 32-bit LX7)",
        "esp32-s3-devkitc-1",
        "esp32s3",
        "esp32s3",
        flash_mb=8.0,
        psram_mb=2.0,
        clock_mhz=240,
        exposed=S3_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB OTG & USB-to-UART",
        notes="PlatformIO build recipe verified; pin map from the ESP32-S3-WROOM-1 datasheet and DevKitC-1 header layout.",
    ),
    _board(
        "adafruit_feather_esp32s3",
        "Adafruit Feather ESP32-S3",
        "Adafruit",
        "ESP32-S3 (Xtensa Dual-core 32-bit LX7)",
        "adafruit_feather_esp32s3",
        "feathers3",
        "esp32s3",
        flash_mb=4.0,
        psram_mb=2.0,
        clock_mhz=240,
        exposed=S3_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C) & USB-to-UART",
        notes="Feather S3 with 2 MB PSRAM.",
    ),
    _board(
        "lolin_s3",
        "WEMOS LOLIN S3",
        "WEMOS",
        "ESP32-S3 (Xtensa Dual-core 32-bit LX7)",
        "lolin_s3",
        "lolins3",
        "esp32s3",
        flash_mb=16.0,
        psram_mb=8.0,
        clock_mhz=240,
        exposed=S3_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C) & USB-to-UART",
        notes="16 MB flash / 8 MB PSRAM variant.",
    ),
    _board(
        "lolin_s3_mini",
        "WEMOS LOLIN S3 Mini",
        "WEMOS",
        "ESP32-S3 (Xtensa Dual-core 32-bit LX7)",
        "lolin_s3_mini",
        "lolins3mini",
        "esp32s3",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=tuple(range(1, 15)),
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C)",
        notes="Small S3 board; only GPIO1-14 are broken out.",
    ),
    _board(
        "seeed_xiao_esp32s3",
        "Seeed XIAO ESP32S3",
        "Seeed Studio",
        "ESP32-S3 (Xtensa Dual-core 32-bit LX7)",
        "seeed_xiao_esp32s3",
        "xiaos3",
        "esp32s3",
        flash_mb=8.0,
        psram_mb=8.0,
        clock_mhz=240,
        exposed=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 43, 44),
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C)",
        notes="Thumb-sized S3 board with 11 header pins.",
    ),
    _board(
        "dfrobot_firebeetle2_esp32s3",
        "DFRobot FireBeetle 2 ESP32-S3",
        "DFRobot",
        "ESP32-S3 (Xtensa Dual-core 32-bit LX7)",
        "dfrobot_firebeetle2_esp32s3",
        "firebeetles3",
        "esp32s3",
        flash_mb=4.0,
        psram_mb=2.0,
        clock_mhz=240,
        exposed=S3_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C) & USB-to-UART",
        notes="Feather-compatible S3 board with a LiPo charger.",
    ),
    _board(
        "arduino_nano_esp32",
        "Arduino Nano ESP32",
        "Arduino",
        "ESP32-S3 (Xtensa Dual-core 32-bit LX7)",
        "arduino_nano_esp32",
        "nanoesp32",
        "esp32s3",
        flash_mb=16.0,
        psram_mb=0.0,
        clock_mhz=240,
        exposed=tuple(range(1, 19)) + (21,) + tuple(range(38, 49)),
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C)",
        notes="Arduino-branded Nano footprint, 16 MB flash.",
    ),
    # ---- ESP32-C3 ----------------------------------------------------------
    _board(
        "esp32-c3-devkitm-1",
        "ESP32-C3 DevKitM-1",
        "Espressif",
        "ESP32-C3 (RISC-V single-core, 160 MHz)",
        "esp32-c3-devkitm-1",
        "esp32c3",
        "esp32c3",
        flash_mb=4.0,
        clock_mhz=160,
        exposed=C3_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        notes="Official C3 mini devkit.",
    ),
    _board(
        "esp32-c3-devkitc-02",
        "ESP32-C3 DevKitC-02",
        "Espressif",
        "ESP32-C3 (RISC-V single-core, 160 MHz)",
        "esp32-c3-devkitc-02",
        "c3devkitc",
        "esp32c3",
        flash_mb=4.0,
        clock_mhz=160,
        exposed=C3_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        notes="ESP32-C3-WROOM-02 devkit.",
    ),
    _board(
        "lolin_c3_mini",
        "WEMOS LOLIN C3 Mini",
        "WEMOS",
        "ESP32-C3 (RISC-V single-core, 160 MHz)",
        "lolin_c3_mini",
        "lolinc3",
        "esp32c3",
        flash_mb=4.0,
        clock_mhz=160,
        exposed=C3_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C)",
        notes="D1-mini-sized C3 board.",
    ),
    _board(
        "seeed_xiao_esp32c3",
        "Seeed XIAO ESP32C3",
        "Seeed Studio",
        "ESP32-C3 (RISC-V single-core, 160 MHz)",
        "seeed_xiao_esp32c3",
        "xiaoc3",
        "esp32c3",
        flash_mb=4.0,
        clock_mhz=160,
        exposed=(2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 21),
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C)",
        notes="Thumb-sized C3 board with 11 header pins.",
    ),
    _board(
        "adafruit_qtpy_esp32c3",
        "Adafruit QT Py ESP32-C3",
        "Adafruit",
        "ESP32-C3 (RISC-V single-core, 160 MHz)",
        "adafruit_qtpy_esp32c3",
        "qtpyc3",
        "esp32c3",
        flash_mb=4.0,
        clock_mhz=160,
        exposed=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C) & STEMMA QT",
        notes="QT Py form factor.",
    ),
    _board(
        "dfrobot_beetle_esp32c3",
        "DFRobot Beetle ESP32-C3",
        "DFRobot",
        "ESP32-C3 (RISC-V single-core, 160 MHz)",
        "dfrobot_beetle_esp32c3",
        "beetlec3",
        "esp32c3",
        flash_mb=4.0,
        clock_mhz=160,
        exposed=C3_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C)",
        notes="Very small C3 board.",
    ),
    # ---- ESP32-C6 ----------------------------------------------------------
    _board(
        "esp32-c6-devkitc-1",
        "ESP32-C6 DevKitC-1",
        "Espressif",
        "ESP32-C6 (RISC-V single-core, 160 MHz)",
        "esp32-c6-devkitc-1",
        "esp32c6",
        "esp32c6",
        flash_mb=8.0,
        clock_mhz=160,
        exposed=C6_DEVKIT,
        ble="Bluetooth 5.0 (BLE)",
        notes="Wi-Fi 6 + Thread/Zigbee capable devkit.",
    ),
    _board(
        "seeed_xiao_esp32c6",
        "Seeed XIAO ESP32C6",
        "Seeed Studio",
        "ESP32-C6 (RISC-V single-core, 160 MHz)",
        "seeed_xiao_esp32c6",
        "xiaoc6",
        "esp32c6",
        flash_mb=4.0,
        clock_mhz=160,
        exposed=(0, 1, 2, 3, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23),
        ble="Bluetooth 5.0 (BLE)",
        usb="Native USB (USB-C)",
        defaults={
            "i2c_sda": "GPIO22",
            "i2c_scl": "GPIO23",
            "relay": "GPIO20",
            "button": "GPIO21",
        },
        notes="Thumb-sized C6 board with 14 header pins.",
    ),
    # ---- ESP32-S2 ----------------------------------------------------------
    _board(
        "esp32-s2-saola-1",
        "ESP32-S2 Saola-1",
        "Espressif",
        "ESP32-S2 (Xtensa single-core 32-bit LX7, 240 MHz)",
        "esp32-s2-saola-1",
        "esp32s2",
        "esp32s2",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=S2_DEVKIT,
        notes="Official S2 devkit; no Bluetooth.",
    ),
    _board(
        "lolin_s2_mini",
        "WEMOS LOLIN S2 Mini",
        "WEMOS",
        "ESP32-S2 (Xtensa single-core 32-bit LX7, 240 MHz)",
        "lolin_s2_mini",
        "lolins2",
        "esp32s2",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=tuple(range(1, 15)),
        usb="Native USB (USB-C)",
        notes="Small S2 board; GPIO1-14 are broken out.",
    ),
    _board(
        "adafruit_feather_esp32s2",
        "Adafruit Feather ESP32-S2",
        "Adafruit",
        "ESP32-S2 (Xtensa single-core 32-bit LX7, 240 MHz)",
        "adafruit_feather_esp32s2",
        "feathers2",
        "esp32s2",
        flash_mb=4.0,
        clock_mhz=240,
        exposed=S2_DEVKIT,
        notes="Feather form factor; no Bluetooth.",
    ),
    # Deliberately a draft: PlatformIO's raspberrypi platform ships `pico`
    # (no Wi-Fi) and `nanorp2040connect`, so a Pico W needs a custom board
    # definition before it can be offered. Hidden from the wizard (drafts are
    # not listed) so nobody gets firmware that cannot connect.
    _board(
        "raspberry-pi-pico-w",
        "Raspberry Pi Pico W",
        "Raspberry Pi",
        "RP2040 Dual ARM Cortex-M0+",
        "rpipicow",
        "pico",
        "rp2040",
        platform="raspberrypi",
        flash_mb=2.0,
        clock_mhz=133,
        pin_naming="GP",
        pins=_pico_pins(),
        usb="Micro-USB (native)",
        status="draft",
        binary_ext=".uf2",
        upload_protocol="uf2",
        defaults={
            "i2c_sda": "GP4",
            "i2c_scl": "GP5",
            "relay": "GP6",
            "button": "GP7",
        },
        notes="Draft: PlatformIO has no verified Pico W board definition yet.",
    ),
] + _esp8266_boards()
