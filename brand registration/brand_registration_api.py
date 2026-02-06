"""
Brand Registration API Module
Handles brand registration data including file uploads and settings
"""

import os
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from datetime import datetime

# Create router for brand registration endpoints
router = APIRouter(prefix="/api/brand-registration", tags=["brand-registration"])

# Data models
class BrandSettings(BaseModel):
    defaultLanguage: str = "en"
    defaultLLM: str = "gpt-4.1"
    productDefaultPct: int = 30

class VoiceProfile(BaseModel):
    formality: int = 30
    humor: int = 60
    warmth: int = 70
    emojiPolicy: str = "medium"

class ContentPillar(BaseModel):
    name: str
    description: str
    weight: int

class BrandPolicies(BaseModel):
    forbiddenPhrases: list[str] = []
    maxHashtags: int = 5
    brandHashtags: list[str] = []

class BrandBlueprint(BaseModel):
    version: str = "1.0.0"
    status: str = "draft"
    voice: VoiceProfile = VoiceProfile()
    pillars: list[ContentPillar] = []
    policies: BrandPolicies = BrandPolicies()
    productDefaultPct: int = 30

class BrandRegistrationData(BaseModel):
    id: str
    name: str
    guidelineDoc: Dict[str, Any] = {"name": "", "size": 0, "status": "none"}
    blueprint: BrandBlueprint = BrandBlueprint()
    settings: BrandSettings = BrandSettings()
    createdAt: str
    updatedAt: str

