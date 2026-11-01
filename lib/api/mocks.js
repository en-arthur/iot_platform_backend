/**
 * Mock Data for AI IoT Builder Frontend
 * Matches the CONTRACT and realistic hardware/project specs.
 */

export const MOCK_BOARDS = [
  {
    id: 'esp32-s3-devkitc-1',
    name: 'ESP32-S3 DevKitC-1',
    vendor: 'Espressif',
    mcu: 'ESP32-S3 (Xtensa Dual-core 32-bit LX7)',
    status: 'tested',
    specs: {
      flash_mb: 8,
      psram_mb: 2,
      clock_mhz: 240,
      wifi: '802.11 b/g/n (2.4 GHz)',
      ble: 'Bluetooth 5.0 (BLE)',
      usb: 'Native USB OTG & USB-to-UART',
    },
    pin_map: {
      GPIO1: { name: 'GPIO1', capabilities: ['ADC', 'RTC'] },
      GPIO2: { name: 'GPIO2', capabilities: ['ADC', 'RTC', 'BOOT'] },
      GPIO4: { name: 'GPIO4', capabilities: ['I2C_SDA', 'GPIO'] },
      GPIO5: { name: 'GPIO5', capabilities: ['I2C_SCL', 'GPIO'] },
      GPIO6: { name: 'GPIO6', capabilities: ['SPI_SCK', 'GPIO'] },
      GPIO7: { name: 'GPIO7', capabilities: ['SPI_MOSI', 'GPIO'] },
      GPIO8: { name: 'GPIO8', capabilities: ['SPI_MISO', 'GPIO'] },
      GPIO9: { name: 'GPIO9', capabilities: ['RELAY_OUT', 'GPIO'] },
      GPIO10: { name: 'GPIO10', capabilities: ['BUTTON_IN', 'GPIO'] },
      GPIO18: { name: 'GPIO18', capabilities: ['USB_D-'] },
      GPIO19: { name: 'GPIO19', capabilities: ['USB_D+'] },
      GPIO21: { name: 'GPIO21', capabilities: ['UART_RX', 'GPIO'] },
      GPIO43: { name: 'GPIO43', capabilities: ['UART_TX', 'GPIO'] },
    },
  },
  {
    id: 'raspberry-pi-pico-w',
    name: 'Raspberry Pi Pico W',
    vendor: 'Raspberry Pi',
    mcu: 'RP2040 Dual ARM Cortex-M0+',
    status: 'draft',
    specs: {
      flash_mb: 2,
      psram_mb: 0,
      clock_mhz: 133,
      wifi: 'CYW43439 802.11n',
      ble: 'Bluetooth 5.2',
    },
    pin_map: {},
  },
];

export const MOCK_PERIPHERALS = [
  {
    id: 'bme280',
    name: 'BME280 Environmental Sensor',
    category: 'Sensors',
    interface: 'I2C',
    default_address: '0x76',
    pins_required: ['SDA', 'SCL', '3V3', 'GND'],
    status: 'tested',
    description: 'Measures temperature, relative humidity, and barometric pressure.',
  },
  {
    id: 'relay-module-5v',
    name: '1-Channel 5V Relay Module (Optocoupled)',
    category: 'Actuators',
    interface: 'Digital Output',
    pins_required: ['IN', 'VCC', 'GND'],
    status: 'tested',
    description: 'High-current relay switch for driving AC or high-load fans/heaters.',
  },
  {
    id: 'push-button',
    name: 'Momentary Tactile Push Button',
    category: 'Inputs',
    interface: 'Digital Input (Pull-up)',
    pins_required: ['SIG', 'GND'],
    status: 'tested',
    description: 'User input button for manual triggers or mode toggles.',
  },
  {
    id: 'ssd1306-oled',
    name: 'SSD1306 0.96 inch I2C OLED Display',
    category: 'Displays',
    interface: 'I2C',
    default_address: '0x3C',
    pins_required: ['SDA', 'SCL', '3V3', 'GND'],
    status: 'tested',
    description: '128x64 monochrome graphic OLED display.',
  },
];

/**
 * 12 Spec Sections for Greenhouse Monitor:
 * Includes 1 pin-conflict error (GPIO4 shared between I2C SDA and Button),
 * 1 warning (MQTT without TLS cert override check),
 * 1 open field (metadata.target_deployment_date or cloud.ingest_auth_token).
 */
