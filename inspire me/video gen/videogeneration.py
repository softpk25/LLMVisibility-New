import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

operation = client.models.generate_videos(
    model="veo-3.1-fast-generate-preview",
    prompt="a close-up shot of a golden retriever playing in a field of sunflowers",
    config=types.GenerateVideosConfig(
      negative_prompt="barking, woofing",
      aspect_ratio="9:16",
      resolution="720p",
    ),
)

# Waiting for the video(s) to be generated
while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)
    print(operation)

generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("golden_retriever.mp4")