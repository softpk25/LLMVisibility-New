import httpx
from typing import List, Optional
from sqlalchemy.orm import Session

import sys
sys.path.append("..")
from models import FacebookSettings
from config import get_settings
from services.facebook_token_validator import FacebookTokenValidator


class FacebookPostService:
    """
    Service for posting content to Facebook pages.
    Translated from Java FacebookPostService.java
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.token_validator = FacebookTokenValidator()
        self._page_access_token: Optional[str] = None
        self._page_id: Optional[str] = None
    
    def _load_credentials(self, validate: bool = True):
        """Load credentials from database or config"""
        fb_settings = self.db.query(FacebookSettings).filter(
            FacebookSettings.client.ilike("%1%")
        ).first()
        
        if fb_settings:
            self._page_access_token = fb_settings.page_access_token
            self._page_id = fb_settings.page_id
        else:
            self._page_access_token = self.settings.FACEBOOK_PAGE_ACCESS_TOKEN
            self._page_id = self.settings.FACEBOOK_PAGE_ID
        
        if not self._page_access_token or not self._page_id:
            raise ValueError("Page access token or page ID not configured. Please initialize settings from .env file.")
        
        # Validate token if requested
        if validate:
            is_valid, error_msg = self.token_validator.validate_page_token(
                self._page_id, 
                self._page_access_token
            )
            if not is_valid:
                raise ValueError(f"Invalid or expired access token: {error_msg}")
        
        print(f"pageaccesstoken=={self._page_access_token[:20]}...")
        print(f"page id=={self._page_id}")
    
    def post_carousel(self, image_urls: List[str], message: str) -> bool:
        """
        Post a carousel (multiple images) to Facebook page.
        
        Args:
            image_urls: List of image URLs to post
            message: Caption/message for the post
            
        Returns:
            True if successful, False otherwise
        """
        self._load_credentials()
        attached_media_ids = []
        
        for image_url in image_urls:
            print(f"imgeurl=={image_url}")
            media_id = self._upload_photo(image_url)
            if media_id:
                attached_media_ids.append(media_id)
        
        if attached_media_ids:
            return self._publish_post(attached_media_ids, message)
        
        return False
    
    def _upload_photo(self, image_url: str) -> Optional[str]:
        """
        Upload a photo to Facebook (unpublished).
        
        Args:
            image_url: URL of the image to upload
            
        Returns:
            Media ID if successful, None otherwise
        """
        url = (
            f"https://graph.facebook.com/{self._page_id}/photos"
            f"?url={image_url}&published=false&access_token={self._page_access_token}"
        )
        
        try:
            with httpx.Client() as client:
                response = client.post(url)
                
                if response.status_code == 200:
                    return response.json().get("id")
                    
        except Exception as e:
            print(f"Error uploading photo: {e}")
        
        return None
    
    def _publish_post(self, media_ids: List[str], message: str) -> bool:
        """
        Publish a post with attached media.
        
        Args:
            media_ids: List of media IDs to attach
            message: Post message/caption
            
        Returns:
            True if successful, False otherwise
        """
        url = f"https://graph.facebook.com/{self._page_id}/feed"
        
        # Build the payload
        payload = {
            "access_token": self._page_access_token,
            "message": message
        }
        
        # Add attached media
        for index, media_id in enumerate(media_ids):
            payload[f"attached_media[{index}]"] = f'{{"media_fbid":"{media_id}"}}'
        
        print(f"payload for feed=={payload}")
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            print(f"Error publishing post: {e}")
            return False
    
    def post_single_image(self, image_url: str, message: str) -> Optional[str]:
        """
        Post a single image to Facebook page.
        
        Args:
            image_url: URL of the image
            message: Caption/message
            
        Returns:
            Post ID if successful, None otherwise
        """
        self._load_credentials(validate=True)
        
        # Use form data instead of URL params for better handling
        url = f"https://graph.facebook.com/v19.0/{self._page_id}/photos"
        
        payload = {
            "url": image_url,
            "message": message or "",
            "access_token": self._page_access_token
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, data=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    post_id = result.get("id") or result.get("post_id")
                    print(f"Successfully posted image. Post ID: {post_id}")
                    return post_id
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error = error_data.get("error", {})
                    error_code = error.get("code")
                    error_subcode = error.get("error_subcode")
                    error_msg = error.get("message", response.text)
                    
                    # Provide user-friendly error messages
                    if error_code == 190 and error_subcode == 467:
                        raise ValueError("Access token expired. Please reconnect your Facebook account or update the token in .env file.")
                    elif error_code == 190:
                        raise ValueError(f"Access token is invalid: {error_msg}")
                    else:
                        raise ValueError(f"Facebook API error: {error_msg} (Code: {error_code})")
                    
        except ValueError:
            raise  # Re-raise validation errors
        except httpx.HTTPError as e:
            print(f"HTTP error posting image: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            print(f"Error posting image: {e}")
            raise
    
    def post_text(self, message: str) -> Optional[str]:
        """
        Post a text-only status to Facebook page.
        
        Args:
            message: The message to post
            
        Returns:
            Post ID if successful, None otherwise
        """
        self._load_credentials(validate=True)
        
        if not message or not message.strip():
            raise ValueError("Message cannot be empty")
        
        url = f"https://graph.facebook.com/v19.0/{self._page_id}/feed"
        
        payload = {
            "message": message,
            "access_token": self._page_access_token
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, data=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    post_id = result.get("id") or result.get("post_id")
                    print(f"Successfully posted text. Post ID: {post_id}")
                    return post_id
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error = error_data.get("error", {})
                    error_code = error.get("code")
                    error_subcode = error.get("error_subcode")
                    error_msg = error.get("message", response.text)
                    
                    # Provide user-friendly error messages
                    if error_code == 190 and error_subcode == 467:
                        raise ValueError("Access token expired. Please reconnect your Facebook account or update the token in .env file.")
                    elif error_code == 190:
                        raise ValueError(f"Access token is invalid: {error_msg}")
                    else:
                        raise ValueError(f"Facebook API error: {error_msg} (Code: {error_code})")
                    
        except ValueError:
            raise  # Re-raise validation errors
        except httpx.HTTPError as e:
            print(f"HTTP error posting text: {e}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            print(f"Error posting text: {e}")
            raise
