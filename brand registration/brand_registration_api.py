"""
Brand Registration API Module
Handles brand registration data including file uploads and settings
"""

import os
import json
import time
import shutil
import re
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from datetime import datetime

try:
    # Lightweight PDF parsing for text extraction
    from PyPDF2 import PdfReader  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    PdfReader = None  # type: ignore

try:
    # Optional DOCX support
    import docx  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    docx = None  # type: ignore

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


def _extract_text_from_guideline(path: Path) -> str:
    """
    Best-effort text extraction from an uploaded guideline document.
    - PDF: uses PyPDF2 if available
    - DOCX: uses python-docx if available
    If the required parser is not installed, returns an empty string so that
    upload still succeeds and the UI can function normally.
    """
    suffix = path.suffix.lower()

    try:
        if suffix == ".pdf" and PdfReader is not None:
            text_parts = []
            with open(path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
            return "\n".join(text_parts)

        if suffix in {".docx", ".doc"} and docx is not None:
            # python-docx cannot read legacy .doc files, but this at least
            # works for modern .docx guidelines.
            document = docx.Document(str(path))
            return "\n".join(p.text for p in document.paragraphs if p.text.strip())
    except Exception:
        # Parsing issues should never break the upload flow
        return ""

    return ""


def _infer_voice_profile(text: str) -> VoiceProfile:
    """Derive a rough voice profile from free-form guideline text."""
    lowered = text.lower()

    # Defaults
    formality = 50
    humor = 40
    warmth = 60

    # Formality
    if re.search(r"\bformal\b|\bprofessional\b", lowered):
        formality = 80
    elif re.search(r"\bcasual\b|\bconversational\b|\brelaxed\b", lowered):
        formality = 30

    # Humor
    if re.search(r"\bserious\b|\bno jokes\b|\bno humor\b", lowered):
        humor = 20
    elif re.search(r"\bplayful\b|\bfun\b|\bhumorous\b|\bquirky\b", lowered):
        humor = 70

    # Warmth
    if re.search(r"\bwarm\b|\bfriendly\b|\bapproachable\b|\bempathetic\b", lowered):
        warmth = 80
    elif re.search(r"\bclinical\b|\bimpersonal\b|\bcorporate\b", lowered):
        warmth = 40

    # Emoji policy
    emoji_policy = "medium"
    if re.search(r"\bno emojis\b|\bavoid emojis\b|\bwithout emojis\b", lowered):
        emoji_policy = "none"
    elif re.search(r"\bsparingly\b.*emoji|\blight use of emojis\b", lowered):
        emoji_policy = "light"
    elif re.search(r"\bemoji[- ]rich\b|\bheavy use of emojis\b", lowered):
        emoji_policy = "rich"

    return VoiceProfile(
        formality=formality,
        humor=humor,
        warmth=warmth,
        emojiPolicy=emoji_policy,
    )


def _infer_product_share(text: str, default_pct: int = 30) -> int:
    """
    Try to infer 'what share of posts should include the product' from text,
    e.g. '70% of posts can be product-led'.
    """
    match = re.search(r"(\d{1,2})\s*%[^.\n]{0,80}\bproduct", text, flags=re.IGNORECASE)
    if match:
        try:
            value = int(match.group(1))
            if 0 <= value <= 100:
                return value
        except ValueError:
            pass
    return default_pct


def _infer_pillars(text: str) -> list[ContentPillar]:
    """
    Build a set of content pillars from bullet-style lines in the guideline.
    This is heuristic but gives the user a helpful starting point.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullet_lines = [
        ln for ln in lines if ln.startswith(("-", "•", "*", "·"))
    ]

    pillars: list[ContentPillar] = []

    for ln in bullet_lines:
        # Strip the bullet character
        clean = ln.lstrip("-•*·").strip()
        if not clean:
            continue

        name = clean
        description = ""

        # Split "Name – Description" or "Name: Description"
        for sep in (" - ", " – ", " — ", ": "):
            if sep in clean:
                name, description = [part.strip() for part in clean.split(sep, 1)]
                break

        # Avoid obviously non-pillar lines (too short)
        if len(name) < 3:
            continue

        pillars.append(
            ContentPillar(
                name=name,
                description=description,
                weight=0,
            )
        )

        if len(pillars) >= 8:
            break

    # If we didn't find any, return an empty list and fall back to defaults
    return pillars


def _infer_policies(text: str) -> BrandPolicies:
    """
    Extract basic guardrails:
    - forbidden phrases from quoted strings after 'avoid', 'do not', 'never say'
    - brand hashtags from text like '#BrandName'
    """
    lowered = text.lower()

    # Forbidden phrases in quotes after common guardrail verbs
    forbidden: list[str] = []
    guardrail_matches = re.finditer(
        r"(avoid|do not|never say)[^\"'\n]*[\"']([^\"']+)[\"']",
        lowered,
        flags=re.IGNORECASE,
    )
    for m in guardrail_matches:
        phrase = m.group(2).strip()
        if phrase and phrase not in forbidden:
            forbidden.append(phrase)

    # Brand hashtags
    hashtags = sorted(
        {tag for tag in re.findall(r"#\w+", text) if len(tag) > 1}
    )

    # Reasonable default cap on hashtags
    max_hashtags = 5

    return BrandPolicies(
        forbiddenPhrases=forbidden,
        maxHashtags=max_hashtags,
        brandHashtags=hashtags[:30],
    )


def parse_guidelines_to_blueprint(
    text: str, existing_blueprint: Optional[Dict[str, Any]] = None
) -> Optional[BrandBlueprint]:
    """
    Convert free-form guideline text into a draft BrandBlueprint.
    This is intentionally heuristic but gives the Blueprint page a useful
    auto-filled starting point that the user can refine.
    """
    if not text or not text.strip():
        return None

    # Start from existing blueprint if we have one, otherwise defaults
    if isinstance(existing_blueprint, dict):
        base = BrandBlueprint(**existing_blueprint)
    else:
        base = BrandBlueprint()

    voice = _infer_voice_profile(text)
    product_pct = _infer_product_share(text, default_pct=base.productDefaultPct)
    pillars = _infer_pillars(text)
    policies = _infer_policies(text)

    # If we didn't infer any pillars, keep existing ones
    if not pillars:
        pillars = base.pillars

    return BrandBlueprint(
        version=base.version,
        status="generated-from-doc",
        voice=voice,
        pillars=pillars,
        policies=policies,
        productDefaultPct=product_pct,
    )

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

    # Best-effort parse of the uploaded document into a draft blueprint
    extracted_text = _extract_text_from_guideline(Path(file_info["path"]))

    existing_blueprint_dict: Optional[Dict[str, Any]] = None
    try:
        existing_brand = brand_service.get_brand(brand_id)
        existing_blueprint_dict = existing_brand.get("blueprint")  # type: ignore[attr-defined]
    except HTTPException as e:
        if e.status_code != 404:
            raise

    generated_blueprint = parse_guidelines_to_blueprint(
        extracted_text, existing_blueprint=existing_blueprint_dict
    )

    # Prepare updates for brand record
    updates: Dict[str, Any] = {
        "guidelineDoc": {
            "name": file_info["original_name"],
            "size": file_info["size"],
            "status": "uploaded",
            "path": file_info["path"],
            "uploadTime": file_info["upload_time"]
        }
    }

    if generated_blueprint is not None:
        updates["blueprint"] = generated_blueprint.dict()

    # Update or create brand data with file + generated blueprint
    try:
        brand_service.update_brand(brand_id, updates)
    except HTTPException as e:
        if e.status_code == 404:
            # Brand doesn't exist, create it
            now = datetime.now().isoformat()
            brand_data = BrandRegistrationData(
                id=brand_id,
                name=f"Brand {brand_id}",
                guidelineDoc=updates["guidelineDoc"],
                blueprint=generated_blueprint or BrandBlueprint(),  # type: ignore[arg-type]
                createdAt=now,
                updatedAt=now
            )
            brand_service.create_brand(brand_data)
        else:
            raise e

    # Return file info plus any generated blueprint so the frontend can
    # immediately update the Blueprint page without an extra API call.
    response_payload = dict(file_info)
    if generated_blueprint is not None:
        response_payload["blueprint"] = generated_blueprint.dict()

    return response_payload

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