# Team Eric HITL

A comprehensive data processing and analysis framework with modular architecture, designed for AI and machine learning projects.

## 🚀 Getting Started (For Beginners)

This guide will help you set up everything you need to start programming with this project. We've provided multiple options, starting with the easiest!

### Prerequisites

Before you begin, make sure you have Docker installed on your computer:

**Install Docker Desktop:**
- Download from [docker.com](https://www.docker.com/products/docker-desktop/)
- Install and start Docker Desktop
- Verify installation by opening a terminal/command prompt and typing: `docker --version`

### Option 0: Dev Containers with VSCode/Cursor (Easiest - Recommended for VSCode/Cursor Users)

This is the **easiest way** to get started if you're using VSCode or Cursor! Dev containers automatically set up everything for you with the perfect development environment.

#### Step 1: Install the Dev Containers Extension
- **VSCode**: Install the "Dev Containers" extension by Microsoft
- **Cursor**: Dev containers are built-in, no extension needed!

#### Step 2: Clone and Open the Repository
```bash
git clone <repository-url>
cd team_eric_hitl
```

#### Step 3: Open in Dev Container
- **VSCode**: Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and type "Dev Containers: Reopen in Container"
- **Cursor**: Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and type "Dev Containers: Reopen in Container"

#### Step 4: Wait for Setup
The dev container will automatically:
- Build the Docker environment
- Install all Python dependencies
- Set up Jupyter Lab
- Configure Python extensions and formatting tools

#### Step 5: Start Programming!
- Open the integrated terminal in VSCode/Cursor
- Run `jupyter lab` to start Jupyter Lab
- Access it at `http://localhost:8888` (token: `devtoken`)
- Or work directly in VSCode/Cursor with full IntelliSense and debugging!

**Benefits of Dev Containers:**
- ✅ No need to install Python or dependencies locally
- ✅ Perfect development environment every time
- ✅ Built-in code formatting and linting
- ✅ Integrated debugging and IntelliSense
- ✅ Works the same on any computer

### Option 1: Docker Setup (Good Alternative)

This is the simplest way to get started - everything runs in a container, so you don't need to worry about Python versions or dependencies!

#### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd team_eric_hitl
```

#### Step 2: Build and Run the Docker Container
```bash
# Build the Docker image (this may take a few minutes the first time)
docker build -t team_eric_hitl .

# Run the container
docker run -p 8888:8888 -v $(pwd):/workspace team_eric_hitl
```

**For Windows PowerShell users:**
```powershell
# Build the Docker image
docker build -t team_eric_hitl .

# Run the container (Windows version)
docker run -p 8888:8888 -v ${PWD}:/workspace team_eric_hitl
```

#### Step 3: Access Jupyter Lab
Once the container is running, open your web browser and go to:
```
http://localhost:8888
```

You'll see Jupyter Lab with all the project files available. The token for access is: `devtoken`

#### Step 4: Start Programming!
- All your project files are available in the Jupyter Lab file browser
- You can create new notebooks, edit Python files, and run code
- Changes you make are automatically saved to your local machine

### Option 2: Local Development Setup (Advanced)

If you prefer to work directly on your local machine:

#### Prerequisites for Local Setup
1. **Python 3.11 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation
   - Verify installation: `python --version`

2. **Git** (for version control)
   - Download from [git-scm.com](https://git-scm.com/)
   - Verify installation: `git --version`

#### Install uv and Dependencies
```bash
# Install uv (fast Python package manager)
# Windows PowerShell (as Administrator):
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
uv shell
```

#### Start Jupyter Lab Locally
```bash
jupyter lab
```

### 🎯 Next Steps

1. **Explore the codebase**: Start with `src/common/` to understand the shared components
2. **Run examples**: Check out `hello.py` for a simple example
3. **Read documentation**: Each module has its own README with detailed explanations
4. **Start coding**: Create your own modules in the `src/` directory

### 🆘 Getting Help

If you run into any issues:

**Dev Container Issues:**
1. **Container won't start**: Make sure Docker Desktop is running
2. **Extension not found**: Install "Dev Containers" extension in VSCode
3. **Build fails**: Try rebuilding the container (Ctrl+Shift+P → "Dev Containers: Rebuild Container")
4. **Port conflicts**: The dev container automatically handles port forwarding

**Docker issues**: Make sure Docker Desktop is running
**Port conflicts**: If port 8888 is busy, change it: `docker run -p 8889:8888 ...`
**File permissions**: On Windows, make sure Docker has access to your drive
**Ask for help** - don't hesitate to reach out to the team!

### 🧪 Testing Your Setup

Once you're set up, you can test that everything is working:

```bash
# In Jupyter Lab, create a new notebook and run:
import pandas as pd
import numpy as np
print("Setup successful!")
```

