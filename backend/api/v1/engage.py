"""
Engage Boost API endpoints
"""

import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path

from schemas.engage import (
    CommentAnalysisRequest,
    CommentAnalysisResult,
    ResponseDecisionRequest,
    ResponseDecisionResult,
    CommentListResponse,
    EngagementAnalyticsResponse,
    ResponseTemplateRequest,
    ResponseTemplate,
    CommentData,
    CommentClassification,
    ResponseDraft,
    CommentIntent,
    CommentSentiment,
    Priority,
    ResponseStatus,
    EngagementMetrics
)
from services.storage import storage
from services.llm_orchestrator import orchestrator
from core.logging_config import get_logger

logger = get_logger("engage_api")
router = APIRouter()


@router.post("/comment", response_model=CommentAnalysisResult)
async def analyze_comment(request: CommentAnalysisRequest):
    """Analyze Facebook comment and generate response draft"""
    try:
        # Create LLM payload for comment analysis
        llm_payload = {
            "task_type": "text_generation",
            "prompt": f"""
            Analyze this social media comment and provide a comprehensive assessment:
            
            Comment Details:
            - Platform: {request.comment.platform}
            - Author: {request.comment.author_name}
            - Content: "{request.comment.content}"
            - Timestamp: {request.comment.timestamp}
            - Likes: {request.comment.likes_count}
            - Replies: {request.comment.replies_count}
            
            Brand Context: {request.brand_id or 'Not provided'}
            Additional Context: {request.context}
            
            Please analyze:
            1. Intent Classification:
               - Determine if this is a question, complaint, compliment, inquiry, feedback, spam, support request, or general comment
               - Provide confidence score (0-1)
            
            2. Sentiment Analysis:
               - Classify as positive, negative, neutral, or mixed
               - Identify emotional tone and intensity
            
            3. Priority Assessment:
               - Assign priority level (low, medium, high, urgent)
               - Determine if human review is required
               - Identify escalation reasons if applicable
            
            4. Response Generation:
               - Create an appropriate response draft
               - Ensure brand-appropriate tone
               - Include suggested actions if needed
               - Provide brand alignment score
            
            5. Keywords and Topics:
               - Extract relevant keywords
               - Identify main topics discussed
            
            Format response as structured JSON with all analysis components.
            """,
            "parameters": {
                "max_tokens": 1500,
                "temperature": 0.3
            },
            "request_id": f"comment_analysis_{request.comment.id}"
        }
        
        start_time = time.time()
        llm_result = await orchestrator.generate(llm_payload)
        processing_time = time.time() - start_time
        
        if not llm_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to analyze comment")
        
        # Parse LLM response and create structured result
        # In production, implement proper JSON parsing from LLM response
        analysis_content = llm_result.get("content", "")
        
        # Create mock structured analysis (replace with actual parsing)
        classification = CommentClassification(
            intent=CommentIntent.QUESTION if "?" in request.comment.content else CommentIntent.GENERAL,
            sentiment=CommentSentiment.POSITIVE if any(word in request.comment.content.lower() 
                     for word in ["great", "love", "awesome", "good"]) else CommentSentiment.NEUTRAL,
            priority=Priority.HIGH if any(word in request.comment.content.lower() 
                    for word in ["urgent", "problem", "issue", "help"]) else Priority.MEDIUM,
            confidence_score=0.85,
            keywords=["customer", "service", "product"],
            topics=["customer service"],
            requires_human_review=False
        )
        
        response_draft = ResponseDraft(
            content=f"Thank you for your comment! We appreciate your feedback and will get back to you soon.",
            tone="friendly and professional",
            confidence_score=0.80,
            reasoning="Standard positive response appropriate for the comment tone",
            suggested_actions=["Follow up within 24 hours", "Check customer account"],
            brand_alignment_score=0.90
        )
        
        # Create analysis result
        analysis_result = CommentAnalysisResult(
            comment_id=request.comment.id,
            classification=classification,
            response_draft=response_draft,
            analysis_timestamp=datetime.utcnow(),
            processing_time=processing_time
        )
        
        # Save analysis result
        await storage.save("engage_analyses", request.comment.id, analysis_result.model_dump())
        
        # Update engagement metrics
        await _update_engagement_metrics(classification)
        
        logger.info(f"Analyzed comment {request.comment.id} - Intent: {classification.intent}, Sentiment: {classification.sentiment}")
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze comment")


