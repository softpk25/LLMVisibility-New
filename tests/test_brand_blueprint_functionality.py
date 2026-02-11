"""
Test Brand Blueprint Functionality - Task 8 Checkpoint
Verifies that all brand blueprint functionality is working correctly:
- All brand blueprint routes are accessible
- File upload validation is working
- Database operations are functioning
- Templates are being served correctly
- No errors occur during normal operations
"""

import pytest
import sys
from pathlib import Path
import time
import requests
from multiprocessing import Process
import uvicorn
import io
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_test_server():
    """Run the server in a separate process for testing"""
    import server
    uvicorn.run(server.app, host="127.0.0.1", port=8002, log_level="error")


@pytest.fixture(scope="module")
def test_server():
    """Start test server and clean up after tests"""
    server_process = Process(target=run_test_server)
    server_process.start()
    
    # Wait for server to start
    time.sleep(3)
    
    # Verify server is running
    max_retries = 5
    for i in range(max_retries):
        try:
            response = requests.get("http://127.0.0.1:8002/health", timeout=2)
            if response.status_code == 200:
                break
        except:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                server_process.terminate()
                pytest.fail("Server failed to start")
    
    yield "http://127.0.0.1:8002"
    
    # Clean up
    server_process.terminate()
    server_process.join(timeout=5)
    if server_process.is_alive():
        server_process.kill()


