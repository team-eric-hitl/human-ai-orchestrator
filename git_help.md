# Git Setup and Development Workflow Guide

This guide provides complete instructions for team members to set up their development environment and contribute to the project.

## 1. Initial Repository Setup

```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>

# Verify you're on main branch
git branch -a
git status
```

## 2. Create Personal Development Branch

```bash
# Create and switch to your personal branch
git checkout -b feature/your-name-feature-description
# or
git checkout -b dev/your-name

# Examples:
git checkout -b feature/alice-human-interface
git checkout -b dev/bob-dashboard
git checkout -b bugfix/charlie-config-validation
```

## 3. Environment Setup

```bash
# Install dependencies with uv
make setup
# or manually:
uv sync --dev

# Verify installation
uv run python --version
uv run python -c "import src; print('Setup successful')"
```

## 4. Configure Environment Variables

Create `.env` file in project root:
```bash
# Copy example if available
cp .env.example .env

# Edit with your API keys
# .env file should contain:
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
LANGCHAIN_API_KEY=your-langsmith-key-here  # optional
LANGCHAIN_TRACING_V2=true  # optional
```

## 5. Verify Setup

```bash
# Run tests to ensure everything works
make test

# Run code quality checks
make check

# Try running the system
make run
```

## 6. Development Workflow

### Daily Development
```bash
# Start each day by syncing with main
git checkout main
git pull origin main

# Switch back to your branch and rebase
git checkout feature/your-branch
git rebase main

# Make your changes
# ... edit files ...

# Test your changes
make test
make check

# Commit your work
git add .
git commit -m "feat: implement new feature

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Push to Remote
```bash
# First time pushing your branch
git push -u origin feature/your-branch

# Subsequent pushes
git push
```

## 7. Configuration Customization

Each team member can customize their local configuration:

```bash
# Create personal config override (optional)
cp config/environments/development.yaml config/environments/personal.yaml

# Edit personal.yaml with your preferences:
# - Preferred models
# - Local model paths
# - Development settings
```

## 8. Working with Model Files (if using local models)

```bash
# Create models directory
mkdir -p models

# Download models you want to use (examples)
# Llama models
wget https://huggingface.co/models/llama-7b.gguf -O models/llama-7b.gguf

# Mistral models  
wget https://huggingface.co/models/mistral-7b.gguf -O models/mistral-7b.gguf

# Update your personal config to point to your model paths
```

## 9. IDE/Editor Setup

### VS Code
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-python.pylint
code --install-extension charliermarsh.ruff

# Open workspace
code .
```

### PyCharm
```bash
# Set Python interpreter to uv environment
# File > Settings > Project > Python Interpreter
# Add interpreter from: .venv/bin/python
```

## 10. Testing Your Setup

```bash
# Run specific test categories
uv run python -m pytest tests/unit/core/ -v
uv run python -m pytest tests/unit/nodes/ -v

# Test with your configuration
uv run python scripts/answer_agent_demo.py

# Test notebook environment
jupyter lab notebooks/agent_tester.ipynb
```

## 11. Pull Request Workflow

When ready to merge your work:

```bash
# Ensure your branch is up to date
git checkout main
git pull origin main
git checkout feature/your-branch
git rebase main

# Push your final changes
git push origin feature/your-branch

# Create PR using GitHub CLI (if available)
gh pr create --title "feat: your feature description" --body "$(cat <<'EOF'
## Summary
- Brief description of changes
- Key features implemented

## Test plan
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"
```

## 12. Common Issues and Solutions

### Environment Issues
```bash
# If uv sync fails
rm -rf .venv
uv sync --dev

# If Python version issues
uv python install 3.11
uv sync --dev
```

### Git Issues
```bash
# If merge conflicts during rebase
git status  # see conflicted files
# Edit files to resolve conflicts
git add .
git rebase --continue
```

### Model Issues
```bash
# If local models fail to load
ls -la models/  # check files exist
# Update model paths in config/shared/models.yaml
```

## 13. Best Practices

### Branch Naming Conventions
- **Features**: `feature/descriptive-name` (e.g., `feature/user-feedback-system`)
- **Bug fixes**: `bugfix/issue-description` (e.g., `bugfix/config-validation`)
- **Development**: `dev/your-name` (e.g., `dev/alice-workspace`)
- **Experiments**: `experiment/what-youre-testing` (e.g., `experiment/new-model-integration`)

### Commit Message Format
Follow this format for consistency:
```
type: brief description

Optional longer description explaining the changes.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

### Development Best Practices
- **Commit frequency**: Commit early and often with descriptive messages
- **Testing**: Always run `make test` before pushing
- **Code quality**: Run `make check` before committing
- **Stay synced**: Rebase with main regularly to avoid conflicts
- **Documentation**: Update relevant docs with your changes
- **Configuration**: Test with different model configurations
- **Reviews**: Request reviews for significant changes

### Code Quality Checklist
Before pushing code, ensure:
- [ ] All tests pass (`make test`)
- [ ] Code formatting is correct (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Type checking passes (`make type-check`)
- [ ] Documentation is updated if needed
- [ ] Configuration changes are documented

## 14. Quick Reference Commands

### Essential Git Commands
```bash
# Check status
git status
git log --oneline -10

# Branch management
git branch -a                    # List all branches
git checkout -b new-branch       # Create and switch to new branch
git branch -d branch-name        # Delete local branch
git push -d origin branch-name   # Delete remote branch

# Syncing with main
git checkout main
git pull origin main
git checkout feature/your-branch
git rebase main

# Stashing changes
git stash                        # Save current changes
git stash pop                    # Restore stashed changes
git stash list                   # List all stashes
```

### Project-Specific Commands
```bash
# Development workflow
make setup                       # Install dependencies
make test                        # Run all tests
make check                       # Run all quality checks
make run                         # Start the application

# Testing specific components
uv run python -m pytest tests/unit/core/ -v
uv run python -m pytest tests/unit/nodes/ -v
uv run python -m pytest tests/integration/ -v

# Running specific scripts
uv run python scripts/answer_agent_demo.py
uv run python -m src.main --config-path config/custom_config.json
```

This guide ensures consistent development practices across the team and helps new contributors get started quickly.