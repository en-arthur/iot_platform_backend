from datetime import datetime, timezone
from typing import Dict
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"
    components: Dict[str, str] = Field(
        default_factory=lambda: {
            "database": "operational",
            "mqtt_broker": "operational",
            "e2b_sandbox": "operational",
            "cloud_service": "operational",
        }
    )
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
