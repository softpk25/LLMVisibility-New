"""
Manual verification script for Task 8 - Brand Blueprint Functionality
This script starts the server and performs manual checks on all endpoints
"""

import requests
import time
import sys
from pathlib import Path

def check_endpoint(url, method="GET", data=None, files=None, expected_status=200):
    """Check if an endpoint is accessible"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=5)
            else:
                response = requests.post(url, json=data, timeout=5)
        
        status_ok = response.status_code == expected_status
        status_symbol = "✓" if status_ok else "✗"
        print(f"  {status_symbol} {method} {url} - Status: {response.status_code}")
        return status_ok
    except Exception as e:
        print(f"  ✗ {method} {url} - Error: {e}")
        return False

def main():
    base_url = "http://localhost:8000"
    
    print("=" * 70)
    print("TASK 8 VERIFICATION - Brand Blueprint Functionality")
    print("=" * 70)
    print()
    
    # Wait for server to be ready
    print("Checking if server is running...")
    max_retries = 5
    server_ready = False
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                server_ready = True
                print("✓ Server is running and healthy")
                break
        except:
            if i < max_retries - 1:
                print(f"  Waiting for server... (attempt {i+1}/{max_retries})")
                time.sleep(2)
    
    if not server_ready:
        print("✗ Server is not running. Please start the server first:")
        print("  python server.py")
        sys.exit(1)
    
    print()
    
    # Test 1: Brand Blueprint Routes
    print("1. Testing Brand Blueprint Routes")
    print("-" * 70)
    
    routes_ok = True
    routes_ok &= check_endpoint(f"{base_url}/health")
    routes_ok &= check_endpoint(f"{base_url}/api/brand/blueprint?brand_id=test")
    routes_ok &= check_endpoint(f"{base_url}/brand-blueprint")
    
    # Test save blueprint
    blueprint_data = {
        "brandId": "verify-test",
        "brandName": "Verification Test",
        "blueprint": {
            "version": "1.0.0",
            "status": "draft",
            "voice": {"formality": 50, "humor": 50, "warmth": 50, "emojiPolicy": "medium"},
            "pillars": [],
            "policies": {"forbiddenPhrases": [], "maxHashtags": 5, "brandHashtags": []},
            "productDefaultPct": 30
        }
    }
    routes_ok &= check_endpoint(f"{base_url}/api/brand/blueprint", method="POST", data=blueprint_data)
    routes_ok &= check_endpoint(f"{base_url}/api/brand/blueprint/approve?brand_id=verify-test", method="POST")
    
    print()
    
    # Test 2: File Upload Validation
    print("2. Testing File Upload Validation")
    print("-" * 70)
    
    import io
    
    # Test invalid file type
    files = {'file': ('test.txt', io.BytesIO(b'test'), 'text/plain')}
    validation_ok = check_endpoint(
        f"{base_url}/api/brand/upload-guideline?brand_id=test",
        method="POST",
        files=files,
        expected_status=400
    )
    
    print()
    
    # Test 3: Database Operations
    print("3. Testing Database Operations")
    print("-" * 70)
    
    # Create a blueprint
    test_brand_id = "db-test-brand"
    test_data = {
        "brandId": test_brand_id,
        "brandName": "Database Test Brand",
        "blueprint": {
            "version": "1.0.0",
            "status": "draft",
            "voice": {"formality": 60, "humor": 40, "warmth": 70, "emojiPolicy": "light"},
            "pillars": [{"name": "Test", "description": "Test pillar", "weight": 100}],
            "policies": {"forbiddenPhrases": ["test"], "maxHashtags": 3, "brandHashtags": ["#Test"]},
            "productDefaultPct": 25
        }
    }
    
    db_ok = check_endpoint(f"{base_url}/api/brand/blueprint", method="POST", data=test_data)
    
    # Retrieve the blueprint
    if db_ok:
        try:
            response = requests.get(f"{base_url}/api/brand/blueprint?brand_id={test_brand_id}")
            data = response.json()
            
            if data["brandId"] == test_brand_id and data["brandName"] == "Database Test Brand":
                print("  ✓ Blueprint retrieved successfully with correct data")
                db_ok = True
            else:
                print("  ✗ Blueprint data mismatch")
                db_ok = False
        except Exception as e:
            print(f"  ✗ Failed to retrieve blueprint: {e}")
            db_ok = False
    
    print()
    
    # Test 4: Templates
    print("4. Testing Template Serving")
    print("-" * 70)
    
    try:
        response = requests.get(f"{base_url}/brand-blueprint")
        if response.status_code == 200 and "text/html" in response.headers.get("content-type", ""):
            print("  ✓ Brand blueprint template served correctly")
            templates_ok = True
        else:
            print("  ✗ Template not served correctly")
            templates_ok = False
    except Exception as e:
        print(f"  ✗ Failed to access template: {e}")
        templates_ok = False
    
    print()
    
    # Test 5: Existing Functionality
    print("5. Testing Existing Functionality Preservation")
    print("-" * 70)
    
    existing_ok = True
    existing_ok &= check_endpoint(f"{base_url}/")
    existing_ok &= check_endpoint(f"{base_url}/FACEBOOK-INSPIRE-ME.html")
    existing_ok &= check_endpoint(f"{base_url}/FACEBOOK-BRAND-REGISTRATION.html")
    
    print()
    
    # Test 6: Error Handling
    print("6. Testing Error Handling")
    print("-" * 70)
    
    # Test 404 for non-existent blueprint
    error_ok = check_endpoint(
        f"{base_url}/api/brand/blueprint/approve?brand_id=non-existent",
        method="POST",
        expected_status=404
    )
    
    # Test 422 for invalid data
    invalid_data = {"brandId": "test"}  # Missing required fields
    error_ok &= check_endpoint(
        f"{base_url}/api/brand/blueprint",
        method="POST",
        data=invalid_data,
        expected_status=422
    )
    
    print()
    
    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    all_tests = [
        ("Brand Blueprint Routes", routes_ok),
        ("File Upload Validation", validation_ok),
        ("Database Operations", db_ok),
        ("Template Serving", templates_ok),
        ("Existing Functionality", existing_ok),
        ("Error Handling", error_ok)
    ]
    
    for test_name, result in all_tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")
    
    print()
    
    all_passed = all(result for _, result in all_tests)
    
    if all_passed:
        print("✓ ALL VERIFICATIONS PASSED - Task 8 Complete!")
        print()
        print("The brand blueprint functionality is working correctly:")
        print("  • All brand blueprint routes are accessible")
        print("  • File upload validation is working")
        print("  • Database operations are functioning")
        print("  • Templates are being served correctly")
        print("  • No errors occur during normal operations")
        print("  • Existing functionality is preserved")
        return 0
    else:
        print("✗ SOME VERIFICATIONS FAILED - Please review the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
