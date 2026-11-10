from pydantic import BaseModel, UUID4
from typing import Any, Optional
from datetime import datetime

class StorageCreate(BaseModel):
    data: dict

class StorageUpdate(BaseModel):
    data: dict

class StorageResponse(BaseModel):
    id: UUID4
    data: dict
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class StorageBatchCreate(BaseModel):
    items: list[dict]

class StorageBatchDelete(BaseModel):
    ids: list[UUID4]
