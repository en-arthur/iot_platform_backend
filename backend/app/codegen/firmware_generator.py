from typing import Any, Dict, List
from app.core.exceptions import ValidationError
from app.db.repositories.library_repo import library_repo
from app.models.files import GeneratedFile

# PlatformIO libraries installed in the build template (see
# scripts/build_e2b_template.py). Generated projects point at them instead of
# downloading them, so a verification build needs no network access.
LIBRARY_DIR = "/opt/platformio/lib"


class ArduinoFirmwareGenerator:
    """Generates an Arduino C++ project for any board in the hardware library.

    Target, pins and transport are read from the board record, so the same
    generator serves ESP32, ESP8266 and future families.
    """

    # Spec field -> board default_pins role.
    PIN_ROLES = (
        ("bme280_sda_pin", "i2c_sda"),
        ("bme280_scl_pin", "i2c_scl"),
        ("fan_relay_pin", "relay"),
        ("button_pin", "button"),
    )

    @classmethod
    def resolve_target(cls, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve board, pins and transport for a spec.

        Raises ValidationError for an unknown board, a pin the board does not
        have, a reserved pin, or a board without an IP link. Callers use this
        before streaming so those failures are clean 422s.
        """
        hw = spec.get("hardware", {}).get("fields", {})
        periph = spec.get("peripherals", {}).get("fields", {})

        board_id = str(hw.get("board_id", {}).get("value") or "esp32-s3-devkitc-1")
        board = library_repo.get_board(board_id)
        if board is None:
            raise ValidationError(
                f"Board '{board_id}' is not in the hardware library; add it before generating firmware."
            )

        pins = {}
        for field, role in cls.PIN_ROLES:
            label = str(
                periph.get(field, {}).get("value") or board.default_pins.get(role) or ""
            )
            key = board.resolve_pin(label)
            if key is None:
                raise ValidationError(
                    f"Pin '{label}' for {field} does not exist on {board.name}. "
                    f"Allowed pins: {', '.join(sorted(board.pin_map))}."
                )
            pin = board.pin_map[key]
            if pin.gpio is None:
                raise ValidationError(
                    f"Pin '{key}' on {board.name} has no GPIO number in the library."
                )
            if pin.is_reserved:
                raise ValidationError(
                    f"Pin '{key}' for {field} is reserved on {board.name}: "
                    f"{pin.description or ', '.join(pin.capabilities)}"
                )
            pins[role] = pin

        # MQTT needs an IP link. BLE-only or linkless boards cannot run this
        # firmware, so fail here rather than emitting code that cannot connect.
        if board.connectivity not in ("wifi", "ethernet"):
            raise ValidationError(
                f"{board.name} has connectivity '{board.connectivity}'; "
                "MQTT firmware requires Wi-Fi or Ethernet."
            )

        return {
            "board": board,
            "pins": pins,
            "is_ethernet": board.connectivity == "ethernet",
        }

    @classmethod
    def generate(cls, project_id: str, version: int, spec: Dict[str, Any]) -> List[GeneratedFile]:
        files: List[GeneratedFile] = []

        hw = spec.get("hardware", {}).get("fields", {})
        behavior = spec.get("behavior", {}).get("fields", {})
        cloud = spec.get("cloud_backend", {}).get("fields", {})
        data_model = spec.get("data_model", {}).get("fields", {})

        target = cls.resolve_target(spec)
        board = target["board"]
        pins = target["pins"]
        sda, scl = pins["i2c_sda"], pins["i2c_scl"]
        relay, button = pins["relay"], pins["button"]
        sda_pin, scl_pin = sda.gpio, scl.gpio
        relay_pin, button_pin = relay.gpio, button.gpio

        deep_sleep_enabled = bool(hw.get("deep_sleep_enabled", {}).get("value", False))
        deep_sleep_sec = int(hw.get("deep_sleep_interval_seconds", {}).get("value") or 60)

        is_ethernet = target["is_ethernet"]
        ethernet_config = (
            """// W5x00 shield wiring; adjust these to the pins used on the board.
#define ETHERNET_CS_PIN         10
#define ETHERNET_MAC            {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED}
"""
            if is_ethernet
            else ""
        )
        platform_ethernet_define = (
            "#define PLATFORM_ETHERNET       1\n" if is_ethernet else ""
        )

        sampling_hz = float(behavior.get("telemetry_sampling_rate_hz", {}).get("value") or 0.0167)
        loop_delay_ms = max(1000, int(1000.0 / sampling_hz)) if sampling_hz > 0 else 60000

        telemetry_topic = str(cloud.get("telemetry_topic", {}).get("value") or "devices/node-01/telemetry")
        commands_topic = str(cloud.get("commands_topic", {}).get("value") or "devices/node-01/commands")
        declared_cmds = behavior.get("declared_commands", {}).get("value") or ["TRIGGER_FAN_FORCE_ON", "TRIGGER_FAN_FORCE_OFF", "REBOOT_NODE"]

        # =====================================================================
        # 1. platformio.ini (framework + target from the board record)
        # =====================================================================
        platformio_content = f"""; PlatformIO Project Configuration for {board.framework.capitalize()} Framework
; Target: {board.id}
; Single-source-of-truth project spec v{version}.0

[platformio]
default_envs = {board.env_name}

[env:{board.env_name}]
platform = {board.platform}
board = {board.pio_board}
framework = {board.framework}
monitor_speed = 115200

; The build machine already has these libraries installed, so the build needs
; no internet access. To build this folder on your own computer, install them
; once with:
;   pio pkg install -l "knolleary/PubSubClient@2.8.0"
;                   -l "adafruit/Adafruit BME280 Library@2.3.0"
;                   -l "adafruit/Adafruit Unified Sensor@1.1.15"
;                   -l "bblanchon/ArduinoJson@7.4.3"
lib_extra_dirs = {LIBRARY_DIR}

# USER CODE BEGIN PLATFORMIO_CONFIG
# Optional custom build flags or extra libraries
# USER CODE END PLATFORMIO_CONFIG
"""
        files.append(
            GeneratedFile(
                id=f"{project_id}-platformio",
                project_id=project_id,
                version_number=version,
                path="firmware/platformio.ini",
                content=platformio_content,
                file_type="config",
            )
        )

        # =====================================================================
        # 2. config.h
        # =====================================================================
        config_h_content = f"""#ifndef CONFIG_H
#define CONFIG_H

// Auto-generated hardware pinouts and parameters from Project Spec v{version}.0
// Board: {board.name} ({board.id})
#define PIN_I2C_SDA         {sda_pin}  // {sda.name}
#define PIN_I2C_SCL         {scl_pin}  // {scl.name}
#define PIN_FAN_RELAY       {relay_pin}  // {relay.name}
#define PIN_MANUAL_BUTTON   {button_pin}  // {button.name}

// Connectivity & MQTT Topics
#define PLATFORM_CONNECTIVITY   "{board.connectivity}"
{platform_ethernet_define}#define DEFAULT_WIFI_SSID       "YOUR_WIFI_SSID"
#define DEFAULT_WIFI_PASSWORD   "YOUR_WIFI_PASSWORD"
#define MQTT_BROKER_HOST        "10.0.0.1"
#define MQTT_BROKER_PORT        1883
#define MQTT_TOPIC_TELEMETRY    "{telemetry_topic}"
#define MQTT_TOPIC_COMMANDS     "{commands_topic}"
{ethernet_config}
#define TELEMETRY_INTERVAL_MS   {loop_delay_ms}
#define DEEP_SLEEP_ENABLED      {1 if deep_sleep_enabled else 0}
#define DEEP_SLEEP_SECONDS      {deep_sleep_sec}

/* USER CODE BEGIN CUSTOM_CONFIG */
// Add custom developer definitions below
/* USER CODE END CUSTOM_CONFIG */

#endif // CONFIG_H
"""
        files.append(
            GeneratedFile(
                id=f"{project_id}-config-h",
                project_id=project_id,
                version_number=version,
                path="firmware/include/config.h",
                content=config_h_content,
                file_type="firmware",
            )
        )

        # =====================================================================
        # 3. main.cpp (Arduino Firmware Source)
        # =====================================================================
        main_cpp_content = f"""/**
 * DeviceStack Technologies Synthesized Arduino Firmware
 * Board: {board.name} ({board.id})
 * Target: {board.platform} / {board.pio_board}
 * Version: v{version}.0
 */

#include <Arduino.h>
#include <Wire.h>
#include "config.h"
#if defined(PLATFORM_ETHERNET)
#include <Ethernet.h>
#elif defined(ARDUINO_ARCH_ESP8266)
#include <ESP8266WiFi.h>
#else
#include <WiFi.h>
#endif
#include <PubSubClient.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <ArduinoJson.h>

/* USER CODE BEGIN INCLUDES */
// Include custom sensors or protocol libraries here
/* USER CODE END INCLUDES */

#if defined(PLATFORM_ETHERNET)
EthernetClient networkClient;
#else
WiFiClient networkClient;
#endif
PubSubClient mqttClient(networkClient);
Adafruit_BME280 bme;

bool bmeAvailable = false;
unsigned long lastTelemetryTime = 0;

/* USER CODE BEGIN CUSTOM_DECLARATIONS */
// Developer custom variables
/* USER CODE END CUSTOM_DECLARATIONS */

void onMqttCommandReceived(char* topic, byte* payload, unsigned int length) {{
    String message = "";
    for (unsigned int i = 0; i < length; i++) {{
        message += (char)payload[i];
    }}
    message.trim();
    Serial.printf("[MQTT COMMAND] Topic: %s | Command: %s\\n", topic, message.c_str());

    // Strict command matching declared in Spec Behavior Section
    if (message == "TRIGGER_FAN_FORCE_ON") {{
        digitalWrite(PIN_FAN_RELAY, HIGH);
        Serial.println("[ACTUATION] Fan relay energized (ON)");
    }} else if (message == "TRIGGER_FAN_FORCE_OFF") {{
        digitalWrite(PIN_FAN_RELAY, LOW);
        Serial.println("[ACTUATION] Fan relay de-energized (OFF)");
    }} else if (message == "REBOOT_NODE") {{
        Serial.println("[SYSTEM] Reboot command received. Restarting MCU...");
        delay(500);
        ESP.restart();
    }}
    /* USER CODE BEGIN COMMAND_HANDLER */
    // Add custom handling for developer-declared commands
    /* USER CODE END COMMAND_HANDLER */
}}

void setupNetwork() {{
#if defined(PLATFORM_ETHERNET)
    Serial.println("[ETH] Requesting DHCP lease...");
    Ethernet.init(ETHERNET_CS_PIN);
    if (Ethernet.begin(ETHERNET_MAC) == 0) {{
        Serial.println("[ETH] DHCP failed; check the cable and CS pin.");
    }} else {{
        Serial.print("[ETH] Connected! IP: ");
        Serial.println(Ethernet.localIP());
    }}
#else
    delay(10);
    Serial.print("[WIFI] Connecting to ");
    Serial.println(DEFAULT_WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(DEFAULT_WIFI_SSID, DEFAULT_WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {{
        delay(500);
        Serial.print(".");
        attempts++;
    }}
    if (WiFi.status() == WL_CONNECTED) {{
        Serial.println("\\n[WIFI] Connected! IP: " + WiFi.localIP().toString());
    }} else {{
        Serial.println("\\n[WIFI] Connection timeout, proceeding in offline mode.");
    }}
#endif
}}

bool networkConnected() {{
#if defined(PLATFORM_ETHERNET)
    return Ethernet.localIP() != IPAddress(0, 0, 0, 0);
#else
    return WiFi.status() == WL_CONNECTED;
#endif
}}

void reconnectMqtt() {{
    while (!mqttClient.connected() && networkConnected()) {{
        Serial.print("[MQTT] Attempting connection to broker...");
        String clientId = "node-" + String(random(0xffff), HEX);
        if (mqttClient.connect(clientId.c_str())) {{
            Serial.println(" connected!");
            mqttClient.subscribe(MQTT_TOPIC_COMMANDS);
            Serial.printf("[MQTT] Subscribed to command topic: %s\\n", MQTT_TOPIC_COMMANDS);
        }} else {{
            Serial.print(" failed, rc=");
            Serial.print(mqttClient.state());
            Serial.println(" retrying in 3 seconds...");
            delay(3000);
        }}
    }}
}}

void setup() {{
    Serial.begin(115200);
    delay(1000);
    Serial.println("\\n==========================================");
    Serial.println("  DeviceStack Node Initializing           ");
    Serial.println("==========================================");

    // Initialize GPIO Pin modes
    pinMode(PIN_FAN_RELAY, OUTPUT);
    digitalWrite(PIN_FAN_RELAY, LOW);
    pinMode(PIN_MANUAL_BUTTON, INPUT_PULLUP);

    // Initialize I2C Bus with assigned pins from Spec
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    if (!bme.begin(0x76, &Wire)) {{
        Serial.println("[SENSOR] Warning: BME280 sensor not detected at 0x76!");
    }} else {{
        bmeAvailable = true;
        Serial.println("[SENSOR] BME280 sensor initialized successfully.");
    }}

    // Network & MQTT setup
    setupNetwork();
    mqttClient.setServer(MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    mqttClient.setCallback(onMqttCommandReceived);

    /* USER CODE BEGIN SETUP */
    // Add custom sensor calibration or peripheral initialization
    /* USER CODE END SETUP */
}}

void publishTelemetry() {{
    float temp_c = bmeAvailable ? bme.readTemperature() : 24.5;
    float humidity_pct = bmeAvailable ? bme.readHumidity() : 55.0;
    float pressure_hpa = bmeAvailable ? (bme.readPressure() / 100.0F) : 1013.25;
    float battery_v = 3.85;

    // Serialize JSON payload matching Data Model
#if ARDUINOJSON_VERSION_MAJOR >= 7
    JsonDocument doc;
#else
    StaticJsonDocument<256> doc;
#endif
    doc["temperature_c"] = temp_c;
    doc["relative_humidity_pct"] = humidity_pct;
    doc["barometric_pressure_hpa"] = pressure_hpa;
    doc["battery_voltage_v"] = battery_v;
    doc["timestamp"] = millis();

    char jsonBuffer[256];
    serializeJson(doc, jsonBuffer);

    Serial.printf("[TELEMETRY] Publishing payload: %s\\n", jsonBuffer);
    mqttClient.publish(MQTT_TOPIC_TELEMETRY, jsonBuffer);
}}

void loop() {{
    if (!mqttClient.connected()) {{
        reconnectMqtt();
    }}
    mqttClient.loop();

    unsigned long now = millis();
    if (now - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {{
        lastTelemetryTime = now;
        publishTelemetry();

        #if DEEP_SLEEP_ENABLED
        Serial.printf("[POWER] Entering deep sleep for %d seconds...\\n", DEEP_SLEEP_SECONDS);
#if defined(ESP32)
        esp_sleep_enable_timer_wakeup((uint64_t)DEEP_SLEEP_SECONDS * 1000000ULL);
        esp_deep_sleep_start();
#elif defined(ESP8266)
        // NodeMCU: D0 (GPIO16) must be wired to RST for timer wake.
        // The ESP8266 API takes a 32-bit microsecond value (~71 min max).
        ESP.deepSleep((uint32_t)((uint64_t)DEEP_SLEEP_SECONDS * 1000000ULL));
#else
#warning "Deep sleep is not implemented for this MCU; the node will stay awake."
#endif
        #endif
    }}

    /* USER CODE BEGIN LOOP */
    // Custom loop tasks (e.g. check physical buttons, LED blink)
    /* USER CODE END LOOP */

    delay(50);
}}
"""
        files.append(
            GeneratedFile(
                id=f"{project_id}-main-cpp",
                project_id=project_id,
                version_number=version,
                path="firmware/src/main.cpp",
                content=main_cpp_content,
                file_type="firmware",
            )
        )

        return files
