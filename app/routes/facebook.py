from fastapi import APIRouter, Depends, HTTPException, Query, Request, Body
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import logging

from app.core.db_sqlalchemy import get_db
from app.models.facebook import FacebookIntegration
from app.schemas.facebook import (
    FacebookPostCreate, FacebookPhotoCreate, FacebookVideoCreate, 
    FacebookStoryCreate, FacebookPollCreate, FacebookStatusResponse
)
from app.services.facebook_oauth import FacebookOAuthService
from app.services.token_manager import TokenManager
from app.services.facebook_publish import FacebookPublishService
from app.utils.encryption import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)
router = APIRouter()

oauth_service = FacebookOAuthService()
token_manager = TokenManager()
publish_service = FacebookPublishService()

# --- OAuth Endpoints ---

@router.get("/auth/facebook/login")
async def facebook_login(brand_id: str):
    """Initiate Facebook OAuth flow."""
    # In production, use a more secure state (CSRF Protection)
    return RedirectResponse(oauth_service.get_login_url(brand_id))

@router.get("/auth/facebook/callback")
async def facebook_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle Facebook OAuth callback."""
    try:
        # 1. Exchange code for user token
        token_data = await oauth_service.exchange_code_for_token(code)
        short_token = token_data.get("access_token")
        
        # 2. Exchange for long-lived user token
        long_token_data = await token_manager.get_long_lived_user_token(short_token)
        long_user_token = long_token_data.get("access_token")
        
        # 3. Get user pages
        pages = await oauth_service.get_user_pages(long_user_token)
        if not pages:
            raise HTTPException(status_code=400, detail="No Facebook pages found for this user")
        
        # Simplified: Link the first page. In a real app, you'd show a UI to select.
        page = pages[0]
        
        # 4. Store/Update in Database
        integration = db.query(FacebookIntegration).filter(FacebookIntegration.brand_id == state).first()
        if not integration:
            integration = FacebookIntegration(brand_id=state)
            db.add(integration)
        
        integration.page_id = page["id"]
        integration.page_name = page["name"]
        integration.page_access_token = encrypt_token(page["access_token"])
        integration.user_access_token = encrypt_token(long_user_token)
        integration.connected = True
        
        db.commit()
        return {"status": "success", "message": f"Connected to page: {page['name']}"}
        
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Publishing Endpoints ---

@router.post("/facebook/publish/post")
async def publish_text_post(brand_id: str, payload: FacebookPostCreate, db: Session = Depends(get_db)):
    integration = db.query(FacebookIntegration).filter(FacebookIntegration.brand_id == brand_id).first()
    if not integration or not integration.connected:
        raise HTTPException(status_code=400, detail="Facebook not connected for this brand")
    
    token = decrypt_token(integration.page_access_token)
    return await publish_service.publish_text_post(integration.page_id, token, payload.message, payload.link)

@router.post("/facebook/publish/photo")
async def publish_photo(brand_id: str, payload: FacebookPhotoCreate, db: Session = Depends(get_db)):
    integration = db.query(FacebookIntegration).filter(FacebookIntegration.brand_id == brand_id).first()
    if not integration or not integration.connected:
        raise HTTPException(status_code=400, detail="Facebook not connected")
    
    token = decrypt_token(integration.page_access_token)
    return await publish_service.publish_photo(integration.page_id, token, payload.url, payload.caption)

@router.post("/facebook/publish/video")
async def publish_video(brand_id: str, payload: FacebookVideoCreate, db: Session = Depends(get_db)):
    integration = db.query(FacebookIntegration).filter(FacebookIntegration.brand_id == brand_id).first()
    if not integration or not integration.connected:
        raise HTTPException(status_code=400, detail="Facebook not connected")
    
    token = decrypt_token(integration.page_access_token)
    return await publish_service.publish_video(integration.page_id, token, payload.file_path, payload.description)

@router.post("/facebook/publish/story")
async def publish_story(brand_id: str, payload: FacebookStoryCreate, db: Session = Depends(get_db)):
    integration = db.query(FacebookIntegration).filter(FacebookIntegration.brand_id == brand_id).first()
    if not integration or not integration.connected:
        raise HTTPException(status_code=400, detail="Facebook not connected")
    
    token = decrypt_token(integration.page_access_token)
    return await publish_service.publish_story(integration.page_id, token, payload.media_url)

@router.post("/facebook/publish/poll")
async def publish_poll(brand_id: str, payload: FacebookPollCreate, db: Session = Depends(get_db)):
    integration = db.query(FacebookIntegration).filter(FacebookIntegration.brand_id == brand_id).first()
    if not integration or not integration.connected:
        raise HTTPException(status_code=400, detail="Facebook not connected")
    
    token = decrypt_token(integration.page_access_token)
    return await publish_service.publish_poll(integration.page_id, token, payload.question, payload.options)

# --- Webhook Endpoint ---

@router.get("/webhook/facebook")
async def verify_webhook(request: Request):
    """Verify Facebook Webhook challenge."""
    params = request.query_params
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN")
    
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == verify_token:
        return int(params.get("hub.challenge"))
    return JSONResponse(content={"status": "error", "message": "Verification failed"}, status_code=403)

@router.post("/webhook/facebook")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Facebook Webhook events."""
    # Log and process comment events
    data = await request.json()
    logger.info(f"Received Facebook Webhook: {data}")
    # Logic to process comment metadata and subscriptions
    return {"status": "received"}

# --- Account Management ---

@router.post("/facebook/disconnect")
async def facebook_disconnect(brand_id: str, db: Session = Depends(get_db)):
    integration = db.query(FacebookIntegration).filter(FacebookIntegration.brand_id == brand_id).first()
    if integration:
        integration.connected = False
        integration.page_access_token = ""
        integration.user_access_token = ""
        db.commit()
    return {"status": "success", "message": "Facebook disconnected"}

@router.get("/facebook/status", response_model=FacebookStatusResponse)
async def facebook_status(brand_id: str, db: Session = Depends(get_db)):
    integration = db.query(FacebookIntegration).filter(FacebookIntegration.brand_id == brand_id).first()
    if not integration:
        return FacebookStatusResponse(connected=False, brand_id=brand_id)
    
    return FacebookStatusResponse(
        connected=integration.connected,
        brand_id=brand_id,
        page_name=integration.page_name,
        token_expiry=integration.token_expiry
    )
