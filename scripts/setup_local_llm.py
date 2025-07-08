#!/usr/bin/env python3
"""
Local LLM Setup Script
Helps download and configure local LLM models
"""
import os
import sys
import yaml
import requests
from pathlib import Path
from urllib.parse import urlparse

def load_config():
    """Load local LLM configuration"""
    config_path = Path("config/local_llm_config.yaml")
    if not config_path.exists():
        print("❌ Configuration file not found: config/local_llm_config.yaml")
        return None
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def download_model(url: str, model_path: Path, chunk_size: int = 8192):
    """Download a model file with progress indicator"""
    print(f"📥 Downloading {urlparse(url).path.split('/')[-1]}...")
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(model_path, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r📥 Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
    
    print(f"\n✅ Downloaded to {model_path}")

def setup_models_directory():
    """Create models directory if it doesn't exist"""
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    print(f"✅ Models directory: {models_dir.absolute()}")
    return models_dir

def list_available_models(config):
    """List available models for download"""
    print("\n📋 Available Models:")
    print("-" * 50)
    
    for model_name, url in config.get("model_downloads", {}).items():
        model_path = Path(f"models/{model_name}.gguf")
        status = "✅ Downloaded" if model_path.exists() else "❌ Not downloaded"
        print(f"{model_name:20} {status}")
        print(f"{'':20} URL: {url}")
        print()

def download_specific_model(config, model_name: str):
    """Download a specific model"""
    downloads = config.get("model_downloads", {})
    
    if model_name not in downloads:
        print(f"❌ Model '{model_name}' not found in configuration")
        print(f"Available models: {list(downloads.keys())}")
        return False
    
    models_dir = setup_models_directory()
    model_path = models_dir / f"{model_name}.gguf"
    
    if model_path.exists():
        print(f"✅ Model {model_name} already exists at {model_path}")
        return True
    
    url = downloads[model_name]
    try:
        download_model(url, model_path)
        return True
    except Exception as e:
        print(f"❌ Failed to download {model_name}: {e}")
        return False

def test_model(config, model_name: str):
    """Test a local model"""
    print(f"\n🧪 Testing model: {model_name}")
    
    # Find model configuration
    model_config = None
    for category in ["llama", "mistral", "codellama", "ctransformers"]:
        if model_name in config.get(category, {}):
            model_config = config[category][model_name]
            provider_type = category
            break
    
    if not model_config:
        print(f"❌ Model configuration not found for {model_name}")
        return False
    
    model_path = Path(model_config["model_path"])
    if not model_path.exists():
        print(f"❌ Model file not found: {model_path}")
        return False
    
    try:
        # Import here to avoid issues if dependencies aren't installed
        from src.integrations.llm_providers import LLMProvider
        
        # Create provider
        provider = LLMProvider(provider_type, model_config)
        
        # Test with a simple prompt
        test_prompt = "Hello! Can you tell me a short joke?"
        print(f"🤖 Testing with prompt: {test_prompt}")
        
        response = provider.generate_response(test_prompt)
        print(f"✅ Model response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Local LLM Setup Script")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    if not config:
        return 1
    
    # Setup models directory
    setup_models_directory()
    
    # List available models
    list_available_models(config)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "download":
            if len(sys.argv) > 2:
                model_name = sys.argv[2]
                download_specific_model(config, model_name)
            else:
                print("❌ Please specify a model name: python scripts/setup_local_llm.py download <model_name>")
                print(f"Available models: {list(config.get('model_downloads', {}).keys())}")
        
        elif command == "test":
            if len(sys.argv) > 2:
                model_name = sys.argv[2]
                test_model(config, model_name)
            else:
                print("❌ Please specify a model name: python scripts/setup_local_llm.py test <model_name>")
        
        elif command == "download-all":
            print("📥 Downloading all available models...")
            for model_name in config.get("model_downloads", {}).keys():
                download_specific_model(config, model_name)
        
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: download, test, download-all")
    
    else:
        # Interactive mode
        print("\n🤔 What would you like to do?")
        print("1. Download a specific model")
        print("2. Test a model")
        print("3. Download all models")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            model_name = input("Enter model name: ").strip()
            download_specific_model(config, model_name)
        
        elif choice == "2":
            model_name = input("Enter model name: ").strip()
            test_model(config, model_name)
        
        elif choice == "3":
            print("📥 Downloading all available models...")
            for model_name in config.get("model_downloads", {}).keys():
                download_specific_model(config, model_name)
        
        elif choice == "4":
            print("👋 Goodbye!")
        
        else:
            print("❌ Invalid choice")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 