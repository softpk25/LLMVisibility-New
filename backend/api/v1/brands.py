"""
Brand Registration API endpoints
"""

import uuid
import os
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Path
from fastapi.responses import JSONResponse

from schemas.brand import (
    BrandRegisterRequest,
    BrandResponse,
    BrandListResponse,
    BrandBlueprintUpdate,
    BrandData,
    BrandStatus,
    FileUploadResponse,
    BrandExtractionResult
)
from services.storage import brand_storage
from services.llm_orchestrator import orchestrator
from core.config import settings
from core.logging_config import get_logger
from core.exceptions import NotFoundError

logger = get_logger("brands_api")
router = APIRouter()


@router.post("/register", response_model=BrandResponse)
async def register_brand(request: BrandRegisterRequest):
    """Register a new brand"""
    try:
        # Create brand data
        brand_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        brand_data = BrandData(
            id=brand_id,
            brand_name=request.brand_name,
            industry=request.industry,
            description=request.description,
            website_url=request.website_url,
            voice_profile=request.voice_profile,
            content_pillars=request.content_pillars,
            brand_guidelines={},  # Will be populated from uploads
            target_demographics=request.target_demographics,
            brand_values=request.brand_values,
            status=BrandStatus.DRAFT,
            created_at=now,
            updated_at=now,
            version="v1"
        )
        
        # Save to storage
        await brand_storage.create_brand(brand_data.dict())
        
        # Generate brand blueprint using LLM
        llm_payload = {
            "task_type": "text_generation",
            "prompt": f"""
            Create a comprehensive brand blueprint for {request.brand_name}.
            
            Brand Information:
            - Industry: {request.industry}
            - Description: {request.description}
            - Website: {request.website_url or 'Not provided'}
            
            Voice Profile:
            - Formality: {request.voice_profile.formality}
            - Humor: {request.voice_profile.humor}
            - Tone: {request.voice_profile.tone}
            - Personality Traits: {request.voice_profile.personality_traits}
            
            Content Pillars:
            {[f"- {pillar.name} ({pillar.type}): {pillar.description}" for pillar in request.content_pillars]}
            
            Brand Values: {request.brand_values}
            
            Generate:
            1. Brand messaging guidelines
            2. Content creation rules
            3. Visual identity suggestions
            4. Communication style guide
            5. Do's and Don'ts for content
            
            Format as structured JSON with clear sections.
            """,
            "parameters": {
                "max_tokens": 2000,
                "temperature": 0.7
            },
            "request_id": f"brand_blueprint_{brand_id}"
        }
        
        try:
            llm_result = await orchestrator.generate(llm_payload)
            
            if llm_result.get("success"):
                # Store generated blueprint
                blueprint_updates = {
                    "ai_generated_blueprint": {
                        "content": llm_result.get("content", ""),
                        "generated_at": datetime.utcnow().isoformat(),
                        "llm_metadata": llm_result.get("orchestrator_metadata", {})
                    },
                    "status": BrandStatus.ACTIVE.value
                }
                
                await brand_storage.update_brand(brand_id, blueprint_updates)
                brand_data.status = BrandStatus.ACTIVE
                
        except Exception as e:
            logger.warning(f"Failed to generate brand blueprint: {e}")
            # Continue without blueprint generation
        
        logger.info(f"Registered brand {brand_id}: {request.brand_name}")
        
        return BrandResponse(
            brand_id=brand_id,
            status="success",
            message="Brand registered successfully",
            data=brand_data
        )
        
    except Exception as e:
        logger.error(f"Failed to register brand: {e}")
        raise HTTPException(status_code=500, detail="Failed to register brand")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_brand_guidelines(file: UploadFile = File(...)):
    """Upload brand guideline documents (PDF/DOCX)"""
    try:
        # Validate file type
        allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")
        
        # Validate file size
        if file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Generate file ID and save
        file_id = str(uuid.uuid4())
        upload_dir = os.path.join(settings.UPLOAD_DIR, "brand_guidelines")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = ".pdf" if file.content_type == "application/pdf" else ".docx"
        file_path = os.path.join(upload_dir, f"{file_id}{file_extension}")
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Uploaded brand guideline file {file_id}: {file.filename}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type,
            upload_url=f"/uploads/brand_guidelines/{file_id}{file_extension}",
            status="uploaded"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


