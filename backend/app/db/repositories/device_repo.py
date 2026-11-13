import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.exceptions import APIError, ConflictError, NotFoundError, ValidationError
from app.db import supabase_store
from app.db.repositories.project_repo import project_repo
from app.models.devices import (
    DeviceAlert,
    DeviceCommandRequest,
    DeviceCommandResponse,
    DeviceCreateRequest,
    DeviceProvisionResponse,
    DeviceResponse,
    TelemetryReading,
)
from app.services.mqtt_service import mqtt_service
from app.services.mqtt_credentials import mqtt_credential_manager


class DeviceRecord:
    def __init__(
        self,
        device_id: str,
        project_id: str,
        name: str,
        token_hash: str,
        status: str = "provisioned",
        created_at: Optional[str] = None,
        last_seen_at: Optional[str] = None,
    ):
        self.device_id = device_id
        self.project_id = project_id
        self.name = name
        self.token_hash = token_hash
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.last_seen_at = last_seen_at


class DeviceRepository:
    """Repository managing device provisioning, credential hashing, declared commands,
    telemetry ingestion, and automated threshold alerts.
    """

    def __init__(self):
        self._devices: Dict[str, DeviceRecord] = {}
        self._telemetry: Dict[str, List[TelemetryReading]] = {}
        self._alerts: Dict[str, List[DeviceAlert]] = {}

        # Prepopulate demo device for greenhouse project ONLY in development/test
        if getattr(settings, "ENVIRONMENT", "development") in ("development", "test"):
            demo_device_id = "dev-greenhouse-01"
            salt_hash = self._hash_secret("gh-demo-secret-token")
            self._devices[demo_device_id] = DeviceRecord(
                device_id=demo_device_id,
                project_id="proj-greenhouse-01",
                name="North GreenHouse ESP32-S3",
                token_hash=salt_hash,
                status="online",
                last_seen_at=datetime.now(timezone.utc).isoformat(),
            )
            self._telemetry[demo_device_id] = [
                TelemetryReading(
                    device_id=demo_device_id,
                    metrics={"temperature_c": 24.2, "humidity_pct": 62.0, "soil_moisture": 450},
                )
            ]
            self._alerts[demo_device_id] = []

    def _hash_secret(self, secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    def provision_device(
        self, project_id: str, req: DeviceCreateRequest, user_id: str
    ) -> DeviceProvisionResponse:
        import asyncio
        from app.services.mqtt_credentials import mqtt_credential_manager

        # Validate project exists and user has access
        project = project_repo.get_project(project_id, user_id)

        # Generate unique device_id and plaintext secret (for DeviceStack auth)
        device_id = f"dev-{uuid.uuid4().hex[:8]}"
        secret = f"dsec_{secrets.token_urlsafe(32)}"
        token_hash = self._hash_secret(secret)

        # Generate per-device MQTT credentials (shown ONLY ONCE)
        mqtt_password = secrets.token_urlsafe(24)
        mqtt_username = mqtt_credential_manager.device_username(device_id)

        now_str = datetime.now(timezone.utc).isoformat()
        record = DeviceRecord(
            device_id=device_id,
            project_id=project_id,
            name=req.name,
            token_hash=token_hash,
            status="provisioned",
            created_at=now_str,
        )
        self._devices[device_id] = record
        self._telemetry[device_id] = []
        self._alerts[device_id] = []

        # Persist so provisioned devices survive a backend restart.
        supabase_store.save_device(record)

        # Register MQTT credentials asynchronously (non-blocking)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(mqtt_credential_manager.register_device(device_id, mqtt_password))
            else:
                loop.run_until_complete(mqtt_credential_manager.register_device(device_id, mqtt_password))
        except Exception as e:
            import logging
            logging.getLogger("app.db.device_repo").warning(
                f"MQTT credential registration failed for {device_id}: {e}"
            )

        # Record audit log
        from app.db.repositories.audit_repo import audit_repo
        audit_repo.record_action(
            action="DEVICE_PROVISION",
            user_id=user_id,
            project_id=project_id,
            payload={"device_id": device_id, "name": req.name},
        )

        return DeviceProvisionResponse(
            device_id=device_id,
            project_id=project_id,
            name=req.name,
            secret=secret,          # DeviceStack API secret — shown ONLY ONCE
            mqtt_broker_host=settings.MQTT_BROKER_HOST,
            # Public TLS endpoint is always 443 on Render.
            mqtt_broker_port=443 if settings.MQTT_USE_TLS else settings.MQTT_BROKER_PORT,
            telemetry_topic=f"devices/{device_id}/telemetry",
            command_topic=f"devices/{device_id}/cmd",
            mqtt_username=mqtt_username,   # Per-device MQTT username — shown ONLY ONCE
            mqtt_password=mqtt_password,   # Per-device MQTT password — shown ONLY ONCE
            created_at=now_str,
        )

    def list_devices(self, project_id: str, user_id: str) -> List[DeviceResponse]:
        project_repo.get_project(project_id, user_id)
        results = []
        for dev in self._devices.values():
            if dev.project_id == project_id:
                results.append(
                    DeviceResponse(
                        device_id=dev.device_id,
                        project_id=dev.project_id,
                        name=dev.name,
                        status=dev.status,
                        telemetry_topic=f"devices/{dev.device_id}/telemetry",
                        command_topic=f"devices/{dev.device_id}/cmd",
                        last_seen_at=dev.last_seen_at,
                        created_at=dev.created_at,
                    )
                )
        return results

    def get_device(self, device_id: str, user_id: str) -> DeviceResponse:
        dev = self._devices.get(device_id)
        if not dev:
            raise NotFoundError(f"Device '{device_id}' not found")
        project_repo.get_project(dev.project_id, user_id)
        return DeviceResponse(
            device_id=dev.device_id,
            project_id=dev.project_id,
            name=dev.name,
            status=dev.status,
            telemetry_topic=f"devices/{dev.device_id}/telemetry",
            command_topic=f"devices/{dev.device_id}/cmd",
            last_seen_at=dev.last_seen_at,
            created_at=dev.created_at,
        )

    def delete_device(self, device_id: str, user_id: str) -> None:
        dev = self._devices.get(device_id)
        if not dev:
            raise NotFoundError(f"Device '{device_id}' not found")
        project_repo.get_project(dev.project_id, user_id)
        del self._devices[device_id]
        self._telemetry.pop(device_id, None)
        self._alerts.pop(device_id, None)
        supabase_store.delete_device(device_id)

    async def dispatch_command(
        self, device_id: str, req: DeviceCommandRequest, user_id: str
    ) -> DeviceCommandResponse:
        dev = self._devices.get(device_id)
        if not dev:
            raise NotFoundError(f"Device '{device_id}' not found")

        project = project_repo.get_project(dev.project_id, user_id)
        spec_dict = project_repo.get_spec(dev.project_id, user_id)

        # CONTRACT REQUIREMENT: Verify command is declared in project's spec.behavior.declared_commands
        behavior_fields = spec_dict.get("behavior", {}).get("fields", {})
        cmd_field = behavior_fields.get("declared_commands", {})
        cmd_values = cmd_field.get("value", []) if isinstance(cmd_field, dict) else []

        declared_cmds = []
        for c in cmd_values:
            if isinstance(c, str):
                declared_cmds.append(c)
            elif isinstance(c, dict) and "name" in c:
                declared_cmds.append(c["name"])

        if not declared_cmds:
            declared_cmds = ["TRIGGER_FAN_FORCE_ON", "TRIGGER_FAN_FORCE_OFF", "REBOOT_NODE"]

        if req.command not in declared_cmds:
            raise ValidationError(
                f"Command '{req.command}' is not declared in project spec behavior.declared_commands. "
                f"Declared commands: {declared_cmds}"
            )

        cmd_id = f"cmd-{uuid.uuid4().hex[:8]}"
        now_str = datetime.now(timezone.utc).isoformat()
        topic = f"devices/{device_id}/cmd"

        payload = {
            "command_id": cmd_id,
            "device_id": device_id,
            "command": req.command,
            "params": req.params,
            "timestamp": now_str,
        }

        published = await mqtt_service.publish(topic, payload)
        if not published:
            raise APIError(
                status_code=503,
                detail=(
                    f"MQTT broker unavailable: command '{req.command}' was not delivered "
                    f"to device '{device_id}'. Check MQTT_BROKER_HOST / MQTT_USE_TLS / "
                    f"MQTT_ADMIN_* credentials. Cause: "
                    f"{mqtt_service.last_error or 'unknown'}"
                ),
            )

        # Record audit log
        from app.db.repositories.audit_repo import audit_repo
        audit_repo.record_action(
            action="DEVICE_COMMAND",
            user_id=user_id,
            project_id=dev.project_id,
            payload={"device_id": device_id, "command": req.command, "params": req.params},
        )

        return DeviceCommandResponse(
            command_id=cmd_id,
            device_id=device_id,
            command=req.command,
            params=req.params,
            status="dispatched",
            dispatched_at=now_str,
        )

    def record_telemetry(self, device_id: str, metrics: Dict[str, Any]) -> TelemetryReading:
        dev = self._devices.get(device_id)
        if not dev:
            raise NotFoundError(f"Device '{device_id}' not found")

        now_str = datetime.now(timezone.utc).isoformat()
        dev.last_seen_at = now_str
        dev.status = "online"

        reading = TelemetryReading(
            device_id=device_id,
            timestamp=now_str,
            metrics=metrics,
        )
        if device_id not in self._telemetry:
            self._telemetry[device_id] = []
        self._telemetry[device_id].append(reading)

        # Mirror the device state and each numeric metric to Supabase.
        supabase_store.save_device(dev)
        for metric, value in metrics.items():
            supabase_store.save_reading(
                device_id=device_id,
                project_id=dev.project_id,
                metric=metric,
                value=value,
                recorded_at=now_str,
            )

        # Check threshold rules against spec or default safety margins
        self._evaluate_thresholds(dev, metrics)

        return reading

    def _evaluate_thresholds(self, dev: DeviceRecord, metrics: Dict[str, Any]):
        # Example check: Temperature > 35C is critical high, Humidity < 20% is low
        temp = metrics.get("temperature_c") or metrics.get("temp")
        if temp is not None and isinstance(temp, (int, float)):
            if temp > 35.0:
                self._add_alert(
                    dev.device_id,
                    severity="critical",
                    metric="temperature_c",
                    current_val=temp,
                    thresh_val=35.0,
                    msg=f"High Temperature Alert: Current temperature {temp}°C exceeds safety threshold 35.0°C",
                )
        hum = metrics.get("humidity_pct") or metrics.get("humidity")
        if hum is not None and isinstance(hum, (int, float)):
            if hum < 20.0:
                self._add_alert(
                    dev.device_id,
                    severity="warning",
                    metric="humidity_pct",
                    current_val=hum,
                    thresh_val=20.0,
                    msg=f"Low Humidity Warning: Current humidity {hum}% is below target threshold 20.0%",
                )

    def _add_alert(self, device_id: str, severity: str, metric: str, current_val: Any, thresh_val: Any, msg: str):
        alert = DeviceAlert(
            alert_id=f"alert-{uuid.uuid4().hex[:8]}",
            device_id=device_id,
            severity=severity,
            metric=metric,
            current_value=current_val,
            threshold_value=thresh_val,
            message=msg,
        )
        if device_id not in self._alerts:
            self._alerts[device_id] = []
        self._alerts[device_id].append(alert)

    def get_telemetry(self, device_id: str, user_id: str, limit: int = 50) -> List[TelemetryReading]:
        self.get_device(device_id, user_id)
        readings = self._telemetry.get(device_id, [])
        return readings[-limit:]

    def get_alerts(self, device_id: str, user_id: str) -> List[DeviceAlert]:
        self.get_device(device_id, user_id)
        return self._alerts.get(device_id, [])


device_repo = DeviceRepository()
