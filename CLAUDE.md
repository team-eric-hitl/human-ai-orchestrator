# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
# Setup development environment
make setup

# Install dependencies directly with uv
uv sync --dev
```

### Testing
```bash
# Run all tests with coverage
make test

# Run unit tests only
uv run python -m pytest tests/unit/ -v

# Run integration tests only
uv run python -m pytest tests/integration/ -v

# Run specific test categories
uv run python -m pytest tests/unit/core/ -v          # Core infrastructure tests
uv run python -m pytest tests/unit/integrations/ -v  # LLM provider tests
uv run python -m pytest tests/unit/nodes/ -v         # Node component tests

# Run specific test file
uv run python -m pytest tests/unit/core/test_config_system.py -v

# Run with verbose output and coverage
uv run python -m pytest --cov=src --cov-report=html -v

# Run with coverage report to terminal
uv run python -m pytest --cov=src --cov-report=term-missing -v
```

### Code Quality
```bash
# Run all code quality checks
make check

# Individual quality checks
make format     # Format code with ruff
make lint       # Lint code with ruff
make lint-fix   # Lint and auto-fix code with ruff
make type-check # Type checking with mypy
```

### Running the System
```bash
# Run the main application
make run

# Run with custom config
uv run python -m src.main --config-path config/custom_config.json

