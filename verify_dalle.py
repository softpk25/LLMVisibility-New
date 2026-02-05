
import requests
import time

url = "http://localhost:8000/api/generate-creative"
payload = {
    "prompt": "A futuristic city with flying cars and neon lights, digital art style",
    "type": "image"
}

try:
    print("Requesting DALL-E generation (this mimics the frontend call)...")
    # This might take a while so we wait
    start = time.time()
    response = requests.post(url, json=payload, timeout=60)
    end = time.time()
    
    print(f"Status Code: {response.status_code}")
    print(f"Time taken: {end - start:.2f}s")
    
    if response.status_code == 200:
        print("Response:", response.json())
        print("SUCCESS: Image generated.")
    else:
        print(f"Error Code: {response.status_code}")
        try:
            print("Error JSON:", response.json())
        except:
            print("Error Text:", response.text)
        print("FAILURE: API returned error.")
        
except Exception as e:
    print(f"EXCEPTION: {str(e)}")
