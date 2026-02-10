import httpx
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

import sys
sys.path.append("..")
from models import FacebookSettings
from config import get_settings


class FacebookService:
    """
    Service for Facebook comment operations.
    Translated from Java FacebookService.java
    """
    
    GRAPH_URL = "https://graph.facebook.com/v20.0/"
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self._fb_token: Optional[str] = None
    
    def _get_fb_token(self) -> str:
        """Get Facebook token from database or config"""
        if self._fb_token:
            return self._fb_token
            
        settings = self.db.query(FacebookSettings).filter(
            FacebookSettings.client.ilike("%1%")
        ).first()
        
        if settings and settings.page_access_token:
            self._fb_token = settings.page_access_token
        else:
            # Fall back to config
            self._fb_token = self.settings.FACEBOOK_PAGE_ACCESS_TOKEN
        
        if not self._fb_token:
            raise ValueError("No Facebook page access token found. Please initialize settings or configure .env file.")
        
        print(f"pageaccesstoken=={self._fb_token}")
        return self._fb_token
    
    def get_comments(self, post_id: str) -> List[Dict[str, str]]:
        """
        Get comments for a Facebook post.
        
        Args:
            post_id: The Facebook post ID
            
        Returns:
            List of comments with id, user, and message
        """
        try:
            fb_token = self._get_fb_token()
            url = f"{self.GRAPH_URL}{post_id}/comments?fields=id,from,message&access_token={fb_token}"
            
            with httpx.Client() as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json().get("data", [])
                
            result = []
            for comment in data:
                result.append({
                    "id": comment.get("id", ""),
                    "user": comment.get("from", {}).get("name", ""),
                    "message": comment.get("message", "")
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []
    
    def reply_to_comment(self, comment_id: str, message: str) -> bool:
        """
        Reply to a Facebook comment.
        
        Args:
            comment_id: The comment ID to reply to
            message: The reply message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            fb_token = self._get_fb_token()
            url = f"{self.GRAPH_URL}{comment_id}/comments"
            
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json={"message": message, "access_token": fb_token}
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            print(f"Error replying to comment: {e}")
            return False
