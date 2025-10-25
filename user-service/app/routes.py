"""
User service routes for authentication and user management.
"""
import logging
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.utils.database import get_db_session
from shared.utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from shared.utils.exceptions import (
    ValidationError,
    AuthenticationError,
    ConflictError,
    ResourceNotFoundError
)
from shared.utils.responses import SuccessResponse
from app.models import User, UserPreferences
from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    AuthResponse,
    RefreshTokenRequest,
    UserPreferencesRequest,
    UserPreferencesResponse,
    UserUpdateRequest,
    HealthResponse
)
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """Dependency to get current authenticated user."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = verify_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user


@router.post("/health", response_model=SuccessResponse[dict])
async def health_check():
    """Health check endpoint."""
    return SuccessResponse(
        data={
            "status": "healthy",
            "service": "user-service",
            "timestamp": datetime.utcnow()
        }
    )


@router.post("/register", response_model=SuccessResponse[AuthResponse])
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new user."""
    # Check if user already exists
    stmt = select(User).where((User.email == request.email) | (User.username == request.username))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = hash_password(request.password)
    new_user = User(
        username=request.username,
        email=request.email,
        password_hash=hashed_password
    )
    db.add(new_user)
    await db.flush()
    
    # Create default preferences
    preferences = UserPreferences(user_id=new_user.id)
    db.add(preferences)
    
    await db.commit()
    await db.refresh(new_user)
    
    # Generate tokens
    access_token = create_access_token({"user_id": new_user.id, "email": new_user.email})
    refresh_token = create_refresh_token({"user_id": new_user.id})
    
    logger.info(f"User registered: {new_user.username}")
    
    return SuccessResponse(
        data=AuthResponse(
            user=UserResponse.from_orm(new_user),
            access_token=access_token,
            refresh_token=refresh_token
        )
    )


@router.post("/login", response_model=SuccessResponse[AuthResponse])
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Login user and return tokens."""
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Update last login
    user.last_login = datetime.utcnow()
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token({"user_id": user.id, "email": user.email})
    refresh_token = create_refresh_token({"user_id": user.id})
    
    logger.info(f"User logged in: {user.username}")
    
    return SuccessResponse(
        data=AuthResponse(
            user=UserResponse.from_orm(user),
            access_token=access_token,
            refresh_token=refresh_token
        )
    )


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Refresh access token using refresh token."""
    try:
        payload = verify_token(request.refresh_token)
        user_id = payload.get("user_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    new_access_token = create_access_token({"user_id": user.id, "email": user.email})
    
    return SuccessResponse(
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=request.refresh_token
        )
    )


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get user profile."""
    # Check authorization - users can only view their own profile or admin can view any
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot view other user profiles")
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return SuccessResponse(data=UserResponse.from_orm(user))


@router.put("/{user_id}", response_model=SuccessResponse[UserResponse])
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Update user profile."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot update other user profiles")
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.username:
        user.username = request.username
    if request.email:
        user.email = request.email
    if request.password:
        user.password_hash = hash_password(request.password)
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"User updated: {user.username}")
    
    return SuccessResponse(data=UserResponse.from_orm(user))


@router.delete("/{user_id}", response_model=SuccessResponse[dict])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Delete user account (soft delete)."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot delete other accounts")
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = False
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"User deleted: {user.username}")
    
    return SuccessResponse(data={"message": "User deleted successfully"})


@router.get("/{user_id}/preferences", response_model=SuccessResponse[UserPreferencesResponse])
async def get_preferences(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get user preferences."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot view other user preferences")
    
    stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
    result = await db.execute(stmt)
    prefs = result.scalar_one_or_none()
    
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    return SuccessResponse(data=UserPreferencesResponse.from_orm(prefs))


@router.put("/{user_id}/preferences", response_model=SuccessResponse[UserPreferencesResponse])
async def update_preferences(
    user_id: int,
    request: UserPreferencesRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Update user preferences."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Cannot update other user preferences")
    
    stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
    result = await db.execute(stmt)
    prefs = result.scalar_one_or_none()
    
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    # Update only provided fields
    if request.theme:
        prefs.theme = request.theme
    if request.notifications_enabled is not None:
        prefs.notifications_enabled = request.notifications_enabled
    if request.email_alerts is not None:
        prefs.email_alerts = request.email_alerts
    if request.language:
        prefs.language = request.language
    if request.currency:
        prefs.currency = request.currency
    
    prefs.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(prefs)
    
    logger.info(f"User preferences updated: {user_id}")
    
    return SuccessResponse(data=UserPreferencesResponse.from_orm(prefs))
