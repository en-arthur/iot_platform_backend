from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class FileUploadResponse(BaseModel):
    id: UUID4
    filename: str
    url: str
    size_bytes: int
    mime_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class FileListResponse(BaseModel):
    id: UUID4
    filename: str
    url: str
    size_bytes: int
    mime_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
