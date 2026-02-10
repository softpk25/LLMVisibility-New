"""
Standalone Brand Blueprint Data Models
Contains all SQLAlchemy and Pydantic models for the brand blueprint feature.
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import Base from your database module
from STANDALONE_DATABASE import Base


# ============================================================================
# SQLAlchemy Models (Database Entities)
# ============================================================================

class BrandBlueprint(Base):
    """Stores brand blueprint configuration"""
    __tablename__ = "brand_blueprints"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand_id = Column(String, index=True, default="brand-001")
    brand_name = Column(String, default="My Brand")
    version = Column(String, default="1.0.0")
    status = Column(String, default="draft")  # draft, generated, approved
    
    # Voice Profile
    voice_formality = Column(Integer, default=50)
    voice_humor = Column(Integer, default=50)
    voice_warmth = Column(Integer, default=50)
    emoji_policy = Column(String, default="medium")
    
    # Content Pillars (stored as JSON)
    pillars = Column(JSON, default=list)
    
    # Policies
    forbidden_phrases = Column(JSON, default=list)
    max_hashtags = Column(Integer, default=5)
    brand_hashtags = Column(JSON, default=list)
    product_default_pct = Column(Integer, default=30)
    
    # Guideline document info
    guideline_doc_name = Column(String, nullable=True)
    guideline_doc_status = Column(String, default="none")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


# ============================================================================
# Pydantic Models for API (Request/Response Schemas)
# ============================================================================

class VoiceProfile(BaseModel):
    """Voice profile settings"""
    formality: int = 50
    humor: int = 50
    warmth: int = 50
    emojiPolicy: str = "medium"


class ContentPillar(BaseModel):
    """Content pillar definition"""
    name: str
    description: str = ""
    weight: int = 25


class Policies(BaseModel):
    """Brand policies and guidelines"""
    forbiddenPhrases: List[str] = []
    maxHashtags: int = 5
    brandHashtags: List[str] = []


class BlueprintData(BaseModel):
    """Complete blueprint data structure"""
    version: str = "1.0.0"
    status: str = "draft"
    voice: VoiceProfile = Field(default_factory=VoiceProfile)
    pillars: List[ContentPillar] = []
    policies: Policies = Field(default_factory=Policies)
    productDefaultPct: int = 30


class BrandBlueprintRequest(BaseModel):
    """Request model for creating/updating brand blueprint"""
    brandId: str = "brand-001"
    brandName: str = "My Brand"
    blueprint: BlueprintData


class BrandBlueprintResponse(BaseModel):
    """Response model for brand blueprint"""
    id: int
    brandId: str
    brandName: str
    blueprint: BlueprintData
    guidelineDoc: Dict[str, Any] = {"name": "", "status": "none"}
    
    class Config:
        from_attributes = True


# ============================================================================
# Additional Models (if needed for extended functionality)
# ============================================================================

class BrandData(BaseModel):
    """Extracted brand data from PDF processing"""
    brandName: str
    industry: str = ""
    targetAudience: str = ""
    pillars: List[ContentPillar] = []
    forbiddenPhrases: List[str] = []
    brandHashtags: List[str] = []
    voice: VoiceProfile = Field(default_factory=VoiceProfile)


class UploadResponse(BaseModel):
    """Response model for file upload"""
    status: str
    message: str
    brandData: Optional[BrandData] = None
    blueprint: Optional[Dict[str, Any]] = None
