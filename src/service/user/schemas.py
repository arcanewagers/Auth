from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, HttpUrl
from typing import Optional
from datetime import datetime

from service.user.entites import UserStatus


class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = Field(None, max_length=100)
    profile_image_url: Optional[HttpUrl] = None

    @field_validator('full_name')
    def validate_full_name(cls, v):
        if v:
            # Remove potentially dangerous characters and normalize whitespace
            import re
            v = re.sub(r'[<>%$]', '', v)
            v = ' '.join(v.split())
        return v

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in '!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=100)
    profile_image: Optional[str] = None  # Base64 encoded image or None to remove

    @field_validator('full_name')
    def validate_full_name(cls, v):
        if v:
            import re
            v = re.sub(r'[<>%$]', '', v)
            v = ' '.join(v.split())
        return v

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    status: UserStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleOAuthPayload(BaseModel):
    token: str
    
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in '!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in '!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError('Password must contain at least one special character')
        return v
