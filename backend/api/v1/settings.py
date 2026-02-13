"""
Settings API endpoints using SQLite backend
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlite3 import Connection

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
    IntegrationStatus,
    EmojiPolicy,
    SectorPreset,
    LanguageCode
)
from core.db import get_db_connection
from core.logging_config import get_logger

logger = get_logger("settings_api")
router = APIRouter()

# Helper to get DB connection
def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# ── Settings (Global/Brand-specific) ──────────────────────────────────

async def _get_global_settings(conn: Connection, brand_id: str, settings_type: str) -> Optional[Dict[str, Any]]:
    cursor = conn.execute(
        "SELECT config_json FROM global_settings WHERE brand_id = ? AND type = ?",
        (brand_id, settings_type)
    )
    row = cursor.fetchone()
    if row:
        return json.loads(row["config_json"])
    return None

async def _save_global_settings(conn: Connection, brand_id: str, settings_type: str, config: Dict[str, Any]):
    now = datetime.utcnow().isoformat()
    config_json = json.dumps(config)
    conn.execute(
        """
        INSERT INTO global_settings (brand_id, type, config_json, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(brand_id, type) DO UPDATE SET
            config_json = excluded.config_json,
            updated_at = excluded.updated_at
        """,
        (brand_id, settings_type, config_json, now)
    )
    conn.commit()

@router.get("/{brand_id}", response_model=Dict[str, Any])
async def get_all_settings(brand_id: str, conn: Connection = Depends(get_db)):
    """Get all settings for a brand"""
    try:
        cursor = conn.execute("SELECT type, config_json FROM global_settings WHERE brand_id = ?", (brand_id,))
        rows = cursor.fetchall()
        settings = {row["type"]: json.loads(row["config_json"]) for row in rows}
        return settings
    except Exception as e:
        logger.error(f"Failed to get settings for {brand_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get settings")

@router.put("/{brand_id}")
async def update_all_settings(brand_id: str, settings: Dict[str, Any], conn: Connection = Depends(get_db)):
    """Update multiple settings types for a brand"""
    try:
        for settings_type, config in settings.items():
            await _save_global_settings(conn, brand_id, settings_type, config)
        return {"status": "success", "message": "Settings updated"}
    except Exception as e:
        logger.error(f"Failed to update settings for {brand_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")

# Compatibility endpoints (default to brand-001)
@router.get("/language", response_model=LanguageSettingsResponse)
async def get_language_settings(conn: Connection = Depends(get_db)):
    data = await _get_global_settings(conn, "brand-001", "language")
    if not data:
        return LanguageSettingsResponse(settings=LanguageSettings())
    return LanguageSettingsResponse(settings=LanguageSettings(**data))

@router.put("/language", response_model=LanguageSettingsResponse)
async def update_language_settings(settings: LanguageSettings, conn: Connection = Depends(get_db)):
    await _save_global_settings(conn, "brand-001", "language", settings.dict())
    return LanguageSettingsResponse(settings=settings)

@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings(conn: Connection = Depends(get_db)):
    data = await _get_global_settings(conn, "brand-001", "llm")
    if not data:
        # Default LLM settings
        return LLMSettingsResponse(settings=LLMSettings(
            primary_provider="openai",
            monthly_budget_limit=100.0,
            models={"text_generation": "gpt-4"}
        ))
    return LLMSettingsResponse(settings=LLMSettings(**data))

@router.put("/llm", response_model=LLMSettingsResponse)
async def update_llm_settings(settings: LLMSettings, conn: Connection = Depends(get_db)):
    await _save_global_settings(conn, "brand-001", "llm", settings.dict())
    return LLMSettingsResponse(settings=settings)

@router.get("/guardrails", response_model=GuardrailSettingsResponse)
async def get_guardrail_settings(conn: Connection = Depends(get_db)):
    data = await _get_global_settings(conn, "brand-001", "guardrails")
    if not data:
        return GuardrailSettingsResponse(settings=GuardrailSettings())
    return GuardrailSettingsResponse(settings=GuardrailSettings(**data))

@router.put("/guardrails", response_model=GuardrailSettingsResponse)
async def update_guardrail_settings(settings: GuardrailSettings, conn: Connection = Depends(get_db)):
    await _save_global_settings(conn, "brand-001", "guardrails", settings.dict())
    return GuardrailSettingsResponse(settings=settings)

# ── Personas ──────────────────────────────────────────────────────────

@router.get("/personas/{brand_id}", response_model=PersonaListResponse)
async def list_personas(
    brand_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    conn: Connection = Depends(get_db)
):
    """List personas for a brand"""
    try:
        cursor = conn.execute(
            "SELECT data_json FROM personas WHERE brand_id = ? LIMIT ? OFFSET ?",
            (brand_id, limit, offset)
        )
        rows = cursor.fetchall()
        personas = [PersonaData(**json.loads(row["data_json"])) for row in rows]
        
        count_cursor = conn.execute("SELECT COUNT(*) FROM personas WHERE brand_id = ?", (brand_id,))
        total = count_cursor.fetchone()[0]
        
        return PersonaListResponse(personas=personas, total=total)
    except Exception as e:
        logger.error(f"Failed to list personas: {e}")
        raise HTTPException(status_code=500, detail="Failed to list personas")

@router.post("/personas/{brand_id}", response_model=PersonaData)
async def create_persona(brand_id: str, request: PersonaCreateRequest, conn: Connection = Depends(get_db)):
    """Create new persona for a brand"""
    try:
        persona_id = str(uuid.uuid4())
        persona_data = PersonaData(
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
        
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO personas (id, brand_id, data_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (persona_id, brand_id, json.dumps(persona_data.dict()), now, now)
        )
        conn.commit()
        return persona_data
    except Exception as e:
        logger.error(f"Failed to create persona: {e}")
        raise HTTPException(status_code=500, detail="Failed to create persona")

@router.get("/persona/{persona_id}", response_model=PersonaData)
async def get_persona(persona_id: str, conn: Connection = Depends(get_db)):
    """Get persona by ID"""
    cursor = conn.execute("SELECT data_json FROM personas WHERE id = ?", (persona_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Persona not found")
    return PersonaData(**json.loads(row["data_json"]))

@router.put("/persona/{persona_id}", response_model=PersonaData)
async def update_persona(persona_id: str, request: PersonaCreateRequest, conn: Connection = Depends(get_db)):
    """Update persona"""
    try:
        cursor = conn.execute("SELECT brand_id, created_at FROM personas WHERE id = ?", (persona_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        brand_id = row["brand_id"]
        created_at = row["created_at"]
        
        persona_data = PersonaData(
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
        
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE personas SET data_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(persona_data.dict()), now, persona_id)
        )
        conn.commit()
        return persona_data
    except Exception as e:
        logger.error(f"Failed to update persona {persona_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update persona")

@router.delete("/persona/{persona_id}")
async def delete_persona(persona_id: str, conn: Connection = Depends(get_db)):
    """Delete persona"""
    cursor = conn.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Persona not found")
    conn.commit()
    return {"status": "success", "message": "Persona deleted"}

# ── Products ──────────────────────────────────────────────────────────

@router.get("/products/{brand_id}", response_model=ProductListResponse)
async def list_products(
    brand_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
    conn: Connection = Depends(get_db)
):
    """List products for a brand"""
    try:
        query = "SELECT data_json FROM products WHERE brand_id = ?"
        params = [brand_id]
        
        cursor = conn.execute(f"{query} LIMIT ? OFFSET ?", (*params, limit, offset))
        rows = cursor.fetchall()
        products = [ProductData(**json.loads(row["data_json"])) for row in rows]
        
        if category:
            products = [p for p in products if p.category == category]
            
        count_cursor = conn.execute("SELECT COUNT(*) FROM products WHERE brand_id = ?", (brand_id,))
        total = count_cursor.fetchone()[0]
        
        return ProductListResponse(products=products, total=total)
    except Exception as e:
        logger.error(f"Failed to list products: {e}")
        raise HTTPException(status_code=500, detail="Failed to list products")

@router.post("/products/{brand_id}", response_model=ProductData)
async def create_product(brand_id: str, request: ProductCreateRequest, conn: Connection = Depends(get_db)):
    """Create new product for a brand"""
    try:
        product_id = str(uuid.uuid4())
        product_data = ProductData(
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
        
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO products (id, brand_id, data_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (product_id, brand_id, json.dumps(product_data.dict()), now, now)
        )
        conn.commit()
        return product_data
    except Exception as e:
        logger.error(f"Failed to create product: {e}")
        raise HTTPException(status_code=500, detail="Failed to create product")

@router.get("/product/{product_id}", response_model=ProductData)
async def get_product(product_id: str, conn: Connection = Depends(get_db)):
    """Get product by ID"""
    cursor = conn.execute("SELECT data_json FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductData(**json.loads(row["data_json"]))

@router.put("/product/{product_id}", response_model=ProductData)
async def update_product(product_id: str, request: ProductCreateRequest, conn: Connection = Depends(get_db)):
    """Update product"""
    try:
        cursor = conn.execute("SELECT brand_id, created_at FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        
        brand_id = row["brand_id"]
        created_at = row["created_at"]
        
        product_data = ProductData(
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
        
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE products SET data_json = ?, updated_at = ? WHERE id = ?",
            (json.dumps(product_data.dict()), now, product_id)
        )
        conn.commit()
        return product_data
    except Exception as e:
        logger.error(f"Failed to update product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update product")

@router.delete("/product/{product_id}")
async def delete_product(product_id: str, conn: Connection = Depends(get_db)):
    """Delete product"""
    cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    conn.commit()
    return {"status": "success", "message": "Product deleted"}



