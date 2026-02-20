"""
Integrations API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional
import os
import urllib.parse
from datetime import datetime
import json

from core.logging_config import get_logger
from core.db import get_db

logger = get_logger("integrations_api")
router = APIRouter()

# Facebook OAuth Details (set real env vars for production)
FB_APP_ID = os.environ.get("FACEBOOK_APP_ID")
FB_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET")

from services.facebook import facebook_service

@router.get("/facebook/auth")
async def facebook_auth(request: Request, brand_id: str = Query(..., description="Brand ID to connect")):
    """Initiate Facebook OAuth flow"""
    try:
        if not FB_APP_ID:
            logger.error("FACEBOOK_APP_ID not configured")
            raise HTTPException(status_code=500, detail="Facebook integration not configured on server")

        state = brand_id
        # Use redirect URI from environment if set, otherwise build it dynamically
        redirect_uri = os.environ.get("FB_APP_REDIRECT_URL")
        if not redirect_uri:
            redirect_uri = str(request.base_url).rstrip("/") + "/api/v1/integrations/facebook/callback"

        params = {
            "client_id": FB_APP_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "pages_show_list,pages_read_engagement,pages_manage_posts,public_profile",
            "response_type": "code"
        }
        oauth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{urllib.parse.urlencode(params)}"
        logger.info(f"Initiating Facebook auth for brand: {brand_id}, redirect_uri: {redirect_uri}")
        return RedirectResponse(url=oauth_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate Facebook auth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate authentication")

@router.get("/facebook/callback")
async def facebook_callback(
    request: Request,
    code: str, 
    state: str,
    conn=Depends(get_db)
):
    """Handle Facebook OAuth callback"""
    try:
        brand_id = state
        logger.info(f"Received Facebook callback for brand: {brand_id}")
        
        # Use redirect URI from environment if set, otherwise build it dynamically
        redirect_uri = os.environ.get("FB_APP_REDIRECT_URL")
        if not redirect_uri:
            redirect_uri = str(request.base_url).rstrip("/") + "/api/v1/integrations/facebook/callback"
        
        # 1. Exchange code for short-lived access token
        token_data = await facebook_service.get_access_token(code, redirect_uri)
        short_token = token_data.get("access_token")
        
        # 2. Get long-lived token
        long_token_data = await facebook_service.get_long_lived_token(short_token)
        long_token = long_token_data.get("access_token")
        
        # 3. Fetch list of pages
        pages = await facebook_service.get_user_pages(long_token)
        
        if not pages:
            logger.warning(f"No pages found for user connecting brand {brand_id}")
            return RedirectResponse(url="/FACEBOOK-SETTINGS.html?tab=settings-integrations&error=no_pages")

        # For this implementation, we take the first page as default or match against a target if provided
        # In a more advanced UI, the user would select from the list.
        # Check if page.id exists in environment as a hint
        target_page_id = os.environ.get("page.id")
        selected_page = None
        
        if target_page_id:
            selected_page = next((p for p in pages if p["id"] == target_page_id), pages[0])
        else:
            selected_page = pages[0]

        logger.info(f"Selected Facebook page {selected_page['name']} ({selected_page['id']}) for brand {brand_id}")
        
        # 4. Save credentials to database (global_settings -> integrations)
        cursor = conn.execute(
            "SELECT config_json FROM global_settings WHERE brand_id = ? AND type = ?",
            (brand_id, "integrations")
        )
        row = cursor.fetchone()

        integrations_data = {}
        if row:
            integrations_data = json.loads(row[0])

        # Update facebook section
        integrations_data["facebook"] = {
            "connected": True,
            "pageId": selected_page["id"],
            "pageName": selected_page["name"],
            "accessToken": selected_page["access_token"], # Page access token
            "userAccessToken": long_token,
            "category": selected_page.get("category"),
            "connectedAt": datetime.utcnow().isoformat()
        }

        if row:
            conn.execute(
                "UPDATE global_settings SET config_json = ?, updated_at = ? WHERE brand_id = ? AND type = ?",
                (json.dumps(integrations_data), datetime.utcnow().isoformat(), brand_id, "integrations")
            )
        else:
            conn.execute(
                "INSERT INTO global_settings (brand_id, type, config_json, updated_at) VALUES (?, ?, ?, ?)",
                (brand_id, "integrations", json.dumps(integrations_data), datetime.utcnow().isoformat())
            )
        conn.commit()
        logger.info(f"Successfully integrated Facebook page for brand {brand_id}")
        
        return RedirectResponse(url="/FACEBOOK-SETTINGS.html?tab=settings-integrations&fb_connected=true")
        
    except Exception as e:
        import traceback
        import urllib.parse
        logger.error(f"Facebook callback failed: {str(e)}")
        logger.error(traceback.format_exc())
        error_msg = urllib.parse.quote(str(e))
        return RedirectResponse(url=f"/FACEBOOK-SETTINGS.html?tab=settings-integrations&error=auth_failed&details={error_msg}")

@router.post("/facebook/disconnect")
async def facebook_disconnect(
    brand_id: str = Query(...),
    conn=Depends(get_db)
):
    """Disconnect Facebook integration"""
    try:
        cursor = conn.execute(
            "SELECT config_json FROM global_settings WHERE brand_id = ? AND type = ?",
            (brand_id, "integrations")
        )
        row = cursor.fetchone()

        if row:
            integrations_data = json.loads(row[0])
            if "facebook" in integrations_data:
                integrations_data["facebook"] = {
                    "connected": False,
                    "pageName": None
                }

                conn.execute(
                    "UPDATE global_settings SET config_json = ?, updated_at = ? WHERE brand_id = ? AND type = ?",
                    (json.dumps(integrations_data), datetime.utcnow().isoformat(), brand_id, "integrations")
                )
                conn.commit()

        return {"status": "success", "message": "Facebook disconnected"}
    except Exception as e:
        logger.error(f"Failed to disconnect Facebook: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Facebook")
