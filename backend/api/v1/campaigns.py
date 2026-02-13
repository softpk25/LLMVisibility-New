"""
Campaign API endpoints
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path

from schemas.brand import ContentPillar
from schemas.campaign import (
    CampaignCreateRequest,
    CampaignResponse,
    CampaignListResponse,
    CampaignData,
    CampaignMetadata,
    PostMixRequest,
    PostUpdateRequest,
    CampaignStatus
)
from services.storage import campaign_storage, brand_storage, persona_storage, product_storage
from services.llm_orchestrator import orchestrator
from core.logging_config import get_logger
from core.exceptions import NotFoundError, ValidationError

logger = get_logger("campaigns_api")
router = APIRouter()


@router.post("/create", response_model=CampaignResponse)
async def create_campaign(request: CampaignCreateRequest):
    """Create a new campaign"""
    logger.info(f"🚀 Campaign creation request received: {request.campaign_name} for brand {request.selected_brand_id}")
    try:
        # Validate brand exists
        try:
            brand_data = await brand_storage.get_brand(request.selected_brand_id)
            logger.info(f"✅ Found brand: {brand_data.get('brand_name', 'Unnamed')}")
        except NotFoundError:
            logger.error(f"❌ Brand not found: {request.selected_brand_id}")
            raise HTTPException(status_code=404, detail=f"Brand '{request.selected_brand_id}' not found in storage")
        
        # Create campaign metadata
        campaign_id = str(uuid.uuid4())
        now = datetime.utcnow()
        logger.debug(f"📋 Generated campaign ID: {campaign_id}")
        
        campaign_metadata = CampaignMetadata(
            id=campaign_id,
            name=request.campaign_name,
            objective=request.campaign_objective,
            target_audience=request.target_audience,
            start_date=request.start_date,
            end_date=request.end_date,
            frequency=request.frequency,
            status=CampaignStatus.DRAFT,
            created_at=now,
            updated_at=now
        )
        
        # Create brand context
        brand_context = {
            "brand_id": request.selected_brand_id,
            "brand_name": brand_data.get("brand_name", ""),
            "voice_profile": brand_data.get("voice_profile", {}),
            "content_pillars": brand_data.get("content_pillars", []),
            "guidelines": brand_data.get("brand_guidelines", {})
        }
        
        # Fetch personas from storage
        personas = []
        for persona_id in request.selected_personas:
            try:
                persona_data = await persona_storage.get_persona(persona_id)
                personas.append(persona_data)
            except NotFoundError:
                logger.warning(f"Persona {persona_id} not found, using name only")
                personas.append({
                    "id": persona_id, 
                    "name": persona_id,
                    "age_range": "Unknown",
                    "interests": [],
                    "demographics": {},
                    "behavior_patterns": []
                })
        
        # Fetch products from storage
        products = []
        if request.product_integration_enabled:
            for product_id in request.selected_products:
                try:
                    product_data = await product_storage.get_product(product_id)
                    products.append(product_data)
                except NotFoundError:
                    logger.warning(f"Product {product_id} not found, using name only")
                    products.append({
                        "id": product_id, 
                        "name": product_id,
                        "category": "Uncategorized"
                    })
        
        # Create complete campaign data
        campaign_data = CampaignData(
            campaign_metadata=campaign_metadata,
            brand_context=brand_context,
            personas=personas,
            products=products,
            language_config=request.language_config,
            status=CampaignStatus.DRAFT,
            version="v1"
        )
        
        # Save to storage (initial save) and get the true system campaign_id
        campaign_id = await campaign_storage.create_campaign(campaign_data.dict())
        
        # Update metadata ID to match storage ID
        campaign_data.campaign_metadata.id = campaign_id
        
        # Generate initial AI Strategy and Content Plan
        llm_payload = {
            "task_type": "text_generation",
            "prompt": f"""
            Create a high-level social media campaign strategy and content plan.
            
            Campaign Details:
            - Name: {request.campaign_name}
            - Objective: {request.campaign_objective}
            - Target Audience: {request.target_audience}
            - Duration: {request.start_date} to {request.end_date}
            - Post Frequency: {request.frequency} per day
            
            Brand Context:
            - Brand: {brand_context['brand_name']}
            - Voice Profile: {brand_context['voice_profile']}
            - Content Pillars: {brand_context['content_pillars']}
            
            Target Personas:
            {[p['name'] for p in personas]}
            
            Product Context:
            {[p['name'] for p in products]}
            
            Please generate:
            1. A brief strategic summary (2-3 sentences).
            2. Key messaging themes for this specific campaign.
            3. A suggested content distribution strategy.
            
            Format the response as a structured text that can be used to guide content creation.
            """,
            "parameters": {
                "max_tokens": 1000,
                "temperature": 0.7
            },
            "request_id": f"campaign_gen_{campaign_id}"
        }
        
        logger.info(f"Triggering AI strategy generation for campaign {campaign_id}")
        try:
            llm_result = await orchestrator.generate(llm_payload)
        except Exception as e:
            logger.error(f"🚨 Critical failure in orchestrator for campaign {campaign_id}: {str(e)}")
            llm_result = {"success": False, "error": str(e)}
        
        if llm_result.get("success"):
            # Add content plan to campaign data
            content_plan = {
                "generated_plan": llm_result.get("content", ""),
                "generated_at": datetime.utcnow().isoformat(),
                "llm_metadata": llm_result.get("orchestrator_metadata", {})
            }

            # Persist updated campaign to storage
            updates = {
                "content_plan": content_plan,
                "updated_at": datetime.utcnow().isoformat()
            }
            await campaign_storage.update_campaign(campaign_id, updates)

            # Update the CampaignData model directly for the response
            campaign_data.content_plan = content_plan
            
            logger.info(f"✅ Campaign {campaign_id} created successfully with AI strategy")

            return CampaignResponse(
                campaign_id=campaign_id,
                status="success",
                message="Campaign created with AI strategy",
                data=campaign_data
            )
        
        logger.info(f"Created campaign {campaign_id} (without AI strategy due to generation error or skip)")
        
        return CampaignResponse(
            campaign_id=campaign_id,
            status="success",
            message="Campaign created successfully",
            data=campaign_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to create campaign")


@router.post("/post-mix", response_model=CampaignResponse)
async def configure_post_mix(request: PostMixRequest):
    """Configure post type and theme distribution for campaign"""
    try:
        # Get existing campaign
        try:
            campaign_data = await campaign_storage.get_campaign(request.campaign_id)
        except NotFoundError:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Update campaign with post mix configuration
        updates = {
            "post_mix": request.post_distribution.dict(),
            "content_types": [ct.value for ct in request.content_types],
            "updated_at": datetime.utcnow().isoformat()
        }
        
        updated_campaign = await campaign_storage.update_campaign(request.campaign_id, updates)
        
        # Generate LLM payload for content planning
        llm_payload = {
            "task_type": "text_generation",
            "prompt": f"""
            Create a content calendar plan for a {campaign_data['campaign_metadata']['objective']} campaign.
            
            Campaign Details:
            - Name: {campaign_data['campaign_metadata']['name']}
            - Target Audience: {campaign_data['campaign_metadata']['target_audience']}
            - Duration: {campaign_data['campaign_metadata']['start_date']} to {campaign_data['campaign_metadata']['end_date']}
            - Frequency: {campaign_data['campaign_metadata']['frequency']} posts per day
            
            Post Mix Distribution:
            {request.post_distribution.dict()}
            
            Content Types: {[ct.value for ct in request.content_types]}
            
            Brand Context:
            - Brand: {campaign_data['brand_context']['brand_name']}
            - Voice: {campaign_data['brand_context']['voice_profile']}
            
            Generate a structured content plan with post ideas for each theme category.
            """,
            "parameters": {
                "max_tokens": 1500,
                "temperature": 0.7
            },
            "request_id": f"post_mix_{request.campaign_id}"
        }
        
        # Send to LLM orchestrator
        llm_result = await orchestrator.generate(llm_payload)
        
        # Store LLM result in campaign
        if llm_result.get("success"):
            updates["content_plan"] = {
                "generated_plan": llm_result.get("content", ""),
                "generated_at": datetime.utcnow().isoformat(),
                "llm_metadata": llm_result.get("orchestrator_metadata", {})
            }
            updated_campaign = await campaign_storage.update_campaign(request.campaign_id, updates)
        
        logger.info(f"Configured post mix for campaign {request.campaign_id}")
        
        return CampaignResponse(
            campaign_id=request.campaign_id,
            status="success",
            message="Post mix configured successfully",
            data=updated_campaign
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure post mix: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure post mix")


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str = Path(..., description="Campaign ID")):
    """Get campaign by ID"""
    try:
        campaign_data = await campaign_storage.get_campaign(campaign_id)
        
        return CampaignResponse(
            campaign_id=campaign_id,
            status="success",
            message="Campaign retrieved successfully",
            data=campaign_data
        )
        
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Campaign not found")
    except Exception as e:
        logger.error(f"Failed to get campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve campaign")


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    limit: int = Query(50, ge=1, le=100, description="Number of campaigns to return"),
    offset: int = Query(0, ge=0, description="Number of campaigns to skip")
):
    """List campaigns with pagination"""
    try:
        campaigns = await campaign_storage.list_campaigns(limit, offset)
        total = await campaign_storage.storage.count_items("campaigns")
        
        # Convert to metadata objects
        campaign_metadata = []
        for campaign in campaigns:
            metadata = campaign.get("campaign_metadata", {})
            if metadata:
                campaign_metadata.append(CampaignMetadata(**metadata))
        
        return CampaignListResponse(
            campaigns=campaign_metadata,
            total=total,
            page=offset // limit + 1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to list campaigns")


@router.put("/{campaign_id}/post", response_model=CampaignResponse)
async def update_post(
    request: PostUpdateRequest,
    campaign_id: str = Path(..., description="Campaign ID")
):
    """Update post content (used by Post Editor)"""
    try:
        # Get existing campaign
        try:
            campaign_data = await campaign_storage.get_campaign(campaign_id)
        except NotFoundError:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Handle content regeneration if requested
        if request.regenerate_content:
            llm_payload = {
                "task_type": "text_generation",
                "prompt": f"""
                Regenerate social media content for post {request.post_id}.
                
                Campaign Context:
                - Objective: {campaign_data['campaign_metadata']['objective']}
                - Target Audience: {campaign_data['campaign_metadata']['target_audience']}
                - Brand: {campaign_data['brand_context']['brand_name']}
                - Voice: {campaign_data['brand_context']['voice_profile']}
                
                Current Caption: {request.caption or 'None'}
                Current Hashtags: {request.hashtags or []}
                
                Generate improved content that aligns with brand voice and campaign objectives.
                """,
                "parameters": {
                    "max_tokens": 800,
                    "temperature": 0.8
                },
                "request_id": f"post_update_{campaign_id}_{request.post_id}"
            }
            
            llm_result = await orchestrator.generate(llm_payload)
            
            if llm_result.get("success"):
                # Parse LLM response for new content (simplified)
                generated_content = llm_result.get("content", "")
                # In real implementation, parse structured response
                request.caption = generated_content[:500]  # Truncate for example

        # Handle content enhancement if requested
        if request.enhance_content:
            llm_payload = {
                "task_type": "text_generation",
                "prompt": f"""
                Enhance the following social media caption for better engagement and brand alignment.
                Keep it professional yet engaging.
                
                Current Caption: {request.caption or post_data.get('caption', 'None')}
                Brand: {campaign_data['brand_context']['brand_name']}
                """,
                "parameters": {
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                "request_id": f"post_enhance_{campaign_id}_{request.post_id}"
            }
            
            llm_result = await orchestrator.generate(llm_payload)
            if llm_result.get("success"):
                request.caption = llm_result.get("content", "")

        # Handle translation if requested
        if request.translate_to:
            llm_payload = {
                "task_type": "text_generation",
                "prompt": f"""
                Translate the following social media caption to {request.translate_to}.
                Ensure the tone remains consistent.
                
                Caption: {request.caption or post_data.get('caption', 'None')}
                """,
                "parameters": {
                    "max_tokens": 800,
                    "temperature": 0.3
                },
                "request_id": f"post_translate_{campaign_id}_{request.post_id}"
            }
            
            llm_result = await orchestrator.generate(llm_payload)
            if llm_result.get("success"):
                request.caption = llm_result.get("content", "")
        
        # Update post in campaign data
        posts = campaign_data.setdefault("posts", {})
        post_data = posts.setdefault(request.post_id, {})
        
        if request.caption is not None:
            post_data["caption"] = request.caption
        if request.hashtags is not None:
            post_data["hashtags"] = request.hashtags
        if request.status is not None:
            post_data["status"] = request.status
        if request.scheduled_time is not None:
            post_data["scheduled_time"] = request.scheduled_time.isoformat()
        
        post_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Save updated campaign
        updated_campaign = await campaign_storage.update_campaign(campaign_id, campaign_data)
        
        logger.info(f"Updated post {request.post_id} in campaign {campaign_id}")
        
        return CampaignResponse(
            campaign_id=campaign_id,
            status="success",
            message="Post updated successfully",
            data=updated_campaign
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update post: {e}")
        raise HTTPException(status_code=500, detail="Failed to update post")


@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str = Path(..., description="Campaign ID")):
    """Delete campaign"""
    try:
        success = await campaign_storage.delete_campaign(campaign_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        logger.info(f"Deleted campaign {campaign_id}")
        
        return {
            "campaign_id": campaign_id,
            "status": "success",
            "message": "Campaign deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete campaign")