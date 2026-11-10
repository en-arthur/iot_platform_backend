from pydantic import BaseModel
from typing import Optional

class ErrorResponse(BaseModel):
    error: dict

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None

def error_response(code: str, message: str, details: dict = None) -> dict:
    """Create standardized error response"""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }
