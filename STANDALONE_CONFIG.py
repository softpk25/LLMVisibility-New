"""
Standalone Brand Blueprint Configuration
Manages environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./brand_blueprint.db"
    
    # Upload Configuration
    UPLOAD_DIR: str = "./uploads/guidelines"
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
