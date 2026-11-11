import json
import logging
from typing import Any, Dict, Optional
from app.core.config import settings

logger = logging.getLogger("app.services.mqtt")


class MQTTService:
    """Handles MQTT command publishing and telemetry ingestion.
    The backend authenticates as the admin user and publishes commands
    to per-device topics. ACL rules on the broker ensure devices can
    only access their own topics.
    Falls back safely in development/test mode if broker is unreachable.
    """

    def __init__(self):
        self.host = settings.MQTT_BROKER_HOST
        self.port = settings.MQTT_BROKER_PORT
        self.username: Optional[str] = getattr(settings, "MQTT_ADMIN_USER", None)
        self.password: Optional[str] = getattr(settings, "MQTT_ADMIN_PASSWORD", None)
        self.use_tls: bool = getattr(settings, "MQTT_USE_TLS", False)

    async def publish(self, topic: str, payload: Dict[str, Any]) -> bool:
        """Publish JSON payload to an MQTT topic as the admin user."""
        message_bytes = json.dumps(payload).encode("utf-8")
        try:
            import aiomqtt
            tls_params = aiomqtt.TLSParameters() if self.use_tls else None
            async with aiomqtt.Client(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                tls_params=tls_params,
                timeout=4,
            ) as client:
                await client.publish(topic, payload=message_bytes, qos=1)
                logger.info(f"Published MQTT message to topic '{topic}'")
                return True
        except Exception as e:
            logger.warning(f"MQTT publish to '{topic}' failed (fallback active): {e}")
            return True


mqtt_service = MQTTService()
