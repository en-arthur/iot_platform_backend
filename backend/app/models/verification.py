from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

VerificationStatus = Literal["queued", "running", "passed", "failed"]


class VerificationRun(BaseModel):
    run_id: str
    project_id: str
    version_number: int
    status: VerificationStatus = "queued"
    sandbox_provider: str = "e2b"
    logs: str = ""
    firmware_binary_url: Optional[str] = None
    selftest_results: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class VerificationTriggerResponse(BaseModel):
    run_id: str
    status: VerificationStatus = "queued"
    message: str = "Verification run scheduled in ephemeral E2B sandbox."


class SelfTestPayload(BaseModel):
    results: Dict[str, Any]
