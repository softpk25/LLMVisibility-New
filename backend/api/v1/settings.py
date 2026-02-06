"""
Settings API endpoints
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path

from schemas.settings import (
    LanguageSettings,
    LLMSettings,
    GuardrailSettings,
    ContentSettings,
    SectorSettings,
    IntegrationConfig,
    PersonaData,
    ProductData,
    LanguageSettingsResponse,
    LLMSettingsResponse,
    GuardrailSettingsResponse,
    IntegrationListResponse,
    PersonaListResponse,
    ProductListResponse,
    PersonaCreateRequest,
    ProductCreateRequest,
    SettingsResponse,
    IntegrationStatus
)
from services.storage import settings_storage, storage
from core.logging_config import get_logger

logger = get_logger("settings_api")
router = APIRouter()


# Language Settings
@router.get("/language", response_model=LanguageSettingsResponse)
async def get_language_settings():
    """Get language settings"""
    try:
        settings_data = await settings_storage.get_settings("language")
        language_settings = LanguageSettings(**settings_data)
        
        return LanguageSettingsResponse(settings=language_settings)
        
    except Exception as e:
        logger.error(f"Failed to get language settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get language settings")


@router.put("/language", response_model=LanguageSettingsResponse)
async def update_language_settings(settings: LanguageSettings):
    """Update language settings"""
    try:
        settings_data = settings.dict()
        await settings_storage.update_settings("language", settings_data)
        
        logger.info("Updated language settings")
        
        return LanguageSettingsResponse(settings=settings)
        
    except Exception as e:
        logger.error(f"Failed to update language settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update language settings")


# LLM Settings
@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings():
    """Get LLM provider settings"""
    try:
        settings_data = await settings_storage.get_settings("llm")
        llm_settings = LLMSettings(**settings_data)
        
        return LLMSettingsResponse(settings=llm_settings)
        
    except Exception as e:
        logger.error(f"Failed to get LLM settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get LLM settings")


@router.put("/llm", response_model=LLMSettingsResponse)
async def update_llm_settings(settings: LLMSettings):
    """Update LLM provider settings"""
    try:
        settings_data = settings.dict()
        await settings_storage.update_settings("llm", settings_data)
        
        logger.info(f"Updated LLM settings - Primary provider: {settings.primary_provider}")
        
        return LLMSettingsResponse(settings=settings)
        
    except Exception as e:
        logger.error(f"Failed to update LLM settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update LLM settings")


# Guardrail Settings
@router.get("/guardrails", response_model=GuardrailSettingsResponse)
async def get_guardrail_settings():
    """Get content guardrail settings"""
    try:
        settings_data = await settings_storage.get_settings("guardrails")
        guardrail_settings = GuardrailSettings(**settings_data)
        
        return GuardrailSettingsResponse(settings=guardrail_settings)
        
    except Exception as e:
        logger.error(f"Failed to get guardrail settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get guardrail settings")


@router.put("/guardrails", response_model=GuardrailSettingsResponse)
async def update_guardrail_settings(settings: GuardrailSettings):
    """Update content guardrail settings"""
    try:
        settings_data = settings.dict()
        await settings_storage.update_settings("guardrails", settings_data)
        
        logger.info("Updated guardrail settings")
        
        return GuardrailSettingsResponse(settings=settings)
        
    except Exception as e:
        logger.error(f"Failed to update guardrail settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update guardrail settings")


# Content Settings
@router.get("/content", response_model=ContentSettings)
async def get_content_settings():
    """Get content generation settings"""
    try:
        settings_data = await settings_storage.get_settings("content")
        content_settings = ContentSettings(**settings_data)
        
        return content_settings
        
    except Exception as e:
        logger.error(f"Failed to get content settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content settings")


@router.put("/content", response_model=ContentSettings)
async def update_content_settings(settings: ContentSettings):
    """Update content generation settings"""
    try:
        settings_data = settings.dict()
        await settings_storage.update_settings("content", settings_data)
        
        logger.info("Updated content settings")
        
        return settings
        
    except Exception as e:
        logger.error(f"Failed to update content settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update content settings")


# Sector Settings
@router.get("/sector", response_model=SectorSettings)
async def get_sector_settings():
    """Get industry sector settings"""
    try:
        settings_data = await settings_storage.get_settings("sector")
        
        if not settings_data:
            # Return default sector settings
            return SectorSettings(
                sector="technology",
                compliance_rules=[],
                industry_keywords=[],
                restricted_topics=[],
                preferred_content_types=[]
            )
        
        sector_settings = SectorSettings(**settings_data)
        return sector_settings
        
    except Exception as e:
        logger.error(f"Failed to get sector settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sector settings")


@router.put("/sector", response_model=SectorSettings)
async def update_sector_settings(settings: SectorSettings):
    """Update industry sector settings"""
    try:
        settings_data = settings.dict()
        await settings_storage.update_settings("sector", settings_data)
        
        logger.info(f"Updated sector settings - Sector: {settings.sector}")
        
        return settings
        
    except Exception as e:
        logger.error(f"Failed to update sector settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update sector settings")


# Integration Settings
@router.get("/integrations", response_model=IntegrationListResponse)
async def get_integrations():
    """Get platform integrations"""
    try:
        integrations_data = await settings_storage.get_settings("integrations")
        
        # Convert to IntegrationConfig objects
        integrations = []
        for platform, config in integrations_data.items():
            integration = IntegrationConfig(
                platform=platform,
                status=IntegrationStatus(config.get("status", "disconnected")),
                credentials=config.get("credentials", {}),
                settings=config.get("settings", {}),
                last_sync=config.get("last_sync"),
                error_message=config.get("error_message")
            )
            integrations.append(integration)
        
        return IntegrationListResponse(integrations=integrations)
        
    except Exception as e:
        logger.error(f"Failed to get integrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integrations")


@router.put("/integrations/{platform}", response_model=IntegrationConfig)
async def update_integration(platform: str, config: IntegrationConfig):
    """Update platform integration configuration"""
    try:
        # Get current integrations
        integrations_data = await settings_storage.get_settings("integrations")
        
        # Update specific platform
        integrations_data[platform] = config.dict()
        
        # Save updated integrations
        await settings_storage.update_settings("integrations", integrations_data)
        
        logger.info(f"Updated integration for platform: {platform}")
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to update integration: {e}")
        raise HTTPException(status_code=500, detail="Failed to update integration")


# Persona Management
@router.get("/personas", response_model=PersonaListResponse)
async def list_personas(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List personas"""
    try:
        personas_data = await storage.list_items("personas", limit=limit, offset=offset)
        total = await storage.count_items("personas")
        
        # Convert to PersonaData objects
        personas = []
        for persona_data in personas_data:
            try:
                persona = PersonaData(**persona_data)
                personas.append(persona)
            except Exception as e:
                logger.warning(f"Failed to parse persona data: {e}")
                continue
        
        return PersonaListResponse(
            personas=personas,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to list personas: {e}")
        raise HTTPException(status_code=500, detail="Failed to list personas")


@router.post("/personas", response_model=PersonaData)
async def create_persona(request: PersonaCreateRequest):
    """Create new persona"""
    try:
        persona_id = str(uuid.uuid4())
        
        persona = PersonaData(
            id=persona_id,
            name=request.name,
            age_range=request.age_range,
            gender=request.gender,
            location=request.location,
            interests=request.interests,
            behaviors=request.behaviors,
            pain_points=request.pain_points,
            preferred_content=request.preferred_content,
            social_platforms=request.social_platforms
        )
        
        # Save persona
        await storage.save("personas", persona_id, persona.dict())
        
        logger.info(f"Created persona {persona_id}: {request.name}")
        
        return persona
        
    except Exception as e:
        logger.error(f"Failed to create persona: {e}")
        raise HTTPException(status_code=500, detail="Failed to create persona")


@router.get("/personas/{persona_id}", response_model=PersonaData)
async def get_persona(persona_id: str = Path(..., description="Persona ID")):
    """Get persona by ID"""
    try:
        persona_data = await storage.load("personas", persona_id)
        persona = PersonaData(**persona_data)
        
        return persona
        
    except Exception as e:
        logger.error(f"Failed to get persona {persona_id}: {e}")
        raise HTTPException(status_code=404, detail="Persona not found")


@router.put("/personas/{persona_id}", response_model=PersonaData)
async def update_persona(persona_id: str, request: PersonaCreateRequest):
    """Update persona"""
    try:
        # Get existing persona
        existing_persona = await storage.load("personas", persona_id)
        
        # Update with new data
        updated_persona = PersonaData(
            id=persona_id,
            name=request.name,
            age_range=request.age_range,
            gender=request.gender,
            location=request.location,
            interests=request.interests,
            behaviors=request.behaviors,
            pain_points=request.pain_points,
            preferred_content=request.preferred_content,
            social_platforms=request.social_platforms
        )
        
        # Save updated persona
        await storage.save("personas", persona_id, updated_persona.dict())
        
        logger.info(f"Updated persona {persona_id}")
        
        return updated_persona
        
    except Exception as e:
        logger.error(f"Failed to update persona {persona_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update persona")


@router.delete("/personas/{persona_id}")
async def delete_persona(persona_id: str = Path(..., description="Persona ID")):
    """Delete persona"""
    try:
        success = await storage.delete("personas", persona_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        logger.info(f"Deleted persona {persona_id}")
        
        return {
            "persona_id": persona_id,
            "status": "success",
            "message": "Persona deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete persona {persona_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete persona")


# Product Management
@router.get("/products", response_model=ProductListResponse)
async def list_products(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None, description="Filter by category")
):
    """List products"""
    try:
        products_data = await storage.list_items("products", limit=limit, offset=offset)
        total = await storage.count_items("products")
        
        # Apply category filter
        if category:
            products_data = [p for p in products_data if p.get("category") == category]
        
        # Convert to ProductData objects
        products = []
        for product_data in products_data:
            try:
                product = ProductData(**product_data)
                products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse product data: {e}")
                continue
        
        return ProductListResponse(
            products=products,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(status_code=500, detail="Failed to list products")


@router.post("/products", response_model=ProductData)
async def create_product(request: ProductCreateRequest):
    """Create new product"""
    try:
        product_id = str(uuid.uuid4())
        
        product = ProductData(
            id=product_id,
            name=request.name,
            category=request.category,
            price=request.price,
            currency=request.currency,
            description=request.description,
            features=request.features,
            benefits=request.benefits,
            target_audience=request.target_audience,
            image_urls=request.image_urls,
            availability=request.availability
        )
        
        # Save product
        await storage.save("products", product_id, product.dict())
        
        logger.info(f"Created product {product_id}: {request.name}")
        
        return product
        
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(status_code=500, detail="Failed to create product")


@router.get("/products/{product_id}", response_model=ProductData)
async def get_product(product_id: str = Path(..., description="Product ID")):
    """Get product by ID"""
    try:
        product_data = await storage.load("products", product_id)
        product = ProductData(**product_data)
        
        return product
        
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {e}")
        raise HTTPException(status_code=404, detail="Product not found")


@router.put("/products/{product_id}", response_model=ProductData)
async def update_product(product_id: str, request: ProductCreateRequest):
    """Update product"""
    try:
        # Get existing product
        existing_product = await storage.load("products", product_id)
        
        # Update with new data
        updated_product = ProductData(
            id=product_id,
            name=request.name,
            category=request.category,
            price=request.price,
            currency=request.currency,
            description=request.description,
            features=request.features,
            benefits=request.benefits,
            target_audience=request.target_audience,
            image_urls=request.image_urls,
            availability=request.availability
        )
        
        # Save updated product
        await storage.save("products", product_id, updated_product.dict())
        
        logger.info(f"Updated product {product_id}")
        
        return updated_product
        
    except Exception as e:
        logger.error(f"Failed to update product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update product")


@router.delete("/products/{product_id}")
async def delete_product(product_id: str = Path(..., description="Product ID")):
    """Delete product"""
    try:
        success = await storage.delete("products", product_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
        
        logger.info(f"Deleted product {product_id}")
        
        return {
            "product_id": product_id,
            "status": "success",
            "message": "Product deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete product")