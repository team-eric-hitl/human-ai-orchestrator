FROM python:3.11-slim

# Install system dependencies including Node.js and npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN pip install --no-cache-dir uv

# Install Claude Code CLI from Anthropic
RUN npm install -g @anthropic-ai/claude-code

# Set workdir
WORKDIR /workspace

# Copy only dependency files first for caching
COPY pyproject.toml uv.lock README.md ./

# Install Python dependencies
RUN uv sync

# Copy source code (excluding .venv and other unnecessary files)
COPY src/ ./src/

# Expose Jupyter port
EXPOSE 8888

# Set environment variables for Jupyter
ENV PYTHONUNBUFFERED=1 \
    JUPYTER_ALLOW_INSECURE_WRITES=1 \
    JUPYTER_TOKEN=devtoken

# Default command: start Jupyter Lab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=devtoken", "--NotebookApp.notebook_dir=/workspace"] 