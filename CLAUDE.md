# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

* Always review src/interfaces before making changes to the code.

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
This is a **Human-in-the-Loop (HITL) AI System** - a sophisticated platform designed to improve both customer and employee experience through intelligent AI-human collaboration. The system intercepts all customer-AI interactions to ensure quality, detect frustration, and route escalations while protecting employee wellbeing. Built around specialized LangGraph nodes that work together to create a comprehensive support experience.

### Key Components

**HITL LangGraph Nodes** (`src/nodes/`):
- `MockAutomationAgent` - Handles routine automated insurance tasks (policy lookups, claims, billing) with intelligent escalation
- `ChatbotAgent` (Chatbot) - Customer service-focused response generation with emotional intelligence
- `QualityAgent` - Reviews all chatbot responses before delivery, with improvement capabilities  
- `FrustrationAgent` - Real-time customer sentiment analysis and intervention triggers
- `RoutingAgent` - Employee wellbeing-aware routing with workload balancing
- `ContextManagerAgent` - Multi-source context aggregation and audience-specific summarization

**Simulation Framework** (`src/simulation/`):
- `HumanCustomerSimulator` - Realistic customer personality and scenario simulation
- `EmployeeSimulator` - Human agent response and workload simulation  
- `DemoOrchestrator` - End-to-end HITL workflow demonstration with 6 scenarios

**Core Infrastructure** (`src/core/`):
- `AgentConfigManager` - Handles agent-centric configuration with hot-reloading
- `ContextManager` - Manages conversation context and memory (SQLite-based)
- `DatabaseConfig` - Centralized database path management and migration utilities
- `SessionTracker` - Tracks metrics and performance data
- `WorkflowOrchestrator` - Coordinates node execution and state management
- Integrated logging/error handling system in `/core/logging/`

**Agent-Centric Configuration System** (`config/`):
- `config/agents/mock_automation_agent/` - Automation task repertoire, insurance mock data, and response templates
- `config/agents/quality_agent/` - Quality assessment thresholds and prompts
- `config/agents/frustration_agent/` - Frustration indicators and intervention settings
- `config/agents/routing_agent/` - Employee wellbeing and routing strategies
- `config/agents/context_manager_agent/` - Context sources and relevance scoring
- `config/agents/chatbot_agent/` - Customer service prompts and service standards
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
│   ├── chatbot_agent/
│   │   ├── config.yaml             # Agent settings & behavior (NO model config)
│   │   ├── prompts.yaml            # Agent prompts & templates
│   │   └── models.yaml             # Agent model preferences (SINGLE SOURCE)
│   ├── evaluator_agent/
│   ├── escalation_router/
│   └── human_interface/
├── shared/                          # Global configurations
│   ├── models.yaml                 # Master model definitions & aliases
│   ├── system.yaml                 # System-wide settings
│   └── providers.yaml              # Provider configurations
├── environments/                    # Environment-specific overrides
│   ├── development.yaml
│   ├── testing.yaml
│   └── production.yaml
└── config.yaml                     # Main configuration coordinator
```

### Model Configuration Consolidation
**IMPORTANT**: As of the latest update, model configuration has been consolidated:
- **models.yaml is the SINGLE SOURCE** for all model preferences per agent
- **config.yaml files NO LONGER contain model sections** - these have been removed
- **Standardized structure** uses `primary_model` and `model_preferences` in models.yaml
- **No duplication** - eliminates conflicts between config.yaml and models.yaml model settings

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

### Database Management
The system uses a **centralized database configuration approach** for consistent data storage:

**Database Organization** (`data/`):
- All database files centralized in `data/` directory
- Context storage: `data/hybrid_system.db` (SQLite)
- Backup storage: `data/backups/` with automated migration backups
- Environment-specific databases: `data/dev/`, `data/test/`, `data/prod/`

**Database Configuration** (`src/core/database_config.py`):
- `DatabaseConfig` class provides centralized path management
- Automatic database migration from legacy locations
- Configurable storage directories per environment
- Backup and cleanup utilities for database maintenance
- Integration with agent configuration system for dynamic paths

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
│   │   ├── test_mock_automation_agent.py # Automation task handling and escalation
│   │   ├── test_chatbot_agent.py   # Chatbot generation logic
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
- **Node Components**: Mock automation agent, answer agents, evaluators, escalation routers
- **Integration**: LLM providers, workflow orchestration, system startup
- **Data Models**: State validation, configuration schemas
- **Edge Cases**: Error conditions, boundary values, performance limits

## Current Implementation Status

**Completed (98%)**:
- Complete HITL architecture with 6 specialized agents including MockAutomationAgent
- Mock automation system for routine insurance tasks with intelligent escalation
- Automation-first workflow: Automation → AI Chatbot → Human Escalation
- Quality interception system with response improvement
- Real-time frustration detection and employee protection
- Intelligent routing with workload balancing and wellbeing considerations
- Multi-source context aggregation with audience-specific summarization
- Comprehensive simulation framework with 6 demo scenarios
- Customer service-focused chatbot with emotional intelligence
- Agent-centric configuration system with extensive customization
- Core infrastructure: context management, session tracking, logging
- LLM provider abstraction with multi-provider support

**In Progress (2%)**:
- Advanced monitoring dashboard for customer satisfaction and employee wellbeing metrics
- Real-time web search integration for context manager
- Multi-language support for frustration detection

**Testing Status**: 
- ✅ Unit tests for all core infrastructure components including MockAutomationAgent
- ✅ Integration tests for system startup and configuration
- ✅ Mock-based testing for LLM providers and external dependencies
- ✅ Error scenario and edge case validation for automation tasks
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
- `config/agents/*/config.yaml` - Agent-specific settings and behavior (**NO model config**)
- `config/agents/*/prompts.yaml` - Agent prompts and templates
- `config/agents/*/models.yaml` - **SINGLE SOURCE** for agent model preferences
- `config/shared/models.yaml` - Global model definitions and aliases
- `config/shared/system.yaml` - System-wide settings
- `config/shared/providers.yaml` - Provider configurations
- `config/environments/*.yaml` - Environment-specific overrides

### Model Configuration Changes (Latest Update)
- **CONSOLIDATED**: All model configuration moved to `models.yaml` files only
- **REMOVED**: Model sections from all `config.yaml` files to eliminate duplication
- **STANDARDIZED**: Consistent `primary_model` + `model_preferences` structure across all agents

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