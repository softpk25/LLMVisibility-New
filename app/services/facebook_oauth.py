import os
import httpx
from typing import Dict, Any, List
from urllib.parse import urlencode

GRAPH_API_VERSION = "v18.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

class FacebookOAuthService:
    """Handles OAuth 2.0 flow for Facebook."""
    
    def __init__(self):
        self.client_id = os.getenv("FACEBOOK_APP_ID")
        self.client_secret = os.getenv("FACEBOOK_APP_SECRET")
        self.redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI")

    def get_login_url(self, state: str) -> str:
        """Generate the Facebook Login URL."""
        scopes = [
            "pages_show_list",
            "pages_read_engagement",
            "pages_manage_posts",
            "pages_manage_metadata",
            "pages_manage_engagement",
            "pages_read_user_content",
            "publish_video"
        ]
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": ",".join(scopes),
            "response_type": "code"
        }
        return f"https://www.facebook.com/{GRAPH_API_VERSION}/dialog/oauth?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for a short-lived user access token."""
        url = f"{BASE_URL}/oauth/access_token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_user_pages(self, user_access_token: str) -> List[Dict[str, Any]]:
        """Fetch list of pages the user has access to."""
        url = f"{BASE_URL}/me/accounts"
        params = {"access_token": user_access_token}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json().get("data", [])
