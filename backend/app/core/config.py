from typing import Annotated, List, Optional
import os
from urllib.parse import urlparse

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "DeviceStack Technologies API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    # Render injects RENDER_GIT_COMMIT; surface it in /health so the deployed
    # revision can be checked from outside.
    GIT_COMMIT: str = (os.getenv("RENDER_GIT_COMMIT") or "unknown")[:7]

    # Supabase Auth & Database
    SUPABASE_URL: str = "https://example.supabase.co"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder-service-role-key"
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_JWKS_URL: Optional[str] = None

    # CORS & Frontend Origins
    FRONTEND_URL: str = "http://localhost:3000"
    # NoDecode: accept both JSON arrays and comma-separated strings from the env.
    # Without it, pydantic-settings JSON-decodes List[str] before validators run.
    BACKEND_CORS_ORIGINS: Annotated[List[str], NoDecode] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            value = v.strip()
            if not value:
                return []
            if value.startswith("["):
                import json

                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return [i.strip() for i in value.strip("[]").split(",") if i.strip()]
            return [i.strip() for i in value.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    # MQTT Configuration
    MQTT_BROKER_HOST: str = "mosquitto"
    MQTT_BROKER_PORT: int = 1883
    MQTT_ADMIN_USER: Optional[str] = "admin"
    MQTT_ADMIN_PASSWORD: Optional[str] = "adminpassword"
    MQTT_USE_TLS: bool = False
    MQTT_MGMT_API_URL: Optional[str] = None  # Optional sidecar API for dynamic credentials

    @field_validator("MQTT_BROKER_HOST", mode="before")
    def normalise_mqtt_broker_host(cls, v):
        """Accept 'https://host/', 'host:10000' or 'host' and keep only the host.

        Render/dashboard values are often pasted as full URLs; passing a scheme to
        aiomqtt or to generated firmware produces an unresolvable hostname and
        silently breaks command delivery.
        """
        if not isinstance(v, str):
            return v
        value = v.strip()
        if not value:
            return value
        if "://" in value:
            return urlparse(value).hostname or value
        # Bare "host:port" (no scheme): drop the port, it lives in MQTT_BROKER_PORT.
        if value.count(":") == 1 and value.rsplit(":", 1)[1].isdigit():
            return value.rsplit(":", 1)[0]
        return value.rstrip("/")

    # AI Model Provider (Defaults to Gemini)
    AI_MODEL_PROVIDER: str = "gemini"  # gemini | openai | anthropic
    AI_MODEL_NAME: str = "gemini-2.5-flash"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Sandbox Runner Provider (Exclusively E2B)
    SANDBOX_PROVIDER: str = "e2b"
    E2B_API_KEY: Optional[str] = None
    # Shared template (built once) containing PlatformIO + the ESP32 toolchain.
    E2B_TEMPLATE: str = "esp32-pio"
    E2B_TIMEOUT_SECONDS: int = 900
    E2B_COMMAND_TIMEOUT_SECONDS: int = 900

    # WorkersCraft Cloud Service
    WORKERSCRAFT_URL: str = "http://localhost:8001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
