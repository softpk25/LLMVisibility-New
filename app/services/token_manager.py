import os
import httpx
import redis
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.utils.encryption import encrypt_token, decrypt_token
from app.core.db_sqlalchemy import SessionLocal
from app.models.facebook import FacebookIntegration

GRAPH_API_VERSION = "v18.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

class TokenManager:
    """Manages Facebook access tokens, long-lived exchange, and caching."""
    
    def __init__(self):
        self.client_id = os.getenv("FACEBOOK_APP_ID")
        self.client_secret = os.getenv("FACEBOOK_APP_SECRET")
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    async def get_long_lived_user_token(self, short_lived_token: str) -> Dict[str, Any]:
        """Exchange short-lived user token for a long-lived one (usually 60 days)."""
        url = f"{BASE_URL}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "fb_exchange_token": short_lived_token
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def cache_token(self, key_id: str, token: str, expiry_seconds: int):
        """Cache the encrypted token in Redis."""
        self.redis_client.setex(f"fb_token:{key_id}", expiry_seconds, token)

    def get_cached_token(self, key_id: str) -> Optional[str]:
        """Retrieve token from Redis cache."""
        return self.redis_client.get(f"fb_token:{key_id}")

    async def refresh_integration_tokens(self, integration_id: int):
        """
        Background-friendly method to refresh tokens for an integration.
        In a real scenario, this would be called by a Celery/rq worker.
        """
        db = SessionLocal()
        try:
            integration = db.query(FacebookIntegration).filter(FacebookIntegration.id == integration_id).first()
            if not integration or not integration.connected:
                return

            # Logic to check expiry and refresh if within buffer (e.g., 7 days)
            # This would involve using the user_access_token to get a new one 
            # or refreshing the page token.
            pass
        finally:
            db.close()
