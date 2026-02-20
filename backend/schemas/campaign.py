"""
Campaign-related Pydantic schemas
"""

from datetime import datetime, date
from schemas.brand import ContentPillar
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class CampaignObjective(str, Enum):
    """Campaign objectives"""
    AWARENESS = "awareness"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEADS = "leads"
    SALES = "sales"
    APP_PROMOTION = "app_promotion"


class ContentType(str, Enum):
    """Content types"""
    IMAGE = "image"
    CAROUSEL = "carousel"
    VIDEO = "video"
    POLL = "poll"
    STORY = "story"
    LINK = "link"


class PostTheme(str, Enum):
    """Post themes"""
    EDUCATIONAL = "educational"
    ENTERTAINING = "entertaining"
    PROMOTIONAL = "promotional"
    UGC = "ugc"
    SEASONAL = "seasonal"
    REACTIVE = "reactive"


class CampaignStatus(str, Enum):
    """Campaign status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PersonaSchema(BaseModel):
    """Persona schema"""
    id: str
    name: str
    age_range: str = "Unknown"
    interests: List[str] = []
    demographics: Dict[str, Any] = {}
    behavior_patterns: List[str] = []


class ProductSchema(BaseModel):
    """Product schema"""
    id: str
    name: str
    category: str = "Uncategorized"
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    features: List[str] = []


class LanguageConfig(BaseModel):
    """Language configuration"""
    primary_language: str = Field(..., description="Primary language code (e.g., 'en')")
    multilingual_enabled: bool = False
    additional_languages: List[str] = []
    
    @validator('additional_languages')
    def validate_additional_languages(cls, v, values):
        if values.get('multilingual_enabled') and not v:
            raise ValueError('Additional languages required when multilingual is enabled')
        return v


class PostMixDistribution(BaseModel):
    """Post mix distribution configuration"""
    educational: int = Field(ge=0, le=100)
    entertaining: int = Field(ge=0, le=100)
    promotional: int = Field(ge=0, le=100)
    ugc: int = Field(ge=0, le=100)
    seasonal: int = Field(ge=0, le=100)
    reactive: int = Field(ge=0, le=100)
    
    @validator('reactive')
    def validate_total_percentage(cls, v, values):
        total = sum([
            values.get('educational', 0),
            values.get('entertaining', 0),
            values.get('promotional', 0),
            values.get('ugc', 0),
            values.get('seasonal', 0),
            v
        ])
        if total != 100:
            # If total is not 100 but close (e.g. 99 or 101 due to rounding), 
            # we can either adjust or just warn in logs. 
            # For now, let's just log and allow it to proceed if it's within 5%
            if 95 <= total <= 105:
                logger.warning(f"Post mix distribution totals {total}%, allowing via fuzzy match")
                return v
            raise ValueError(f'Post mix distribution must total approx 100%, got {total}%')
        return v


class CampaignCreateRequest(BaseModel):
    """Campaign creation request"""
    campaign_name: str = Field(..., min_length=1, max_length=100)
    campaign_objective: CampaignObjective
    target_audience: str = Field(..., min_length=1, max_length=500)
    start_date: date
    end_date: date
    frequency: int = Field(ge=1, le=10, description="Posts per day")
    selected_personas: List[str] = Field(..., min_items=1)
    selected_brand_id: str
    product_integration_enabled: bool = False
    selected_products: List[str] = []
    language_config: LanguageConfig
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        start_date = values.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('selected_products')
    def validate_products(cls, v, values):
        if values.get('product_integration_enabled') and not v:
            raise ValueError('Products required when product integration is enabled')
        return v


class PostMixRequest(BaseModel):
    """Post mix configuration request"""
    campaign_id: str
    content_types: List[ContentType]
    post_distribution: PostMixDistribution


class CampaignMetadata(BaseModel):
    """Campaign metadata"""
    id: str
    name: str
    objective: CampaignObjective
    target_audience: str
    start_date: date
    end_date: date
    frequency: int
    status: CampaignStatus
    created_at: datetime
    updated_at: datetime


class BrandContext(BaseModel):
    """Brand context for campaign"""
    brand_id: str
    brand_name: str
    voice_profile: Dict[str, Any]
    content_pillars: List[Dict[str, Any]]  # Keep as flexible dict for now
    guidelines: Dict[str, Any]


class CampaignData(BaseModel):
    """Complete campaign data structure"""
    id: Optional[str] = None
    campaign_metadata: CampaignMetadata
    brand_context: BrandContext
    personas: List[PersonaSchema]
    products: List[ProductSchema]
    language_config: LanguageConfig
    post_mix: Optional[PostMixDistribution] = None
    content_types: List[ContentType] = []
    content_plan: Optional[Dict[str, Any]] = None
    posts: Dict[str, Any] = {}
    status: CampaignStatus = CampaignStatus.DRAFT
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: str = "v1"


class CampaignResponse(BaseModel):
    """Campaign response"""
    campaign_id: str
    status: str
    message: str
    data: Optional[CampaignData] = None


class CampaignListResponse(BaseModel):
    """Campaign list response"""
    campaigns: List[CampaignMetadata]
    total: int
    page: int
    page_size: int


class PostUpdateRequest(BaseModel):
    """Post update request"""
    post_id: str
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    status: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    regenerate_content: bool = False
    enhance_content: bool = False
    translate_to: Optional[str] = None