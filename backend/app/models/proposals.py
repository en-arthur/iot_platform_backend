from datetime import datetime, timezone
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field

ProposalStatus = Literal["pending", "approved", "rejected"]


class SpecChangeItem(BaseModel):
    path: str  # e.g. "peripherals.button_pin"
    old: Any
    new: Any
    reason: str


class SpecProposal(BaseModel):
    proposal_id: str
    project_id: str
    summary: str
    changes: List[SpecChangeItem] = Field(default_factory=list)
    status: ProposalStatus = "pending"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None


class ProposalResolutionResponse(BaseModel):
    success: bool
    proposal_id: str
    status: ProposalStatus
    new_version: Optional[int] = None
    message: str
