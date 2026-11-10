from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    user_id: UUID4
    email: str
    access_token: str
    refresh_token: str
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    user_id: UUID4
    email: str
    created_at: datetime
    
class PasswordChange(BaseModel):
    old_password: str
    new_password: str
