import os
import sys
import json
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, List

# Set base directories and environment variables FIRST
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["DATA_DIR"] = os.path.join(BASE_DIR, 'backend', 'data')
os.environ["UPLOAD_DIR"] = os.path.join(BASE_DIR, 'backend', 'uploads')

# Add all module paths to sys.path
backend_path = os.path.join(BASE_DIR, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

inspire_path = os.path.join(BASE_DIR, 'inspire me')
if inspire_path not in sys.path:
    sys.path.append(inspire_path)

brand_reg_path = os.path.join(BASE_DIR, 'brand registration')
if brand_reg_path not in sys.path:
    sys.path.append(brand_reg_path)

# Load environment variables
load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(inspire_path, '.env'))

# Initialize logging early
from core.logging_config import setup_logging
setup_logging()

# Now perform imports that might depend on environment or sys.path
try:
    from app.database import init_db as brand_init_db
except ImportError:
    brand_init_db = lambda: print("Warning: brand_init_db not found")

from core.db import init_db as settings_init_db, get_db
from newimg import ImageRater
from brand_registration_api import router as brand_router
try:
    from app.main import blueprint_router
except ImportError:
    from fastapi import APIRouter
    blueprint_router = APIRouter()
    print("Warning: blueprint_router (app.main) not found. Using empty router.")

from api.v1.router import api_router as campaign_api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Startup
        print("Initializing brand blueprint database...")
        brand_init_db()
        print("Brand blueprint database initialized.")
        
        print("Initializing settings database (SQLite)...")
        settings_init_db()
        print("Settings database initialized.")
        
        # Create necessary directories for Campaign module
        data_dir_path = os.environ.get("DATA_DIR", "data")
        data_dir = Path(data_dir_path)
        (data_dir / "campaigns").mkdir(parents=True, exist_ok=True)
        (data_dir / "brands").mkdir(parents=True, exist_ok=True)
        (data_dir / "settings").mkdir(parents=True, exist_ok=True)
        (data_dir / "inspire").mkdir(parents=True, exist_ok=True)
        (data_dir / "engage").mkdir(parents=True, exist_ok=True)
        
        # Ensure uploads directory exists
        upload_dir_path = os.environ.get("UPLOAD_DIR", "uploads")
        uploads_dir = Path(upload_dir_path)
        uploads_dir.mkdir(parents=True, exist_ok=True)
        (uploads_dir / "guidelines").mkdir(parents=True, exist_ok=True)
        
        print(f"Ensured campaign module data directories exist in {data_dir}")
        
        yield
        
        # Shutdown (if needed in future)
        print("Shutting down...")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(brand_router)
app.include_router(blueprint_router)
app.include_router(campaign_api_router, prefix="/api/v1")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import logging
    logger = logging.getLogger("uvicorn")
    logger.error(f"❌ Validation error at {request.url.path}: {exc.errors()}")
    try:
        body = await request.json()
        logger.error(f"📦 Request body: {json.dumps(body, indent=2)}")
    except:
        logger.error("📦 Could not parse request body as JSON")
    
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Initialize ImageRater
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Warning: OPENAI_API_KEY not found in environment variables.")

rater = None
if api_key:
    rater = ImageRater(api_key=api_key)

# Mount templates directory to serve static files if needed, 
# but for specific HTML file requests we might want endpoints.
# However, the requirement is to serve existing HTML. 
# We can mount the current directory to serve everything relative.
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.mount("/inspire me", StaticFiles(directory="inspire me"), name="inspire_me")

# Mount app/static for brand blueprint assets
app.mount("/brand-static", StaticFiles(directory="app/static"), name="brand_static")

@app.get("/facebook/callback")
async def facebook_callback_shortcut(
    request: Request,
    code: str, 
    state: str,
    conn=Depends(get_db)
):
    from api.v1.integrations import facebook_callback
    return await facebook_callback(request, code, state, conn)

@app.get("/routes")
async def get_routes():
    return [{"path": route.path, "name": route.name, "methods": route.methods} for route in app.routes]

@app.get("/")
async def root():
    return {"message": "Server is running"}

@app.get("/FACEBOOK-INSPIRE-ME.html", response_class=HTMLResponse)
async def read_item():
    with open("templates/FACEBOOK-INSPIRE-ME.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/FACEBOOK-BRAND-REGISTRATION.html", response_class=HTMLResponse)
async def read_brand_registration():
    with open("templates/FACEBOOK-BRAND-REGISTRATION.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/FACEBOOK-CREATE-CAMPAIGN.html", response_class=HTMLResponse)
async def read_create_campaign():
    with open("templates/FACEBOOK-CREATE-CAMPAIGN.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/FACEBOOK-SETTINGS.html", response_class=HTMLResponse)
async def read_settings():
    with open("templates/FACEBOOK-SETTINGS.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/FACEBOOK-ENGAGE-BOOST.html", response_class=HTMLResponse)
async def read_engage_boost():
    with open("templates/FACEBOOK-ENGAGE-BOOST.html", "r", encoding="utf-8") as f:
        return f.read()

from pydantic import BaseModel
import time

class GenerationRequest(BaseModel):
    prompt: str
    type: str = "image"

@app.post("/api/generate-creative")
async def generate_creative(request: GenerationRequest):
    if not rater:
        raise HTTPException(status_code=500, detail="Server not configured with OpenAI API Key")
    
    # Create generated directory if it doesn't exist
    generated_dir = Path("generated")
    generated_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = int(time.time())
    filename = f"generated_{timestamp}.png"
    output_path = generated_dir / filename
    
    # Generate image
    result = rater.generate_image_dalle(request.prompt, output_path)
    
    if result.get("success"):
        # Analyze the generated image and save structured JSON metadata
        try:
            analysis = rater.get_image_description(output_path)
        except Exception as e:
            analysis = {"error": f"failed_to_analyze_image: {str(e)}"}
        
        # Save analysis JSON next to the image using the same base name
        try:
            metadata_path = output_path.with_suffix(".json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # If saving fails, we still return success for the image itself
            analysis.setdefault("metadata_save_error", str(e))

        return {
            "success": True,
            "image_url": f"/generated/{filename}",
            "local_path": str(output_path),
            "revised_prompt": result.get("revised_prompt"),
            "analysis": analysis
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error"))

# Create generated directory if it doesn't exist
Path("generated").mkdir(exist_ok=True)

# Mount generated directory
app.mount("/generated", StaticFiles(directory="generated"), name="generated")

@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if not rater:
        raise HTTPException(status_code=500, detail="Server not configured with OpenAI API Key")
    
    # Save uploaded file temporarily
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Get description
        result = rater.get_image_description(temp_path)
        
        # Persist analysis JSON for later reuse / auditing
        try:
            analysis_dir = Path("image_analysis")
            analysis_dir.mkdir(exist_ok=True)
            
            # Use original filename stem plus timestamp to avoid collisions
            safe_stem = Path(file.filename).stem or "uploaded_image"
            timestamp = int(time.time())
            json_filename = f"{safe_stem}_{timestamp}.json"
            json_path = analysis_dir / json_filename
            
            payload = {
                "source_filename": file.filename,
                "analysis": result,
            }
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # Don't fail the endpoint if persistence has issues
            if isinstance(result, dict):
                result.setdefault("metadata_save_error", str(e))
        
        # Clean up
        os.remove(temp_path)
        
        return result
        
    except Exception as e:
        if temp_path.exists():
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    logger = logging.getLogger("uvicorn")
    logger.info("Starting server via python execution...")
    
    # Run server
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
