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
FB_APP_ID = os.environ.get("FACEBOOK_APP_ID", "mock_app_id")
FB_APP_SECRET = os.environ.get("FACEBOOK_APP_SECRET", "mock_app_secret")

@router.get("/facebook/auth")
async def facebook_auth(request: Request, brand_id: str = Query(..., description="Brand ID to connect")):
    """Initiate Facebook OAuth flow"""
    try:
        state = brand_id
        # Build redirect URI dynamically from the incoming request
        redirect_uri = str(request.base_url).rstrip("/") + "/api/v1/integrations/facebook/callback"

        # Mock flow when no real Facebook credentials
        if FB_APP_ID == "mock_app_id":
            return RedirectResponse(url=f"/api/v1/integrations/facebook/callback?code=mock_code&state={state}")

        params = {
            "client_id": FB_APP_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "pages_show_list,pages_read_engagement,pages_manage_posts",
            "response_type": "code"
        }
        oauth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{urllib.parse.urlencode(params)}"
        return RedirectResponse(url=oauth_url)
        
    except Exception as e:
        logger.error(f"Failed to initiate Facebook auth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate authentication")

@router.get("/facebook/callback")
async def facebook_callback(
    code: str, 
    state: str,
    conn=Depends(get_db)
):
    """Handle Facebook OAuth callback"""
    try:
        brand_id = state
        logger.info(f"Received Facebook callback for brand: {brand_id} with code: {code}")
        
        # In a real implementation:
        # 1. Exchange code for access token
        # 2. Get long-lived token
        # 3. Fetch list of pages
        # 4. Save credentials to database (global_settings -> integrations)
        
        # Update integrations settings in global_settings table
        cursor = conn.execute(
            "SELECT config_json FROM global_settings WHERE brand_id = ? AND type = ?",
            (brand_id, "integrations")
        )
        row = cursor.fetchone()

        now = datetime.utcnow().isoformat()
        integrations_data = {}
        if row:
            integrations_data = json.loads(row[0])

        # Update facebook section
        if "facebook" not in integrations_data:
            integrations_data["facebook"] = {}
        integrations_data["facebook"]["connected"] = True
        integrations_data["facebook"]["pageName"] = "TechBrand Official"  # Mock Page Name

        if row:
            conn.execute(
                "UPDATE global_settings SET config_json = ?, updated_at = ? WHERE brand_id = ? AND type = ?",
                (json.dumps(integrations_data), now, brand_id, "integrations")
            )
        else:
            conn.execute(
                "INSERT INTO global_settings (brand_id, type, config_json, updated_at) VALUES (?, ?, ?, ?)",
                (brand_id, "integrations", json.dumps(integrations_data), now)
            )
        conn.commit()
        logger.info(f"Updated Facebook settings for brand {brand_id}")
        
        return RedirectResponse(url="/FACEBOOK-SETTINGS.html?tab=settings-integrations&fb_connected=true")
        
    except Exception as e:
        logger.error(f"Facebook callback failed: {e}")
        return RedirectResponse(url="/FACEBOOK-SETTINGS.html?tab=settings-integrations&error=auth_failed")

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
                integrations_data["facebook"]["connected"] = False
                integrations_data["facebook"]["pageName"] = None

                conn.execute(
                    "UPDATE global_settings SET config_json = ?, updated_at = ? WHERE brand_id = ? AND type = ?",
                    (json.dumps(integrations_data), datetime.utcnow().isoformat(), brand_id, "integrations")
                )
                conn.commit()

        return {"status": "success", "message": "Facebook disconnected"}
    except Exception as e:
        logger.error(f"Failed to disconnect Facebook: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Facebook")
