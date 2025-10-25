"""
Shared configuration module for all services.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Base settings for all services."""
    
    # Database
    DATABASE_URL: str = "postgresql://crypto_user:crypto_password@postgres:5432/crypto_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Kafka
    KAFKA_BROKERS: str = "kafka:29092"
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
