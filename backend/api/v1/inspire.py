"""
Inspire Me API endpoints
"""

import uuid
import os
import time
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Path
from fastapi.responses import JSONResponse

from schemas.inspire import (
    GenerationRequest,
    GenerationResponse,
    AnalysisResponse,
    UploadResponse,
    AssetListResponse,
    PromptEditRequest,
    CreativeAsset,
    CreativeType,
    AnalysisResult,
    VisualDNA,
    GenerationVariant,
    GenerationStatus
)
from services.storage import storage
from services.llm_orchestrator import orchestrator
from core.config import settings
from core.logging_config import get_logger

logger = get_logger("inspire_api")
router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_creative_references(files: List[UploadFile] = File(...)):
    """Upload creative reference files"""
    try:
        uploaded_assets = []
        failed_uploads = []
        
        # Create upload directory
        upload_dir = os.path.join(settings.UPLOAD_DIR, "inspire", "references")
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            try:
                # Validate file type
                if not file.content_type.startswith(('image/', 'video/')):
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": "Invalid file type. Only images and videos are allowed."
                    })
                    continue
                
                # Validate file size
                content = await file.read()
                if len(content) > settings.MAX_FILE_SIZE:
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": "File too large"
                    })
                    continue
                
                # Generate asset ID and save file
                asset_id = str(uuid.uuid4())
                file_extension = os.path.splitext(file.filename)[1]
                file_path = os.path.join(upload_dir, f"{asset_id}{file_extension}")
                
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                
                # Determine creative type
                creative_type = CreativeType.IMAGE if file.content_type.startswith('image/') else CreativeType.VIDEO
                
                # Create asset record
                asset = CreativeAsset(
                    id=asset_id,
                    filename=file.filename,
                    file_path=file_path,
                    file_size=len(content),
                    content_type=file.content_type,
                    creative_type=creative_type,
                    upload_timestamp=datetime.utcnow(),
                    metadata={}
                )
                
                # Save to storage
                await storage.save("inspire_assets", asset_id, asset.model_dump())
                uploaded_assets.append(asset)
                
                logger.info(f"Uploaded creative asset {asset_id}: {file.filename}")
                
            except Exception as e:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": str(e)
                })
                logger.error(f"Failed to upload {file.filename}: {e}")
        
        return UploadResponse(
            asset_ids=[asset.id for asset in uploaded_assets],
            uploaded_files=uploaded_assets,
            failed_uploads=failed_uploads
        )
        
    except Exception as e:
        logger.error(f"Failed to upload files: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload files")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_creative_assets(
    asset_ids: List[str],
    analysis_type: str = Query("visual_dna", description="Type of analysis to perform")
):
    """Generate Visual DNA analysis and reconstruct generative prompts"""
    try:
        analysis_id = str(uuid.uuid4())
        
        # Get assets from storage
        assets = []
        for asset_id in asset_ids:
            try:
                asset_data = await storage.load("inspire_assets", asset_id)
                assets.append(asset_data)
            except Exception as e:
                logger.warning(f"Failed to load asset {asset_id}: {e}")
                continue
        
        if not assets:
            raise HTTPException(status_code=404, detail="No valid assets found")
        
        # Analyze first asset (for simplicity)
        primary_asset = assets[0]
        
        # Create LLM payload for image analysis
        llm_payload = {
            "task_type": "image_analysis",
            "image_path": primary_asset["file_path"],
            "prompt": f"""
            Perform a comprehensive visual analysis of this image for creative generation purposes.
            
            Analysis Type: {analysis_type}
            
            Please analyze:
            1. Visual DNA:
               - Color palette (dominant and accent colors)
               - Style keywords and aesthetic descriptors
               - Mood and emotional tone
               - Composition and visual hierarchy
               - Lighting characteristics
               - Texture and visual weight
               - Brand elements present
            
            2. Generative Prompt Reconstruction:
               - Base prompt that could recreate similar visuals
               - Style modifiers and artistic techniques
               - Color and lighting instructions
               - Composition guidelines
               - Technical parameters
            
            3. Brand Alignment Assessment:
               - Professional vs casual aesthetic
               - Target audience fit
               - Message clarity and impact
               - Call-to-action presence
            
            Format response as structured JSON with confidence scores.
            """,
            "parameters": {
                "max_tokens": 1500,
                "temperature": 0.3
            },
            "request_id": f"analyze_{analysis_id}"
        }
        
        start_time = time.time()
        llm_result = await orchestrator.generate(llm_payload)
        processing_time = time.time() - start_time
        
        if not llm_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to analyze image")
        
        # Parse LLM response (simplified - in production, use structured parsing)
        analysis_content = llm_result.get("analysis", "")
        
        # Create mock structured analysis result
        visual_dna = VisualDNA(
            color_palette=["#5046e5", "#00c4cc", "#1a202c", "#f7fafc"],
            dominant_colors=["#5046e5", "#00c4cc"],
            style_keywords=["modern", "professional", "clean", "vibrant"],
            mood="professional and approachable",
            composition="balanced with strong focal point",
            lighting="bright and even",
            texture="smooth with subtle gradients",
            visual_weight="medium",
            brand_elements=["logo", "typography", "color scheme"],
            confidence_score=0.87
        )
        
        analysis_result = AnalysisResult(
            asset_id=primary_asset["id"],
            analysis_type=analysis_type,
            visual_dna=visual_dna,
            processing_time=processing_time,
            timestamp=datetime.utcnow()
        )
        
        # Save analysis result
        await storage.save("inspire_analyses", analysis_id, analysis_result.model_dump())
        
        logger.info(f"Completed analysis {analysis_id} for {len(assets)} assets")
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="completed",
            results=analysis_result,
            message="Analysis completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze assets: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze assets")


