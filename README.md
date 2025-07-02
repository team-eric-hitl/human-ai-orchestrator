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

---

## 📚 Project Overview

This framework provides a modular architecture for data processing and analysis with the following key features:

- **Modular Design**: Clean separation of concerns with base interfaces
- **Data Processing**: Built-in support for CSV and other data formats
- **Configuration Management**: YAML-based configuration system
- **Logging**: Comprehensive logging with Loguru
- **Error Handling**: Robust error handling and validation
- **Jupyter Integration**: Ready-to-use Jupyter Lab environment

## 📁 Project Structure

```
team_eric_hitl/
├── src/
│   ├── base_interfaces/     # Base classes and interfaces
│   └── common/             # Shared utilities and components
├── pyproject.toml          # Project configuration and dependencies
├── Dockerfile             # Docker configuration
└── README.md              # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and formatting checks
5. Submit a pull request

## 📄 License

This project is part of the Team Eric HITL.

# Application Framework with Error Handling

This project provides a comprehensive application framework with structured error handling, logging, and file management capabilities.

## Architecture Overview

The project follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  Error Handler Factory  │  App Logger  │  Config Manager   │
├─────────────────────────────────────────────────────────────┤
│                    File Handler Layer                       │
│              (LocalAppFileHandler with Error Handling)      │
├─────────────────────────────────────────────────────────────┤
│                    Base Interfaces                          │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling Architecture

### Problem Solved
The original architecture had a circular dependency issue:
- `error_handler` depends on `app_logger`
- `app_logger` depends on `config_manager`
- `config_manager` depends on `app_file_handler`
- `app_file_handler` needed error handling but couldn't depend on `error_handler`

### Solution: Optional Logger Pattern

We implemented an **Optional Logger Pattern** that allows error handling to work at any layer:

1. **Error Handler Factory with Optional Logger**: The `ErrorHandlerFactory` can be initialized with or without a logger
2. **Graceful Degradation**: When no logger is available, errors are still raised but not logged
3. **Runtime Wiring**: The logger can be set later using `set_logger()` method

### Key Components

#### 1. Error Handler Factory
```python
# Can be used without logger (for lower-level components)
error_factory = ErrorHandlerFactory()

# Can be used with logger (for higher-level components)
error_factory = ErrorHandlerFactory(app_logger)

# Can set logger later
error_factory.set_logger(app_logger)
```

#### 2. File Operation Errors
```python
# Specific error type for file operations
FileOperationError - Handles file reading, writing, and system operations
```

#### 3. Integration in File Handler
```python
class LocalAppFileHandler(BaseAppFileHandler):
    def __init__(self):
        self.error_factory = ErrorHandlerFactory()
    
    def set_error_logger(self, app_logger):
        self.error_factory.set_logger(app_logger)
    
    def read_yaml(self, path):
        try:
            # File operations
            pass
        except Exception as e:
            raise self.error_factory.create_error_handler(
                "file_operation",
                f"Error reading YAML file: {path}",
                file_path=str(path),
                operation="read",
                original_error=str(e)
            )
```

## Usage Examples

### Basic Error Handling
```python
from src.common.app_file_handling.app_file_handler import LocalAppFileHandler
from src.common.app_logging.app_logger import AppLogger
from src.common.config_management.config_manager import ConfigManager

# Create components
file_handler = LocalAppFileHandler()
config_manager = ConfigManager(file_handler)
app_logger = AppLogger(config_manager)

# Set up logging
app_logger.setup("app.log")

# Wire up error handling
file_handler.set_error_logger(app_logger)

# Now file operations will have proper error handling
try:
    data = file_handler.read_yaml("config.yaml")
except FileOperationError as e:
    print(f"File error: {e}")
    print(f"Details: {e.additional_info}")
```

### Error Handler Factory Usage
```python
from src.common.error_handling.error_handler_factory import ErrorHandlerFactory

# Create factory with logger
factory = ErrorHandlerFactory(app_logger)

# Create specific error types
config_error = factory.create_error_handler(
    "configuration",
    "Invalid configuration file",
    config_file="config.yaml"
)

file_error = factory.create_error_handler(
    "file_operation",
    "Cannot read file",
    file_path="/path/to/file",
    operation="read"
)
```

## Error Types Available

- `ConfigurationError` - Configuration issues
- `FileOperationError` - File system operations
- `DataValidationError` - Data validation failures
- `DataProcessingError` - Data processing issues
- `WebDriverError` - Browser automation errors
- `ScrapingError` - Web scraping errors
- And many more...

## Benefits

1. **No Circular Dependencies**: Error handling can be used at any layer
2. **Structured Errors**: All errors include context and metadata
3. **Flexible Logging**: Errors can be logged when logger is available
4. **Type Safety**: Specific error types for different scenarios
5. **Easy Testing**: Error handling can be tested independently

## Running the Example

```bash
python hello.py
```

This will demonstrate error handling in action with file operations.

## Project Structure

```
src/
├── base_interfaces/          # Abstract base classes
├── common/
│   ├── app_file_handling/    # File operations with error handling
│   ├── app_logging/          # Structured logging
│   ├── config_management/    # Configuration management
│   ├── error_handling/       # Error handling system
│   └── data_access/          # Data access layer
└── common_di_container.py    # Dependency injection
```

## Best Practices

1. **Always use specific error types** rather than generic exceptions
2. **Include context** in error messages and additional_info
3. **Wire up error handling** after logger initialization
4. **Handle errors gracefully** at the appropriate layer
5. **Use structured logging** for better debugging and monitoring
