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

    # Generate content
    print("Generating analysis...")
    # Using gemini-2.0-flash as confirmed working in previous tests
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=[
            myfile, 
            "Summarize this video in great detail and give me a very descriptive prompt that i can use to make a video very similar to the one i provided. Focus on visual style, composition, lighting, and movement."
        ]
    )

    print("\n--- Analysis Result ---\n")
    print(response.text)
    return response.text

if __name__ == "__main__":
    # Test run
    test_video = "WhatsApp Video 2026-02-06 at 11.15.19 AM.mp4"
    try:
        analyze_video(os.path.join(os.path.dirname(__file__), test_video))
    except Exception as e:
        print(f"Error: {e}")
