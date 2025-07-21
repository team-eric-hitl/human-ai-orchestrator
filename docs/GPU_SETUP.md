# GPU Setup Guide

This guide explains how to configure GPU acceleration for the AI Chatbot system using Docker.

## Prerequisites

### Hardware Requirements
- NVIDIA GPU with CUDA support (GTX 1060 or newer recommended)
- At least 8GB VRAM for 7B models, 16GB+ for 13B models
- 16GB+ system RAM

### Software Requirements
- Docker 20.10+ with Docker Compose
- NVIDIA GPU drivers (515+ recommended)
- NVIDIA Docker runtime (nvidia-docker2)

## Quick Start

### 1. Check GPU Availability
```bash
# Run GPU detection
make gpu-check
```

### 2. Build and Run with GPU Support
```bash
# Auto-detects GPU and runs appropriate container
make docker-run-gpu
```

### 3. Access Jupyter Lab
Open http://localhost:8888 in your browser (token: `devtoken`)

## Detailed Setup

### Step 1: Install NVIDIA Docker Runtime

#### Ubuntu/Debian
```bash
# Add NVIDIA GPG key
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Add repository
curl -s -L https://nvidia.github.io/libnvidia-container/ubuntu20.04/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker
```

#### Windows (WSL2)
1. Install Docker Desktop with WSL2 backend
2. Install NVIDIA drivers for Windows
3. Install CUDA toolkit in WSL2:
```bash
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda-repo-wsl-ubuntu-12-1-local_12.1.0-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-1-local_12.1.0-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-1-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

### Step 2: Verify GPU Access
```bash
# Test NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi

# Run project GPU check
make gpu-check
```

### Step 3: Build GPU-Enabled Images
```bash
# Build GPU-enabled image
make docker-build-gpu

# Or build both CPU and GPU images
make docker-build
make docker-build-gpu
```

### Step 4: Run with GPU Support
```bash
# Automatic GPU detection and container selection
make docker-run-gpu

# Or manually specify GPU container
docker-compose -f docker-compose.gpu.yml up -d ai-chatbot-gpu
```

## Configuration

### Model Configuration

GPU settings are automatically configured by the `gpu_detect.py` script:

```yaml
# config/shared/models.yaml
models:
  llama-7b:
    path: "models/llama-7b.gguf"
    type: "llama"
    gpu_layers: 40              # Auto-set based on GPU availability
    context_length: 2048
    temperature: 0.7
```

### Manual Configuration

To manually adjust GPU settings:

```yaml
# Disable GPU for a specific model
gpu_layers: 0                   # CPU only

# Partial GPU offloading (hybrid CPU/GPU)
gpu_layers: 20                  # 20 layers on GPU, rest on CPU

# Full GPU offloading
gpu_layers: 40                  # All layers on GPU (default for 7B models)
```

### Environment Variables

The system supports these GPU-related environment variables:

```bash
# Force GPU usage
CUDA_VISIBLE_DEVICES=all
GPU_AVAILABLE=true

# Force CPU-only mode
CUDA_VISIBLE_DEVICES=""
GPU_AVAILABLE=false

# Select specific GPU
CUDA_VISIBLE_DEVICES=0          # Use only GPU 0
```

## Troubleshooting

### Common Issues

#### 1. "nvidia-smi not found"
```bash
# Install NVIDIA drivers
sudo apt install nvidia-driver-515

# Or download from NVIDIA website
# Reboot after installation
```

#### 2. "Docker: unknown flag --gpus"
```bash
# Update Docker to 19.03+
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install nvidia-docker2
sudo apt install nvidia-docker2
sudo systemctl restart docker
```

#### 3. "Out of memory" errors
```bash
# Reduce gpu_layers in model config
gpu_layers: 20                  # Instead of 40

# Or use smaller model
local_general_budget: "mistral-7b"  # Instead of llama-13b
```

#### 4. "Model file not found"
```bash
# Download models to the models/ directory
mkdir -p models/
# Download from Hugging Face or other sources
```

### Performance Optimization

#### Memory Management
```yaml
# For 8GB VRAM
gpu_layers: 30                  # Leave some VRAM for system

# For 16GB+ VRAM  
gpu_layers: 40                  # Full offloading
```

#### Model Selection
```yaml
# Best performance/quality balance
local_general_standard: "llama-7b"

# Maximum performance
local_general_budget: "mistral-7b"

# Maximum quality (requires more VRAM)
local_general_premium: "llama-13b"
```

## Container Management

### Useful Commands
```bash
# Check container status
docker-compose -f docker-compose.gpu.yml ps

# View logs
make docker-logs

# Open shell in container
make docker-shell

# Stop containers
make docker-stop

# Restart with new configuration
make docker-stop
make docker-run-gpu
```

### Data Persistence

Important directories are mounted as volumes:
- `./models/` - Model files (persistent)
- `./data/` - Database files (persistent)  
- `./notebooks/experiment_runs/` - Experiment results (persistent)
- `./config/` - Configuration files (live editing)

### Performance Monitoring

#### Inside Container
```python
# Add to notebook cells
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")

if torch.cuda.is_available():
    print(f"Current GPU: {torch.cuda.get_device_name()}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
```

#### Host System
```bash
# Monitor GPU usage
watch -n 1 nvidia-smi

# Monitor container resources
docker stats ai-chatbot-gpu
```

## Advanced Configuration

### Custom GPU Models

For custom models with specific GPU requirements:

```yaml
# config/shared/models.yaml
models:
  custom-model:
    path: "models/custom-model.gguf"
    type: "llama"
    gpu_layers: 35              # Adjust based on model size
    context_length: 4096
    temperature: 0.7
    description: "Custom fine-tuned model"
```

### Multi-GPU Setup

For multiple GPUs:

```yaml
# docker-compose.gpu.yml
services:
  ai-chatbot-gpu:
    environment:
      - CUDA_VISIBLE_DEVICES=0,1    # Use GPUs 0 and 1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ['0', '1']   # Specific GPU IDs
              capabilities: [gpu]
```

### Development vs Production

#### Development (live code editing)
```bash
# Use docker-compose for development
make docker-run-gpu
```

#### Production (optimized image)
```bash
# Build optimized production image
docker build -f Dockerfile.gpu --target production -t ai-chatbot:gpu-prod .

# Run production container
docker run -d --gpus all --name ai-chatbot-prod ai-chatbot:gpu-prod
```

## Security Considerations

### Container Security
- Containers run with minimal privileges
- GPU access is restricted to specified containers
- Model files are isolated in containers

### Network Security
- Default ports: 8888 (Jupyter), 8000 (API)
- Use reverse proxy for production
- Configure firewall rules appropriately

### API Key Management
```bash
# Use environment variables, not hardcoded keys
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"

# Or use .env file (not committed to git)
echo "OPENAI_API_KEY=your-key" >> .env
```

## Support

### Getting Help
1. Run `make gpu-check` for diagnostic information
2. Check container logs: `make docker-logs`
3. Verify GPU access: `nvidia-smi` in container
4. Review configuration: Check `config/shared/models.yaml`

### Performance Expectations

| Model Size | VRAM Usage | CPU Usage | Response Time |
|------------|------------|-----------|---------------|
| 7B (GPU)   | 6-8GB      | Low       | 1-3 seconds   |
| 7B (CPU)   | 1-2GB      | High      | 15-30 seconds |
| 13B (GPU)  | 12-16GB    | Low       | 2-5 seconds   |
| 13B (CPU)  | 2-4GB      | Very High | 30-60 seconds |

The GPU acceleration provides 5-10x performance improvement over CPU-only inference.