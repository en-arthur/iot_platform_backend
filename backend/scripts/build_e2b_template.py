"""Build the shared E2B template used by verification runs.

Run this ONCE (or again when the toolchain/libraries change). It creates an
image with PlatformIO and the ESP32 toolchain pre-installed, so each
verification sandbox can compile offline in seconds. It is not per project or
per device.

    cd backend
    E2B_API_KEY=e2b_... python scripts/build_e2b_template.py

Optional: E2B_TEMPLATE=esp32-pio (alias to create/update).
"""

import os
import sys

from e2b import Template, default_build_logger, wait_for_timeout

TEMPLATE_NAME = os.getenv("E2B_TEMPLATE", "esp32-pio")

# Libraries referenced by the generated firmware (platformio.ini).
LIBRARIES = [
    "knolleary/PubSubClient",
    "adafruit/Adafruit BME280 Library",
    "adafruit/Adafruit Unified Sensor",
    "bblanchon/ArduinoJson",
]


def main() -> int:
    if not os.getenv("E2B_API_KEY"):
        print("E2B_API_KEY is not set", file=sys.stderr)
        return 1

    template = (
        Template()
        .from_python_image("3.12-slim")
        .apt_install(["git", "curl", "ca-certificates", "build-essential"])
        .pip_install(["platformio"])
        # Keep the toolchain outside /root so the default sandbox user can use it.
        .set_envs({"PLATFORMIO_CORE_DIR": "/opt/platformio"})
        .run_cmd("mkdir -p /opt/platformio /home/user/project")
        .run_cmd("pio pkg install --global --platform espressif32")
    )
    for lib in LIBRARIES:
        template = template.run_cmd(f'pio pkg install --global --library "{lib}"')
    template = (
        template.run_cmd("chmod -R 777 /opt/platformio /home/user/project")
        .set_workdir("/home/user/project")
        .set_start_cmd("sleep infinity", wait_for_timeout(1))
    )

    print(f"Building E2B template '{TEMPLATE_NAME}' (first build takes ~10-20 min)...")
    info = Template.build(
        template,
        name=TEMPLATE_NAME,
        alias=TEMPLATE_NAME,
        cpu_count=4,
        memory_mb=4096,
        min_free_disk_mb=2048,
        on_build_logs=default_build_logger(),
    )
    print(f"Done: {info}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