export const MOCK_SPEC_12_SECTIONS = {
  metadata: {
    title: '1. Project Metadata',
    fields: {
      project_name: {
        value: 'Solar LoRaWAN Soil Moisture Array',
        state: 'confirmed',
        source: 'user',
      },
      description: {
        value: 'Long-range ultra low-power moisture sensing array with capacitive probes, deep sleep cycles, and LoRaWAN/MQTT telemetry.',
        state: 'confirmed',
        source: 'user',
      },
      target_deployment_date: {
        value: null,
        state: 'open', // Blocking open field!
        source: 'user',
        override_reason: 'Engineer must supply targeted deployment deadline before production lock.',
      },
      author: {
        value: 'Sarah Chen (Hardware Systems)',
        state: 'confirmed',
        source: 'user',
      },
    },
  },
  hardware: {
    title: '2. Hardware',
    fields: {
      board_id: {
        value: 'esp32-s3-devkitc-1',
        state: 'confirmed',
        source: 'from_library',
      },
      mcu_clock_mhz: {
        value: 240,
        state: 'defaulted',
        source: 'library',
      },
      power_source: {
        value: 'LiPo Battery (3.7V 2500mAh) + Solar Harvester',
        state: 'confirmed',
        source: 'user',
      },
      deep_sleep_enabled: {
        value: true,
        state: 'inferred',
        source: 'ai',
      },
      deep_sleep_interval_seconds: {
        value: 60,
        state: 'confirmed',
        source: 'user',
      },
    },
  },
  peripherals: {
    title: '3. Peripherals',
    fields: {
      bme280_sda_pin: {
        value: 'GPIO4',
        state: 'confirmed',
        source: 'user',
      },
      bme280_scl_pin: {
        value: 'GPIO5',
        state: 'confirmed',
        source: 'user',
      },
      bme280_i2c_addr: {
        value: '0x76',
        state: 'from_library',
        source: 'library',
      },
      fan_relay_pin: {
        value: 'GPIO9',
        state: 'confirmed',
        source: 'user',
      },
      // PIN CONFLICT ERROR: GPIO4 assigned to both BME280 SDA and Manual Button Input!
      manual_override_button_pin: {
        value: 'GPIO4',
        state: 'confirmed',
        source: 'user',
        override_reason: 'Pin collision with BME280 SDA on GPIO4',
      },
    },
  },
  behavior: {
    title: '4. Behavior',
    fields: {
      sample_interval_sec: {
        value: 60,
        state: 'confirmed',
        source: 'user',
      },
      fan_relay_threshold_celsius: {
        value: 30.0,
        state: 'confirmed',
        source: 'user',
      },
      high_temp_alert_threshold_celsius: {
        value: 35.0,
        state: 'confirmed',
        source: 'user',
      },
      high_temp_alert_duration_minutes: {
        value: 10,
        state: 'confirmed',
        source: 'user',
      },
      declared_commands: {
        value: [
          'TRIGGER_FAN_FORCE_ON',
          'TRIGGER_FAN_AUTO',
          'REBOOT_NODE',
          'CALIBRATE_TEMP_OFFSET',
        ],
        state: 'confirmed',
        source: 'user',
      },
    },
  },
  data_model: {
    title: '5. Data Model',
    fields: {
      metrics: {
        value: [
          { name: 'temperature', unit: '°C', type: 'float', min: -40, max: 85 },
          { name: 'humidity', unit: '%RH', type: 'float', min: 0, max: 100 },
          { name: 'pressure', unit: 'hPa', type: 'float', min: 300, max: 1100 },
          { name: 'fan_state', unit: 'bool', type: 'boolean' },
          { name: 'battery_mv', unit: 'mV', type: 'integer', min: 2800, max: 4200 },
        ],
        state: 'inferred',
        source: 'ai',
      },
      serialization_format: {
        value: 'JSON Compact',
        state: 'defaulted',
        source: 'platform_default',
      },
    },
  },
  connectivity: {
    title: '6. Connectivity (MQTT First)',
    fields: {
      protocol: {
        value: 'MQTT over TLS v1.3',
        state: 'confirmed',
        source: 'user',
      },
      broker_host: {
        value: 'mqtt.iotbuilder.cloud',
        state: 'defaulted',
        source: 'platform_default',
      },
      broker_port: {
        value: 8883,
        state: 'defaulted',
        source: 'platform_default',
      },
      qos_level: {
        value: 1,
        state: 'defaulted',
        source: 'platform_default',
      },
      // WARNING: Keepalive set high for battery nodes
      keep_alive_seconds: {
        value: 120,
        state: 'inferred',
        source: 'ai',
      },
    },
  },
  cloud_backend: {
    title: '7. Cloud Backend',
    fields: {
      ingestion_endpoint: {
        value: '/api/v1/telemetry/ingest',
        state: 'defaulted',
        source: 'platform_default',
      },
      time_series_retention_days: {
        value: 90,
        state: 'confirmed',
        source: 'user',
      },
      alert_dispatch_webhook: {
        value: 'https://hooks.slack.com/services/T00/B00/XXXXX',
        state: 'confirmed',
        source: 'user',
      },
    },
  },
  interface: {
    title: '8. Interface (Dashboard or Web App)',
    fields: {
      interface_type: {
        value: 'web app', // 'dashboard' or 'web app'
        state: 'confirmed',
        source: 'user',
      },
      allowed_controls: {
        value: ['TRIGGER_FAN_FORCE_ON', 'TRIGGER_FAN_AUTO', 'REBOOT_NODE'],
        state: 'confirmed',
        source: 'user',
      },
      enable_role_based_access: {
        value: true,
        state: 'inferred',
        source: 'ai',
      },
    },
  },
  security: {
    title: '9. Security',
    fields: {
      device_cert_type: {
        value: 'ECDSA P-256',
        state: 'defaulted',
        source: 'platform_default',
      },
      secure_boot_enabled: {
        value: true,
        state: 'confirmed',
        source: 'user',
      },
      flash_encryption: {
        value: 'AES-XTS-256',
        state: 'defaulted',
        source: 'platform_default',
      },
    },
  },
  updates: {
    title: '10. Updates (OTA)',
    fields: {
      ota_mechanism: {
        value: 'Dual-partition A/B Rollback',
        state: 'defaulted',
        source: 'platform_default',
      },
      rollback_on_selftest_fail: {
        value: true,
        state: 'confirmed',
        source: 'user',
      },
    },
  },
  verification: {
    title: '11. Verification',
    fields: {
      hil_sim_target: {
        value: 'Wokwi ESP32-S3 QEMU Container',
        state: 'defaulted',
        source: 'platform_default',
      },
      selftest_suite: {
        value: ['i2c_bus_scan', 'bme280_who_am_i', 'gpio_loopback', 'mqtt_handshake'],
        state: 'inferred',
        source: 'ai',
      },
    },
  },
  provenance: {
    title: '12. Provenance',
    fields: {
      git_commit_hash: {
        value: '7f9c2d18e4b',
        state: 'confirmed',
        source: 'ai',
      },
      created_by_agent_version: {
        value: 'AI-IoT-Core v2.4.1',
        state: 'from_library',
        source: 'library',
      },
    },
  },
};

