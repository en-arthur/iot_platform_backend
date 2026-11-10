from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, Response, status
from app.core.auth import get_current_user
from app.db.repositories.device_repo import device_repo
from app.models.auth import AuthUser
from app.models.devices import (
    DeviceAlert,
    DeviceCommandRequest,
    DeviceCommandResponse,
    DeviceCreateRequest,
    DeviceProvisionResponse,
    DeviceResponse,
    TelemetryReading,
)

router = APIRouter(tags=["Devices & Ingestion"])


@router.post(
    "/projects/{project_id}/devices",
    response_model=DeviceProvisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def provision_device(
    project_id: str,
    req: DeviceCreateRequest,
    current_user: AuthUser = Depends(get_current_user),
) -> DeviceProvisionResponse:
    """Provision a new hardware device.
    Generates cryptographic credentials and returns secret ONLY ONCE.
    """
    return device_repo.provision_device(project_id, req, current_user.id)


@router.get(
    "/projects/{project_id}/devices",
    response_model=List[DeviceResponse],
)
def list_devices(
    project_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> List[DeviceResponse]:
    """List all registered devices for a project."""
    return device_repo.list_devices(project_id, current_user.id)


@router.get(
    "/devices/{device_id}",
    response_model=DeviceResponse,
)
def get_device(
    device_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> DeviceResponse:
    """Get metadata for a specific device."""
    return device_repo.get_device(device_id, current_user.id)


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_device(
    device_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Decommission and delete a device."""
    device_repo.delete_device(device_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/devices/{device_id}/commands",
    response_model=DeviceCommandResponse,
)
async def dispatch_device_command(
    device_id: str,
    req: DeviceCommandRequest,
    current_user: AuthUser = Depends(get_current_user),
) -> DeviceCommandResponse:
    """Dispatch a command to a device over MQTT.
    Verifies that the command is declared in project spec behavior.declared_commands!
    """
    return await device_repo.dispatch_command(device_id, req, current_user.id)


@router.get(
    "/devices/{device_id}/telemetry",
    response_model=List[TelemetryReading],
)
def get_device_telemetry(
    device_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    current_user: AuthUser = Depends(get_current_user),
) -> List[TelemetryReading]:
    """Retrieve historical telemetry readings for a device."""
    return device_repo.get_telemetry(device_id, current_user.id, limit=limit)


@router.post(
    "/devices/{device_id}/telemetry",
    response_model=TelemetryReading,
)
def record_device_telemetry(
    device_id: str,
    metrics: Dict[str, Any],
    current_user: AuthUser = Depends(get_current_user),
) -> TelemetryReading:
    """Ingest telemetry metrics and trigger automated alerts on threshold violation."""
    return device_repo.record_telemetry(device_id, metrics)


@router.get(
    "/devices/{device_id}/alerts",
    response_model=List[DeviceAlert],
)
def get_device_alerts(
    device_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> List[DeviceAlert]:
    """Retrieve automated threshold alerts for a device."""
    return device_repo.get_alerts(device_id, current_user.id)
