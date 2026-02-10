import os
import sys
import logging
import time

# Add parent directory to path to import neighboring modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the refactored modules
try:
    from videounderstand import analyze_video
    from videogeneration import generate_video
    # We need to import ImageRater from the parent directory's newimg module.
    # Adjusting path for that:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from newimg import ImageRater
except ImportError as e:
    logging.error(f"Failed to import modules: {e}")

# Load env variables for ImageRater
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def json_prompt_to_text(prompt_json):
    """
    Convert structured JSON prompt to a text prompt for video generation.

    Args:
        prompt_json (dict): Structured prompt with scene, subjects, style, etc.

    Returns:
        str: Formatted text prompt
    """
    import json

    parts = []

    # Scene
    if prompt_json.get("scene"):
        parts.append(f"Scene: {prompt_json['scene']}")

    # Subjects
    if prompt_json.get("subjects"):
        subject_descriptions = []
        for subj in prompt_json["subjects"]:
            desc = f"{subj.get('type', 'subject')}"
            if subj.get("description"):
                desc += f" - {subj['description']}"
            if subj.get("position"):
                desc += f" (positioned {subj['position']})"
            subject_descriptions.append(desc)
        parts.append("Subjects: " + ", ".join(subject_descriptions))

    # Style
    if prompt_json.get("style"):
        parts.append(f"Style: {prompt_json['style']}")

    # Color palette
    if prompt_json.get("color_palette"):
        colors = ", ".join(prompt_json["color_palette"])
        parts.append(f"Colors: {colors}")

    # Lighting
    if prompt_json.get("lighting"):
        parts.append(f"Lighting: {prompt_json['lighting']}")

    # Mood
    if prompt_json.get("mood"):
        parts.append(f"Mood: {prompt_json['mood']}")

    # Camera
    if prompt_json.get("camera"):
        parts.append(f"Camera: {prompt_json['camera']}")

    # Movement
    if prompt_json.get("movement"):
        parts.append(f"Movement: {prompt_json['movement']}")

    return ". ".join(parts)


def process_creative_request(file_path, file_type, instructions="", output_path="generated/output_video.mp4"):
    """
    Unified function to handle creative video generation requests.

    Args:
        file_path (str): Path to the uploaded inspiration file.
        file_type (str): 'image' or 'video'.
        instructions (str): User provided transformation instructions.
        output_path (str): Where to save the final video.

    Returns:
        dict: Result with 'success', 'video_path', 'analysis_text', 'final_prompt', 'prompt_json'.
    """

    logging.info(f"Processing Request: Type={file_type}, File={file_path}")

    try:
        base_prompt = ""
        prompt_json = None
        analysis_data = None

        # --- Step 1: Understand/Analyze the Input ---
        if file_type.lower() in ['image', 'jpg', 'png', 'jpeg']:
            logging.info("Analyzing Image...")
            if not OPENAI_API_KEY:
                return {"success": False, "error": "OpenAI API Key missing"}

            rater = ImageRater(api_key=OPENAI_API_KEY)
            analysis = rater.get_image_description(file_path)

            if "error" in analysis:
                return {"success": False, "error": f"Image analysis failed: {analysis['error']}"}

            # Get video_prompt_json if available
            prompt_json = analysis.get("video_prompt_json")
            analysis_data = analysis

            if prompt_json:
                base_prompt = json_prompt_to_text(prompt_json)
            else:
                # Fallback to prompt_reconstruction
                base_prompt = analysis.get("prompt_reconstruction", "")

        elif file_type.lower() in ['video', 'mp4', 'mov', 'avi']:
            logging.info("Analyzing Video...")
            # Use Gemini to understand video - now returns structured JSON
            analysis = analyze_video(file_path)

            if isinstance(analysis, dict):
                prompt_json = analysis
                analysis_data = analysis
                # Convert JSON to text prompt
                if "raw_analysis" in analysis:
                    # Fallback case
                    base_prompt = analysis["raw_analysis"]
                else:
                    base_prompt = json_prompt_to_text(prompt_json)
            else:
                # Old string format fallback
                base_prompt = str(analysis)

        else:
            return {"success": False, "error": f"Unsupported file type: {file_type}"}

        if not base_prompt:
             return {"success": False, "error": "Could not extract prompt/analysis from input file."}

        # --- Step 2: Formulate Final Prompt ---
        final_prompt = base_prompt
        if instructions:
            final_prompt = f"{instructions}. {base_prompt}"

        logging.info(f"Generated Final Prompt: {final_prompt[:100]}...")

        # --- Step 3: Generate Video ---
        logging.info("Generating Video...")
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Call Gemini Veo
        generated_file = generate_video(final_prompt, output_filename=output_path)

        if generated_file:
            return {
                "success": True,
                "video_path": generated_file,
                "analysis_text": base_prompt,
                "final_prompt": final_prompt,
                "prompt_json": prompt_json,
                "analysis_data": analysis_data
            }
        else:
             return {"success": False, "error": "Video generation failed (API error or quota)"}

    except Exception as e:
        logging.error(f"Error in process_creative_request: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {"success": False, "error": str(e)}
