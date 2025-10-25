"""
User service database models.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship
from shared.utils.database import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    preferences = relationship("UserPreferences", uselist=False, back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")


class UserPreferences(Base):
    """User preferences model."""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    theme = Column(String(20), default="dark")
    notifications_enabled = Column(Boolean, default=True)
    email_alerts = Column(Boolean, default=True)
    price_alert_threshold = Column(Float, default=5.0)
    language = Column(String(10), default="en")
    currency = Column(String(10), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class RefreshToken(Base):
    """Refresh token model for token blacklisting."""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="refresh_tokens")


# Import for proper relationship setup
from sqlalchemy import Float
