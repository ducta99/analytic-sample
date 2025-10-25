"""
User service request/response schemas with comprehensive validation.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
import re


class UserRegisterRequest(BaseModel):
    """User registration request with validation."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username must be 3-50 characters"
    )
    email: EmailStr = Field(..., description="Valid email address required")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password must be 8-100 characters with at least 1 uppercase, 1 digit"
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """User response model."""
    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class AuthResponse(BaseModel):
    """Authentication response with user and tokens."""
    user: UserResponse
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="Valid refresh token")


class UserPreferencesRequest(BaseModel):
    """User preferences update request."""
    theme: Optional[str] = Field(
        default=None,
        pattern="^(light|dark|auto)$",
        description="UI theme preference"
    )
    notifications_enabled: Optional[bool] = None
    email_alerts: Optional[bool] = None
    language: Optional[str] = Field(
        default=None,
        pattern="^[a-z]{2}(-[A-Z]{2})?$",
        description="Language code (e.g., en, en-US)"
    )
    currency: Optional[str] = Field(
        default=None,
        pattern="^[A-Z]{3}$",
        description="Currency code (e.g., USD, EUR)"
    )


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
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """User profile update request."""
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50
    )
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=100
    )
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format if provided."""
        if v is not None and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Validate password strength if provided."""
        if v is not None:
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not re.search(r'[0-9]', v):
                raise ValueError('Password must contain at least one digit')
        return v


class HealthResponse(BaseModel):
    """Service health response."""
    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    service: str
    version: str
    timestamp: datetime