@router.post("/extract/{file_id}", response_model=BrandExtractionResult)
async def extract_brand_guidelines(file_id: str = Path(..., description="File ID")):
    """Extract brand guidelines from uploaded document using AI"""
    try:
        # Find uploaded file
        upload_dir = os.path.join(settings.UPLOAD_DIR, "brand_guidelines")
        
        # Check for both PDF and DOCX
        file_path = None
        for ext in [".pdf", ".docx"]:
            potential_path = os.path.join(upload_dir, f"{file_id}{ext}")
            if os.path.exists(potential_path):
                file_path = potential_path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Create LLM payload for document analysis
        llm_payload = {
            "task_type": "text_generation",
            "prompt": f"""
            Analyze the uploaded brand guideline document and extract key information.
            
            File: {file_path}
            
            Extract and structure the following information:
            1. Brand voice characteristics (formality, humor, tone)
            2. Content pillars and themes
            3. Visual guidelines (colors, fonts, imagery style)
            4. Messaging guidelines and key phrases
            5. Do's and Don'ts for brand communication
            6. Target audience information
            7. Brand values and personality traits
            
            Format the response as structured JSON with confidence scores for each extracted element.
            
            Note: This is a mock extraction. In production, implement actual document parsing.
            """,
            "parameters": {
                "max_tokens": 1500,
                "temperature": 0.3
            },
            "request_id": f"extract_guidelines_{file_id}"
        }
        
        llm_result = await orchestrator.generate(llm_payload)
        
        if not llm_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to analyze document")
        
        # Mock extraction result (in production, parse actual document)
        extraction_result = BrandExtractionResult(
            extracted_text=llm_result.get("content", ""),
            voice_suggestions={
                "formality": "neutral",
                "humor": "subtle", 
                "tone": "friendly",
                "personality_traits": ["professional", "approachable", "innovative"],
                "do_phrases": ["We believe", "Our mission", "Together we"],
                "dont_phrases": ["Never", "Impossible", "Can't"]
            },
            pillar_suggestions=[
                {
                    "id": str(uuid.uuid4()),
                    "name": "Innovation",
                    "type": "educational",
                    "description": "Showcasing cutting-edge solutions",
                    "keywords": ["technology", "innovation", "future"],
                    "percentage": 40
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Community",
                    "type": "community",
                    "description": "Building connections with our audience",
                    "keywords": ["community", "together", "support"],
                    "percentage": 30
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Excellence",
                    "type": "promotional",
                    "description": "Demonstrating quality and expertise",
                    "keywords": ["quality", "excellence", "expertise"],
                    "percentage": 30
                }
            ],
            guideline_suggestions={
                "logo_usage": {"minimum_size": "24px", "clear_space": "2x logo height"},
                "color_palette": ["#5046e5", "#00c4cc", "#1a202c", "#f7fafc"],
                "typography": {"primary": "Inter", "secondary": "Arial"},
                "imagery_style": {"style": "modern", "mood": "professional", "colors": "vibrant"},
                "messaging_guidelines": {"tone": "conversational", "voice": "expert"},
                "compliance_rules": ["Always include disclaimer", "Avoid medical claims"]
            },
            confidence_score=0.85
        )
        
        logger.info(f"Extracted brand guidelines from file {file_id}")
        
        return extraction_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract guidelines: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract guidelines")


@router.put("/{brand_id}/blueprint", response_model=BrandResponse)
async def update_brand_blueprint(
    request: BrandBlueprintUpdate,
    brand_id: str = Path(..., description="Brand ID")
):
    """Update brand blueprint (voice, pillars, guidelines)"""
    try:
        # Get existing brand
        try:
            brand_data = await brand_storage.get_brand(brand_id)
        except NotFoundError:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Prepare updates
        updates = {"updated_at": datetime.utcnow().isoformat()}
        
        if request.voice_profile is not None:
            updates["voice_profile"] = request.voice_profile.dict()
        
        if request.content_pillars is not None:
            updates["content_pillars"] = [pillar.dict() for pillar in request.content_pillars]
        
        if request.brand_guidelines is not None:
            updates["brand_guidelines"] = request.brand_guidelines.dict()
        
        if request.brand_values is not None:
            updates["brand_values"] = request.brand_values
        
        # Update version
        current_version = brand_data.get("version", "v1")
        version_num = int(current_version.replace("v", "")) + 1
        updates["version"] = f"v{version_num}"
        
        # Save updates
        updated_brand = await brand_storage.update_brand(brand_id, updates)
        
        logger.info(f"Updated brand blueprint {brand_id}")
        
        return BrandResponse(
            brand_id=brand_id,
            status="success",
            message="Brand blueprint updated successfully",
            data=updated_brand
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update brand blueprint: {e}")
        raise HTTPException(status_code=500, detail="Failed to update brand blueprint")


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(brand_id: str = Path(..., description="Brand ID")):
    """Get brand by ID"""
    try:
        brand_data = await brand_storage.get_brand(brand_id)
        
        return BrandResponse(
            brand_id=brand_id,
            status="success",
            message="Brand retrieved successfully",
            data=brand_data
        )
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Brand not found")
    except Exception as e:
        logger.error(f"Failed to get brand {brand_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve brand")


@router.get("/", response_model=BrandListResponse)
async def list_brands():
    """List all brands"""
    try:
        brands = await brand_storage.list_brands(limit=100)
        
        return BrandListResponse(
            brands=brands,
            total=len(brands)
        )
        
    except Exception as e:
        logger.error(f"Failed to list brands: {e}")
        raise HTTPException(status_code=500, detail="Failed to list brands")


@router.delete("/{brand_id}")
async def delete_brand(brand_id: str = Path(..., description="Brand ID")):
    """Delete brand"""
    try:
        success = await brand_storage.storage.delete("brands", brand_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        logger.info(f"Deleted brand {brand_id}")
        
        return {
            "brand_id": brand_id,
            "status": "success",
            "message": "Brand deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete brand {brand_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete brand")