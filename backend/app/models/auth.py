from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr


class AuthUser(BaseModel):
    id: str
    email: Optional[EmailStr] = None
    role: str = "authenticated"
    raw_claims: Dict[str, Any] = {}
