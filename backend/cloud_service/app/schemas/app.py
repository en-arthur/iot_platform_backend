from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class AppCreate(BaseModel):
    project_id: UUID4
    name: str
    owner_id: UUID4

class AppResponse(BaseModel):
    id: UUID4
    project_id: UUID4
    name: str
    owner_id: UUID4
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class AppWithId(BaseModel):
    app_id: UUID4
