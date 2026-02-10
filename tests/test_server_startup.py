"""
Test Server Startup
Verifies that the server can start without errors
"""

import pytest
import sys
from pathlib import Path
import time
import requests
from multiprocessing import Process
import uvicorn

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_server():
    """Run the server in a separate process"""
    import server
    uvicorn.run(server.app, host="127.0.0.1", port=8001, log_level="error")


class TestServerStartup:
    """Test that server can start without errors"""
    
    def test_server_starts_without_errors(self):
        """Test that server can start and respond to requests"""
        # Start server in background process
        server_process = Process(target=run_server)
        server_process.start()
        
        try:
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is running
            assert server_process.is_alive(), "Server process died during startup"
            
            # Try to connect to server
            try:
                response = requests.get("http://127.0.0.1:8001/", timeout=5)
                assert response.status_code == 200, f"Server returned status {response.status_code}"
                
                # Verify response
                data = response.json()
                assert "message" in data, "Response missing 'message' field"
                assert data["message"] == "Server is running", "Unexpected message"
                
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Failed to connect to server: {e}")
                
        finally:
            # Clean up
            server_process.terminate()
            server_process.join(timeout=5)
            if server_process.is_alive():
                server_process.kill()
    
    def test_health_endpoint(self):
        """Test that health endpoint is accessible"""
        # Start server in background process
        server_process = Process(target=run_server)
        server_process.start()
        
        try:
            # Wait for server to start
            time.sleep(3)
            
            # Try to access health endpoint
            try:
                response = requests.get("http://127.0.0.1:8001/health", timeout=5)
                assert response.status_code == 200, f"Health endpoint returned status {response.status_code}"
                
                # Verify response
                data = response.json()
                assert "status" in data, "Health response missing 'status' field"
                assert data["status"] == "healthy", "Server not healthy"
                
            except requests.exceptions.RequestException as e:
                pytest.fail(f"Failed to connect to health endpoint: {e}")
                
        finally:
            # Clean up
            server_process.terminate()
            server_process.join(timeout=5)
            if server_process.is_alive():
                server_process.kill()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
