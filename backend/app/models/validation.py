from typing import Dict, List, Literal
from pydantic import BaseModel, Field

ValidationLayer = Literal["completeness", "electrical", "logical", "resource", "security"]
ValidationSeverity = Literal["error", "warning", "info"]


class ValidationIssue(BaseModel):
    id: str
    layer: ValidationLayer
    severity: ValidationSeverity
    field_path: str
    message: str


class ValidationResponse(BaseModel):
    issues: List[ValidationIssue] = Field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    can_confirm: bool = True
