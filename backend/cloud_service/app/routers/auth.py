from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, 
    RefreshTokenRequest, UserResponse, PasswordChange
)
from app.services.auth_service import AuthService
from app.services.app_service import AppService
from app.middleware.auth import verify_app_id, security, get_current_user
from app.utils.errors import error_response
from app.utils.jwt import get_token_expiry

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Verify app exists
    app_id = await verify_app_id(request)
    app = AppService.get_app_by_id(db, app_id)
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("APP_NOT_FOUND", "App not found")
        )
    
    try:
        # Create user
        user = AuthService.register_user(db, app_id, user_data.email, user_data.password)
        
        # Create tokens
        access_token, refresh_token = AuthService.create_tokens(db, user)
        
        return TokenResponse(
            user_id=user.id,
            email=user.email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=get_token_expiry("access")
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_response("DUPLICATE_EMAIL", str(e))
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user"""
    # Verify app exists
    app_id = await verify_app_id(request)
    app = AppService.get_app_by_id(db, app_id)
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("APP_NOT_FOUND", "App not found")
        )
    
    # Authenticate user
    user = AuthService.authenticate_user(db, app_id, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("INVALID_CREDENTIALS", "Invalid email or password")
        )
    
    # Create tokens
    access_token, refresh_token = AuthService.create_tokens(db, user)
    
    return TokenResponse(
        user_id=user.id,
        email=user.email,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=get_token_expiry("access")
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    # Verify app exists
    app_id = await verify_app_id(request)
    
    result = AuthService.refresh_access_token(db, token_data.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("INVALID_REFRESH_TOKEN", "Invalid or expired refresh token")
        )
    
    access_token, refresh_token, user = result
    
    return TokenResponse(
        user_id=user.id,
        email=user.email,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=get_token_expiry("access")
    )

@router.get("/me", response_model=UserResponse)
async def get_me(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user info"""
    current_user = await get_current_user(request, credentials)
    
    user = AuthService.get_user_by_id(db, current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("USER_NOT_FOUND", "User not found")
        )
    
    return UserResponse(
        user_id=user.id,
        email=user.email,
        created_at=user.created_at
    )

@router.put("/password")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Change user password"""
    current_user = await get_current_user(request, credentials)
    
    user = AuthService.get_user_by_id(db, current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("USER_NOT_FOUND", "User not found")
        )
    
    success = AuthService.change_password(
        db, user, password_data.old_password, password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_response("INVALID_PASSWORD", "Invalid old password")
        )
    
    return {"success": True}

@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete user account"""
    current_user = await get_current_user(request, credentials)
    
    success = AuthService.delete_user(db, current_user["user_id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response("USER_NOT_FOUND", "User not found")
        )
    
    return None
