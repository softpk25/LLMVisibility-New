"""
Brand-related Pydantic schemas
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class VoiceFormality(str, Enum):
    """Voice formality levels"""
    VERY_FORMAL = "very_formal"
    FORMAL = "formal"
    NEUTRAL = "neutral"
    CASUAL = "casual"
    VERY_CASUAL = "very_casual"


class VoiceHumor(str, Enum):
    """Voice humor levels"""
    NONE = "none"
    SUBTLE = "subtle"
    MODERATE = "moderate"
    PLAYFUL = "playful"
    VERY_PLAYFUL = "very_playful"


class VoiceTone(str, Enum):
    """Voice tone options"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    EMPATHETIC = "empathetic"
    ENTHUSIASTIC = "enthusiastic"
    CONVERSATIONAL = "conversational"


class ContentPillarType(str, Enum):
    """Content pillar types"""
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    PROMOTIONAL = "promotional"
    ENTERTAINMENT = "entertainment"
    COMMUNITY = "community"
    BEHIND_SCENES = "behind_scenes"


class BrandStatus(str, Enum):
    """Brand registration status"""
    DRAFT = "draft"
    PROCESSING = "processing"
    ACTIVE = "active"
    INACTIVE = "inactive"


class VoiceProfile(BaseModel):
    """Brand voice profile configuration"""
    formality: VoiceFormality = VoiceFormality.NEUTRAL
    humor: VoiceHumor = VoiceHumor.SUBTLE
    tone: VoiceTone = VoiceTone.FRIENDLY
    personality_traits: List[str] = []
    do_phrases: List[str] = []
    dont_phrases: List[str] = []
    
    @validator('personality_traits')
    def validate_personality_traits(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 personality traits allowed')
        return v


class ContentPillar(BaseModel):
    """Content pillar definition"""
    id: str
    name: str
    type: ContentPillarType
    description: str
    keywords: List[str] = []
    percentage: int = Field(ge=0, le=100, description="Percentage of content for this pillar")


class BrandGuidelines(BaseModel):
    """Brand guidelines"""
    logo_usage: Dict[str, Any] = {}
    color_palette: List[str] = []
    typography: Dict[str, str] = {}
    imagery_style: Dict[str, Any] = {}
    messaging_guidelines: Dict[str, Any] = {}
    compliance_rules: List[str] = []


class BrandRegisterRequest(BaseModel):
    """Brand registration request"""
    brand_name: str = Field(..., min_length=1, max_length=100)
    industry: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=10, max_length=1000)
    website_url: Optional[str] = None
    voice_profile: VoiceProfile
    content_pillars: List[ContentPillar]
    target_demographics: Dict[str, Any] = {}
    brand_values: List[str] = []
    
    @validator('content_pillars')
    def validate_content_pillars(cls, v):
        if not v:
            raise ValueError('At least one content pillar is required')
        
        total_percentage = sum(pillar.percentage for pillar in v)
        if total_percentage != 100:
            raise ValueError(f'Content pillar percentages must total 100%, got {total_percentage}%')
        
        return v


class BrandBlueprintUpdate(BaseModel):
    """Brand blueprint update request"""
    voice_profile: Optional[VoiceProfile] = None
    content_pillars: Optional[List[ContentPillar]] = None
    brand_guidelines: Optional[BrandGuidelines] = None
    brand_values: Optional[List[str]] = None
    
    @validator('content_pillars')
    def validate_content_pillars(cls, v):
        if v is not None:
            total_percentage = sum(pillar.percentage for pillar in v)
            if total_percentage != 100:
                raise ValueError(f'Content pillar percentages must total 100%, got {total_percentage}%')
        return v


class BrandData(BaseModel):
    """Complete brand data structure"""
    id: str
    brand_name: str
    industry: str
    description: str
    website_url: Optional[str] = None
    voice_profile: VoiceProfile
    content_pillars: List[ContentPillar]
    brand_guidelines: BrandGuidelines
    target_demographics: Dict[str, Any] = {}
    brand_values: List[str] = []
    status: BrandStatus = BrandStatus.DRAFT
    created_at: datetime
    updated_at: datetime
    version: str = "v1"


class BrandResponse(BaseModel):
    """Brand response"""
    brand_id: str
    status: str
    message: str
    data: Optional[BrandData] = None


class BrandListResponse(BaseModel):
    """Brand list response"""
    brands: List[BrandData]
    total: int


class FileUploadResponse(BaseModel):
    """File upload response"""
    file_id: str
    filename: str
    file_size: int
    content_type: str
    upload_url: str
    status: str = "uploaded"


class BrandExtractionResult(BaseModel):
    """Brand guideline extraction result"""
    extracted_text: str
    voice_suggestions: VoiceProfile
    pillar_suggestions: List[ContentPillar]
    guideline_suggestions: BrandGuidelines
    confidence_score: float = Field(ge=0.0, le=1.0)