class TestBrandBlueprintRoutes:
    """Test that all brand blueprint routes are accessible"""
    
    def test_health_endpoint(self, test_server):
        """Test health check endpoint"""
        response = requests.get(f"{test_server}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
    
    def test_get_blueprint_endpoint(self, test_server):
        """Test GET /api/brand/blueprint endpoint"""
        response = requests.get(f"{test_server}/api/brand/blueprint?brand_id=test-brand")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "brandId" in data
        assert "brandName" in data
        assert "blueprint" in data
        assert "guidelineDoc" in data
        
        # Verify blueprint structure
        blueprint = data["blueprint"]
        assert "version" in blueprint
        assert "status" in blueprint
        assert "voice" in blueprint
        assert "pillars" in blueprint
        assert "policies" in blueprint
    
    def test_save_blueprint_endpoint(self, test_server):
        """Test POST /api/brand/blueprint endpoint"""
        blueprint_data = {
            "brandId": "test-brand-save",
            "brandName": "Test Brand",
            "blueprint": {
                "version": "1.0.0",
                "status": "draft",
                "voice": {
                    "formality": 60,
                    "humor": 40,
                    "warmth": 70,
                    "emojiPolicy": "medium"
                },
                "pillars": [
                    {"name": "Innovation", "description": "Latest trends", "weight": 30},
                    {"name": "Education", "description": "Learning content", "weight": 30}
                ],
                "policies": {
                    "forbiddenPhrases": ["buy now", "limited time"],
                    "maxHashtags": 5,
                    "brandHashtags": ["#TestBrand"]
                },
                "productDefaultPct": 30
            }
        }
        
        response = requests.post(
            f"{test_server}/api/brand/blueprint",
            json=blueprint_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data
    
    def test_approve_blueprint_endpoint_not_found(self, test_server):
        """Test POST /api/brand/blueprint/approve endpoint with non-existent brand"""
        response = requests.post(
            f"{test_server}/api/brand/blueprint/approve?brand_id=non-existent-brand"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_approve_blueprint_endpoint_success(self, test_server):
        """Test POST /api/brand/blueprint/approve endpoint with existing brand"""
        # First create a blueprint
        blueprint_data = {
            "brandId": "test-brand-approve",
            "brandName": "Test Brand Approve",
            "blueprint": {
                "version": "1.0.0",
                "status": "draft",
                "voice": {
                    "formality": 50,
                    "humor": 50,
                    "warmth": 50,
                    "emojiPolicy": "medium"
                },
                "pillars": [],
                "policies": {
                    "forbiddenPhrases": [],
                    "maxHashtags": 5,
                    "brandHashtags": []
                },
                "productDefaultPct": 30
            }
        }
        
        save_response = requests.post(
            f"{test_server}/api/brand/blueprint",
            json=blueprint_data
        )
        assert save_response.status_code == 200
        
        # Now approve it
        approve_response = requests.post(
            f"{test_server}/api/brand/blueprint/approve?brand_id=test-brand-approve"
        )
        assert approve_response.status_code == 200
        data = approve_response.json()
        assert data["status"] == "success"
    
    def test_brand_blueprint_html_endpoint(self, test_server):
        """Test GET /brand-blueprint endpoint returns HTML"""
        response = requests.get(f"{test_server}/brand-blueprint")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert len(response.text) > 0


class TestFileUploadValidation:
    """Test file upload validation"""
    
    def test_upload_invalid_file_type(self, test_server):
        """Test that invalid file types are rejected"""
        # Create a fake .txt file
        files = {
            'file': ('test.txt', io.BytesIO(b'test content'), 'text/plain')
        }
        
        response = requests.post(
            f"{test_server}/api/brand/upload-guideline?brand_id=test-brand",
            files=files
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Invalid file type" in data["detail"]
    
    def test_upload_valid_pdf_extension(self, test_server):
        """Test that .pdf extension is accepted (will fail processing but pass validation)"""
        # Create a minimal PDF-like file
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF'
        files = {
            'file': ('test.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        response = requests.post(
            f"{test_server}/api/brand/upload-guideline?brand_id=test-upload-pdf",
            files=files
        )
        
        # Should not fail with file type validation error
        # May fail with processing error, but that's expected
        assert response.status_code in [200, 400, 500]
        if response.status_code == 400:
            data = response.json()
            # Should not be a file type error
            assert "Invalid file type" not in data.get("detail", "")
    
    def test_upload_file_size_limit(self, test_server):
        """Test that files exceeding 50 MB are rejected"""
        # Create a file larger than 50 MB (51 MB)
        large_content = b'x' * (51 * 1024 * 1024)
        files = {
            'file': ('large.pdf', io.BytesIO(large_content), 'application/pdf')
        }
        
        response = requests.post(
            f"{test_server}/api/brand/upload-guideline?brand_id=test-brand",
            files=files,
            timeout=30
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "50 MB" in data["detail"] or "size" in data["detail"].lower()


class TestDatabaseOperations:
    """Test database operations"""
    
    def test_create_and_retrieve_blueprint(self, test_server):
        """Test creating and retrieving a blueprint"""
        brand_id = "test-db-ops"
        
        # Create blueprint
        blueprint_data = {
            "brandId": brand_id,
            "brandName": "Test DB Operations",
            "blueprint": {
                "version": "1.0.0",
                "status": "draft",
                "voice": {
                    "formality": 55,
                    "humor": 45,
                    "warmth": 65,
                    "emojiPolicy": "light"
                },
                "pillars": [
                    {"name": "Test Pillar", "description": "Test description", "weight": 50}
                ],
                "policies": {
                    "forbiddenPhrases": ["test phrase"],
                    "maxHashtags": 3,
                    "brandHashtags": ["#TestDB"]
                },
                "productDefaultPct": 25
            }
        }
        
        save_response = requests.post(
            f"{test_server}/api/brand/blueprint",
            json=blueprint_data
        )
        assert save_response.status_code == 200
        
        # Retrieve blueprint
        get_response = requests.get(
            f"{test_server}/api/brand/blueprint?brand_id={brand_id}"
        )
        assert get_response.status_code == 200
        
        data = get_response.json()
        assert data["brandId"] == brand_id
        assert data["brandName"] == "Test DB Operations"
        assert data["blueprint"]["voice"]["formality"] == 55
        assert len(data["blueprint"]["pillars"]) == 1
        assert data["blueprint"]["pillars"][0]["name"] == "Test Pillar"
    
    def test_update_existing_blueprint(self, test_server):
        """Test updating an existing blueprint"""
        brand_id = "test-update"
        
        # Create initial blueprint
        initial_data = {
            "brandId": brand_id,
            "brandName": "Initial Name",
            "blueprint": {
                "version": "1.0.0",
                "status": "draft",
                "voice": {
                    "formality": 50,
                    "humor": 50,
                    "warmth": 50,
                    "emojiPolicy": "medium"
                },
                "pillars": [],
                "policies": {
                    "forbiddenPhrases": [],
                    "maxHashtags": 5,
                    "brandHashtags": []
                },
                "productDefaultPct": 30
            }
        }
        
        requests.post(f"{test_server}/api/brand/blueprint", json=initial_data)
        
        # Update blueprint
        updated_data = {
            "brandId": brand_id,
            "brandName": "Updated Name",
            "blueprint": {
                "version": "2.0.0",
                "status": "approved",
                "voice": {
                    "formality": 70,
                    "humor": 30,
                    "warmth": 80,
                    "emojiPolicy": "rich"
                },
                "pillars": [
                    {"name": "New Pillar", "description": "New", "weight": 100}
                ],
                "policies": {
                    "forbiddenPhrases": ["new phrase"],
                    "maxHashtags": 10,
                    "brandHashtags": ["#Updated"]
                },
                "productDefaultPct": 40
            }
        }
        
        update_response = requests.post(
            f"{test_server}/api/brand/blueprint",
            json=updated_data
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = requests.get(
            f"{test_server}/api/brand/blueprint?brand_id={brand_id}"
        )
        data = get_response.json()
        
        assert data["brandName"] == "Updated Name"
        assert data["blueprint"]["version"] == "2.0.0"
        assert data["blueprint"]["voice"]["formality"] == 70
        assert len(data["blueprint"]["pillars"]) == 1


class TestTemplateServing:
    """Test that templates are being served correctly"""
    
    def test_brand_blueprint_template_accessible(self, test_server):
        """Test that brand blueprint template is accessible"""
        response = requests.get(f"{test_server}/brand-blueprint")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        
        # Check for expected HTML content
        html = response.text
        assert len(html) > 100  # Should have substantial content
        assert "<!DOCTYPE html>" in html or "<html" in html


class TestErrorHandling:
    """Test error handling"""
    
    def test_invalid_json_request(self, test_server):
        """Test that invalid JSON is handled properly"""
        response = requests.post(
            f"{test_server}/api/brand/blueprint",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_missing_required_fields(self, test_server):
        """Test that missing required fields are handled"""
        incomplete_data = {
            "brandId": "test-incomplete"
            # Missing brandName and blueprint
        }
        
        response = requests.post(
            f"{test_server}/api/brand/blueprint",
            json=incomplete_data
        )
        assert response.status_code == 422  # Validation error


class TestExistingFunctionality:
    """Test that existing server functionality still works"""
    
    def test_root_endpoint(self, test_server):
        """Test that root endpoint still works"""
        response = requests.get(f"{test_server}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_facebook_inspire_me_html(self, test_server):
        """Test that existing HTML pages are still accessible"""
        response = requests.get(f"{test_server}/FACEBOOK-INSPIRE-ME.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_facebook_brand_registration_html(self, test_server):
        """Test that brand registration HTML is accessible"""
        response = requests.get(f"{test_server}/FACEBOOK-BRAND-REGISTRATION.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
