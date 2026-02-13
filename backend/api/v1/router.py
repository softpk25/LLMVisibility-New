"""
Main API router for Prometrix v1
"""

from fastapi import APIRouter

from api.v1 import (
    campaigns,
    brands,
    inspire,
    engage,
    settings,
    integrations
)

# Create main API router
api_router = APIRouter()

# Include module routers
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(brands.router, prefix="/brands", tags=["brands"])
api_router.include_router(inspire.router, prefix="/inspire", tags=["inspire"])
api_router.include_router(engage.router, prefix="/engage", tags=["engage"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])


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