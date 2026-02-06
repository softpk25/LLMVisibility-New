import os
import time
import json
import jwt
import requests
import argparse
from dotenv import load_dotenv

class KlingAI:
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = "https://api.klingai.com/v1"
        self.token = None
        self.token_expiry = 0

    def _get_token(self):
        """Generates or retrieves a valid JWT token."""
        current_time = int(time.time())
        # Refresh if token is missing or about to expire (within 60 seconds)
        if not self.token or current_time >= self.token_expiry - 60:
            headers = {
                "alg": "HS256",
                "typ": "JWT"
            }
            # Token valid for 30 minutes
            self.token_expiry = current_time + 1800 
            payload = {
                "iss": self.access_key,
                "exp": self.token_expiry, 
                "nbf": current_time - 5
            }
            self.token = jwt.encode(payload, self.secret_key, algorithm="HS256", headers=headers)
        return self.token

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self._get_token()}",
            # "Content-Type" is set automatically by requests for multipart/form-data, 
            # or manually for json. We'll handle it per request type.
        }

    def upload_file(self, file_path, file_type="video"):
        """Upload video or image file to Kling"""
        upload_url = f"{self.base_url}/files/upload"
        
        print(f"Uploading {file_type}: {file_path}...")
        headers = {"Authorization": f"Bearer {self._get_token()}"}
        
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {"type": file_type}
            # requests handles the boundary and Content-Type for multipart uploads
            response = requests.post(upload_url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                file_id = data['data']['file_id']
                print(f"✅ Upload successful. File ID: {file_id}")
                return file_id
            else:
                 raise Exception(f"Upload API error: {data}")
        else:
            raise Exception(f"Upload HTTP error: {response.text}")

    def create_inpainting_task(self, video_path, reference_image_path, prompt, mask_prompt=None):
        """
        Create a video inpainting task workflow:
        1. Upload Video
        2. Upload Reference Image
        3. Create Task
        """
        # 1. Upload Video
        video_id = self.upload_file(video_path, "video")
        
        # 2. Upload Reference Image
        image_id = self.upload_file(reference_image_path, "image")
        
        # 3. Create Task
        task_url = f"{self.base_url}/videos/inpainting"
        
        payload = {
            "model": "kling-v1", # Verify model name if needed
            "video_id": video_id,
            "reference_image_id": image_id,
            "prompt": prompt,
            "mode": "smart",  # "smart" attempts to auto-segment
        }
        
        if mask_prompt:
            payload["mask_prompt"] = mask_prompt
        
        print(f"Creating inpainting task with prompt: '{prompt}'...")
        headers = self._get_headers()
        headers["Content-Type"] = "application/json"
        
        response = requests.post(task_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                task_id = data['data']['task_id']
                print(f"✅ Task created successfully. Task ID: {task_id}")
                return task_id
            else:
                 raise Exception(f"Task creation API error: {data}")
        else:
            raise Exception(f"Task creation HTTP error: {response.text}")

    def get_task_status(self, task_id):
        """Check the status of a task"""
        status_url = f"{self.base_url}/videos/inpainting/{task_id}"
        headers = self._get_headers()
        
        response = requests.get(status_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Status check failed: {response.text}")

    def wait_for_completion(self, task_id, check_interval=10, max_wait_time=900):
        """Wait for task to complete"""
        print(f"Waiting for task {task_id} to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_data = self.get_task_status(task_id)
            
            # API structure might vary, adapting to common Kling response
            if status_data.get("code") != 0:
                print(f"Warning: Status check returned code {status_data.get('code')}")
                time.sleep(check_interval)
                continue
                
            data = status_data.get("data", {})
            status = data.get("task_status")
            
            print(f"Status: {status}")
            
            if status == "succeed":
                # Assuming result structure
                result = data.get("task_result", {})
                return result
            elif status == "failed":
                error_msg = data.get("task_status_msg", "Unknown error")
                raise Exception(f"Task failed: {error_msg}")
            
            time.sleep(check_interval)
        
        raise Exception("Task timed out")

    def download_result(self, result_data, output_path):
        """Download the generated video"""
        # 'videos' key usually contains list of dicts with 'url'
        videos = result_data.get("videos", [])
        if not videos:
            print("No video URL found in result.")
            return

        video_url = videos[0].get("url")
        print(f"Downloading video from {video_url}...")
        
        response = requests.get(video_url, stream=True)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Video saved to {output_path}")
        else:
            raise Exception(f"Download failed: {response.text}")

def main():
    parser = argparse.ArgumentParser(description="Kling AI Video Inpainting Tool")
    parser.add_argument("--video", required=True, help="Path to the original video file")
    parser.add_argument("--image", required=True, help="Path to the reference image file")
    parser.add_argument("--prompt", required=True, help="Text description of the modification")
    parser.add_argument("--mask", help="Optional mask prompt to identify object to replace")
    parser.add_argument("--output", default="inpainted_output.mp4", help="Output filename")
    
    args = parser.parse_args()
    
    # Load environment
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))
    
    # Get Credentials
    access_key = os.getenv("KLING_ACCESS_KEY")
    secret_key = os.getenv("KLING_SECRET_KEY")
    
    if not access_key or not secret_key:
        print("Error: KLING_ACCESS_KEY or KLING_SECRET_KEY not found in .env")
        return

    # Check files
    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        return
    if not os.path.exists(args.image):
        print(f"Error: Image file not found: {args.image}")
        return

    try:
        kling = KlingAI(access_key, secret_key)
        
        task_id = kling.create_inpainting_task(
            video_path=args.video,
            reference_image_path=args.image,
            prompt=args.prompt,
            mask_prompt=args.mask
        )
        
        result = kling.wait_for_completion(task_id)
        kling.download_result(result, args.output)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()