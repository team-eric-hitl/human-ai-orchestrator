#!/usr/bin/env python3
"""
GPU Detection and Configuration Script
Detects available GPU hardware and configures the system accordingly.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path


def check_nvidia_smi():
    """Check if nvidia-smi is available and working"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "nvidia-smi not found or timeout"


def check_cuda_devices():
    """Check for CUDA device files"""
    cuda_devices = list(Path('/dev').glob('nvidia*'))
    return len(cuda_devices) > 0, cuda_devices


def check_pytorch_cuda():
    """Check if PyTorch can detect CUDA"""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        device_count = torch.cuda.device_count() if cuda_available else 0
        
        gpu_info = []
        if cuda_available:
            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)
                gpu_info.append({
                    'id': i,
                    'name': props.name,
                    'memory': f"{props.total_memory / 1024**3:.1f}GB",
                    'compute_capability': f"{props.major}.{props.minor}"
                })
        
        return cuda_available, device_count, gpu_info
    except ImportError:
        return False, 0, []


def check_llama_cpp_cuda():
    """Check if llama-cpp-python has CUDA support"""
    try:
        # Try to import llama_cpp and check for CUDA support
        import llama_cpp
        
        # Check if CUDA symbols are available
        has_cuda = hasattr(llama_cpp, '_lib') and hasattr(llama_cpp._lib, 'llama_supports_gpu_offload')
        
        if has_cuda:
            try:
                supports_gpu = llama_cpp._lib.llama_supports_gpu_offload()
                return True, supports_gpu
            except:
                return True, False
        else:
            return False, False
    except ImportError:
        return False, False


def update_model_config(has_gpu: bool, gpu_count: int = 0):
    """Update model configuration based on GPU availability"""
    config_path = Path('/workspace/config/shared/models.yaml')
    
    if not config_path.exists():
        print(f"⚠️  Model config not found at {config_path}")
        return
    
    # Read current config
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except ImportError:
        print("⚠️  PyYAML not available, skipping config update")
        return
    except Exception as e:
        print(f"⚠️  Error reading config: {e}")
        return
    
    # Update GPU layers based on availability
    models_section = config.get('models', {})
    updated = False
    
    for model_name, model_config in models_section.items():
        if isinstance(model_config, dict) and 'type' in model_config:
            model_type = model_config.get('type')
            
            if model_type in ['llama', 'mistral']:  # Local models that support GPU
                current_gpu_layers = model_config.get('gpu_layers', 0)
                
                if has_gpu and current_gpu_layers == 0:
                    # Enable GPU acceleration
                    model_config['gpu_layers'] = 40  # Default safe value
                    updated = True
                    print(f"✅ Enabled GPU for {model_name}: {model_config['gpu_layers']} layers")
                elif not has_gpu and current_gpu_layers > 0:
                    # Disable GPU acceleration
                    model_config['gpu_layers'] = 0
                    updated = True
                    print(f"⚠️  Disabled GPU for {model_name}: using CPU only")
    
    # Save updated config
    if updated:
        try:
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"✅ Updated model configuration saved to {config_path}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    else:
        print("ℹ️  No model configuration changes needed")


def main():
    """Main GPU detection and setup function"""
    print("🔍 GPU Detection and Configuration")
    print("=" * 50)
    
    # Environment info
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Working directory: {os.getcwd()}")
    print()
    
    # Check 1: nvidia-smi
    print("1. Checking nvidia-smi...")
    nvidia_available, nvidia_output = check_nvidia_smi()
    if nvidia_available:
        print("✅ nvidia-smi is available")
        # Extract GPU count from output
        gpu_lines = [line for line in nvidia_output.split('\n') if 'GeForce' in line or 'RTX' in line or 'GTX' in line or 'Quadro' in line or 'Tesla' in line]
        print(f"   Detected GPUs: {len(gpu_lines)}")
    else:
        print(f"❌ nvidia-smi not available: {nvidia_output}")
    print()
    
    # Check 2: CUDA device files
    print("2. Checking CUDA device files...")
    cuda_devices_available, cuda_devices = check_cuda_devices()
    if cuda_devices_available:
        print(f"✅ CUDA devices found: {len(cuda_devices)}")
        for device in cuda_devices:
            print(f"   {device}")
    else:
        print("❌ No CUDA device files found in /dev")
    print()
    
    # Check 3: PyTorch CUDA
    print("3. Checking PyTorch CUDA support...")
    pytorch_cuda, device_count, gpu_info = check_pytorch_cuda()
    if pytorch_cuda:
        print(f"✅ PyTorch CUDA available with {device_count} device(s)")
        for gpu in gpu_info:
            print(f"   GPU {gpu['id']}: {gpu['name']} ({gpu['memory']}, CC {gpu['compute_capability']})")
    else:
        print("❌ PyTorch CUDA not available")
    print()
    
    # Check 4: llama-cpp-python CUDA
    print("4. Checking llama-cpp-python CUDA support...")
    llama_available, llama_supports_gpu = check_llama_cpp_cuda()
    if llama_available:
        if llama_supports_gpu:
            print("✅ llama-cpp-python with CUDA support available")
        else:
            print("⚠️  llama-cpp-python available but without CUDA support")
    else:
        print("❌ llama-cpp-python not available")
    print()
    
    # Overall GPU status
    print("=" * 50)
    has_gpu = nvidia_available and cuda_devices_available and pytorch_cuda
    
    if has_gpu:
        print("🎉 GPU ACCELERATION AVAILABLE!")
        print(f"   GPU devices: {device_count}")
        print("   Local models will use GPU acceleration")
        
        # Set environment variable for other processes
        os.environ['CUDA_VISIBLE_DEVICES'] = 'all'
        os.environ['GPU_AVAILABLE'] = 'true'
        
    else:
        print("💻 CPU-ONLY MODE")
        print("   No GPU acceleration available")
        print("   Local models will run on CPU (slower but functional)")
        
        # Set environment variables
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['GPU_AVAILABLE'] = 'false'
    
    print()
    
    # Update model configuration
    print("5. Updating model configuration...")
    update_model_config(has_gpu, device_count)
    print()
    
    # Recommendations
    print("📋 Recommendations:")
    if not has_gpu:
        print("   • For GPU support, ensure:")
        print("     - NVIDIA GPU drivers are installed")
        print("     - NVIDIA Docker runtime is configured")
        print("     - Docker containers are run with --gpus all")
        print("   • For now, use cloud models (OpenAI/Anthropic) for faster responses")
    else:
        print("   • GPU acceleration is ready!")
        print("   • Local models will be significantly faster")
        print("   • Consider downloading larger models for better quality")
    
    print()
    print("✅ GPU detection complete!")
    
    return 0 if has_gpu else 1


if __name__ == '__main__':
    sys.exit(main())