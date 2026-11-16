from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

HardwareStatus = Literal["draft", "tested", "deprecated", "unverified"]
# How the board reaches the platform's cloud contract. BLE-only boards cannot
# speak MQTT/IP and must not be offered for the standard firmware flow.
Connectivity = Literal["wifi", "ethernet", "ble", "none"]


class PinCapability(BaseModel):
    name: str
    capabilities: List[str] = Field(default_factory=list)
    is_reserved: bool = False
    is_bootstrapping: bool = False
    voltage_v: float = 3.3
    description: Optional[str] = None

    # The MCU GPIO number this header pin drives. Code generation emits this
    # number, never the silkscreen label, so "D2" and "GPIO4" are the same pin.
    gpio: Optional[int] = None
    # Alternative labels users may type or existing specs may contain.
    aliases: List[str] = Field(default_factory=list)


class BoardSpecs(BaseModel):
    # Required: a board that forgets to declare its flash would otherwise
    # inherit the ESP32-S3 numbers and pass the OTA sizing rule by accident.
    flash_mb: float
    psram_mb: float = 0.0
    clock_mhz: int = 240
    operating_voltage_v: float = 3.3
    wifi: Optional[str] = None
    ble: Optional[str] = None
    usb: Optional[str] = None


class Board(BaseModel):
    id: str
    name: str
    vendor: str
    mcu: str
    status: HardwareStatus = "tested"

    # PlatformIO build recipe. This is the single source of truth for code
    # generation: platformio.ini is derived from these fields, never hardcoded.
    platform: str  # PlatformIO development platform, e.g. "espressif32"
    pio_board: str  # PlatformIO board id, e.g. "esp32-s3-devkitc-1"
    framework: str = "arduino"
    env_name: str  # PlatformIO environment name, e.g. "esp32s3"
    connectivity: Connectivity
    pin_naming: str  # How this board names pins: "GPIO", "GP", "D", "P"
    binary_ext: str = ".bin"
    upload_protocol: str = "esptool"

    specs: BoardSpecs
    pin_map: Dict[str, PinCapability]

    # Role -> pin label, used to seed a new project's spec. Kept on the board so
    # code generation never falls back to ESP32 pin numbers on another MCU.
    default_pins: Dict[str, str] = Field(default_factory=dict)
    tested_notes: Optional[str] = None

    def resolve_pin(self, label: Any) -> Optional[str]:
        """Canonical pin_map key for a user-supplied label ("D2", "gpio4", "4")."""
        if label is None:
            return None
        needle = str(label).strip().lower()
        if not needle:
            return None
        for key, pin in self.pin_map.items():
            names = {key.lower(), pin.name.lower(), *(a.lower() for a in pin.aliases)}
            if pin.gpio is not None:
                names.add(str(pin.gpio))
            if needle in names:
                return key
        return None

    def pin_number(self, label: Any) -> Optional[int]:
        """GPIO number for a label, or None when the board does not have it."""
        key = self.resolve_pin(label)
        return self.pin_map[key].gpio if key else None


class Peripheral(BaseModel):
    id: str
    name: str
    category: str  # Sensors | Actuators | Inputs | Displays | Power
    interface: str  # I2C | SPI | UART | Digital Input | Digital Output | ADC
    default_address: Optional[str] = None
    operating_voltage_v: float = 3.3
    pins_required: List[str]
    status: HardwareStatus = "tested"
    description: str
    datasheet_url: Optional[str] = None


class DriverBlock(BaseModel):
    id: str
    peripheral_id: str
    framework: str = "esp-idf"
    header_code: str
    source_code: str
    config_schema: Dict[str, Any] = Field(default_factory=dict)


class Pattern(BaseModel):
    id: str
    name: str
    description: str
    category: str  # Power | Sampling | Networking | Lifecycle
    template_slots: List[str]
    status: HardwareStatus = "tested"
