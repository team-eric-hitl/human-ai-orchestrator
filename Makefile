.PHONY: install install-dev test run demo setup clean format lint type-check docker-build docker-build-gpu docker-run docker-run-gpu docker-stop docker-logs gpu-check

# Install production dependencies
install:
	uv sync

# Install development dependencies
install-dev:
	uv sync --group dev

# Run tests
test:
	uv run pytest tests/ -v

# Run the main demo
run:
	uv run python main.py

# Run the comprehensive demo
demo:
	uv run python scripts/demo.py

# Setup the project (install deps, create .env, run tests)
setup:
	uv run python scripts/setup.py

# Clean up generated files
clean:
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf *.db
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Format code
format:
	uv run ruff format src/ tests/

# Lint and fix code
lint:
	uv run ruff check src/ tests/

# Lint and auto-fix code
lint-fix:
	uv run ruff check --fix src/ tests/

# Type checking
type-check:
	uv run mypy src/

# Run all code quality checks
check: format lint type-check test

# Docker Commands
docker-build:
	docker build -t ai-chatbot:cpu .

docker-build-gpu:
	docker build -f Dockerfile.gpu -t ai-chatbot:gpu .

docker-run:
	docker-compose -f docker-compose.gpu.yml --profile cpu-only up -d ai-chatbot-cpu

docker-run-gpu:
	@echo "Checking for GPU support..."
	@if command -v nvidia-smi >/dev/null 2>&1; then \
		echo "✅ NVIDIA GPU detected, starting GPU-enabled container..."; \
		docker-compose -f docker-compose.gpu.yml up -d ai-chatbot-gpu; \
	else \
		echo "⚠️  No GPU detected, starting CPU-only container..."; \
		docker-compose -f docker-compose.gpu.yml --profile cpu-only up -d ai-chatbot-cpu; \
	fi

docker-stop:
	docker-compose -f docker-compose.gpu.yml down

docker-logs:
	docker-compose -f docker-compose.gpu.yml logs -f

docker-shell:
	@if docker ps --format "table {{.Names}}" | grep -q ai-chatbot-gpu; then \
		docker exec -it ai-chatbot-gpu bash; \
	elif docker ps --format "table {{.Names}}" | grep -q ai-chatbot-cpu; then \
		docker exec -it ai-chatbot-cpu bash; \
	else \
		echo "No running AI chatbot containers found. Run 'make docker-run-gpu' first."; \
	fi

gpu-check:
	@echo "=== GPU Detection Report ==="
	@if command -v nvidia-smi >/dev/null 2>&1; then \
		echo "✅ nvidia-smi found"; \
		nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv; \
	else \
		echo "❌ nvidia-smi not found"; \
	fi
	@if command -v docker >/dev/null 2>&1; then \
		echo "✅ Docker found"; \
		if docker info 2>/dev/null | grep -q "nvidia"; then \
			echo "✅ Docker NVIDIA runtime detected"; \
		else \
			echo "⚠️  Docker NVIDIA runtime not configured"; \
		fi; \
	else \
		echo "❌ Docker not found"; \
	fi
	@echo "=== Python GPU Check ==="
	@python3 -c "import sys; print('Python:', sys.version)" 2>/dev/null || echo "❌ Python not available"
	@python3 scripts/gpu_detect.py 2>/dev/null || echo "⚠️  GPU detection script not available"

# Help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  run          - Run the main demo"
	@echo "  demo         - Run the comprehensive demo"
	@echo "  setup        - Setup the project (install deps, create .env, run tests)"
	@echo "  clean        - Clean up generated files"
	@echo ""
	@echo "Code Quality:"
	@echo "  format       - Format code with ruff"
	@echo "  lint         - Lint code with ruff"
	@echo "  lint-fix     - Lint and auto-fix code with ruff"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  check        - Run all code quality checks"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build     - Build CPU-only Docker image"
	@echo "  docker-build-gpu - Build GPU-enabled Docker image"
	@echo "  docker-run       - Run CPU-only container"
	@echo "  docker-run-gpu   - Run GPU container (auto-detects GPU)"
	@echo "  docker-stop      - Stop all containers"
	@echo "  docker-logs      - View container logs"
	@echo "  docker-shell     - Open shell in running container"
	@echo "  gpu-check        - Check GPU and Docker setup"
	@echo ""
	@echo "  help         - Show this help message" 