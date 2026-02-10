import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def analyze_video(video_path):
    """
    Uploads a video to Gemini and generates a descriptive prompt and summary.
    Returns: a string containing the analysis/prompt.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env")

    client = genai.Client(api_key=GEMINI_API_KEY)

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at {video_path}")

    print(f"Uploading video for analysis: {video_path}...")
    myfile = client.files.upload(file=video_path)
    print(f"Uploaded: {myfile.name}")

    # Wait for processing
    print("Waiting for video processing...")
    while True:
        file = client.files.get(name=myfile.name)
        if file.state.name == "ACTIVE":
            print("Video is active and ready for processing.")
            break
        elif file.state.name == "FAILED":
            raise RuntimeError("Video processing failed.")
        
        print("Processing...")
        time.sleep(5)

    # Generate content with structured JSON output
    print("Generating structured analysis...")

    prompt = """Analyze this video and return a JSON object with a structured video generation prompt.

Use this exact JSON schema:

{
  "scene": "description of the setting/environment",
  "subjects": [
    {
      "type": "main subject type (e.g., person, product, animal)",
      "description": "detailed description of the subject",
      "position": "position in frame (e.g., center, left, right)"
    }
  ],
  "style": "overall visual style (e.g., cinematic, documentary, commercial)",
  "color_palette": ["color1", "color2", "color3"],
  "lighting": "lighting description (e.g., soft natural light, dramatic studio lighting)",
  "mood": "emotional tone (e.g., energetic, calm, professional)",
  "camera": "camera movement and angles (e.g., slow pan, static wide shot)",
  "movement": "subject/scene movement description",
  "duration_suggestion": "recommended duration in seconds"
}

Instructions:
- Analyze the video carefully
- Extract ALL key visual elements
- Be specific with colors, movements, and composition
- Make the description detailed enough to recreate a similar video
- Return ONLY valid JSON (no markdown code blocks or extra text)
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[myfile, prompt]
    )

    print("\n--- Structured Analysis Result ---\n")
    print(response.text)

    # Try to parse and return as dict, fallback to string
    try:
        import json
        cleaned_content = response.text.strip()
        if cleaned_content.startswith('```json'):
            cleaned_content = cleaned_content[7:]
        if cleaned_content.startswith('```'):
            cleaned_content = cleaned_content[3:]
        if cleaned_content.endswith('```'):
            cleaned_content = cleaned_content[:-3]
        cleaned_content = cleaned_content.strip()

        return json.loads(cleaned_content)
    except:
        # Fallback: return as-is if JSON parsing fails
        print("Warning: Could not parse JSON, returning raw text")
        return {"raw_analysis": response.text}

if __name__ == "__main__":
    # Test run
    test_video = "WhatsApp Video 2026-02-06 at 11.15.19 AM.mp4"
    try:
        analyze_video(os.path.join(os.path.dirname(__file__), test_video))
    except Exception as e:
        print(f"Error: {e}")