# Run in development mode with monitoring
uv run python -m src.main --env development
```

## Architecture Overview

### Core System Design
This is a **Modular LangGraph Hybrid System** - a flexible AI workflow orchestration platform that combines AI agents with human-in-the-loop capabilities. The system is built around LangGraph nodes that can be composed into complex workflows.

### Key Components

**LangGraph Nodes** (`src/nodes/`):
- `AnswerAgent` - Handles direct query responses using configured LLMs
- `EvaluatorAgent` - Evaluates response quality and determines escalation needs
- `EscalationRouter` - Routes complex queries to appropriate human agents
- `HumanAgent` - Manages human agent interactions and handoffs

**Core Infrastructure** (`src/core/`):
- `AgentConfigManager` - Handles agent-centric configuration with hot-reloading
- `ContextManager` - Manages conversation context and memory (SQLite-based)
- `SessionTracker` - Tracks metrics and performance data
- `WorkflowOrchestrator` - Coordinates node execution and state management

- integrated logging/error handling system in /core/logging/

**Agent-Centric Configuration System** (`config/`):
- `config/agents/*/` - Agent-specific configurations, prompts, and model preferences
- `config/shared/` - Global models, providers, and system settings
- `config/environments/` - Environment-specific overrides (dev/test/prod)
- `config/config.yaml` - Main configuration coordinator
- Environment variables for API keys and runtime settings

### Interface Separation Pattern
The codebase follows a strict interface separation philosophy in `src/interfaces/`:
- **Core interfaces** (`src/interfaces/core/`) define contracts for ConfigProvider, ContextProvider, SessionTrackerInterface
- **Domain interfaces** (`src/interfaces/nodes/`, `src/interfaces/workflows/`) define node and workflow contracts
- This enables AI tools to quickly understand system architecture and reduces context window usage

### Configuration Management
The system uses an **agent-centric configuration approach** that provides maximum modularity and flexibility:

### Agent-Centric Configuration
- **Agent-specific configs** (`config/agents/`) - Each agent has its own configuration namespace
- **Shared configurations** (`config/shared/`) - Global settings, models, and providers
- **Environment overrides** (`config/environments/`) - Environment-specific settings
- **Hot-reloading** - Configuration changes can be applied without restart
- **Dynamic configuration** loading with validation

### Configuration Structure
```
config/
├── agents/                          # Agent-specific configurations
│   ├── answer_agent/
│   │   ├── config.yaml             # Agent settings & behavior
│   │   ├── prompts.yaml            # Agent prompts & templates
│   │   └── models.yaml             # Agent model preferences
│   ├── evaluator_agent/
│   ├── escalation_router/
│   └── human_interface/
├── shared/                          # Global configurations
│   ├── models.yaml                 # Master model definitions
│   ├── system.yaml                 # System-wide settings
│   └── providers.yaml              # Provider configurations
├── environments/                    # Environment-specific overrides
│   ├── development.yaml
│   ├── testing.yaml
│   └── production.yaml
└── config.yaml                     # Main configuration coordinator
```

### Benefits of Agent-Centric Configuration
- **Developer Isolation**: Each agent has its own configuration namespace
- **Modular Testing**: Agents can be tested independently
- **Easy Agent Development**: New agents can be added without touching existing configs
- **Environment Management**: Clean separation of dev/test/prod settings
- **Hot-Reloading**: Configuration changes can be applied without restart
- **Clear Separation**: Agents, shared configs, and environments are clearly separated

### Human-in-the-Loop Architecture
- **Escalation thresholds** configurable per query type
- **Human agent routing** based on complexity and domain
- **Seamless handoff** between AI and human agents
- **Context preservation** across agent transitions

## Testing Structure

The system uses a comprehensive pytest-based test suite organized for maximum maintainability and coverage:

### Test Organization
```
tests/
├── unit/                           # Isolated unit tests
│   ├── core/                       # Core infrastructure tests
│   │   ├── test_config_system.py   # Configuration management (replaces simple_scripts/test_setup)
│   │   ├── test_logging_system.py  # Logging & error handling (replaces simple_scripts/test_logging)
│   │   ├── test_context_management.py # Context storage & retrieval
│   │   └── test_session_tracking.py   # Session metrics & lifecycle
│   ├── nodes/                      # LangGraph node tests
│   │   ├── test_answer_agent.py    # Answer generation logic
│   │   ├── test_evaluator_agent.py # Response evaluation
│   │   └── test_escalation_router.py # Human agent routing
│   ├── integrations/               # Integration component tests
│   │   ├── test_llm_providers.py   # LLM provider abstraction (replaces simple_scripts/test_local)
│   │   └── test_langsmith_setup.py # LangSmith integration
│   └── schemas/                    # Data model tests
│       ├── test_state_schema.py    # State validation
│       └── test_config_schemas.py  # Config validation
├── integration/                    # End-to-end integration tests
│   ├── test_workflow_orchestration.py # Complete workflow testing
│   ├── test_provider_factory.py      # Provider creation & switching
│   └── test_system_startup.py        # System initialization testing
├── fixtures/                       # Test data and utilities
│   ├── config_files/              # Test configurations
│   ├── mock_responses/             # LLM response mocks
│   └── test_data/                  # Sample conversations
└── README.md                       # Complete test documentation
```

### Test Features
- **Comprehensive Coverage**: Tests all critical system components with >90% code coverage target
- **Mock Strategy**: External APIs, file system, and heavy operations properly mocked
- **Error Testing**: Both success and failure scenarios thoroughly tested
- **Performance Testing**: Large datasets and concurrent operation validation
- **CI/CD Ready**: Fast execution, no external dependencies, reliable results

### Test Categories
- **Core Infrastructure**: Configuration, logging, context management, session tracking
- **Node Components**: Answer agents, evaluators, escalation routers
- **Integration**: LLM providers, workflow orchestration, system startup
- **Data Models**: State validation, configuration schemas
- **Edge Cases**: Error conditions, boundary values, performance limits

## Current Implementation Status

**Completed (75%)**:
- Core architecture and interfaces
- Configuration management system with comprehensive validation
- Context and session tracking with SQLite backend
- Structured logging and error handling system
- Comprehensive test suite with >90% coverage
- LLM provider abstraction and factory pattern
- Basic node implementations (AnswerAgent, EvaluatorAgent, EscalationRouter)

**In Progress**:
- Real LLM integration (infrastructure complete, models being integrated)
- Advanced workflow orchestration with LangGraph
- Human agent integration and handoff mechanisms
- Production monitoring and observability features

**Testing Status**: 
- ✅ Unit tests for all core infrastructure components
- ✅ Integration tests for system startup and configuration
- ✅ Mock-based testing for LLM providers and external dependencies
- ✅ Error scenario and edge case validation
- ✅ Performance and concurrency testing

## Dependencies and Tech Stack

- **Python 3.11+** with uv for dependency management
- **LangGraph/LangChain** for AI workflow orchestration
- **SQLite** for context storage and session tracking
- **Pydantic** for data validation and configuration
- **pytest** for testing with coverage reporting
- **ruff** for fast linting and code formatting
- **LangSmith** for workflow tracing and monitoring (optional)

## Key Configuration Files

### Agent-Centric Structure
- `config/config.yaml` - Main configuration coordinator and loading strategy
- `config/agents/*/config.yaml` - Agent-specific settings and behavior
- `config/agents/*/prompts.yaml` - Agent prompts and templates
- `config/agents/*/models.yaml` - Agent model preferences
- `config/shared/models.yaml` - Global model definitions
- `config/shared/system.yaml` - System-wide settings
- `config/shared/providers.yaml` - Provider configurations
- `config/environments/*.yaml` - Environment-specific overrides

### Development Files
- `pyproject.toml` - Project dependencies and tool configuration
- `Makefile` - Development workflow commands
- `scripts/configuration_tutorial.py` - Configuration tutorial and examples
- `config/config.json` - Experimentation settings (legacy format for compatibility)

## Environment Variables

Set these for full functionality:
- `OPENAI_API_KEY` - OpenAI API access
- `ANTHROPIC_API_KEY` - Anthropic API access
- `LANGCHAIN_API_KEY` - LangSmith tracing (optional)
- `LANGCHAIN_TRACING_V2` - Enable LangSmith tracing