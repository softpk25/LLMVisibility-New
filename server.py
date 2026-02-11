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
from typing import Optional, List

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


from fastapi.concurrency import run_in_threadpool

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
            
        # Get description for image
        # Run rater in threadpool as it uses OpenAI sync client
        result = await run_in_threadpool(rater.get_image_description, temp_path)
            
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
            try:
                os.remove(temp_path)
            except:
                pass
        # Log the full error for debugging
        print(f"Error in analyze_image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-video")
async def analyze_video_endpoint(file: UploadFile = File(...)):
    """
    Endpoint specifically for analyzing video files.
    """
    # Save uploaded file temporarily
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
             raise HTTPException(status_code=400, detail="Invalid video file format")

        # Import on demand to avoid circular imports or startup issues if not used
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), 'inspire me', 'video gen'))
            from videounderstand import analyze_video
        except ImportError as e:
            raise HTTPException(status_code=500, detail=f"Could not import videounderstand: {e}")

        # Analyze video in threadpool to avoid blocking event loop
        video_prompt = await run_in_threadpool(analyze_video, str(temp_path))
        
        # Construct a response that mimics the image analysis structure so frontend doesn't break
        result = {
            "analysis": {
                "visual_dna": {
                    "composition": "Video content",
                    "palette": "Dynamic video palette",
                    "lighting": "Video lighting",
                    "style": "Video style"
                },
                "strategic_analysis": {
                    "tone": "Video tone",
                    "cta_style": "Video CTA",
                    "emotional_angle": "Video emotion",
                    "audience": "Video audience"
                },
                "image_composition_analysis": {
                    "focal_points": "Video subjects",
                    "typography_style": "N/A"
                },
                "prompt_reconstruction": video_prompt
            }
        }
        
        # Clean up temp file
        os.remove(temp_path)
        
        return result

    except Exception as e:
        if temp_path.exists():
             try:
                os.remove(temp_path)
             except:
                pass
        print(f"Error in analyze_video_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount analyzed_images directory
Path("analyzed_images").mkdir(exist_ok=True)
app.mount("/analyzed_images", StaticFiles(directory="analyzed_images"), name="analyzed_images")



# Import video processor
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), 'inspire me', 'video gen'))
    from video_processor import process_creative_request
except ImportError as e:
    print(f"Warning: Could not import video_processor: {e}")

@app.post("/api/generate-video")
async def generate_video_endpoint(
    file: UploadFile = File(...),
    instructions: str = Form(None),
    creative_type: str = Form("reel") # 'reel' or 'gif'
):
    """
    Endpoint to generate video from uploaded image or video. yay
    """
    # Create temp directory for uploads
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    
    # Save uploaded file
    file_ext = Path(file.filename).suffix
    temp_filename = f"upload_{int(time.time())}{file_ext}"
    temp_path = temp_dir / temp_filename
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Determine file type
        file_type = "image"
        if file_ext.lower() in ['.mp4', '.mov', '.avi']:
            file_type = "video"
            
        # Define output path
        generated_dir = Path("generated")
        generated_dir.mkdir(exist_ok=True)
        output_filename = f"gen_video_{int(time.time())}.mp4"
        output_path = generated_dir / output_filename
        
        # Process request
        # Run in threadpool to avoid blocking
        result = await run_in_threadpool(
            process_creative_request,
            file_path=str(temp_path),
            file_type=file_type,
            instructions=instructions or "",
            output_path=str(output_path)
        )
        
        # Clean up temp input
        if temp_path.exists():
            os.remove(temp_path)
            
        if result.get("success"):
            return {
                "success": True,
                "video_url": f"/generated/{output_filename}",
                "analysis": result.get("analysis_text"),
                "prompt": result.get("final_prompt"),
                "prompt_json": result.get("prompt_json"),
                "analysis_data": result.get("analysis_data")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        if temp_path.exists():
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-carousel")
async def generate_carousel_endpoint(
    file: Optional[UploadFile] = File(None),
    instructions: str = Form(...),
    panel_count: int = Form(3)
):
    """
    Endpoint to generate a carousel (sequence of images)
    """
    if not rater:
          raise HTTPException(status_code=500, detail="Server not configured")
    
    # Save uploaded file temporarily (optional)
    temp_path = None
    if file:
        temp_dir = Path("temp_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / file.filename
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            print(f"Error saving temp file: {e}")
            temp_path = None
            
    try:
        # 1. Generate prompts
        # Run in threadpool
        prompts = await run_in_threadpool(
            rater.generate_carousel_prompts,
            base_image_path=str(temp_path) if temp_path else None,
            instructions=instructions,
            count=panel_count
        )
        
        if not prompts:
             raise HTTPException(status_code=500, detail="Failed to generate storyboard prompts")
             
        # 2. Generate images for each prompt
        image_urls = []
        generated_dir = Path("generated")
        generated_dir.mkdir(exist_ok=True)
        
        for i, prompt in enumerate(prompts):
            output_filename = f"carousel_{int(time.time())}_{i+1}.png"
            output_path = generated_dir / output_filename
            
            # Call DALL-E (in threadpool for concurrency if possible, but serial here is safer for rate limits)
            # Actually, DALL-E 3 has simple rate limits, serial is fine
            result = await run_in_threadpool(
                rater.generate_image_dalle,
                prompt=prompt,
                output_path=str(output_path)
            )
            
            if result.get("success"):
                image_urls.append(f"/generated/{output_filename}")
            else:
                print(f"Failed to generate panel {i+1}: {result.get('error')}")
                # We optionally continue or fail? Let's continue and return what we have
                
        if not image_urls:
            raise HTTPException(status_code=500, detail="Failed to generate any images")
            
        return {
            "success": True,
            "image_urls": image_urls,
            "prompts": prompts
        }
        
    finally:
        if temp_path and temp_path.exists():
            try:
                os.remove(temp_path)
            except:
                pass


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