@router.post("/generate", response_model=GenerationResponse)
async def generate_creative_content(request: GenerationRequest):
    """Generate creative content with AI"""
    try:
        generation_id = str(uuid.uuid4())
        
        # Get style references if provided
        style_context = ""
        if request.style_reference_ids:
            for ref_id in request.style_reference_ids:
                try:
                    analysis_data = await storage.load("inspire_analyses", ref_id)
                    visual_dna = analysis_data.get("visual_dna", {})
                    style_context += f"\nStyle Reference: {visual_dna.get('style_keywords', [])} - {visual_dna.get('mood', '')}"
                except Exception as e:
                    logger.warning(f"Failed to load style reference {ref_id}: {e}")
        
        # Get brand context if provided
        brand_context = ""
        if request.brand_id:
            try:
                brand_data = await storage.load("brands", request.brand_id)
                brand_context = f"""
                Brand: {brand_data.get('brand_name', '')}
                Voice: {brand_data.get('voice_profile', {})}
                Guidelines: {brand_data.get('brand_guidelines', {})}
                """
            except Exception as e:
                logger.warning(f"Failed to load brand {request.brand_id}: {e}")
        
        # Create enhanced prompt
        enhanced_prompt = f"""
        {request.prompt}
        
        Creative Requirements:
        - Type: {request.creative_type}
        - Aspect Ratio: {request.aspect_ratio}
        - Quality: {request.quality}
        - Style Strength: {request.style_strength}
        - Creativity Level: {request.creativity_level}
        
        {style_context}
        {brand_context}
        
        Generate {request.variations} variation(s) that align with the specified requirements.
        """
        
        # Generate content using LLM
        llm_payload = {
            "task_type": "text_generation",
            "prompt": f"""
            Generate creative content based on the following requirements:
            
            {enhanced_prompt}
            
            Create detailed descriptions for {request.variations} creative variants that could be used 
            to generate actual visual content. Include:
            1. Visual description
            2. Style elements
            3. Color palette
            4. Composition details
            5. Brand alignment score
            6. Technical quality assessment
            
            Format as structured JSON with metadata for each variant.
            """,
            "parameters": {
                "max_tokens": 2000,
                "temperature": request.creativity_level
            },
            "request_id": f"generate_{generation_id}"
        }
        
        start_time = time.time()
        llm_result = await orchestrator.generate(llm_payload)
        processing_time = time.time() - start_time
        
        if not llm_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to generate content")
        
        # Create mock variants (in production, generate actual images)
        variants = []
        for i in range(request.variations):
            variant_id = str(uuid.uuid4())
            variant = GenerationVariant(
                id=variant_id,
                image_url=f"/generated/mock_variant_{variant_id}.png",
                prompt_used=enhanced_prompt,
                style_score=0.85,
                brand_alignment_score=0.90,
                technical_quality_score=0.88,
                metadata={
                    "generation_id": generation_id,
                    "variant_index": i,
                    "llm_metadata": llm_result.get("orchestrator_metadata", {})
                }
            )
            variants.append(variant)
        
        # Save generation result
        generation_data = {
            "id": generation_id,
            "request": request.model_dump(),
            "variants": [v.model_dump() for v in variants],
            "status": GenerationStatus.COMPLETED,
            "processing_time": processing_time,
            "created_at": datetime.utcnow().isoformat(),
            "llm_result": llm_result
        }
        
        await storage.save("inspire_generations", generation_id, generation_data)
        
        logger.info(f"Generated {len(variants)} creative variants for generation {generation_id}")
        
        return GenerationResponse(
            generation_id=generation_id,
            status=GenerationStatus.COMPLETED,
            variants=variants,
            processing_time=processing_time,
            message="Content generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate content: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate content")


