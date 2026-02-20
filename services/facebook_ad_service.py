import httpx
from typing import Optional
from sqlalchemy.orm import Session
from pathlib import Path

import sys
sys.path.append("..")
from models import FacebookSettings
from config import get_settings


class FacebookAdService:
    """
    Service for Facebook Ads operations.
    Translated from Java FacebookAdService.java
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self._access_token: Optional[str] = None
        self._ad_account_id: Optional[str] = None
        self._page_id: Optional[str] = None
        self._ad_set_id: Optional[str] = None
    
    def _load_credentials(self):
        """Load ad credentials from database or config"""
        fb_settings = self.db.query(FacebookSettings).filter(
            FacebookSettings.client.ilike("%1%")
        ).first()
        
        if fb_settings:
            self._access_token = fb_settings.page_access_token
            self._ad_account_id = fb_settings.ad_account_id
            self._page_id = fb_settings.page_id
            self._ad_set_id = fb_settings.ad_set_id
        else:
            # Fall back to config settings
            self._access_token = self.settings.FACEBOOK_PAGE_ACCESS_TOKEN
            self._ad_account_id = self.settings.FACEBOOK_AD_ACCOUNT_ID
            self._page_id = self.settings.FACEBOOK_PAGE_ID
            self._ad_set_id = self.settings.FACEBOOK_AD_SET_ID
        
        print(f"pageaccesstoken=={self._access_token}")
    
    def post_image_ad(self, image_path: str, message: str, link_url: str) -> Optional[str]:
        """
        Create and post an image ad to Facebook.
        
        Args:
            image_path: Local path to the image file
            message: Ad message/copy
            link_url: Destination URL for the ad
            
        Returns:
            Ad ID if successful, None otherwise
        """
        try:
            image_hash = self._upload_image(image_path)
            if not image_hash:
                print("Failed to upload image")
                return None
                
            creative_id = self._create_ad_creative(image_hash, message, link_url)
            if not creative_id:
                print("Failed to create ad creative")
                return None
                
            return self._create_ad(creative_id)
            
        except Exception as e:
            print(f"Error creating ad: {e}")
            return None
    
    def _upload_image(self, image_path: str) -> Optional[str]:
        """
        Upload an image to Facebook Ads account.
        
        Args:
            image_path: Local path to the image
            
        Returns:
            Image hash if successful, None otherwise
        """
        self._load_credentials()
        
        url = f"https://graph.facebook.com/v19.0/{self._ad_account_id}/adimages?access_token={self._access_token}"
        
        image_file = Path(image_path)
        if not image_file.exists():
            print(f"Image file not found: {image_path}")
            return None
        
        try:
            with httpx.Client() as client:
                with open(image_path, "rb") as f:
                    files = {"filename": (image_file.name, f, "image/png")}
                    response = client.post(url, files=files)
                    response.raise_for_status()
                    
                    data = response.json()
                    images = data.get("images", {})
                    
                    # Get the first image hash
                    for img_data in images.values():
                        return img_data.get("hash")
                        
        except Exception as e:
            print(f"Error uploading image: {e}")
        
        return None
    
    def _create_ad_creative(self, image_hash: str, message: str, link_url: str) -> Optional[str]:
        """
        Create an ad creative with the uploaded image.
        
        Args:
            image_hash: Hash of the uploaded image
            message: Ad message
            link_url: Destination URL
            
        Returns:
            Creative ID if successful, None otherwise
        """
        self._load_credentials()
        
        url = f"https://graph.facebook.com/v19.0/{self._ad_account_id}/adcreatives"
        
        payload = {
            "name": "Python SDK Ad",
            "object_story_spec": {
                "page_id": self._page_id,
                "link_data": {
                    "image_hash": image_hash,
                    "link": link_url,
                    "message": message
                }
            },
            "access_token": self._access_token
        }
        
        print(f"pageaccesstoken=={self._access_token}")
        
        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                return response.json().get("id")
                
        except Exception as e:
            print(f"Error creating ad creative: {e}")
        
        return None
    
    def _create_ad(self, creative_id: str) -> Optional[str]:
        """
        Create an ad using the creative.
        
        Args:
            creative_id: ID of the ad creative
            
        Returns:
            Ad ID if successful, None otherwise
        """
        self._load_credentials()
        
        url = f"https://graph.facebook.com/v19.0/{self._ad_account_id}/ads"
        
        payload = {
            "name": "Ad created from Python FastAPI",
            "adset_id": self._ad_set_id,
            "creative": {"creative_id": creative_id},
            "status": "PAUSED",  # Set to "ACTIVE" to publish
            "access_token": self._access_token
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                ad_id = response.json().get("id")
                print(f"Ad created with ID: {ad_id}")
                return ad_id
                
        except Exception as e:
            print(f"Error creating ad: {e}")
        
        return None
