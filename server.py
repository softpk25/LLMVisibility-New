import os
import json
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
from dotenv import load_dotenv
from app.database import init_db

# Import the ImageRater from the inspire me/newimg.py
# We need to add the directory to sys.path to import it
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'inspire me'))
from newimg import ImageRater

# Import brand registration API
sys.path.append(os.path.join(os.path.dirname(__file__), 'brand registration'))
from brand_registration_api import router as brand_router

# Import brand blueprint router
from app.main import blueprint_router

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'inspire me', '.env'))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing brand blueprint database...")
    init_db()
    print("Brand blueprint database initialized successfully.")
    
    # Ensure uploads directory exists
    uploads_dir = Path("uploads/guidelines")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured uploads directory exists: {uploads_dir}")
    
    yield
    
    # Shutdown (if needed in future)
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include brand registration router
app.include_router(brand_router)

# Include brand blueprint router
app.include_router(blueprint_router)

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
    uvicorn.run(app, host="0.0.0.0", port=8000)
