import asyncio
import json
import logging
from typing import Any, Dict, Optional
from app.core.config import settings

logger = logging.getLogger("app.services.mqtt")


class MQTTService:
    """Handles MQTT command publishing via aiomqtt.
    
    When MQTT_USE_TLS=true (production/Render), connects over WSS (WebSocket Secure)
    to the Mosquitto broker's public URL on port 443, since Render only exposes
    services via HTTPS/WSS â€” not raw TCP.

    When MQTT_USE_TLS=false (local development), connects directly via raw MQTT TCP.
    """

    def __init__(self):
        self.host = settings.MQTT_BROKER_HOST
        self.port = settings.MQTT_BROKER_PORT
        self.username: Optional[str] = getattr(settings, "MQTT_ADMIN_USER", None)
        self.password: Optional[str] = getattr(settings, "MQTT_ADMIN_PASSWORD", None)
        self.use_tls: bool = getattr(settings, "MQTT_USE_TLS", False)
        # Last publish failure (surfaced in the 503 so the cause is visible
        # without Render log access). Never contains the password.
        self.last_error: Optional[str] = None

    async def publish(
        self, topic: str, payload: Dict[str, Any], *, attempts: int = 3
    ) -> bool:
        """Publish JSON payload to an MQTT topic as the admin user.

        The broker runs on a free Render instance and sleeps when idle, so the
        first connection after a quiet period can be refused at the WebSocket
        handshake. Retry with backoff instead of surfacing that as a hard 503.
        """
        message_bytes = json.dumps(payload).encode("utf-8")
        backoff = (0.0, 2.0, 6.0, 12.0)
        attempts = max(1, attempts)

        for attempt in range(attempts):
            delay = backoff[min(attempt, len(backoff) - 1)]
            if delay:
                await asyncio.sleep(delay)
            try:
                import aiomqtt

                if self.use_tls:
                    # Production (Render): connect over WSS.
                    # Render proxies HTTPS/WSS on port 443 → internal WebSocket listener.
                    # transport="websockets" is required: websocket_path alone does not
                    # switch paho off raw TCP, which just hangs against the HTTPS proxy.
                    async with aiomqtt.Client(
                        hostname=self.host,
                        port=443,
                        username=self.username,
                        password=self.password,
                        transport="websockets",
                        tls_params=aiomqtt.TLSParameters(),
                        websocket_path="/mqtt",
                        timeout=10,
                    ) as client:
                        await client.publish(topic, payload=message_bytes, qos=1)
                else:
                    # Local development: raw TCP MQTT
                    async with aiomqtt.Client(
                        hostname=self.host,
                        port=self.port,
                        username=self.username,
                        password=self.password,
                        timeout=10,
                    ) as client:
                        await client.publish(topic, payload=message_bytes, qos=1)

                logger.info(f"Published MQTT message to '{topic}'")
                self.last_error = None
                return True

            except Exception as e:
                self.last_error = f"{type(e).__name__}: {e}"
                logger.warning(
                    "MQTT publish attempt %s/%s to '%s' failed: %s",
                    attempt + 1,
                    attempts,
                    topic,
                    e,
                )

        logger.error(f"MQTT publish to '{topic}' failed after {attempts} attempts")
        return False


mqtt_service = MQTTService()
