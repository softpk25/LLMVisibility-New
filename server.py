import os
import json
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Import the ImageRater from the inspire me/newimg.py
# We need to add the directory to sys.path to import it
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'inspire me'))
from newimg import ImageRater

# Load environment variables from root .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
# Import brand registration API
sys.path.append(os.path.join(os.path.dirname(__file__), 'brand registration'))
from brand_registration_api import router as brand_router

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), 'inspire me', '.env'))

app = FastAPI()

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

# Create creative_briefs directory if it doesn't exist
Path("creative_briefs").mkdir(exist_ok=True)

# Mount generated directory
app.mount("/generated", StaticFiles(directory="generated"), name="generated")

@app.post("/api/save-brief")
async def save_brief(brief_data: dict):
    """Save creative brief data to JSON file"""
    try:
        # Generate filename with timestamp
        timestamp = int(time.time())
        creative_type = brief_data.get("creative_type", "unknown")
        filename = f"brief_{creative_type}_{timestamp}.json"
        
        brief_path = Path("creative_briefs") / filename
        
        with open(brief_path, "w", encoding="utf-8") as f:
            json.dump(brief_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "filename": filename,
            "path": str(brief_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transform-image")
async def transform_image(
    base_image: UploadFile = File(...),
    reference_image: UploadFile = File(...),
    prompt: str = Form(None),
    analysis_json: str = Form(None),
    custom_instructions: str = Form(None)
):
    """
    Transform a base image using a reference image and prompt with gpt-image-1.
    
    Args:
        base_image: The original image to transform
        reference_image: The reference image to incorporate
        prompt: Direct prompt for transformation (optional if analysis_json provided)
        analysis_json: JSON string from image analysis (optional, will extract prompt_reconstruction)
        custom_instructions: Additional transformation instructions
    """
    if not rater:
        raise HTTPException(status_code=500, detail="Server not configured with OpenAI API Key")
    
    # Create temp directory for uploaded files
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    # Create output directory
    transformed_dir = Path("transformed")
    transformed_dir.mkdir(exist_ok=True)
    
    try:
        # Save base image temporarily
        base_path = temp_dir / f"base_{int(time.time())}_{base_image.filename}"
        with open(base_path, "wb") as buffer:
            shutil.copyfileobj(base_image.file, buffer)
        
        # Save reference image temporarily
        ref_path = temp_dir / f"ref_{int(time.time())}_{reference_image.filename}"
        with open(ref_path, "wb") as buffer:
            shutil.copyfileobj(reference_image.file, buffer)
        
        # Generate output path
        timestamp = int(time.time())
        output_filename = f"transformed_{timestamp}.png"
        output_path = transformed_dir / output_filename
        
        # Determine which method to use
        if analysis_json:
            # Parse analysis JSON and use transform_from_analysis
            try:
                analysis_data = json.loads(analysis_json)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid analysis_json format")
            
            result = rater.transform_from_analysis(
                base_image_path=base_path,
                reference_image_path=ref_path,
                analysis_json=analysis_data,
                output_path=output_path,
                custom_instructions=custom_instructions
            )
        elif prompt:
            # Use direct prompt
            result = rater.transform_image_with_reference(
                base_image_path=base_path,
                reference_image_path=ref_path,
                prompt=prompt,
                output_path=output_path,
                transformation_instructions=custom_instructions
            )
        else:
            raise HTTPException(status_code=400, detail="Either prompt or analysis_json is required")
        
        # Clean up temp files
        if base_path.exists():
            os.remove(base_path)
        if ref_path.exists():
            os.remove(ref_path)
        
        if result.get("success"):
            return {
                "success": True,
                "image_url": f"/transformed/{output_filename}",
                "local_path": str(output_path),
                "prompt_used": result.get("prompt_used", "")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
            
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if 'base_path' in locals() and base_path.exists():
            os.remove(base_path)
        if 'ref_path' in locals() and ref_path.exists():
            os.remove(ref_path)
        raise HTTPException(status_code=500, detail=str(e))

# Mount transformed directory
Path("transformed").mkdir(exist_ok=True)
app.mount("/transformed", StaticFiles(directory="transformed"), name="transformed")


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
        
        # Save image for later transformation use
        try:
            analyzed_images_dir = Path("analyzed_images")
            analyzed_images_dir.mkdir(exist_ok=True)
            
            # Store with same naming as the analysis JSON
            image_ext = Path(file.filename).suffix or ".jpg"
            stored_image_path = analyzed_images_dir / f"{safe_stem}_{timestamp}{image_ext}"
            shutil.copy(temp_path, stored_image_path)
            
            # Add stored path to result
            if isinstance(result, dict):
                result["stored_image_path"] = str(stored_image_path)
                result["stored_image_url"] = f"/analyzed_images/{stored_image_path.name}"
        except Exception as e:
            if isinstance(result, dict):
                result.setdefault("image_save_error", str(e))
        
        # Clean up temp file
        os.remove(temp_path)
        
        return result
        
    except Exception as e:
        if temp_path.exists():
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

# Mount analyzed_images directory
Path("analyzed_images").mkdir(exist_ok=True)
app.mount("/analyzed_images", StaticFiles(directory="analyzed_images"), name="analyzed_images")

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
