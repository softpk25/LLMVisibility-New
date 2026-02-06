#!/usr/bin/env python3
"""
Prometrix Backend Startup Script
Simple script to start the backend with proper configuration
"""

import os
import sys
import subprocess
from pathlib import Path


def check_requirements():
    """Check if all requirements are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import pydantic_settings
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: python setup.py")
        return False


def check_environment():
    """Check environment configuration"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        print("Please copy .env.example to .env and configure your settings")
        return False
    
    print("✅ Environment file found")
    
    # Check for API keys
    with open(env_file) as f:
        content = f.read()
        
    if "your-openai-api-key" in content:
        print("⚠️  Warning: OpenAI API key not configured (using mock provider)")
    
    if "your-anthropic-api-key" in content:
        print("⚠️  Warning: Anthropic API key not configured")
        
    return True


def start_server():
    """Start the Prometrix backend server"""
    print("🚀 Starting Prometrix Backend Server...")
    print("📖 API Documentation will be available at: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📋 API Root: http://localhost:8000/api/v1/")
    print("\nPress Ctrl+C to stop the server\n")
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


def main():
    """Main startup function"""
    print("🎯 Prometrix Backend Startup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Start server
    start_server()


if __name__ == "__main__":
    main()