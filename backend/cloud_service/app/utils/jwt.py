from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings
from typing import Optional
import uuid

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_admin_token(app_id: str, owner_id: str) -> str:
    """Create long-lived admin JWT token for app owner"""
    to_encode = {"app_id": app_id, "owner_id": owner_id}
    expire = datetime.utcnow() + timedelta(days=365)
    to_encode.update({"exp": expire, "type": "admin"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None

def get_token_expiry(token_type: str = "access") -> int:
    """Get token expiry in seconds"""
    if token_type == "access":
        return settings.access_token_expire_minutes * 60
    return settings.refresh_token_expire_days * 24 * 60 * 60
