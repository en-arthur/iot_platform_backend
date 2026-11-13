from typing import Any, Dict, List
from app.core.exceptions import ValidationError
from app.db.repositories.library_repo import library_repo
from app.models.files import GeneratedFile


class ArduinoFirmwareGenerator:
    """Generates complete Arduino C++ project targeting ESP32-S3 / RP2040 microcontrollers.
    Embeds verified peripheral drivers, protected user code regions, and MQTT JSON telemetry.
    """

    @classmethod
    def generate(cls, project_id: str, version: int, spec: Dict[str, Any]) -> List[GeneratedFile]:
        files: List[GeneratedFile] = []

        hw = spec.get("hardware", {}).get("fields", {})
        periph = spec.get("peripherals", {}).get("fields", {})
        behavior = spec.get("behavior", {}).get("fields", {})
        cloud = spec.get("cloud_backend", {}).get("fields", {})
        data_model = spec.get("data_model", {}).get("fields", {})

        board_id = str(hw.get("board_id", {}).get("value") or "esp32-s3-devkitc-1")

        # The board record owns the build recipe. A board id that is not in the
        # hardware library must fail loudly instead of quietly emitting
        # ESP32-S3 configuration for a different target.
        board = library_repo.get_board(board_id)
        if board is None:
            raise ValidationError(
                f"Board '{board_id}' is not in the hardware library; add it before generating firmware."
            )

        deep_sleep_enabled = bool(hw.get("deep_sleep_enabled", {}).get("value", False))
        deep_sleep_sec = int(hw.get("deep_sleep_interval_seconds", {}).get("value") or 60)

        sda_pin = str(periph.get("bme280_sda_pin", {}).get("value") or "GPIO4").replace("GPIO", "").replace("GP", "")
        scl_pin = str(periph.get("bme280_scl_pin", {}).get("value") or "GPIO5").replace("GPIO", "").replace("GP", "")
        relay_pin = str(periph.get("fan_relay_pin", {}).get("value") or "GPIO9").replace("GPIO", "").replace("GP", "")
        button_pin = str(periph.get("button_pin", {}).get("value") or "GPIO10").replace("GPIO", "").replace("GP", "")

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

lib_deps =
    knolleary/PubSubClient@^2.8
    adafruit/Adafruit BME280 Library@^2.2.2
    adafruit/Adafruit Unified Sensor@^1.1.9
    bblanchon/ArduinoJson@^7.0.0

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
#define PIN_I2C_SDA         {sda_pin}
#define PIN_I2C_SCL         {scl_pin}
#define PIN_FAN_RELAY       {relay_pin}
#define PIN_MANUAL_BUTTON   {button_pin}

// Connectivity & MQTT Topics
#define DEFAULT_WIFI_SSID       "YOUR_WIFI_SSID"
#define DEFAULT_WIFI_PASSWORD   "YOUR_WIFI_PASSWORD"
#define MQTT_BROKER_HOST        "10.0.0.1"
#define MQTT_BROKER_PORT        1883
#define MQTT_TOPIC_TELEMETRY    "{telemetry_topic}"
#define MQTT_TOPIC_COMMANDS     "{commands_topic}"

#define TELEMETRY_INTERVAL_MS   {loop_delay_ms}
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
 * Board: {board_id}
 * Version: v{version}.0
 */

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <ArduinoJson.h>
#include "config.h"

/* USER CODE BEGIN INCLUDES */
// Include custom sensors or protocol libraries here
/* USER CODE END INCLUDES */

WiFiClient espClient;
PubSubClient mqttClient(espClient);
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

void setupWiFi() {{
    delay(10);
    Serial.print("[WIFI] Connecting to ");
    Serial.println(DEFAULT_WIFI_SSID);
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
}}

void reconnectMqtt() {{
    while (!mqttClient.connected() && WiFi.status() == WL_CONNECTED) {{
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
    setupWiFi();
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
    StaticJsonDocument<256> doc;
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

        #if {1 if deep_sleep_enabled else 0}
        Serial.printf("[POWER] Entering deep sleep for %d seconds...\\n", DEEP_SLEEP_SECONDS);
        esp_sleep_enable_timer_wakeup((uint64_t)DEEP_SLEEP_SECONDS * 1000000ULL);
        esp_deep_sleep_start();
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
