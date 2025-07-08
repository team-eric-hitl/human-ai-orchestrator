.PHONY: install install-dev test run demo setup clean format lint type-check

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

# Help
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  run          - Run the main demo"
	@echo "  demo         - Run the comprehensive demo"
	@echo "  setup        - Setup the project (install deps, create .env, run tests)"
	@echo "  clean        - Clean up generated files"
	@echo "  format       - Format code with ruff"
	@echo "  lint         - Lint code with ruff"
	@echo "  lint-fix     - Lint and auto-fix code with ruff"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  check        - Run all code quality checks"
	@echo "  help         - Show this help message" 