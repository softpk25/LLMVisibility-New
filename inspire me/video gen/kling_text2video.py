import os
import time
import jwt
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY")

if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
    print("Error: KLING_ACCESS_KEY or KLING_SECRET_KEY not found in .env")
    exit(1)

def get_jwt_token(ak, sk):
    """
    Generate JWT token for Kling API authentication.
    """
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800,  # Token valid for 30 minutes
        "nbf": int(time.time()) - 5      # Valid from 5 seconds ago
    }
    token = jwt.encode(payload, sk, algorithm="HS256", headers=headers)
    return token

def create_text2video_task(token, prompt):
    url = "https://api.klingai.com/v1/videos/text2video"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "kling-v1", # Adjust model name if specific version required, e.g. "kling-v1-standard"
        "prompt": prompt,
        "cfg_scale": 0.5,
        "mode": "std",
        "aspect_ratio": "16:9"
    }
    
    print(f"Sending request to {url} with prompt: '{prompt}'")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0: # Assuming 0 is success based on typical APIs, or check 'task_id' presence
             return data.get("data", {}).get("task_id")
        else:
             print(f"API Error Code: {data.get('code')}, Message: {data.get('message')}")
             return None
    else:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
        return None

def get_task_details(token, task_id):
    url = f"https://api.klingai.com/v1/videos/text2video/{task_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def main():
    print("Generating Kling API Token...")
    token = get_jwt_token(KLING_ACCESS_KEY, KLING_SECRET_KEY)
    
    prompt = "A cinematic drone shot of a futuristic cyberpunk city at night with neon lights and flying cars"
    
    print("Creating Video Generation Task...")
    task_id = create_text2video_task(token, prompt)
    
    if not task_id:
        print("Failed to create task.")
        return

    print(f"Task Created! ID: {task_id}")
    print("Waiting for completion...")
    
    start_time = time.time()
    while True:
        # Refresh token if needed or just reuse (short task)
        # Note: In long running loops, regenerate token if > 30m
        
        details = get_task_details(token, task_id)
        if details:
            data = details.get("data", {})
            status = data.get("task_status")
            print(f"Status: {status}")
            
            if status == "succeed":
                video_url = data.get("task_result", {}).get("videos", [{}])[0].get("url")
                print("\nSUCCESS!")
                print(f"Video URL: {video_url}")
                # Download logic could be added here
                break
            elif status == "failed":
                print("\nFAILED.")
                print(f"Reason: {data.get('task_status_msg')}")
                break
        
        if time.time() - start_time > 600: # 10 minutes timeout
            print("Timeout waiting for video.")
            break
            
        time.sleep(5)

if __name__ == "__main__":
    main()
