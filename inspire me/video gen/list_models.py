import os
import sys
from dotenv import load_dotenv
from google import genai

# Load environment variables
try:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
except:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

print("Listing available models...")
try:
    for m in client.models.list():
        if "gemini" in m.name:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
