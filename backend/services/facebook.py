import os
import httpx
import urllib.parse
from typing import Dict, Any, List, Optional
from core.logging_config import get_logger

logger = get_logger("facebook_service")

class FacebookService:
    def __init__(self):
        self.app_id = os.environ.get("FACEBOOK_APP_ID")
        self.app_secret = os.environ.get("FACEBOOK_APP_SECRET")
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.app_id or not self.app_secret:
            logger.warning("FACEBOOK_APP_ID or FACEBOOK_APP_SECRET not set in environment.")

    async def get_access_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange auth code for access token"""
        url = f"{self.base_url}/oauth/access_token"
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "client_secret": self.app_secret,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to get access token: {e.response.text}")
                raise Exception(f"Facebook Auth Error: {e.response.text}")

    async def get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """Exchange short-lived token for a long-lived one (usually 60 days)"""
        url = f"{self.base_url}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_lived_token
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to get long-lived token: {e.response.text}")
                raise Exception(f"Facebook Token Exchange Error: {e.response.text}")

    async def get_user_pages(self, user_access_token: str) -> List[Dict[str, Any]]:
        """Fetch list of Facebook pages the user has access to"""
        url = f"{self.base_url}/me/accounts"
        params = {
            "access_token": user_access_token,
            "fields": "id,name,access_token,category,tasks"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("data", [])
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to fetch user pages: {e.response.text}")
                raise Exception(f"Facebook Pages Fetch Error: {e.response.text}")

    async def get_page_info(self, page_id: str, page_access_token: str) -> Dict[str, Any]:
        """Fetch specific page details"""
        url = f"{self.base_url}/{page_id}"
        params = {
            "access_token": page_access_token,
            "fields": "id,name,picture"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Failed to fetch page info: {e.response.text}")
                raise Exception(f"Facebook Page Info Error: {e.response.text}")

facebook_service = FacebookService()
