from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

ProjectLifecycle = Literal["draft", "validated", "confirmed", "generated", "verified", "deployed"]
InterfaceType = Literal["dashboard", "web app"]


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    board_id: str = "esp32-s3-devkitc-1"
    interface_type: InterfaceType = "dashboard"


class ProjectCreate(ProjectBase):
    custom_peripherals: Optional[List[str]] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    board_id: Optional[str] = None
    interface_type: Optional[InterfaceType] = None
    lifecycle: Optional[ProjectLifecycle] = None


class Project(ProjectBase):
    id: str
    user_id: str
    lifecycle: ProjectLifecycle = "draft"
    version: int = 1
    deployed_version: Optional[str] = "v1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BehaviorDraftRequest(BaseModel):
    """Context from wizard step 1 used to draft the behavior specification."""

    name: Optional[str] = Field(default=None, max_length=120)
    goal: Optional[str] = Field(default=None, max_length=4000)
    board_id: Optional[str] = None
    peripherals: List[str] = Field(default_factory=list)
    custom_peripherals: List[str] = Field(default_factory=list)
    interface_type: Optional[str] = None


class BehaviorDraftResponse(BaseModel):
    behavior: str
    source: Literal["ai", "template"] = "template"


class ProjectConfirmResponse(BaseModel):
    success: bool = True
    lifecycle: ProjectLifecycle = "confirmed"
    version: int
    message: str = "Project spec verified and signed off for engineering synthesis."
