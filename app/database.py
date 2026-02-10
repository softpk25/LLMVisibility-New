"""
Standalone Brand Blueprint Database Configuration
Manages database connection and session handling.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import get_settings

# Get settings
settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def init_db():
    """
    Initialize database by creating all tables.
    Call this on application startup.
    """
    # Import models to register them with Base
    from app.models import BrandBlueprint
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Use with FastAPI Depends().
    
    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_db():
    """
    Drop all tables and recreate them.
    WARNING: This will delete all data!
    Use only for development/testing.
    """
    from app.models import BrandBlueprint
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("WARNING: Database reset complete - all data deleted")


# ============================================================================
# Database Utilities
# ============================================================================

def get_db_session() -> Session:
    """
    Get a database session for use outside of FastAPI routes.
    Remember to close the session when done.
    
    Example:
        db = get_db_session()
        try:
            items = db.query(Item).all()
        finally:
            db.close()
    """
    return SessionLocal()


def check_db_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection is successful, False otherwise.
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
