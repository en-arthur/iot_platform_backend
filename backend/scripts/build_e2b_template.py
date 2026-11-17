"""Build the shared E2B template used by verification runs.

Run this ONCE (or again when the toolchain/libraries change). It creates one
image with PlatformIO and the toolchains for every supported board family, so
each verification sandbox can compile offline in seconds. It is not per project
or per device.

    cd backend
    E2B_API_KEY=e2b_... python scripts/build_e2b_template.py

Optional: E2B_TEMPLATE=esp32-pio (alias to create/update).
"""

import os
import sys

from e2b import Template, default_build_logger, wait_for_timeout

TEMPLATE_NAME = os.getenv("E2B_TEMPLATE", "esp32-pio")

# Boards used to warm the toolchain cache. Every PlatformIO platform listed here
# gets its framework and compiler downloaded into PLATFORMIO_CORE_DIR so the
# verification sandbox can build with outbound network blocked. The env name must
# match the generated platformio.ini, because PLATFORMIO_LIBDEPS_DIR keeps
# libraries in an env-named subdirectory.
WARMUP_TARGETS = [
    ("espressif32", "esp32-s3-devkitc-1", "esp32s3"),
    ("espressif8266", "nodemcuv2", "nodemcuv2"),
]

# Libraries referenced by the generated firmware (platformio.ini).
LIBRARIES = [
    "knolleary/PubSubClient@^2.8",
    "adafruit/Adafruit BME280 Library@^2.2.2",
    "adafruit/Adafruit Unified Sensor@^1.1.9",
    "bblanchon/ArduinoJson@^7.0.0",
]


def warmup_command(platform: str, board: str, env_name: str) -> str:
    directory = f"/tmp/warm-{env_name}"
    lib_deps = "".join(f"    {lib}\\n" for lib in LIBRARIES)
    return (
        f"mkdir -p {directory}/src && "
        f"cd {directory} && "
        "printf '[env:%s]\\nplatform = %s\\nboard = %s\\nframework = arduino\\n"
        "lib_deps =\\n%s' "
        "> platformio.ini && "
        "printf '#include <Arduino.h>\\nvoid setup() {}\\nvoid loop() {}\\n' > src/main.cpp && "
        "pio run && "
        f"cd / && rm -rf {directory}"
    ) % (env_name, platform, board, lib_deps)


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
        .set_envs(
            {
                "PLATFORMIO_CORE_DIR": "/opt/platformio",
                "PLATFORMIO_LIBDEPS_DIR": "/opt/platformio/libdeps",
                "PLATFORMIO_SETTING_ENABLE_TELEMETRY": "false",
            }
        )
        .run_cmd("mkdir -p /opt/platformio /opt/platformio/libdeps /home/user/project", user="root")
    )
    for lib in LIBRARIES:
        template = template.run_cmd(f'pio pkg install --global --library "{lib}"', user="root")
    for platform, board, env_name in WARMUP_TARGETS:
        # A real build downloads the framework, compiler and libraries, not just
        # the platform package. Without this the offline sandbox cannot build.
        template = template.run_cmd(warmup_command(platform, board, env_name), user="root")
    template = (
        template.run_cmd("chmod -R 777 /opt/platformio /home/user/project", user="root")
        .set_user("user")
        .set_workdir("/home/user/project")
        .set_start_cmd("sleep infinity", wait_for_timeout(1))
    )

    print(f"Building E2B template '{TEMPLATE_NAME}' (first build takes ~15-30 min)...")
    info = Template.build(
        template,
        name=TEMPLATE_NAME,
        alias=TEMPLATE_NAME,
        cpu_count=4,
        memory_mb=4096,
        min_free_disk_mb=4096,
        on_build_logs=default_build_logger(),
    )
    print(f"Done: {info}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
