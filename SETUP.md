# 🚀 Setup Guide: Getting Started with VSCode/Cursor and Dev Containers

This guide will walk you through setting up the Hybrid AI-Human System in VSCode or Cursor using the provided development container. This setup ensures you have all the right tools and dependencies without any local installation headaches!

## 🎯 What You'll Get

By the end of this guide, you'll have:
- ✅ A fully configured Python development environment
- ✅ All project dependencies automatically installed
- ✅ Jupyter Lab ready for running the tutorial
- ✅ Code formatting, linting, and testing tools configured
- ✅ AI coding assistants (GitHub Copilot) ready to use

## 📋 Prerequisites

### Option A: VSCode (Recommended for beginners)
1. **Install VSCode**: Download from [code.visualstudio.com](https://code.visualstudio.com/)
2. **Install Docker Desktop**: Download from [docker.com](https://www.docker.com/products/docker-desktop/)
3. **Install Dev Containers Extension**: 
   - Open VSCode
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "Dev Containers" by Microsoft
   - Click Install

### Option B: Cursor (AI-powered editor)
1. **Install Cursor**: Download from [cursor.sh](https://cursor.sh/)
2. **Install Docker Desktop**: Download from [docker.com](https://www.docker.com/products/docker-desktop/)
3. **Install Dev Containers Extension**:
   - Open Cursor
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "Dev Containers" by Microsoft
   - Click Install

### 🚀 GPU Support (Optional)
If you have an NVIDIA GPU and want to use local LLM models with GPU acceleration:

1. **Install NVIDIA GPU drivers** and **NVIDIA Docker runtime**
2. **Use the GPU devcontainer**: The project includes a GPU-enabled devcontainer configuration
   - Located at `.devcontainer/devcontainer.gpu.json`
   - Automatically configured for GPU access with `--gpus all`
   - Includes CUDA environment variables
3. **Select GPU devcontainer**: When opening in VSCode/Cursor, choose the GPU configuration if prompted

For detailed GPU setup instructions, see [docs/GPU_SETUP.md](docs/GPU_SETUP.md)

## 🔧 Step-by-Step Setup

### Step 1: Get the Project

#### Option A: Clone from GitHub (if you have the repository)
```bash
git clone [repository-url]
cd hybrid-ai-system
```

#### Option B: Download and Extract
1. Download the project files
2. Extract to a folder like `hybrid-ai-system`
3. Open a terminal and navigate to the folder

### Step 2: Open in VSCode/Cursor

1. **Launch your editor** (VSCode or Cursor)
2. **Open the project folder**:
   - File → Open Folder
   - Select the `hybrid-ai-system` folder
3. **You should see a popup** saying: 
   > "Folder contains a Dev Container configuration file. Reopen in container?"
4. **Click "Reopen in Container"**

If you don't see the popup:
- Open Command Palette (Ctrl+Shift+P)
- Type "Dev Containers: Reopen in Container"
- Press Enter

### Step 3: Wait for Container Setup

The first time you open the project, it will:
1. **Build the development container** (this takes 3-5 minutes)
   - For GPU support: Uses `Dockerfile.gpu` with CUDA runtime
   - For CPU-only: Uses standard `Dockerfile`
2. **Install Python dependencies** with `uv sync`
3. **Configure all the development tools**
4. **Setup GPU access** (if using GPU devcontainer)

You'll see progress in the bottom-right corner of your editor.

**Note**: The GPU devcontainer will automatically detect and configure GPU access. You can verify GPU availability once the container is running by checking `nvidia-smi` in the terminal.

### Step 4: Verify Everything Works

Once the container is ready:

1. **Open a terminal** in your editor (Terminal → New Terminal)
2. **Check Python is working**:
   ```bash
   python --version
   # Should show: Python 3.11.x
   ```
3. **Check uv is working**:
   ```bash
   uv --version
   # Should show the uv version
   ```
4. **Run a quick test**:
   ```bash
   make test
   ```
5. **Check GPU availability** (if using GPU container):
   ```bash
   nvidia-smi
   # Should show your GPU information
   
   # Test GPU in Python
   python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
   ```

## 🎓 Your First Steps

### 1. Start with the Tutorial
```bash
# Launch Jupyter Lab (will open in your browser)
jupyter lab

# Or use the make command
make jupyter
```

Navigate to `notebooks/AI_Agents_Tutorial.ipynb` and start learning!

### 2. Configure Your Environment Variables

Create your environment file:
```bash
# Copy the example file
cp .env.example .env

# Edit with your API keys (optional)
nano .env
```

### 3. Run the System

```bash
# Run the main application
make run

# Or run tests
make test

# See all available commands
make help
```

## 🛠️ Development Tools Available

Your dev container comes pre-configured with:

### Code Quality Tools
- **Black**: Code formatting (auto-runs on save)
- **Ruff**: Fast linting and import sorting
- **MyPy**: Type checking
- **Pytest**: Testing framework

### AI Assistance
- **GitHub Copilot**: AI code completion (if you have access)
- **Pylance**: Advanced Python language server

### Debugging & Testing
- **Python Debugger**: Set breakpoints and debug code
- **Pytest Integration**: Run tests from the editor
- **Jupyter Support**: Interactive notebooks

## 🔍 Exploring the Project

### Key Files to Understand
```
hybrid-ai-system/
├── 📓 notebooks/
│   └── AI_Agents_Tutorial.ipynb    # START HERE - Learning tutorial
├── 🧠 src/
│   ├── nodes/                      # The AI agents
│   ├── core/                       # Core system components
│   └── workflows/                  # How agents work together
├── ⚙️ config/                       # System configuration
├── 🧪 tests/                       # Test suites
├── 📚 README.md                    # Main documentation
└── 🚀 SETUP.md                     # This guide!
```

### Recommended Learning Path
1. **Read the README.md** - Understand what the system does
2. **Open the Tutorial Notebook** - Learn AI agent concepts
3. **Explore the Source Code** - See how it's implemented
4. **Run the Tests** - Understand how testing works
5. **Make Changes** - Try modifying and extending the system

## 🎯 Common Tasks

### Running Tests
```bash
# Run all tests
make test

# Run specific test categories
uv run pytest tests/unit/core/ -v       # Core components
uv run pytest tests/unit/nodes/ -v      # AI agents
uv run pytest tests/integration/ -v     # End-to-end tests
```

### Code Formatting
```bash
# Format all code
make format

# Check code quality
make lint

# Type checking
make type-check

# Run all quality checks
make check
```

### Working with Jupyter
```bash
# Start Jupyter Lab
jupyter lab

# Or with make
make jupyter
```

## 🐛 Troubleshooting

### Container Won't Start
1. **Check Docker is running**: Look for Docker Desktop in your system tray
2. **Restart Docker Desktop**: Sometimes it needs a restart
3. **Rebuild container**: Command Palette → "Dev Containers: Rebuild Container"

### Python Import Errors
```bash
# Reinstall dependencies
uv sync --dev

# Check Python path
which python
# Should be: /workspace/.venv/bin/python
```

### Jupyter Won't Start
```bash
# Install Jupyter if missing
uv add jupyter

# Start manually
uv run jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
```

### Port Already in Use
If port 8888 is busy:
```bash
# Use a different port
jupyter lab --port=8889
```

## 💡 Pro Tips

### 1. Use the Integrated Terminal
- Your terminal is already configured with the Python environment
- All project commands work immediately

### 2. Leverage AI Assistance
- GitHub Copilot can help you understand and write code
- Use Ctrl+I for inline suggestions

### 3. Use the Makefile
```bash
make help    # See all available commands
make test    # Run tests
make run     # Start the application
make clean   # Clean up generated files
```

### 4. Debugging
- Set breakpoints in VSCode/Cursor by clicking the line numbers
- Use F5 to start debugging
- Inspect variables and step through code

### 5. Git Integration
- Your editor has full Git integration
- Use the Source Control panel (Ctrl+Shift+G)
- Commit, push, and pull directly from the editor

## 🚀 Next Steps

Once you're set up:

1. **Complete the Tutorial**: Work through `notebooks/AI_Agents_Tutorial.ipynb`
2. **Explore the Codebase**: Understand how the agents work
3. **Run Some Tests**: See how the system is tested
4. **Make Changes**: Try modifying configuration or adding features
5. **Contribute**: Consider contributing improvements back to the project

## 🤝 Getting Help

If you run into issues:

1. **Check the logs**: Look in the terminal for error messages
2. **Restart the container**: Sometimes a fresh start helps
3. **Check Docker resources**: Ensure Docker has enough memory/CPU
4. **Read the error messages**: They usually contain helpful information
5. **Ask for help**: Use the project's issue tracker or discussions

## 🎉 You're Ready!

Congratulations! You now have a fully configured development environment for working with AI agents. The hard part (setup) is done - now comes the fun part of learning and building!

Start with the tutorial notebook and enjoy exploring the world of AI agents! 🤖✨