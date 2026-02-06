import os
import sys
import time
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Add parent directory to path to import newimg
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from newimg import ImageRater
except ImportError:
    print("Error: Could not import 'newimg'. Make sure 'newimg.py' is in the parent directory.")
    sys.exit(1)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in .env")
    sys.exit(1)

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

def analyze_image_dna(image_path):
    """
    Uses OpenAI Vision to extract the visual DNA and prompt reconstruction from the image.
    """
    print(f"\n🔍 Analyzing image: {image_path}...")
    rater = ImageRater(api_key=OPENAI_API_KEY)
    
    try:
        # We use get_image_description which returns structured JSON including 'prompt_reconstruction'
        analysis = rater.get_image_description(image_path)
        
        if "error" in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            return None
            
        print("✅ Image analysis complete.")
        return analysis
    except Exception as e:
        print(f"❌ Error during image analysis: {e}")
        return None

def generate_video_from_prompt(prompt, output_filename="generated_video.mp4"):
    """
    Uses Gemini Veo to generate a video from the text prompt.
    """
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
            
            output_path = os.path.join(os.path.dirname(__file__), output_filename)
            generated_video.video.save(output_path)
            print(f"💾 Video saved to: {output_path}")
            return output_path
        else:
            print("❌ Video generation failed or returned no results.")
            if operation.error:
                 print(f"Error details: {operation.error}")
            return None
            
    except Exception as e:
        print(f"❌ Error during video generation: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Generate video from image analysis + instructions")
    parser.add_argument("--image", required=True, help="Path to the input image")
    parser.add_argument("--instructions", default="", help="Transformation instructions (optional)")
    parser.add_argument("--output", default="output_video.mp4", help="Output video filename")
    
    args = parser.parse_args()
    
    image_path = args.image
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return

    # Step 1: Analyze Image
    analysis = analyze_image_dna(image_path)
    if not analysis:
        return
    
    base_prompt = analysis.get("prompt_reconstruction", "")
    if not base_prompt:
        print("Error: Could not extract prompt reconstruction from analysis.")
        return
        
    print(f"\n📝 Extracted Base Prompt:\n{base_prompt}")
    
    # Step 2: Combine with Instructions
    final_prompt = base_prompt
    if args.instructions:
        final_prompt = f"{args.instructions}. Style and composition reference: {base_prompt}"
        print(f"\n✨ Applied Transformation Instructions:\n{args.instructions}")
    
    print(f"\n🚀 Final Prompt for Video:\n{final_prompt}")
    
    # Step 3: Generate Video
    generate_video_from_prompt(final_prompt, args.output)

if __name__ == "__main__":
    main()
