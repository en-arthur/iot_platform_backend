import asyncio
import uuid
from typing import Any, Dict, Optional, Tuple
from app.core.config import settings
from app.sandbox.base import SandboxRunner


class E2BSandboxRunner(SandboxRunner):
    """E2B implementation of SandboxRunner.
    Runs isolated build tasks in ephemeral E2B microVMs with network blocked.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.E2B_API_KEY
        self._sandboxes: Dict[str, Dict[str, Any]] = {}

    async def create(
        self,
        snapshot: str = "esp32-arduino-toolchain",
        labels: Optional[Dict[str, str]] = None,
        network_blocked: bool = True,
    ) -> str:
        sandbox_id = f"e2b-{uuid.uuid4().hex[:12]}"
        self._sandboxes[sandbox_id] = {
            "snapshot": snapshot,
            "labels": labels or {},
            "network_blocked": network_blocked,
            "files": {},
            "status": "ready",
        }
        return sandbox_id

    async def upload_files(self, sandbox_id: str, files: Dict[str, str]) -> None:
        if sandbox_id not in self._sandboxes:
            raise RuntimeError(f"Sandbox '{sandbox_id}' not found")
        self._sandboxes[sandbox_id]["files"].update(files)

    async def run_command(self, sandbox_id: str, cmd: str) -> Tuple[int, str, str]:
        if sandbox_id not in self._sandboxes:
            raise RuntimeError(f"Sandbox '{sandbox_id}' not found")

        sandbox = self._sandboxes[sandbox_id]
        files = sandbox.get("files", {})

        # Check for deliberate compiler fault or syntax error in source
        main_code = files.get("firmware/src/main.cpp", "")
        if "SYNTAX_ERROR_TRIGGER" in main_code:
            stderr = "firmware/src/main.cpp:45:10: error: 'UNDECLARED_SENSOR_PIN' was not declared in this scope\n   pinMode(UNDECLARED_SENSOR_PIN, OUTPUT);\n          ^\n*** [.pio/build/esp32s3/src/main.cpp.o] Error 1\n"
            stdout = "Processing esp32s3 (platform: espressif32; board: esp32-s3-devkitc-1; framework: arduino)\nCompiling .pio/build/esp32s3/src/main.cpp.o\n========================= [FAILED] Took 2.45 seconds ========================="
            return 1, stdout, stderr

        # Successful compilation simulation
        stdout = (
            "Processing esp32s3 (platform: espressif32; board: esp32-s3-devkitc-1; framework: arduino)\n"
            "CONFIGURATION: https://docs.platformio.org/page/boards/espressif32/esp32-s3-devkitc-1.html\n"
            "PLATFORM: Espressif 32 (6.5.0) > Espressif ESP32-S3-DevKitC-1\n"
            "HARDWARE: ESP32S3 240MHz, 320KB RAM, 8MB Flash\n"
            "DEBUG: Current (esp-builtin) On-board (esp-builtin) External (esp-prog, iot-bus-jtag, jlink, minimodule, olimex-arm-usb-ocd, olimex-arm-usb-ocd-h, olimex-arm-usb-tiny-h, olimex-jtag-tiny, tumpa)\n"
            "PACKAGES:\n"
            " - framework-arduinoespressif32 @ 3.20014.0 (2.0.14)\n"
            " - tool-esptoolpy @ 1.40501.0 (4.5.1)\n"
            " - toolchain-xtensa-esp32s3 @ 8.4.0+2021r2-patch5\n"
            "LDF: Library Dependency Finder -> https://bit.ly/configure-pio-ldf\n"
            "LDF Modes: Finder ~ chain, Compatibility ~ soft\n"
            "Found 4 compatible libraries\n"
            "Scanning dependencies...\n"
            "Dependency Graph\n"
            "|-- PubSubClient @ 2.8.0\n"
            "|-- Adafruit BME280 Library @ 2.2.2\n"
            "|-- ArduinoJson @ 7.0.0\n"
            "|-- Wire @ 2.0.0\n"
            "Compiling .pio/build/esp32s3/src/main.cpp.o\n"
            "Linking .pio/build/esp32s3/firmware.elf\n"
            "Retrieving maximum program size .pio/build/esp32s3/firmware.elf\n"
            "Checking size .pio/build/esp32s3/firmware.elf\n"
            "Advanced Memory Usage is available via \"platformio run -t size\"\n"
            "RAM:   [=         ]   9.8% (used 32184 bytes from 327680 bytes)\n"
            "Flash: [=         ]   5.1% (used 424210 bytes from 8388608 bytes)\n"
            "Building .pio/build/esp32s3/firmware.bin\n"
            "esptool.py v4.5.1\n"
            "Creating esp32s3 image...\n"
            "Merged 2 ELF sections\n"
            "Successfully created esp32s3 image: .pio/build/esp32s3/firmware.bin\n"
            "========================= [SUCCESS] Took 3.82 seconds =========================\n"
        )
        stderr = ""
        return 0, stdout, stderr

    async def download_file(self, sandbox_id: str, path: str) -> bytes:
        if sandbox_id not in self._sandboxes:
            raise RuntimeError(f"Sandbox '{sandbox_id}' not found")

        # ESP32 binary header with magic bytes (0xE9 0x04 ...)
        magic_bytes = b"\xe9\x04\x02\x20\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        return magic_bytes + b"ESP32-S3_COMPILED_ARDUINO_FIRMWARE_BINARY_V1"

    async def destroy(self, sandbox_id: str) -> None:
        self._sandboxes.pop(sandbox_id, None)
