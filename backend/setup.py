#!/usr/bin/env python3
"""
Setup script for Prometrix backend
Handles dependency conflicts and environment setup
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return None


def setup_environment():
    """Setup the backend environment"""
    print("🚀 Setting up Prometrix Backend Environment\n")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install core dependencies first to avoid conflicts
    core_deps = [
        "pydantic==2.11.9",
        "pydantic-settings==2.11.0", 
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-dotenv==1.1.1",
        "httpx==0.28.1"
    ]
    
    for dep in core_deps:
        run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}")
    
    # Install remaining dependencies
    remaining_deps = [
        "python-multipart==0.0.6",
        "aiofiles==23.2.1",
        "openai==1.70.0",
        "anthropic==0.7.0",
        "google-generativeai==0.7.0",
        "python-magic==0.4.27",
        "Pillow==10.1.0",
        "pytest==7.4.3",
        "pytest-asyncio==0.21.1"
    ]
    
    for dep in remaining_deps:
        run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created")
        print("⚠️  Please edit .env file and add your LLM API keys")
    
    # Create necessary directories
    directories = ["data", "uploads", "data/campaigns", "data/brands", "data/settings"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Created necessary directories")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file and add your LLM API keys")
    print("2. Run: python main.py")
    print("3. Visit: http://localhost:8000/docs")


if __name__ == "__main__":
    setup_environment()