@router.post("/decision", response_model=ResponseDecisionResult)
async def make_response_decision(request: ResponseDecisionRequest):
    """Approve, reject, or edit AI-generated response"""
    try:
        # Get original analysis
        try:
            analysis_data = await storage.load("engage_analyses", request.comment_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Comment analysis not found")
        
        # Determine final response and status
        final_response = None
        status = ResponseStatus.REJECTED
        
        if request.action == "approve":
            final_response = analysis_data["response_draft"]["content"]
            status = ResponseStatus.APPROVED
        elif request.action == "edit":
            final_response = request.edited_response
            status = ResponseStatus.APPROVED
        elif request.action == "reject":
            status = ResponseStatus.REJECTED
        
        # Create decision result
        decision_result = ResponseDecisionResult(
            comment_id=request.comment_id,
            action_taken=request.action,
            final_response=final_response,
            status=status,
            timestamp=datetime.utcnow(),
            reviewer_id=request.reviewer_id
        )
        
        # Save decision
        decision_data = decision_result.model_dump()
        decision_data["feedback"] = request.feedback
        await storage.save("engage_decisions", request.comment_id, decision_data)
        
        # Update analysis with decision
        analysis_data["decision"] = decision_data
        await storage.save("engage_analyses", request.comment_id, analysis_data)
        
        # Learn from feedback for future improvements
        if request.feedback:
            await _process_feedback_for_learning(request.comment_id, request.feedback, analysis_data)
        
        logger.info(f"Decision made for comment {request.comment_id}: {request.action}")
        
        return decision_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to process decision")


@router.get("/comments", response_model=CommentListResponse)
async def list_comments(
    status: str = Query(None, description="Filter by status"),
    sentiment: str = Query(None, description="Filter by sentiment"),
    priority: str = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List analyzed comments with filtering"""
    try:
        offset = (page - 1) * page_size
        
        # Get all analyses
        analyses = await storage.list_items("engage_analyses", limit=page_size * 2, offset=offset)
        total = await storage.count_items("engage_analyses")
        
        # Apply filters
        filtered_analyses = []
        for analysis_data in analyses:
            # Status filter
            if status:
                decision_status = analysis_data.get("decision", {}).get("status", "pending_review")
                if decision_status != status:
                    continue
            
            # Sentiment filter
            if sentiment:
                analysis_sentiment = analysis_data.get("classification", {}).get("sentiment")
                if analysis_sentiment != sentiment:
                    continue
            
            # Priority filter
            if priority:
                analysis_priority = analysis_data.get("classification", {}).get("priority")
                if analysis_priority != priority:
                    continue
            
            filtered_analyses.append(analysis_data)
            
            if len(filtered_analyses) >= page_size:
                break
        
        # Convert to CommentAnalysisResult objects
        comment_results = []
        pending_count = 0
        
        for analysis_data in filtered_analyses:
            try:
                result = CommentAnalysisResult(**analysis_data)
                comment_results.append(result)
                
                # Count pending reviews
                if not analysis_data.get("decision"):
                    pending_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to parse analysis data: {e}")
                continue
        
        return CommentListResponse(
            comments=comment_results,
            total=len(filtered_analyses),
            pending_review=pending_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to list comments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list comments")


@router.get("/analytics", response_model=EngagementAnalyticsResponse)
async def get_engagement_analytics(
    time_period: str = Query("7d", description="Time period for analytics")
):
    """Get engagement analytics and metrics"""
    try:
        # Calculate time range
        now = datetime.utcnow()
        days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
        days = days_map[time_period]
        start_date = now - timedelta(days=days)
        
        # Get all analyses in time period
        all_analyses = await storage.list_items("engage_analyses", limit=1000)
        
        # Filter by time period
        period_analyses = []
        for analysis in all_analyses:
            analysis_time = datetime.fromisoformat(analysis.get("analysis_timestamp", ""))
            if analysis_time >= start_date:
                period_analyses.append(analysis)
        
        # Calculate metrics
        total_comments = len(period_analyses)
        processed_comments = len([a for a in period_analyses if a.get("decision")])
        pending_review = total_comments - processed_comments
        auto_approved = len([a for a in period_analyses 
                           if a.get("decision", {}).get("action_taken") == "approve"])
        human_reviewed = len([a for a in period_analyses 
                            if a.get("decision", {}).get("reviewer_id")])
        
        # Calculate response rate
        response_rate = processed_comments / total_comments if total_comments > 0 else 0
        
        # Calculate average response time (mock data)
        avg_response_time = 45.5  # minutes
        
        # Sentiment breakdown
        sentiment_breakdown = {}
        intent_breakdown = {}
        
        for analysis in period_analyses:
            classification = analysis.get("classification", {})
            
            sentiment = classification.get("sentiment", "neutral")
            sentiment_breakdown[sentiment] = sentiment_breakdown.get(sentiment, 0) + 1
            
            intent = classification.get("intent", "general")
            intent_breakdown[intent] = intent_breakdown.get(intent, 0) + 1
        
        metrics = EngagementMetrics(
            total_comments=total_comments,
            processed_comments=processed_comments,
            pending_review=pending_review,
            auto_approved=auto_approved,
            human_reviewed=human_reviewed,
            response_rate=response_rate,
            avg_response_time=avg_response_time,
            sentiment_breakdown=sentiment_breakdown,
            intent_breakdown=intent_breakdown
        )
        
        # Calculate trends (simplified)
        trends = {
            "comment_volume_trend": "increasing",
            "sentiment_trend": "stable",
            "response_time_trend": "improving"
        }
        
        return EngagementAnalyticsResponse(
            metrics=metrics,
            time_period=time_period,
            trends=trends
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.post("/templates", response_model=ResponseTemplate)
async def create_response_template(request: ResponseTemplateRequest):
    """Create response template for automated responses"""
    try:
        template_id = str(uuid.uuid4())
        
        template = ResponseTemplate(
            id=template_id,
            name=request.name,
            template=request.template,
            intent_types=request.intent_types,
            sentiment_types=request.sentiment_types,
            variables=request.variables,
            brand_id=request.brand_id,
            usage_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save template
        await storage.save("engage_templates", template_id, template.model_dump())
        
        logger.info(f"Created response template {template_id}: {request.name}")
        
        return template
        
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.get("/templates", response_model=List[ResponseTemplate])
async def list_response_templates(
    brand_id: str = Query(None, description="Filter by brand ID"),
    intent_type: str = Query(None, description="Filter by intent type")
):
    """List response templates"""
    try:
        templates = await storage.list_items("engage_templates", limit=100)
        
        # Apply filters
        if brand_id:
            templates = [t for t in templates if t.get("brand_id") == brand_id]
        
        if intent_type:
            templates = [t for t in templates if intent_type in t.get("intent_types", [])]
        
        # Convert to ResponseTemplate objects
        template_objects = []
        for template_data in templates:
            try:
                template = ResponseTemplate(**template_data)
                template_objects.append(template)
            except Exception as e:
                logger.warning(f"Failed to parse template data: {e}")
                continue
        
        return template_objects
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


async def _update_engagement_metrics(classification: CommentClassification):
    """Update engagement metrics (internal helper)"""
    try:
        # Get current metrics
        try:
            metrics_data = await storage.load("engage_metrics", "current")
        except:
            metrics_data = {
                "total_comments": 0,
                "sentiment_counts": {},
                "intent_counts": {},
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # Update counts
        metrics_data["total_comments"] += 1
        
        sentiment_counts = metrics_data.setdefault("sentiment_counts", {})
        sentiment_counts[classification.sentiment] = sentiment_counts.get(classification.sentiment, 0) + 1
        
        intent_counts = metrics_data.setdefault("intent_counts", {})
        intent_counts[classification.intent] = intent_counts.get(classification.intent, 0) + 1
        
        metrics_data["last_updated"] = datetime.utcnow().isoformat()
        
        # Save updated metrics
        await storage.save("engage_metrics", "current", metrics_data)
        
    except Exception as e:
        logger.warning(f"Failed to update metrics: {e}")


async def _process_feedback_for_learning(comment_id: str, feedback: str, analysis_data: Dict[str, Any]):
    """Process feedback for machine learning improvements (internal helper)"""
    try:
        # Store feedback for future model training
        feedback_data = {
            "comment_id": comment_id,
            "feedback": feedback,
            "original_analysis": analysis_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        feedback_id = str(uuid.uuid4())
        await storage.save("engage_feedback", feedback_id, feedback_data)
        
        logger.info(f"Stored feedback for learning: {comment_id}")
        
    except Exception as e:
        logger.warning(f"Failed to process feedback: {e}")