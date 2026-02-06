"""
Settings-related Pydantic schemas
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LanguageCode(str, Enum):
    """Supported language codes"""
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    IT = "it"
    PT = "pt"
    RU = "ru"
    ZH = "zh"
    JA = "ja"
    KO = "ko"
    AR = "ar"
    HI = "hi"


class EmojiPolicy(str, Enum):
    """Emoji usage policies"""
    NONE = "none"
    MINIMAL = "minimal"
    MODERATE = "moderate"
    LIBERAL = "liberal"


class SectorPreset(str, Enum):
    """Industry sector presets"""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    RETAIL = "retail"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    FOOD_BEVERAGE = "food_beverage"
    FASHION = "fashion"
    AUTOMOTIVE = "automotive"
    REAL_ESTATE = "real_estate"
    TRAVEL = "travel"
    FITNESS = "fitness"


class IntegrationStatus(str, Enum):
    """Integration connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"


class LanguageSettings(BaseModel):
    """Language settings configuration"""
    primary_language: LanguageCode = LanguageCode.EN
    supported_languages: List[LanguageCode] = [LanguageCode.EN]
    auto_translate: bool = False
    translation_quality: str = Field(default="standard", pattern=r"^(standard|premium)$")


class LLMSettings(BaseModel):
    """LLM provider settings"""
    primary_provider: LLMProvider = LLMProvider.OPENAI
    fallback_providers: List[LLMProvider] = []
    monthly_budget_limit: float = Field(ge=0, description="Monthly budget limit in USD")
    current_usage: float = Field(default=0, ge=0, description="Current month usage in USD")
    models: Dict[str, str] = {
        "text_generation": "gpt-4",
        "image_analysis": "gpt-4-vision-preview",
        "content_moderation": "text-moderation-latest"
    }
    
    @validator('current_usage')
    def validate_usage_within_budget(cls, v, values):
        budget = values.get('monthly_budget_limit', 0)
        if v > budget:
            raise ValueError('Current usage cannot exceed monthly budget limit')
        return v


class GuardrailSettings(BaseModel):
    """Content guardrail settings"""
    forbidden_phrases: List[str] = []
    required_disclaimers: List[str] = []
    content_moderation_enabled: bool = True
    profanity_filter: bool = True
    political_content_filter: bool = True
    adult_content_filter: bool = True
    violence_filter: bool = True


class ContentSettings(BaseModel):
    """Content generation settings"""
    emoji_policy: EmojiPolicy = EmojiPolicy.MODERATE
    hashtag_limit: int = Field(default=10, ge=1, le=30)
    max_caption_length: int = Field(default=2200, ge=100, le=2200)
    include_call_to_action: bool = True
    brand_mention_frequency: float = Field(default=0.3, ge=0.0, le=1.0)


class SectorSettings(BaseModel):
    """Industry sector-specific settings"""
    sector: SectorPreset
    compliance_rules: List[str] = []
    industry_keywords: List[str] = []
    restricted_topics: List[str] = []
    preferred_content_types: List[str] = []


class IntegrationConfig(BaseModel):
    """Integration configuration"""
    platform: str
    status: IntegrationStatus
    credentials: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}
    last_sync: Optional[str] = None
    error_message: Optional[str] = None


class PersonaData(BaseModel):
    """Persona data structure"""
    id: str
    name: str
    age_range: str
    gender: Optional[str] = None
    location: Optional[str] = None
    interests: List[str] = []
    behaviors: List[str] = []
    pain_points: List[str] = []
    preferred_content: List[str] = []
    social_platforms: List[str] = []


class ProductData(BaseModel):
    """Product data structure"""
    id: str
    name: str
    category: str
    price: Optional[float] = None
    currency: str = "USD"
    description: str
    features: List[str] = []
    benefits: List[str] = []
    target_audience: List[str] = []
    image_urls: List[str] = []
    availability: bool = True


class SettingsResponse(BaseModel):
    """Generic settings response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class LanguageSettingsResponse(BaseModel):
    """Language settings response"""
    settings: LanguageSettings


class LLMSettingsResponse(BaseModel):
    """LLM settings response"""
    settings: LLMSettings


class GuardrailSettingsResponse(BaseModel):
    """Guardrail settings response"""
    settings: GuardrailSettings


class IntegrationListResponse(BaseModel):
    """Integration list response"""
    integrations: List[IntegrationConfig]


class PersonaListResponse(BaseModel):
    """Persona list response"""
    personas: List[PersonaData]
    total: int


class ProductListResponse(BaseModel):
    """Product list response"""
    products: List[ProductData]
    total: int


class PersonaCreateRequest(BaseModel):
    """Persona creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    age_range: str = Field(..., pattern=r"^\d+-\d+$")
    gender: Optional[str] = None
    location: Optional[str] = None
    interests: List[str] = Field(..., min_items=1)
    behaviors: List[str] = []
    pain_points: List[str] = []
    preferred_content: List[str] = []
    social_platforms: List[str] = []


class ProductCreateRequest(BaseModel):
    """Product creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    price: Optional[float] = Field(None, ge=0)
    currency: str = "USD"
    description: str = Field(..., min_length=10, max_length=1000)
    features: List[str] = []
    benefits: List[str] = []
    target_audience: List[str] = []
    image_urls: List[str] = []
    availability: bool = True