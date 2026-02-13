"""
Prometrix FastAPI Backend
Production-ready backend for AI-powered Facebook SMM Agent platform
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from core.config import settings
from core.logging_config import setup_logging
from core.exceptions import setup_exception_handlers
from api.v1.router import api_router

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


from core.db import init_db as settings_init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Prometrix Backend...")
    
    # Initialize settings database
    logger.info("Initializing settings database...")
    settings_init_db()
    
    # Create necessary directories
    os.makedirs("data/campaigns", exist_ok=True)

    os.makedirs("data/brands", exist_ok=True)
    os.makedirs("data/settings", exist_ok=True)
    os.makedirs("data/inspire", exist_ok=True)
    os.makedirs("data/engage", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    yield
    
    logger.info("Shutting down Prometrix Backend...")


# Create FastAPI app
app = FastAPI(
    title="Prometrix API",
    description="AI-powered Facebook Social Media Marketing Agent platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup CORS
cors_origins = settings.ALLOWED_ORIGINS
if isinstance(cors_origins, str):
    if cors_origins == "*":
        cors_origins = ["*"]
    else:
        cors_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static files
app.mount("/templates", StaticFiles(directory="../templates"), name="templates")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Serve HTML templates (for development/testing)
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint serving campaign creation page"""
    try:
        with open("../templates/FACEBOOK-CREATE-CAMPAIGN.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>Prometrix Backend is running</h1><p>Frontend templates not found</p>")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "prometrix-backend",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )