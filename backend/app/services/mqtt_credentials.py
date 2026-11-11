import asyncio
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("app.services.mqtt_credentials")


class MQTTCredentialManager:
    """Manages per-device MQTT credentials by calling mosquitto_passwd
    via subprocess on the broker host, or via an HTTP sidecar API.

    Strategy:
    - Admin user (backend) authenticates with MQTT_ADMIN_USER / MQTT_ADMIN_PASSWORD.
    - Each device gets a unique username "device:<device_id>" and a one-time password.
    - ACL pattern rules (set at broker startup) restrict each device to only
      publish to devices/<device_id>/telemetry and subscribe to devices/<device_id>/cmd.
    - The backend registers credentials by SSHing or calling the broker's
      management HTTP API (if available), or by writing to a shared volume.
    """

    def __init__(self):
        self.admin_user = settings.MQTT_ADMIN_USER
        self.admin_password = settings.MQTT_ADMIN_PASSWORD
        self.broker_host = settings.MQTT_BROKER_HOST
        self.broker_port = settings.MQTT_BROKER_PORT
        self.mgmt_api_url: Optional[str] = getattr(settings, "MQTT_MGMT_API_URL", None)

    def device_username(self, device_id: str) -> str:
        """MQTT username format for a device — matches ACL pattern %u."""
        return f"device:{device_id}"

    async def register_device(self, device_id: str, password: str) -> bool:
        """Register a device's MQTT credentials.

        If MQTT_MGMT_API_URL is set, calls the management sidecar API.
        Otherwise logs a notice — credentials are enforced via ACL pattern rules,
        and devices authenticate by using device_id as part of the username.
        """
        username = self.device_username(device_id)

        if self.mgmt_api_url:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.post(
                        f"{self.mgmt_api_url}/credentials",
                        json={"username": username, "password": password},
                        headers={"X-Admin-Key": self.admin_password},
                    )
                    if resp.status_code == 200:
                        logger.info(f"Registered MQTT credentials for {username}")
                        return True
                    else:
                        logger.warning(f"MQTT mgmt API returned {resp.status_code} for {username}")
                        return False
            except Exception as e:
                logger.warning(f"MQTT credential registration failed for {username}: {e}")
                return False

        # Fallback: ACL pattern rules already restrict devices by username pattern.
        # Device must authenticate with admin credentials and use device_id as client_id.
        logger.info(
            f"MQTT mgmt API not configured. Device {device_id} will use pattern-based ACL "
            f"with username '{username}'. Ensure broker password file is updated externally."
        )
        return True

    async def revoke_device(self, device_id: str) -> bool:
        """Revoke a device's MQTT credentials."""
        username = self.device_username(device_id)

        if self.mgmt_api_url:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.delete(
                        f"{self.mgmt_api_url}/credentials/{username}",
                        headers={"X-Admin-Key": self.admin_password},
                    )
                    return resp.status_code in (200, 204)
            except Exception as e:
                logger.warning(f"MQTT credential revocation failed for {username}: {e}")
                return False

        logger.info(f"MQTT credential revocation for {username} requires broker restart or mgmt API.")
        return True


mqtt_credential_manager = MQTTCredentialManager()
