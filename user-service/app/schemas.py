"""
User service request/response schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserRegisterRequest(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Authentication response with user and tokens."""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class UserPreferencesRequest(BaseModel):
    """User preferences update request."""
    theme: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_alerts: Optional[bool] = None
    language: Optional[str] = None
    currency: Optional[str] = None


class UserPreferencesResponse(BaseModel):
    """User preferences response."""
    user_id: int
    theme: str
    notifications_enabled: bool
    email_alerts: bool
    language: str
    currency: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """User profile update request."""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class HealthResponse(BaseModel):
    """Service health response."""
    status: str
    service: str
    version: str
    timestamp: datetime
