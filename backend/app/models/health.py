import os
from datetime import datetime, timezone
from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"
    # Render injects RENDER_GIT_COMMIT, so the deployed revision can be verified
    # from outside without dashboard access.
    commit: str = "unknown"
    # "jwks" (asymmetric Supabase keys), "hs256" (legacy secret) or "none".
    jwt_verification: str = "unknown"

    components: Dict[str, str] = Field(
        default_factory=lambda: {
            "database": "operational",
            "mqtt_broker": "operational",
            "e2b_sandbox": "operational",
            "cloud_service": "operational",
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