/**
 * Initial Validation Issues for the sample project:
 * 1 error (pin conflict), 1 warning (keepalive vs sleep), 1 info.
 */
export const MOCK_VALIDATION_ISSUES = [
  {
    id: 'iss-err-1',
    layer: 'electrical',
    severity: 'error',
    field_path: 'peripherals.manual_override_button_pin',
    message: 'Electrical Pin Collision: GPIO4 is mapped to both BME280 I2C SDA and Button Input. Remap Button to GPIO10.',
  },
  {
    id: 'iss-warn-1',
    layer: 'resource',
    severity: 'warning',
    field_path: 'connectivity.keep_alive_seconds',
    message: 'MQTT KeepAlive (120s) exceeds deep sleep cycle (60s). Node might miss broker keepalive ping during sleep.',
  },
  {
    id: 'iss-block-open',
    layer: 'completeness',
    severity: 'error',
    field_path: 'metadata.target_deployment_date',
    message: 'Blocking field "target_deployment_date" is currently open and has not been filled or confirmed.',
  },
];

export const MOCK_AI_FIX_PROPOSAL = {
  proposal_id: 'prop-fix-pin-conflict',
  summary: 'Resolve GPIO4 Pin Conflict by remapping Button to GPIO10 and auto-fill deployment date',
  changes: [
    {
      path: 'peripherals.manual_override_button_pin',
      old: 'GPIO4',
      new: 'GPIO10',
      reason: 'Relocates tactile switch to vacant digital input pin GPIO10, freeing GPIO4 for BME280 I2C SDA.',
    },
    {
      path: 'metadata.target_deployment_date',
      old: null,
      new: '2026-12-01',
      reason: 'Sets tentative pilot test deployment date to resolve completeness requirement.',
    },
  ],
};

