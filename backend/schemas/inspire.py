"""
Inspire Me module Pydantic schemas
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class CreativeType(str, Enum):
    """Creative content types"""
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


class AnalysisType(str, Enum):
    """Analysis types"""
    VISUAL_DNA = "visual_dna"
    STYLE_ANALYSIS = "style_analysis"
    CONTENT_ANALYSIS = "content_analysis"
    BRAND_ALIGNMENT = "brand_alignment"


class GenerationStatus(str, Enum):
    """Generation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VisualDNA(BaseModel):
    """Visual DNA analysis result"""
    color_palette: List[str] = []
    dominant_colors: List[str] = []
    style_keywords: List[str] = []
    mood: str
    composition: str
    lighting: str
    texture: str
    visual_weight: str
    brand_elements: List[str] = []
    confidence_score: float = Field(ge=0.0, le=1.0)


class StyleAnalysis(BaseModel):
    """Style analysis result"""
    photography_style: str
    color_grading: str
    composition_rules: List[str] = []
    visual_hierarchy: str
    typography_style: Optional[str] = None
    brand_consistency: float = Field(ge=0.0, le=1.0)
    recommendations: List[str] = []


class ContentAnalysis(BaseModel):
    """Content analysis result"""
    subject_matter: List[str] = []
    emotions_conveyed: List[str] = []
    target_audience_fit: float = Field(ge=0.0, le=1.0)
    message_clarity: float = Field(ge=0.0, le=1.0)
    call_to_action_present: bool
    brand_message_alignment: float = Field(ge=0.0, le=1.0)


class GenerativePrompt(BaseModel):
    """Generative prompt structure"""
    base_prompt: str
    style_modifiers: List[str] = []
    color_instructions: List[str] = []
    composition_instructions: List[str] = []
    mood_instructions: List[str] = []
    technical_parameters: Dict[str, Any] = {}


class CreativeAsset(BaseModel):
    """Creative asset data"""
    id: str
    filename: str
    file_path: str
    file_size: int
    content_type: str
    creative_type: CreativeType
    upload_timestamp: datetime
    metadata: Dict[str, Any] = {}


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    asset_id: str
    analysis_type: AnalysisType
    visual_dna: Optional[VisualDNA] = None
    style_analysis: Optional[StyleAnalysis] = None
    content_analysis: Optional[ContentAnalysis] = None
    generative_prompt: Optional[GenerativePrompt] = None
    processing_time: float
    timestamp: datetime


class GenerationRequest(BaseModel):
    """Creative generation request"""
    prompt: str = Field(..., min_length=10, max_length=1000)
    creative_type: CreativeType = CreativeType.IMAGE
    style_reference_ids: List[str] = []
    brand_id: Optional[str] = None
    aspect_ratio: str = Field(default="1:1", pattern=r"^\d+:\d+$")
    quality: str = Field(default="standard", pattern=r"^(draft|standard|high)$")
    variations: int = Field(default=1, ge=1, le=4)
    style_strength: float = Field(default=0.7, ge=0.0, le=1.0)
    creativity_level: float = Field(default=0.7, ge=0.0, le=1.0)


class GenerationSliders(BaseModel):
    """Generation control sliders"""
    creativity: float = Field(default=0.7, ge=0.0, le=1.0)
    brand_adherence: float = Field(default=0.8, ge=0.0, le=1.0)
    style_strength: float = Field(default=0.7, ge=0.0, le=1.0)
    color_vibrancy: float = Field(default=0.5, ge=0.0, le=1.0)
    composition_complexity: float = Field(default=0.5, ge=0.0, le=1.0)


class GenerationVariant(BaseModel):
    """Generated creative variant"""
    id: str
    image_url: str
    prompt_used: str
    style_score: float = Field(ge=0.0, le=1.0)
    brand_alignment_score: float = Field(ge=0.0, le=1.0)
    technical_quality_score: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = {}


class UploadResponse(BaseModel):
    """File upload response"""
    asset_ids: List[str]
    uploaded_files: List[CreativeAsset]
    failed_uploads: List[Dict[str, str]] = []


class AnalysisResponse(BaseModel):
    """Analysis response"""
    analysis_id: str
    status: str
    results: Optional[AnalysisResult] = None
    message: str


class GenerationResponse(BaseModel):
    """Generation response"""
    generation_id: str
    status: GenerationStatus
    variants: List[GenerationVariant] = []
    processing_time: Optional[float] = None
    message: str


class AssetListResponse(BaseModel):
    """Asset list response"""
    assets: List[CreativeAsset]
    total: int
    page: int
    page_size: int


class PromptEditRequest(BaseModel):
    """Prompt editing request"""
    original_prompt: str
    edits: Dict[str, Any]
    sliders: GenerationSliders
    preserve_style: bool = True