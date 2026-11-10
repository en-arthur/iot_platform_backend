from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    id: str = Field(..., description="Audit record unique identifier")
    user_id: str
    project_id: Optional[str] = None
    action: str = Field(
        ...,
        description="Audit action type: SPEC_CONFIRM, CODE_GENERATE, VERIFICATION_RUN, DEVICE_PROVISION, DEVICE_COMMAND, PROJECT_DEPLOY",
    )
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogEntry]
