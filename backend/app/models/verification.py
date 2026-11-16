from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

VerificationStatus = Literal["queued", "running", "passed", "failed"]

# How the published artifact must be flashed:
# - esp-segments: one image per offset (bootloader, partition table, app, ...)
# - uf2: a single UF2 image copied to the board's USB mass-storage volume
ArtifactFormat = Literal["esp-segments", "uf2"]


class VerificationRun(BaseModel):
    run_id: str
    project_id: str
    version_number: int
    status: VerificationStatus = "queued"
    sandbox_provider: str = "e2b"
    logs: str = ""
    board_id: Optional[str] = None
    # Real build output. These fields describe what was actually produced by
    # the compiler; nothing is fabricated when a build does not produce one.
    firmware_binary_url: Optional[str] = None
    artifact_name: Optional[str] = None
    artifact_size_bytes: Optional[int] = None
    artifact_format: Optional[ArtifactFormat] = None
    artifact_available: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class ArtifactSegment(BaseModel):
    """One flashable image and the address it must be written to."""

    name: str
    offset: int
    size: int
    data_b64: str


class FirmwareArtifact(BaseModel):
    run_id: str
    project_id: str
    board_id: str
    format: ArtifactFormat
    artifact_name: str
    total_bytes: int
    segments: List[ArtifactSegment]


class VerificationTriggerResponse(BaseModel):
    run_id: str
    status: VerificationStatus = "queued"
    message: str = "Verification run scheduled in ephemeral E2B sandbox."
