from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

HardwareStatus = Literal["draft", "tested", "deprecated", "unverified"]


class PinCapability(BaseModel):
    name: str
    capabilities: List[str] = Field(default_factory=list)
    is_reserved: bool = False
    is_bootstrapping: bool = False
    voltage_v: float = 3.3
    description: Optional[str] = None


class BoardSpecs(BaseModel):
    flash_mb: float = 8.0
    psram_mb: float = 2.0
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
    specs: BoardSpecs
    pin_map: Dict[str, PinCapability]
    tested_notes: Optional[str] = None


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