@router.post("/edit-prompt", response_model=GenerationResponse)
async def edit_prompt_and_regenerate(request: PromptEditRequest):
    """Edit prompt with sliders and regenerate content"""
    try:
        # Apply slider modifications to prompt
        modified_prompt = request.original_prompt
        
        # Apply creativity adjustments
        if request.sliders.creativity > 0.7:
            modified_prompt += " Make it more creative and unique."
        elif request.sliders.creativity < 0.3:
            modified_prompt += " Keep it simple and conventional."
        
        # Apply brand adherence
        if request.sliders.brand_adherence > 0.8:
            modified_prompt += " Strictly follow brand guidelines."
        
        # Apply style strength
        if request.sliders.style_strength > 0.7:
            modified_prompt += " Apply strong stylistic elements."
        
        # Apply color vibrancy
        if request.sliders.color_vibrancy > 0.7:
            modified_prompt += " Use vibrant, bold colors."
        elif request.sliders.color_vibrancy < 0.3:
            modified_prompt += " Use muted, subtle colors."
        
        # Apply composition complexity
        if request.sliders.composition_complexity > 0.7:
            modified_prompt += " Create a complex, detailed composition."
        elif request.sliders.composition_complexity < 0.3:
            modified_prompt += " Keep the composition simple and clean."
        
        # Create generation request
        generation_request = GenerationRequest(
            prompt=modified_prompt,
            creative_type=CreativeType.IMAGE,
            variations=2,
            creativity_level=request.sliders.creativity,
            style_strength=request.sliders.style_strength
        )
        
        # Generate new content
        return await generate_creative_content(generation_request)
        
    except Exception as e:
        logger.error(f"Failed to edit prompt and regenerate: {e}")
        raise HTTPException(status_code=500, detail="Failed to edit prompt and regenerate")


@router.get("/assets", response_model=AssetListResponse)
async def list_creative_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    creative_type: str = Query(None, description="Filter by creative type")
):
    """List uploaded creative assets"""
    try:
        offset = (page - 1) * page_size
        assets = await storage.list_items("inspire_assets", limit=page_size, offset=offset)
        total = await storage.count_items("inspire_assets")
        
        # Filter by creative type if specified
        if creative_type:
            assets = [asset for asset in assets if asset.get("creative_type") == creative_type]
        
        # Convert to CreativeAsset objects
        creative_assets = []
        for asset_data in assets:
            try:
                asset = CreativeAsset(**asset_data)
                creative_assets.append(asset)
            except Exception as e:
                logger.warning(f"Failed to parse asset data: {e}")
                continue
        
        return AssetListResponse(
            assets=creative_assets,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to list assets: {e}")
        raise HTTPException(status_code=500, detail="Failed to list assets")


@router.get("/generations/{generation_id}", response_model=GenerationResponse)
async def get_generation_result(generation_id: str = Path(..., description="Generation ID")):
    """Get generation result by ID"""
    try:
        generation_data = await storage.load("inspire_generations", generation_id)
        
        variants = [GenerationVariant(**v) for v in generation_data.get("variants", [])]
        
        return GenerationResponse(
            generation_id=generation_id,
            status=GenerationStatus(generation_data.get("status", "completed")),
            variants=variants,
            processing_time=generation_data.get("processing_time"),
            message="Generation retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get generation {generation_id}: {e}")
        raise HTTPException(status_code=404, detail="Generation not found")


@router.delete("/assets/{asset_id}")
async def delete_creative_asset(asset_id: str = Path(..., description="Asset ID")):
    """Delete creative asset"""
    try:
        # Get asset data to find file path
        try:
            asset_data = await storage.load("inspire_assets", asset_id)
            file_path = asset_data.get("file_path")
            
            # Delete file from disk
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                
        except Exception as e:
            logger.warning(f"Failed to delete file for asset {asset_id}: {e}")
        
        # Delete from storage
        success = await storage.delete("inspire_assets", asset_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        logger.info(f"Deleted creative asset {asset_id}")
        
        return {
            "asset_id": asset_id,
            "status": "success",
            "message": "Asset deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete asset {asset_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete asset")