export const MOCK_PROJECTS = [
  {
    id: 'proj-greenhouse-01',
    name: 'Solar LoRaWAN Soil Moisture Array',
    description: 'Long-range ultra low-power moisture sensing array with capacitive probes, deep sleep cycles, and LoRaWAN/MQTT telemetry.',
    board_id: 'esp32-s3-devkitc-1',
    interface_type: 'web app',
    lifecycle: 'draft',
    created_at: '2026-10-28T14:30:00Z',
    updated_at: '2026-11-01T08:15:00Z',
    version: 3,
    version_display: 'v3.1 draft',
    deployed_version: 'v3.0',
  },
  {
    id: 'proj-lora-soil-02',
    name: 'LoRaWAN Repeater & Gateway Node',
    description: 'Solar-buffered field gateway aggregating multi-node soil telemetry over 868MHz.',
    board_id: 'esp32-s3-devkitc-1',
    interface_type: 'dashboard',
    lifecycle: 'draft',
    created_at: '2026-10-15T09:00:00Z',
    updated_at: '2026-10-25T11:20:00Z',
    version: 1,
    version_display: 'v1.0 draft',
    deployed_version: null,
  },
];

export const MOCK_GENERATED_FILES = [
  {
    path: 'firmware/main.cpp',
    type: 'firmware',
    content: `// AI IoT Builder - ESP32-S3 Firmware
// Generated from Spec v1.0 (Greenhouse Node)
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

#define BME_SDA_PIN 4
#define BME_SCL_PIN 5
#define RELAY_PIN 9
#define BUTTON_PIN 10

Adafruit_BME280 bme;
WiFiClientSecure wifiClient;
PubSubClient mqttClient(wifiClient);

/* [PROTECTED_REGION_START: USER_CUSTOM_CALIBRATION] */
// User calibration curve: custom zero-point offsets
float user_temp_offset_celsius = 0.0f;
float user_humidity_multiplier = 1.0f;
/* [PROTECTED_REGION_END: USER_CUSTOM_CALIBRATION] */

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  Wire.begin(BME_SDA_PIN, BME_SCL_PIN);
  if (!bme.begin(0x76, &Wire)) {
    Serial.println("Error: BME280 sensor not detected on I2C bus!");
  }
}

void loop() {
  float temp = bme.readTemperature() + user_temp_offset_celsius;
  float hum = bme.readHumidity() * user_humidity_multiplier;
  
  // Ventilation threshold logic
  if (temp >= 30.0) {
    digitalWrite(RELAY_PIN, HIGH);
  } else {
    digitalWrite(RELAY_PIN, LOW);
  }

  delay(60000);
}
`,
    protected_regions: [
      {
        start_line: 17,
        end_line: 22,
        reason: 'User manual calibration offset logic preserved across AI regeneration',
      },
    ],
  },
  {
    path: 'backend/server.py',
    type: 'backend',
    content: `# FastAPI Ingestion & Control Server
# Generated for Project: Smart Greenhouse Monitor
from fastapi import FastAPI, Depends, HTTPException, Security
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Greenhouse IoT Cloud Backend", version="1.0.0")

class TelemetryPayload(BaseModel):
    device_id: str
    temperature: float
    humidity: float
    pressure: float
    fan_state: bool
    battery_mv: int

@app.post("/api/v1/telemetry/ingest")
async def ingest_telemetry(payload: TelemetryPayload):
    # Enforce alert threshold > 35.0 C
    if payload.temperature > 35.0:
        trigger_high_temp_alert(payload.device_id, payload.temperature)
    return {"status": "accepted", "timestamp": "2026-11-01T09:40:00Z"}

@app.post("/devices/{device_id}/commands")
async def execute_command(device_id: str, command: str):
    # Only allow declared commands from spec
    allowed = ["TRIGGER_FAN_FORCE_ON", "TRIGGER_FAN_AUTO", "REBOOT_NODE"]
    if command not in allowed:
        raise HTTPException(status_code=400, detail="Command not declared in spec behavior")
    return {"device_id": device_id, "command": command, "executed": True}
`,
    protected_regions: [],
  },
  {
    path: 'interface/controls_app.jsx',
    type: 'interface',
    content: `// Web App Interface Bundle
// Generated for Smart Greenhouse Monitor
import React, { useState } from 'react';

export default function GreenhouseControlCenter({ deviceId, onSendCommand }) {
  const [fanOverride, setFanOverride] = useState(false);

  return (
    <div className="p-6 bg-slate-900 text-white rounded-xl">
      <h3 className="text-lg font-bold">Ventilation Controls</h3>
      <p className="text-sm text-slate-400">Controls map to verified hardware commands.</p>
      
      <div className="mt-4 flex gap-3">
        <button 
          onClick={() => { setFanOverride(true); onSendCommand('TRIGGER_FAN_FORCE_ON'); }}
          className="px-4 py-2 bg-emerald-600 rounded-lg hover:bg-emerald-500 font-semibold"
        >
          Force Fan ON
        </button>
        <button 
          onClick={() => { setFanOverride(false); onSendCommand('TRIGGER_FAN_AUTO'); }}
          className="px-4 py-2 bg-slate-700 rounded-lg hover:bg-slate-600 font-semibold"
        >
          Auto Mode (30°C Trigger)
        </button>
      </div>
    </div>
  );
}
`,
    protected_regions: [],
  },
];

