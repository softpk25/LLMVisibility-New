"""
Test to verify file size validation logic in upload_brand_guideline endpoint.
This test confirms that:
1. Files under 50 MB are accepted
2. Files over 50 MB are rejected with a 400 error
"""

from fastapi.testclient import TestClient
from io import BytesIO
import sys
from pathlib import Path

# Add the parent directory to the path so we can import server
sys.path.insert(0, str(Path(__file__).parent))

from server import app

client = TestClient(app)


def test_file_size_under_limit():
    """Test that files under 50 MB are accepted for processing."""
    # Create a file that's 1 MB (well under the limit)
    file_size = 1 * 1024 * 1024  # 1 MB
    file_content = b"x" * file_size
    
    files = {
        "file": ("test_guideline.pdf", BytesIO(file_content), "application/pdf")
    }
    
    response = client.post(
        "/api/brand/upload-guideline?brand_id=test-brand",
        files=files
    )
    
    # Should not fail due to file size (may fail for other reasons like missing OpenAI key)
    # The important thing is it's NOT a 400 error about file size
    assert response.status_code != 400 or "File size exceeds" not in response.json().get("detail", "")
    print(f"✓ 1 MB file accepted (status: {response.status_code})")


def test_file_size_at_limit():
    """Test that files exactly at 50 MB are accepted."""
    # Create a file that's exactly 50 MB
    file_size = 50 * 1024 * 1024  # 50 MB
    file_content = b"x" * file_size
    
    files = {
        "file": ("test_guideline.pdf", BytesIO(file_content), "application/pdf")
    }
    
    response = client.post(
        "/api/brand/upload-guideline?brand_id=test-brand",
        files=files
    )
    
    # Should not fail due to file size
    assert response.status_code != 400 or "File size exceeds" not in response.json().get("detail", "")
    print(f"✓ 50 MB file accepted (status: {response.status_code})")


def test_file_size_over_limit():
    """Test that files over 50 MB are rejected with a 400 error."""
    # Create a file that's 51 MB (over the limit)
    file_size = 51 * 1024 * 1024  # 51 MB
    file_content = b"x" * file_size
    
    files = {
        "file": ("test_guideline.pdf", BytesIO(file_content), "application/pdf")
    }
    
    response = client.post(
        "/api/brand/upload-guideline?brand_id=test-brand",
        files=files
    )
    
    # Should return 400 error with file size message
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "File size exceeds 50 MB limit" in response.json()["detail"]
    print(f"✓ 51 MB file rejected with 400 error: {response.json()['detail']}")


def test_file_size_way_over_limit():
    """Test that files significantly over 50 MB are rejected."""
    # Create a file that's 100 MB (way over the limit)
    file_size = 100 * 1024 * 1024  # 100 MB
    file_content = b"x" * file_size
    
    files = {
        "file": ("test_guideline.pdf", BytesIO(file_content), "application/pdf")
    }
    
    response = client.post(
        "/api/brand/upload-guideline?brand_id=test-brand",
        files=files
    )
    
    # Should return 400 error with file size message
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "File size exceeds 50 MB limit" in response.json()["detail"]
    print(f"✓ 100 MB file rejected with 400 error: {response.json()['detail']}")


if __name__ == "__main__":
    print("\n=== Testing File Size Validation ===\n")
    
    print("Test 1: File under 50 MB limit")
    test_file_size_under_limit()
    
    print("\nTest 2: File exactly at 50 MB limit")
    test_file_size_at_limit()
    
    print("\nTest 3: File over 50 MB limit (51 MB)")
    test_file_size_over_limit()
    
    print("\nTest 4: File way over 50 MB limit (100 MB)")
    test_file_size_way_over_limit()
    
    print("\n=== All File Size Validation Tests Passed ✓ ===\n")
