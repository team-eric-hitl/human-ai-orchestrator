#!/usr/bin/env python3
"""
Setup script for the modular LangGraph hybrid system using uv
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_uv_installed():
    """Check if uv is installed"""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_project():
    """Setup the project with uv"""
    print("🚀 Setting up Modular LangGraph Hybrid System")
    print("=" * 50)
    
    # Check if uv is installed
    if not check_uv_installed():
        print("❌ uv is not installed. Installing uv...")
        if not run_command("pip install uv", "Installing uv"):
            print("❌ Failed to install uv. Please install it manually: pip install uv")
            return False
    
    # Install dependencies
    print("\n📦 Installing project dependencies...")
    if not run_command("uv sync --group dev", "Installing dependencies"):
        print("❌ Failed to install dependencies")
        return False
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📝 Creating .env file...")
        env_content = """# API Keys
LANGSMITH_API_KEY=your_langsmith_key_here
OPENAI_API_KEY=your_openai_key_here

# System Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ Created .env file with template values")
        print("⚠️  Please update the API keys in .env file")
    
    # Run tests to verify setup
    print("\n🧪 Running tests to verify setup...")
    if run_command("uv run pytest tests/ -v", "Running tests"):
        print("✅ All tests passed!")
    else:
        print("⚠️  Some tests failed, but setup is complete")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update API keys in .env file")
    print("2. Run the demo: uv run python main.py")
    print("3. Or run the comprehensive demo: uv run python scripts/demo.py")
    
    return True

if __name__ == "__main__":
    success = setup_project()
    sys.exit(0 if success else 1) 