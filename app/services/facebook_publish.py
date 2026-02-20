import httpx
import os
from typing import Dict, Any, Optional, List

GRAPH_API_VERSION = "v18.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

class FacebookPublishService:
    """Handles publishing content to Facebook Pages via Graph API."""

    async def publish_text_post(self, page_id: str, page_access_token: str, message: str, link: Optional[str] = None) -> Dict[str, Any]:
        """Publish a text-based post to the page feed."""
        url = f"{BASE_URL}/{page_id}/feed"
        payload = {
            "message": message,
            "access_token": page_access_token
        }
        if link:
            payload["link"] = link
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload)
            response.raise_for_status()
            return response.json()

    async def publish_photo(self, page_id: str, page_access_token: str, photo_url: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Publish a photo to the page."""
        url = f"{BASE_URL}/{page_id}/photos"
        payload = {
            "url": photo_url,
            "access_token": page_access_token
        }
        if caption:
            payload["caption"] = caption
            
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload)
            response.raise_for_status()
            return response.json()

    async def publish_video(self, page_id: str, page_access_token: str, video_url: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Publish a video. Note: For large videos, a resumable upload flow is recommended."""
        url = f"{BASE_URL}/{page_id}/videos"
        # v18.0 supports file_url for video uploads
        payload = {
            "file_url": video_url,
            "description": description or "",
            "access_token": page_access_token
        }
            
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload)
            response.raise_for_status()
            return response.json()

    async def publish_story(self, page_id: str, page_access_token: str, media_url: str) -> Dict[str, Any]:
        """Publish a story. This often uses the same photo/video endpoints with story-specific flags."""
        # This implementation follows the common pattern for stories in v18.0
        # Specific story endpoints may vary by account eligibility
        url = f"{BASE_URL}/{page_id}/photos"
        payload = {
            "url": media_url,
            "access_token": page_access_token,
            "published": "false", # For stories, often uploaded as unpublished first
            "target_type": "STORY"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload)
            response.raise_for_status()
            return response.json()

    async def publish_poll(self, page_id: str, page_access_token: str, question: str, options: List[str]) -> Dict[str, Any]:
        """Simulation of a poll if native API is restricted."""
        # Native Facebook Poll API is often restricted to specific page types or via interactive posts
        # Simulating via a structured post if native is unavailable
        message = f"POLL: {question}\n\n" + "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        return await self.publish_text_post(page_id, page_access_token, message)
