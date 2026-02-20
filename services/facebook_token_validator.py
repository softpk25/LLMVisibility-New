"""
Facebook Token Validation Service
Validates and provides helpful error messages for expired/invalid tokens
"""

import httpx
from typing import Dict, Optional, Tuple
from config import get_settings


class FacebookTokenValidator:
    """Service for validating Facebook access tokens"""
    
    def __init__(self):
        self.settings = get_settings()
        self.graph_api_url = self.settings.FACEBOOK_GRAPH_API_URL
    
    def validate_token(self, access_token: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate a Facebook access token.
        
        Args:
            access_token: The access token to validate
            
        Returns:
            Tuple of (is_valid, error_message, token_info)
        """
        if not access_token:
            return False, "Access token is empty", None
        
        url = f"{self.graph_api_url}/me?access_token={access_token}"
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    return True, None, data
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error = error_data.get("error", {})
                    error_code = error.get("code")
                    error_message = error.get("message", "Unknown error")
                    error_subcode = error.get("error_subcode")
                    
                    # Provide user-friendly error messages
                    if error_code == 190:
                        if error_subcode == 467:
                            return False, "Access token expired. The user logged out or the token is invalid. Please reconnect your Facebook account or update the token in .env file.", None
                        else:
                            return False, f"Access token is invalid or expired. Error: {error_message}", None
                    elif error_code == 102:
                        return False, "Access token is invalid. Please check your token configuration.", None
                    else:
                        return False, f"Token validation failed: {error_message} (Code: {error_code})", None
                        
        except httpx.HTTPError as e:
            return False, f"Network error validating token: {str(e)}", None
        except Exception as e:
            return False, f"Error validating token: {str(e)}", None
    
    def validate_page_token(self, page_id: str, page_access_token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a page access token by checking if we can access the page.
        
        Args:
            page_id: The Facebook page ID
            page_access_token: The page access token
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not page_access_token or not page_id:
            return False, "Page access token or page ID is missing"
        
        url = f"{self.graph_api_url}/{page_id}?fields=id,name&access_token={page_access_token}"
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                
                if response.status_code == 200:
                    return True, None
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error = error_data.get("error", {})
                    error_code = error.get("code")
                    error_message = error.get("message", "Unknown error")
                    error_subcode = error.get("error_subcode")
                    
                    if error_code == 190 and error_subcode == 467:
                        return False, "Page access token expired. Please reconnect your Facebook account or update the token."
                    else:
                        return False, f"Page token validation failed: {error_message}"
                        
        except Exception as e:
            return False, f"Error validating page token: {str(e)}"
