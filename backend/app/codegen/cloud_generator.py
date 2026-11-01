from typing import Any, Dict, List
from app.models.files import GeneratedFile


class CloudBackendGenerator:
    """Generates the Cloud Telemetry Ingestion Worker, Command Bridge, and
    integration client for WorkersCraft CloudService.
    """

    @classmethod
    def generate(cls, project_id: str, version: int, spec: Dict[str, Any]) -> List[GeneratedFile]:
        files: List[GeneratedFile] = []

        cloud = spec.get("cloud_backend", {}).get("fields", {})
        behavior = spec.get("behavior", {}).get("fields", {})
        data_model = spec.get("data_model", {}).get("fields", {})

        broker_host = str(cloud.get("broker_host", {}).get("value") or "localhost")
        broker_port = int(cloud.get("broker_port", {}).get("value") or 1883)
        telemetry_topic = str(cloud.get("telemetry_topic", {}).get("value") or "devices/+/telemetry")
        commands_topic = str(cloud.get("commands_topic", {}).get("value") or "devices/+/commands")
        high_temp_thresh = float(behavior.get("high_temperature_threshold_c", {}).get("value") or 30.0)

        # =====================================================================
        # 1. cloud_service_client.py (WorkersCraft CloudService Integration)
        # =====================================================================
        client_code = f"""import os
import httpx
from typing import Any, Dict, List, Optional

CLOUD_SERVICE_URL = os.getenv("CLOUD_SERVICE_URL", "http://localhost:8000")
APP_ID = os.getenv("APP_ID", "{project_id}")


class WorkersCraftClient:
    \"\"\"Client integrating with WorkersCraft CloudService for multi-tenant auth,
    generic JSONB telemetry storage, and R2 file hosting.
    \"\"\"

    def __init__(self, base_url: str = CLOUD_SERVICE_URL, app_id: str = APP_ID):
        self.base_url = base_url.rstrip("/")
        self.app_id = app_id
        self.client = httpx.AsyncClient(timeout=10.0)

    async def register_app(self, name: str, owner_id: str) -> Dict[str, Any]:
        \"\"\"Register app in WorkersCraft CloudService.\"\"\"
        res = await self.client.post(
            f"{{self.base_url}}/api/apps/register",
            json={{"name": name, "owner_id": owner_id}},
        )
        res.raise_for_status()
        return res.json()

    async def store_reading(self, payload: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        \"\"\"Persist telemetry reading into generic JSONB storage collection.\"\"\"
        headers = {{"X-App-ID": self.app_id}}
        if token:
            headers["Authorization"] = f"Bearer {{token}}"

        res = await self.client.post(
            f"{{self.base_url}}/api/storage/readings",
            json={{"data": payload}},
            headers=headers,
        )
        if res.status_code == 404:
            # Fallback or dev mode mock
            return {{"status": "recorded_mock", "data": payload}}
        res.raise_for_status()
        return res.json()


cloud_client = WorkersCraftClient()
"""
        files.append(
            GeneratedFile(
                id=f"{project_id}-cloud-client",
                project_id=project_id,
                version_number=version,
                path="cloud_backend/cloud_service_client.py",
                content=client_code,
                file_type="backend",
            )
        )

        # =====================================================================
        # 2. mqtt_worker.py (Async Ingestion & Alert Engine)
        # =====================================================================
        worker_code = f"""import asyncio
import json
import logging
import os
import aiomqtt
from cloud_service_client import cloud_client

# USER CODE BEGIN IMPORTS
# Optional developer imports
# USER CODE END IMPORTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mqtt_worker")

BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "{broker_host}")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", {broker_port}))
TELEMETRY_TOPIC = "{telemetry_topic}"
HIGH_TEMP_THRESHOLD = {high_temp_thresh}


async def evaluate_alert_rules(data: dict):
    temp = data.get("temperature_c")
    if temp is not None and float(temp) > HIGH_TEMP_THRESHOLD:
        logger.warning(
            f"[ALERT TRIGGERED] Temperature {{temp}}°C exceeds threshold {{HIGH_TEMP_THRESHOLD}}°C!"
        )
        # USER CODE BEGIN ON_ALERT
        # Custom SMS, webhook, or Slack alert dispatch logic
        # USER CODE END ON_ALERT


async def handle_telemetry_message(topic: str, payload_str: str):
    try:
        data = json.loads(payload_str)
        logger.info(f"[TELEMETRY RECEIVED] Topic: {{topic}} | Data: {{data}}")

        # 1. Evaluate real-time threshold alert rules
        await evaluate_alert_rules(data)

        # 2. Persist to WorkersCraft CloudService
        await cloud_client.store_reading(data)

    except json.JSONDecodeError:
        logger.error(f"Malformed JSON telemetry received: {{payload_str}}")
    except Exception as e:
        logger.error(f"Error handling telemetry: {{e}}")


async def run_worker():
    logger.info(f"Connecting to MQTT broker at {{BROKER_HOST}}:{{BROKER_PORT}}...")
    while True:
        try:
            async with aiomqtt.Client(hostname=BROKER_HOST, port=BROKER_PORT) as client:
                await client.subscribe(TELEMETRY_TOPIC)
                logger.info(f"Subscribed to telemetry topic: {{TELEMETRY_TOPIC}}")

                async for message in client.messages:
                    payload = message.payload.decode("utf-8")
                    await handle_telemetry_message(str(message.topic), payload)

        except aiomqtt.MqttError as err:
            logger.warning(f"MQTT connection lost: {{err}}. Reconnecting in 3 seconds...")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_worker())
"""
        files.append(
            GeneratedFile(
                id=f"{project_id}-mqtt-worker",
                project_id=project_id,
                version_number=version,
                path="cloud_backend/mqtt_worker.py",
                content=worker_code,
                file_type="backend",
            )
        )

        # =====================================================================
        # 3. server.py (FastAPI Command Gateway)
        # =====================================================================
        server_code = f"""from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiomqtt
import os

app = FastAPI(title="Project Command Gateway", version="v{version}.0")

BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "{broker_host}")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", {broker_port}))
COMMANDS_TOPIC = "{commands_topic}".replace("+", "node-01")

DECLARED_COMMANDS = {behavior.get("declared_commands", {}).get("value") or ["TRIGGER_FAN_FORCE_ON", "TRIGGER_FAN_FORCE_OFF", "REBOOT_NODE"]}


class CommandPayload(BaseModel):
    command: str


@app.post("/api/commands/dispatch")
async def dispatch_command(payload: CommandPayload):
    if payload.command not in DECLARED_COMMANDS:
        raise HTTPException(
            status_code=400,
            detail=f"Command '{{payload.command}}' is not declared in specification.",
        )

    # Publish command to MQTT broker
    async with aiomqtt.Client(hostname=BROKER_HOST, port=BROKER_PORT) as client:
        await client.publish(COMMANDS_TOPIC, payload.command.encode("utf-8"))

    return {{"status": "published", "command": payload.command, "topic": COMMANDS_TOPIC}}
"""
        files.append(
            GeneratedFile(
                id=f"{project_id}-cloud-server",
                project_id=project_id,
                version_number=version,
                path="cloud_backend/server.py",
                content=server_code,
                file_type="backend",
            )
        )

        return files
