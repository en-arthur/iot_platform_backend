from typing import List, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI IoT Builder API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Supabase Auth & Database
    SUPABASE_URL: str = "https://example.supabase.co"
    SUPABASE_ANON_KEY: str = "placeholder-anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder-service-role-key"
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_JWKS_URL: Optional[str] = None

    # CORS & Frontend Origins
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    # MQTT Configuration
    MQTT_BROKER_HOST: str = "mosquitto"
    MQTT_BROKER_PORT: int = 1883
    MQTT_ADMIN_USER: Optional[str] = "admin"
    MQTT_ADMIN_PASSWORD: Optional[str] = "adminpassword"
    MQTT_USE_TLS: bool = False

    # AI / Agno Model Provider
    AI_MODEL_PROVIDER: str = "openai"  # openai | anthropic | gemini
    AI_MODEL_NAME: str = "gpt-4o"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Sandbox Runner Provider
    SANDBOX_PROVIDER: str = "e2b"  # e2b | daytona
    E2B_API_KEY: Optional[str] = None
    DAYTONA_API_KEY: Optional[str] = None

    # WorkersCraft Cloud Service
    WORKERSCRAFT_URL: str = "http://localhost:8001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
