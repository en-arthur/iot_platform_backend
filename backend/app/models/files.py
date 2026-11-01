import hashlib
from datetime import datetime, timezone
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

FileType = Literal["firmware", "backend", "interface", "config"]


class GeneratedFile(BaseModel):
    id: str
    project_id: str
    version_number: int
    path: str
    content: str
    file_type: FileType
    is_protected: bool = False
    checksum: str = Field(default="")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def model_post_init(self, __context):
        if not self.checksum and self.content:
            self.checksum = hashlib.sha256(self.content.encode("utf-8")).hexdigest()


class FileContentUpdate(BaseModel):
    content: str
    record_as_protected: bool = True


class FileListItem(BaseModel):
    path: str
    file_type: FileType
    size_bytes: int
    is_protected: bool
    checksum: str
