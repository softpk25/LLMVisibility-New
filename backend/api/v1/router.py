"""
Main API router for Prometrix v1
"""

from fastapi import APIRouter

from .campaigns import router as campaigns_router
from .brands import router as brands_router
from .inspire import router as inspire_router
from .engage import router as engage_router
from .settings import router as settings_router

# Create main API router
api_router = APIRouter()

# Include module routers
api_router.include_router(campaigns_router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(brands_router, prefix="/brands", tags=["brands"])
api_router.include_router(inspire_router, prefix="/inspire", tags=["inspire"])
api_router.include_router(engage_router, prefix="/engage", tags=["engage"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])


@api_router.get("/")
async def api_root():
    """API root endpoint"""
    return {
        "message": "Prometrix API v1",
        "version": "1.0.0",
        "modules": [
            "campaigns",
            "brands", 
            "inspire",
            "engage",
            "settings"
        ]
    }