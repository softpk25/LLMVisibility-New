"""
Engage Boost module Pydantic schemas
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class CommentIntent(str, Enum):
    """Comment intent classification"""
    QUESTION = "question"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    INQUIRY = "inquiry"
    FEEDBACK = "feedback"
    SPAM = "spam"
    SUPPORT_REQUEST = "support_request"
    GENERAL = "general"


class CommentSentiment(str, Enum):
    """Comment sentiment"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class ResponseStatus(str, Enum):
    """Response status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class Priority(str, Enum):
    """Comment priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Platform(str, Enum):
    """Social media platforms"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"


class CommentData(BaseModel):
    """Comment data from webhook"""
    id: str
    platform: Platform
    post_id: str
    author_id: str
    author_name: str
    content: str
    timestamp: datetime
    parent_comment_id: Optional[str] = None
    likes_count: int = 0
    replies_count: int = 0
    metadata: Dict[str, Any] = {}


class CommentClassification(BaseModel):
    """Comment classification result"""
    intent: CommentIntent
    sentiment: CommentSentiment
    priority: Priority
    confidence_score: float = Field(ge=0.0, le=1.0)
    keywords: List[str] = []
    topics: List[str] = []
    requires_human_review: bool = False
    escalation_reason: Optional[str] = None


class ResponseDraft(BaseModel):
    """AI-generated response draft"""
    content: str
    tone: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    suggested_actions: List[str] = []
    brand_alignment_score: float = Field(ge=0.0, le=1.0)


class CommentAnalysisRequest(BaseModel):
    """Comment analysis request"""
    comment: CommentData
    brand_id: Optional[str] = None
    context: Dict[str, Any] = {}


class CommentAnalysisResult(BaseModel):
    """Complete comment analysis result"""
    comment_id: str
    classification: CommentClassification
    response_draft: ResponseDraft
    analysis_timestamp: datetime
    processing_time: float


class ResponseDecisionRequest(BaseModel):
    """Response decision request"""
    comment_id: str
    action: str = Field(..., pattern=r"^(approve|reject|edit)$")
    edited_response: Optional[str] = None
    feedback: Optional[str] = None
    reviewer_id: Optional[str] = None


class ResponseDecisionResult(BaseModel):
    """Response decision result"""
    comment_id: str
    action_taken: str
    final_response: Optional[str] = None
    status: ResponseStatus
    timestamp: datetime
    reviewer_id: Optional[str] = None


class EngagementMetrics(BaseModel):
    """Engagement metrics"""
    total_comments: int
    processed_comments: int
    pending_review: int
    auto_approved: int
    human_reviewed: int
    response_rate: float = Field(ge=0.0, le=1.0)
    avg_response_time: float  # in minutes
    sentiment_breakdown: Dict[str, int] = {}
    intent_breakdown: Dict[str, int] = {}


class CommentThread(BaseModel):
    """Comment thread structure"""
    parent_comment: CommentData
    replies: List[CommentData] = []
    thread_sentiment: CommentSentiment
    requires_attention: bool = False


class KnowledgeBaseEntry(BaseModel):
    """Knowledge base entry for contextual responses"""
    id: str
    title: str
    content: str
    keywords: List[str] = []
    category: str
    last_updated: datetime
    usage_count: int = 0


class AutoResponseRule(BaseModel):
    """Automated response rule"""
    id: str
    name: str
    trigger_conditions: Dict[str, Any]
    response_template: str
    enabled: bool = True
    priority: int = Field(ge=1, le=100)
    created_at: datetime


class CommentListResponse(BaseModel):
    """Comment list response"""
    comments: List[CommentAnalysisResult]
    total: int
    pending_review: int
    page: int
    page_size: int


class EngagementAnalyticsResponse(BaseModel):
    """Engagement analytics response"""
    metrics: EngagementMetrics
    time_period: str
    trends: Dict[str, Any] = {}


class ResponseTemplateRequest(BaseModel):
    """Response template creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    template: str = Field(..., min_length=10, max_length=500)
    intent_types: List[CommentIntent]
    sentiment_types: List[CommentSentiment]
    variables: List[str] = []
    brand_id: Optional[str] = None


class ResponseTemplate(BaseModel):
    """Response template"""
    id: str
    name: str
    template: str
    intent_types: List[CommentIntent]
    sentiment_types: List[CommentSentiment]
    variables: List[str] = []
    brand_id: Optional[str] = None
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime