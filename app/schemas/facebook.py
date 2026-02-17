from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class FacebookPostCreate(BaseModel):
    message: str = Field(..., description="Text content of the post")
    link: Optional[str] = Field(None, description="Optional link to include")

class FacebookPhotoCreate(BaseModel):
    caption: Optional[str] = None
    url: str

class FacebookVideoCreate(BaseModel):
    description: Optional[str] = None
    file_path: str  # Assuming local file path or URL for internal processing

class FacebookStoryCreate(BaseModel):
    media_url: str

class FacebookPollCreate(BaseModel):
    question: str
    options: List[str]

class FacebookStatusResponse(BaseModel):
    connected: bool
    brand_id: str
    page_name: Optional[str] = None
    permissions: List[str] = []
    token_expiry: Optional[datetime] = None

class FacebookPageInfo(BaseModel):
    id: str
    name: str
    access_token: str
    category: Optional[str] = None
