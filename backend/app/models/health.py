from datetime import datetime, timezone
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    environment: str = "development"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
