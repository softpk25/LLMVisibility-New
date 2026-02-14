"""
Configuration settings for Prometrix backend
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: str = "*"
    
    # Database/Storage
    DATA_DIR: str = "data"
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # LLM Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    
    # Default LLM settings
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEFAULT_MODEL: str = "gpt-4"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Facebook/Instagram/Social Media (optional - allow extra fields)
    FB_APP_ID: str = ""
    FB_APP_SECRET: str = ""
    FB_APP_REDIRECT_URL: str = ""
    FACEBOOK_GRAPH_API_URL: str = ""
    FACEBOOK_ACCESS_TOKEN: str = ""
    FACEBOOK_PAGE_ID: str = ""
    FACEBOOK_PAGE_ACCESS_TOKEN: str = ""
    INSTAGRAM_BUSINESS_ID: str = ""
    FACEBOOK_AD_ACCOUNT_ID: str = ""
    FACEBOOK_AD_SET_ID: str = ""
    
    # Database
    DATABASE_URL: str = ""
    
    # Additional API Keys
    GEMINI_API_KEY: str = ""
    KLING_ACCESS_KEY: str = ""
    KLING_SECRET_KEY: str = ""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields from .env that aren't defined here
    )


# Global settings instance
settings = Settings()