export const MOCK_VERIFICATION_RUN = {
  run_id: 'run-gh-test-901',
  project_id: 'proj-greenhouse-01',
  status: 'failed',
  created_at: '2026-11-01T09:35:10Z',
  steps: [
    { name: 'compile', status: 'success', duration_ms: 4120, details: 'ESP-IDF v5.1 compiled firmware binary (1,048,576 bytes)' },
    { name: 'simulate', status: 'success', duration_ms: 8400, details: 'QEMU virtual hardware emulation finished without panic' },
    { name: 'flash', status: 'success', duration_ms: 12000, details: 'Virtual testbed flashed via serial at 921,600 baud' },
    { name: 'selftest', status: 'failed', duration_ms: 1950, details: 'Pin collision test failed during self-test assertion' },
  ],
  logs: [
    '[09:35:10] Initiating clean firmware compilation for target: ESP32-S3...',
    '[09:35:12] Compiling firmware/main.cpp with Xtensa toolchain gcc 12.2.0...',
    '[09:35:14] Compilation successful. Binary size: 1.04MB (26% flash partition).',
    '[09:35:15] Launching Wokwi ESP32-S3 HIL emulation container...',
    '[09:35:19] Virtual bootloader OK, CPU freq 240MHz, 2MB PSRAM detected.',
    '[09:35:21] Running self-test suite: [i2c_bus_scan, bme280_who_am_i, gpio_loopback]...',
    '[09:35:22] [PASS] i2c_bus_scan: Found device at address 0x76 (BME280).',
    '[09:35:22] [FAIL] gpio_loopback: Pin GPIO4 pulled LOW by tactile switch during I2C transaction!',
    '[09:35:23] Assertion Failed: Pin GPIO4 multiplexing contention detected. Halting.',
  ],
  tests: [
    { id: 't1', name: 'ESP-IDF Firmware Compilation', passed: true, message: 'Clean compilation without warnings' },
    { id: 't2', name: 'I2C Bus Probe (0x76)', passed: true, message: 'BME280 acknowledged WHO_AM_I register (0x60)' },
    {
      id: 't3',
      name: 'GPIO Pin Multiplexing & Signal Integrity',
      passed: false,
      message: 'GPIO4 is shared by I2C SDA and Button Input, causing bus lockup.',
      fix_proposal: MOCK_AI_FIX_PROPOSAL,
    },
    { id: 't4', name: 'MQTT Broker TLS Handshake', passed: true, message: 'TLS v1.3 cipher suite negotiation successful' },
  ],
};

export const MOCK_DEVICES = [
  {
    id: 'dev-node-alpha',
    name: 'Greenhouse Alpha (Zone 1)',
    project_id: 'proj-greenhouse-01',
    status: 'online',
    last_seen: 'Just now',
    ip_address: '192.168.1.142',
    firmware_version: 'v1.0.4',
  },
  {
    id: 'dev-node-beta',
    name: 'Greenhouse Beta (Zone 2)',
    project_id: 'proj-greenhouse-01',
    status: 'online',
    last_seen: '2 mins ago',
    ip_address: '192.168.1.143',
    firmware_version: 'v1.0.4',
  },
];

export const MOCK_TELEMETRY = [
  { id: 'r1', device_id: 'dev-node-alpha', timestamp: '10:00', metric: 'temperature', value: 24.2, unit: '°C' },
  { id: 'r2', device_id: 'dev-node-alpha', timestamp: '10:05', metric: 'temperature', value: 25.1, unit: '°C' },
  { id: 'r3', device_id: 'dev-node-alpha', timestamp: '10:10', metric: 'temperature', value: 27.8, unit: '°C' },
  { id: 'r4', device_id: 'dev-node-alpha', timestamp: '10:15', metric: 'temperature', value: 31.4, unit: '°C' },
  { id: 'r5', device_id: 'dev-node-alpha', timestamp: '10:20', metric: 'temperature', value: 33.2, unit: '°C' },
  { id: 'r6', device_id: 'dev-node-alpha', timestamp: '10:25', metric: 'temperature', value: 29.5, unit: '°C' },
];
