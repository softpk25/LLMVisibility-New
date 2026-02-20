"""
Standalone Brand Blueprint Configuration
Manages environment variables and application settings.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

# Project root for absolute paths (set by server.py in production)
_ROOT = Path(os.environ.get("PROJECT_ROOT", os.getcwd()))


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    
    # Database Configuration (absolute path for production)
    DATABASE_URL: str = f"sqlite:///{_ROOT / 'brand_blueprint.db'}"
    
    # Upload Configuration (absolute path for production)
    UPLOAD_DIR: str = str(_ROOT / "uploads" / "guidelines")
    MAX_UPLOAD_SIZE: int = 52428800  # 50 MB in bytes
    
    # Application Configuration
    APP_NAME: str = "Brand Blueprint API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # CORS Configuration (if needed)
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid reading .env file multiple times.
    """
    return Settings()


def ensure_directories():
    """Ensure required directories exist"""
    settings = get_settings()
    
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Create database directory if using SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)


# Initialize directories on import
ensure_directories()