class BrandRegistrationService:
    """Service class to handle brand registration operations"""
    
    def __init__(self, data_file: str = "brand_registrations.json"):
        self.data_file = Path(data_file)
        self.upload_dir = Path("brand registration/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_data(self) -> Dict[str, Any]:
        """Load brand registration data from JSON file"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"brands": {}}
        return {"brands": {}}
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save brand registration data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise HTTPException(status_code=500, detail=f"Failed to save data: {str(e)}")
    
    def create_brand(self, brand_data: BrandRegistrationData) -> Dict[str, Any]:
        """Create a new brand registration"""
        data = self._load_data()
        
        # Generate unique ID if not provided
        if not brand_data.id:
            brand_data.id = f"brand-{int(time.time())}"
        
        # Set timestamps
        now = datetime.now().isoformat()
        brand_data.createdAt = now
        brand_data.updatedAt = now
        
        # Save to data store
        data["brands"][brand_data.id] = brand_data.dict()
        self._save_data(data)
        
        return {"success": True, "brand_id": brand_data.id, "data": brand_data.dict()}
    
    def update_brand(self, brand_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing brand registration"""
        data = self._load_data()
        
        if brand_id not in data["brands"]:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        # Update the brand data
        brand_data = data["brands"][brand_id]
        brand_data.update(updates)
        brand_data["updatedAt"] = datetime.now().isoformat()
        
        self._save_data(data)
        
        return {"success": True, "brand_id": brand_id, "data": brand_data}
    
    def get_brand(self, brand_id: str) -> Dict[str, Any]:
        """Get brand registration by ID"""
        data = self._load_data()
        
        if brand_id not in data["brands"]:
            raise HTTPException(status_code=404, detail="Brand not found")
        
        return data["brands"][brand_id]
    
    def list_brands(self) -> Dict[str, Any]:
        """List all brand registrations"""
        data = self._load_data()
        return {"brands": list(data["brands"].values())}
    
    def save_uploaded_file(self, file: UploadFile, brand_id: str) -> Dict[str, Any]:
        """Save uploaded brand guideline file"""
        # Create brand-specific upload directory
        brand_upload_dir = self.upload_dir / brand_id
        brand_upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = int(time.time())
        file_extension = Path(file.filename).suffix
        safe_filename = f"guideline_{timestamp}{file_extension}"
        file_path = brand_upload_dir / safe_filename
        
        try:
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            return {
                "success": True,
                "filename": safe_filename,
                "original_name": file.filename,
                "size": file_path.stat().st_size,
                "path": str(file_path),
                "upload_time": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

# Initialize service
brand_service = BrandRegistrationService()

def handle_guideline_upload(event):
    file = event.target.files[0]
    reader = PdfReader(file)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + '\n'
    extracted_info = parse_guidelines(text)
    save_to_json(extracted_info)


def parse_guidelines(text):
    # Implement your parsing logic here
    return extracted_info


def save_to_json(data):
    with open('brand_guidelines.json', 'w') as json_file:
        json.dump(data, json_file)

@router.post("/upload-guideline/{brand_id}")
async def upload_brand_guideline(
    brand_id: str,
    file: UploadFile = File(...)
):
    """Upload brand guideline document"""
    # Validate file type
    allowed_extensions = {'.pdf', '.docx', '.doc'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail="Only PDF and DOCX files are allowed"
        )
    
    # Check file size (50MB limit)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 50MB limit"
        )
    
    # Save file
    file_info = brand_service.save_uploaded_file(file, brand_id)
    
    # Update brand data with file info
    try:
        brand_service.update_brand(brand_id, {
            "guidelineDoc": {
                "name": file_info["original_name"],
                "size": file_info["size"],
                "status": "uploaded",
                "path": file_info["path"],
                "uploadTime": file_info["upload_time"]
            }
        })
    except HTTPException as e:
        if e.status_code == 404:
            # Brand doesn't exist, create it
            now = datetime.now().isoformat()
            brand_data = BrandRegistrationData(
                id=brand_id,
                name=f"Brand {brand_id}",
                guidelineDoc={
                    "name": file_info["original_name"],
                    "size": file_info["size"],
                    "status": "uploaded",
                    "path": file_info["path"],
                    "uploadTime": file_info["upload_time"]
                },
                createdAt=now,
                updatedAt=now
            )
            brand_service.create_brand(brand_data)
        else:
            raise e
    
    return file_info

@router.post("/save-settings/{brand_id}")
async def save_brand_settings(
    brand_id: str,
    settings: BrandSettings
):
    """Save brand default settings"""
    try:
        result = brand_service.update_brand(brand_id, {
            "settings": settings.dict()
        })
        return result
    except HTTPException as e:
        if e.status_code == 404:
            # Brand doesn't exist, create it
            now = datetime.now().isoformat()
            brand_data = BrandRegistrationData(
                id=brand_id,
                name=f"Brand {brand_id}",
                settings=settings,
                createdAt=now,
                updatedAt=now
            )
            return brand_service.create_brand(brand_data)
        else:
            raise e

@router.post("/save-blueprint/{brand_id}")
async def save_brand_blueprint(
    brand_id: str,
    blueprint: BrandBlueprint
):
    """Save brand content blueprint"""
    try:
        result = brand_service.update_brand(brand_id, {
            "blueprint": blueprint.dict()
        })
        return result
    except HTTPException as e:
        if e.status_code == 404:
            # Brand doesn't exist, create it
            now = datetime.now().isoformat()
            brand_data = BrandRegistrationData(
                id=brand_id,
                name=f"Brand {brand_id}",
                blueprint=blueprint,
                createdAt=now,
                updatedAt=now
            )
            return brand_service.create_brand(brand_data)
        else:
            raise e

@router.get("/brand/{brand_id}")
async def get_brand_data(brand_id: str):
    """Get brand registration data"""
    return brand_service.get_brand(brand_id)

@router.get("/brands")
async def list_all_brands():
    """List all brand registrations"""
    return brand_service.list_brands()

@router.post("/create-brand")
async def create_new_brand(brand_data: BrandRegistrationData):
    """Create a new brand registration"""
    return brand_service.create_brand(brand_data)

@router.put("/update-brand/{brand_id}")
async def update_brand_data(brand_id: str, updates: Dict[str, Any]):
    """Update brand registration data"""
    return brand_service.update_brand(brand_id, updates)

@router.get("/export-json/{brand_id}")
async def export_brand_json(brand_id: str):
    """Export complete brand data as JSON file"""
    try:
        brand_data = brand_service.get_brand(brand_id)
        
        # Create export data structure
        export_data = {
            "brand": brand_data,
            "exportedAt": datetime.now().isoformat(),
            "exportVersion": "1.0.0",
            "description": "Complete brand content management data export"
        }
        
        # Create filename
        filename = f"brand-content-data-{brand_id}-{datetime.now().strftime('%Y-%m-%d')}.json"
        
        # Return JSON response with download headers
        from fastapi.responses import JSONResponse
        response = JSONResponse(content=export_data)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "application/json"
        
        return response
        
    except HTTPException:
        raise HTTPException(status_code=404, detail="Brand not found")

@router.delete("/brand/{brand_id}")
async def delete_brand(brand_id: str):
    """Delete brand registration"""
    data = brand_service._load_data()
    
    if brand_id not in data["brands"]:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Remove brand data
    del data["brands"][brand_id]
    brand_service._save_data(data)
    
    # Clean up uploaded files
    brand_upload_dir = brand_service.upload_dir / brand_id
    if brand_upload_dir.exists():
        shutil.rmtree(brand_upload_dir)
    
    return {"success": True, "message": f"Brand {brand_id} deleted successfully"}