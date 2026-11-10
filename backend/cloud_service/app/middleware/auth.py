from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.jwt import decode_token
from app.utils.errors import error_response
from typing import Optional
import uuid

security = HTTPBearer()

async def verify_app_id(request: Request) -> uuid.UUID:
    """Verify X-App-ID header exists and is valid"""
    app_id = request.headers.get("X-App-ID")
    
    if not app_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("MISSING_APP_ID", "X-App-ID header is required")
        )
    
    try:
        return uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("INVALID_APP_ID", "Invalid app ID format")
        )

async def verify_token(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify JWT token"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("INVALID_TOKEN", "Invalid or expired token")
        )
    
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("INVALID_TOKEN_TYPE", "Invalid token type")
        )
    
    return payload

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = None
) -> dict:
    """Get current user from token and verify app_id matches"""
    # Verify app_id header
    app_id = await verify_app_id(request)
    
    # Verify token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("MISSING_TOKEN", "Authorization token required")
        )
    
    payload = await verify_token(credentials)
    
    # Verify token's app_id matches header
    token_app_id = payload.get("app_id")
    if not token_app_id or uuid.UUID(token_app_id) != app_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response("APP_MISMATCH", "Token does not belong to this app")
        )
    
    return {
        "user_id": uuid.UUID(payload["user_id"]),
        "app_id": uuid.UUID(payload["app_id"]),
        "email": payload["email"]
    }

async def verify_admin_token(
    app_id: uuid.UUID,
    credentials: HTTPAuthorizationCredentials
) -> dict:
    """Verify admin JWT token for app owner"""
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("INVALID_ADMIN_TOKEN", "Invalid or expired admin token")
        )

    if uuid.UUID(payload.get("app_id", "")) != app_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response("APP_MISMATCH", "Admin token does not belong to this app")
        )

    return {"app_id": uuid.UUID(payload["app_id"]), "owner_id": payload["owner_id"]}
