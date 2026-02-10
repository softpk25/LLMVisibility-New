import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_video(prompt, output_filename="generated_video.mp4"):
    """
    Generates a video using Gemini Veo based on the provided prompt.
    Returns: Path to the saved video file.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in .env")

    print(f"\n🎥 Generating video with prompt: '{prompt}'...")
    print("(This may take a minute...)")
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        operation = client.models.generate_videos(
            model="veo-3.1-fast-generate-preview",
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16", # Defaulting to social media vertical format
                resolution="720p",
            ),
        )
        
        # Waiting for the video(s) to be generated
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)
            print("...processing...")
            
        if operation.result and operation.result.generated_videos:
            generated_video = operation.result.generated_videos[0]
            print(f"✅ Video generated successfully!")
            
            output_dir = os.path.dirname(output_filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Download remote file first (crucial fix from previous step)
            client.files.download(file=generated_video.video)
            
            generated_video.video.save(output_filename)
            print(f"💾 Video saved to: {output_filename}")
            return output_filename
        else:
            print("❌ Video generation failed or returned no results.")
            if operation.error:
                 print(f"Error details: {operation.error}")
            return None
            
    except Exception as e:
        print(f"❌ Error during video generation: {e}")
        return None

if __name__ == "__main__":
    # Test run
    try:
        generate_video("A cinematic drone shot of a futuristic cyberpunk city with neon lights and flying cars, rain reflecting on streets, 4k resolution")
    except Exception as e:
        print(f"Error: {e}")