import httpx
from typing import Optional, List
from sqlalchemy.orm import Session

import sys
sys.path.append("..")
from models import PollRequest
from config import get_settings


class FacebookPollService:
    """
    Service for Facebook Poll operations.
    Translated from Java FacebookPollService.java
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.graph_api_url = self.settings.FACEBOOK_GRAPH_API_URL
        self.access_token = self.settings.FACEBOOK_ACCESS_TOKEN
    
    def create_page_poll(self, page_id: str, poll_request: PollRequest) -> Optional[str]:
        """
        Create a poll on a Facebook Page.
        
        Args:
            page_id: The Facebook Page ID
            poll_request: Poll configuration
            
        Returns:
            Post ID if successful, None otherwise
        """
        url = f"{self.graph_api_url}/{page_id}/feed"
        
        request_body = {
            "message": poll_request.question,
            "allow_multiple_choices": poll_request.allow_multiple_choices,
            "access_token": self.access_token
        }
        
        # Add poll options
        options = [{"option_text": opt.title} for opt in poll_request.options]
        request_body["poll_options"] = options
        
        # Add duration if specified
        if poll_request.duration_in_seconds:
            request_body["poll_options"] = {
                "duration": poll_request.duration_in_seconds
            }
            # Re-add options after duration
            request_body["poll_options"] = options
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json().get("id")
                
        except Exception as e:
            print(f"Error creating page poll: {e}")
            return None
    
    def create_group_poll(self, group_id: str, poll_request: PollRequest) -> Optional[str]:
        """
        Create a poll in a Facebook Group.
        
        Args:
            group_id: The Facebook Group ID
            poll_request: Poll configuration
            
        Returns:
            Post ID if successful, None otherwise
        """
        url = f"{self.graph_api_url}/{group_id}/feed"
        
        # Group polls use different format
        options = [opt.title for opt in poll_request.options]
        
        request_body = {
            "question": poll_request.question,
            "allow_multiple_choices": poll_request.allow_multiple_choices,
            "options": options,
            "access_token": self.access_token
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=request_body,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json().get("id")
                
        except Exception as e:
            print(f"Error creating group poll: {e}")
            return None
