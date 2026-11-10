from sqlalchemy.orm import Session
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token, decode_token, get_token_expiry
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import uuid
import hashlib

class AuthService:
    @staticmethod
    def register_user(db: Session, app_id: uuid.UUID, email: str, password: str) -> User:
        """Register a new user"""
        # Check if user exists
        existing = db.query(User).filter(
            User.app_id == app_id,
            User.email == email
        ).first()
        
        if existing:
            raise ValueError("Email already registered")
        
        # Create user
        user = User(
            id=uuid.uuid4(),
            app_id=app_id,
            email=email,
            password_hash=hash_password(password),
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def authenticate_user(db: Session, app_id: uuid.UUID, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = db.query(User).filter(
            User.app_id == app_id,
            User.email == email,
            User.is_active == True
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    def create_tokens(db: Session, user: User) -> Tuple[str, str]:
        """Create access and refresh tokens for user"""
        # Create access token
        access_token = create_access_token({
            "user_id": str(user.id),
            "app_id": str(user.app_id),
            "email": user.email
        })
        
        # Create refresh token
        refresh_token = create_refresh_token({
            "user_id": str(user.id),
            "app_id": str(user.app_id)
        })
        
        # Store refresh token hash in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        db_token = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        db.add(db_token)
        db.commit()
        
        return access_token, refresh_token
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[Tuple[str, str, User]]:
        """Refresh access token using refresh token"""
        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("user_id")
        app_id = payload.get("app_id")
        
        if not user_id or not app_id:
            return None
        
        # Verify token exists in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        db_token = db.query(RefreshToken).filter(
            RefreshToken.user_id == uuid.UUID(user_id),
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not db_token:
            return None
        
        # Get user
        user = db.query(User).filter(
            User.id == uuid.UUID(user_id),
            User.app_id == uuid.UUID(app_id),
            User.is_active == True
        ).first()
        
        if not user:
            return None
        
        # Update last used
        db_token.last_used_at = datetime.utcnow()
        
        # Delete old refresh token
        db.delete(db_token)
        
        # Create new tokens
        new_access_token, new_refresh_token = AuthService.create_tokens(db, user)
        
        return new_access_token, new_refresh_token, user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
        """Change user password"""
        if not verify_password(old_password, user.password_hash):
            return False
        
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def get_users_by_app(db: Session, app_id: uuid.UUID) -> List[User]:
        """Get all users for an app"""
        return db.query(User).filter(User.app_id == app_id).order_by(User.created_at.desc()).all()

    @staticmethod
    def delete_user(db: Session, user_id: uuid.UUID) -> bool:
        """Soft delete user"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False
            db.commit()
            return True
        return False
