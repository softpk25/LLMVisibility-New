"""
Brand Blueprint Router Module
This file contains all the routes and logic for the brand blueprint feature.
Exports blueprint_router to be included in the main server application.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Body, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

# Import from app modules
from app.config import get_settings, Settings
from app.database import get_db, init_db
from app.models import (
    BrandBlueprint,
    BrandBlueprintRequest,
    BrandBlueprintResponse
)

# Get the directory of this file
BASE_DIR = Path(__file__).resolve().parent

# Setup templates for route handlers to use
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Create APIRouter instead of FastAPI app
blueprint_router = APIRouter(
    prefix="",
    tags=["brand-blueprint"]
)


# ============================================================================
# BRAND BLUEPRINT API ENDPOINTS
# ============================================================================

@blueprint_router.post("/api/brand/upload-guideline")
async def upload_brand_guideline(
    file: UploadFile = File(...),
    brand_id: str = Query("brand-001"),
    db: Session = Depends(get_db)
):
    """
    Upload and process brand guideline PDF/DOCX file.
    Extracts brand data using AI and updates the blueprint.
    """
    from app.services.pdf_processor import PDFProcessor
    
    # Validate file type
    allowed_extensions = ['.pdf', '.docx', '.doc']
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Validate file size (50 MB limit)
    max_size = 50 * 1024 * 1024  # 50 MB
    file_content = await file.read()
    
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 50 MB limit"
        )
    
    try:
        # Save uploaded file
        processor = PDFProcessor()
        file_path = processor.save_uploaded_file(file_content, file.filename)
        
        # Process the file and extract brand data
        brand_data = processor.process_guideline_file(file_path)
        
        # Get or create blueprint
        existing = db.query(BrandBlueprint).filter(
            BrandBlueprint.brand_id == brand_id
        ).first()
        
        if existing:
            blueprint = existing
        else:
            blueprint = BrandBlueprint()
            blueprint.brand_id = brand_id
        
        # Update blueprint with extracted data
        blueprint.brand_name = brand_data.get("brandName", "My Brand")
        blueprint.version = "1.0.0"
        blueprint.status = "generated"
        
        # Voice profile
        voice = brand_data.get("voice", {})
        blueprint.voice_formality = voice.get("formality", 50)
        blueprint.voice_humor = voice.get("humor", 50)
        blueprint.voice_warmth = voice.get("warmth", 50)
        blueprint.emoji_policy = voice.get("emojiPolicy", "medium")
        
        # Content pillars
        blueprint.pillars = brand_data.get("pillars", [])
        
        # Policies
        blueprint.forbidden_phrases = brand_data.get("forbiddenPhrases", [])
        blueprint.brand_hashtags = brand_data.get("brandHashtags", [])
        blueprint.max_hashtags = 5
        blueprint.product_default_pct = 30
        
        # Guideline document info
        blueprint.guideline_doc_name = file.filename
        blueprint.guideline_doc_status = "processed"
        
        db.add(blueprint)
        db.commit()
        db.refresh(blueprint)
        
        return {
            "status": "success",
            "message": "Brand guideline processed successfully",
            "brandData": {
                "brandName": brand_data.get("brandName"),
                "industry": brand_data.get("industry"),
                "targetAudience": brand_data.get("targetAudience"),
                "pillars": brand_data.get("pillars", []),
                "forbiddenPhrases": brand_data.get("forbiddenPhrases", []),
                "brandHashtags": brand_data.get("brandHashtags", []),
                "voice": voice
            },
            "blueprint": {
                "id": blueprint.id,
                "brandId": blueprint.brand_id,
                "brandName": blueprint.brand_name,
                "version": blueprint.version,
                "status": blueprint.status
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error processing guideline file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process guideline file: {str(e)}"
        )


@blueprint_router.get("/api/brand/blueprint")
async def get_brand_blueprint(
    brand_id: str = Query("brand-001"),
    db: Session = Depends(get_db)
):
    """Get brand blueprint by brand ID."""
    blueprint = db.query(BrandBlueprint).filter(
        BrandBlueprint.brand_id == brand_id
    ).first()
    
    if not blueprint:
        # Return default blueprint
        return {
            "id": 0,
            "brandId": brand_id,
            "brandName": "My Brand",
            "blueprint": {
                "version": "1.0.0",
                "status": "draft",
                "voice": {"formality": 50, "humor": 50, "warmth": 50, "emojiPolicy": "medium"},
                "pillars": [
                    {"name": "Innovation", "description": "Latest trends and breakthroughs", "weight": 30},
                    {"name": "Education", "description": "Teaching and learning content", "weight": 25},
                    {"name": "Community", "description": "Building connections", "weight": 25},
                    {"name": "Product", "description": "Product features and benefits", "weight": 20}
                ],
                "policies": {
                    "forbiddenPhrases": ["buy now", "limited time", "act fast"],
                    "maxHashtags": 5,
                    "brandHashtags": ["#MyBrand", "#Innovation"]
                },
                "productDefaultPct": 30
            },
            "guidelineDoc": {"name": "", "status": "none"}
        }
    
    return {
        "id": blueprint.id,
        "brandId": blueprint.brand_id,
        "brandName": blueprint.brand_name,
        "blueprint": {
            "version": blueprint.version,
            "status": blueprint.status,
            "voice": {
                "formality": blueprint.voice_formality,
                "humor": blueprint.voice_humor,
                "warmth": blueprint.voice_warmth,
                "emojiPolicy": blueprint.emoji_policy
            },
            "pillars": blueprint.pillars or [],
            "policies": {
                "forbiddenPhrases": blueprint.forbidden_phrases or [],
                "maxHashtags": blueprint.max_hashtags,
                "brandHashtags": blueprint.brand_hashtags or []
            },
            "productDefaultPct": blueprint.product_default_pct
        },
        "guidelineDoc": {
            "name": blueprint.guideline_doc_name or "",
            "status": blueprint.guideline_doc_status or "none"
        }
    }


@blueprint_router.post("/api/brand/blueprint")
async def save_brand_blueprint(
    request: BrandBlueprintRequest,
    db: Session = Depends(get_db)
):
    """Save or update brand blueprint."""
    existing = db.query(BrandBlueprint).filter(
        BrandBlueprint.brand_id == request.brandId
    ).first()
    
    if existing:
        blueprint = existing
    else:
        blueprint = BrandBlueprint()
        blueprint.brand_id = request.brandId
    
    blueprint.brand_name = request.brandName
    blueprint.version = request.blueprint.version
    blueprint.status = request.blueprint.status
    blueprint.voice_formality = request.blueprint.voice.formality
    blueprint.voice_humor = request.blueprint.voice.humor
    blueprint.voice_warmth = request.blueprint.voice.warmth
    blueprint.emoji_policy = request.blueprint.voice.emojiPolicy
    blueprint.pillars = [p.model_dump() for p in request.blueprint.pillars]
    blueprint.forbidden_phrases = request.blueprint.policies.forbiddenPhrases
    blueprint.max_hashtags = request.blueprint.policies.maxHashtags
    blueprint.brand_hashtags = request.blueprint.policies.brandHashtags
    blueprint.product_default_pct = request.blueprint.productDefaultPct
    
    db.add(blueprint)
    db.commit()
    db.refresh(blueprint)
    
    return {"status": "success", "message": "Blueprint saved", "id": blueprint.id}


@blueprint_router.post("/api/brand/blueprint/approve")
async def approve_brand_blueprint(
    brand_id: str = Query("brand-001"),
    db: Session = Depends(get_db)
):
    """Approve brand blueprint."""
    blueprint = db.query(BrandBlueprint).filter(
        BrandBlueprint.brand_id == brand_id
    ).first()
    
    if not blueprint:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    
    blueprint.status = "approved"
    db.commit()
    
    return {"status": "success", "message": "Blueprint approved"}


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@blueprint_router.get("/brand-blueprint", response_class=HTMLResponse)
async def brand_blueprint(request: Request):
    """Serve the brand blueprint page."""
    return templates.TemplateResponse("brand-blueprint.html", {"request": request})


@blueprint_router.get("/FACEBOOK-BRAND-REGISTRATION.html", response_class=HTMLResponse)
async def brand_registration(request: Request):
    """Serve the brand registration page (legacy route)."""
    return templates.TemplateResponse("brand-blueprint.html", {"request": request})


# ============================================================================
# HEALTH CHECK
# ============================================================================

@blueprint_router.get("/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "Brand Blueprint API",
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }
