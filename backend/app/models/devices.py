from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DeviceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Human readable device name")


class DeviceProvisionResponse(BaseModel):
    device_id: str
    project_id: str
    name: str
    secret: str = Field(..., description="Plaintext authentication secret. Shown ONLY ONCE upon creation.")
    mqtt_broker_host: str
    mqtt_broker_port: int
    telemetry_topic: str
    command_topic: str
    created_at: str


class DeviceResponse(BaseModel):
    device_id: str
    project_id: str
    name: str
    status: str = Field(..., description="'online', 'offline', or 'provisioned'")
    telemetry_topic: str
    command_topic: str
    last_seen_at: Optional[str] = None
    created_at: str


class DeviceCommandRequest(BaseModel):
    command: str = Field(..., description="Action name, e.g. 'turn_on_fan', 'open_valve'")
    params: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")


class DeviceCommandResponse(BaseModel):
    command_id: str
    device_id: str
    command: str
    params: Dict[str, Any]
    status: str = Field(..., description="'dispatched' or 'queued'")
    dispatched_at: str


class TelemetryReading(BaseModel):
    device_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metrics: Dict[str, Any] = Field(..., description="Key-value metrics, e.g. {'temperature_c': 24.5}")


class DeviceAlert(BaseModel):
    alert_id: str
    device_id: str
    severity: str = Field(..., description="'info', 'warning', or 'critical'")
    metric: str
    current_value: Any
    threshold_value: Any
    message: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DeploymentResponse(BaseModel):
    deployment_id: str
    project_id: str
    status: str
    broker_url: str
    cloud_service_app_id: str
    deployed_at: str
    message: str
