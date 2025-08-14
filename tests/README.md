# Test Suite Documentation

This directory contains comprehensive unit and integration tests for the Modular LangGraph Hybrid System.

## Test Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── core/                       # Core infrastructure tests
│   │   └── test_agent_config_system.py # Agent-centric configuration management
│   ├── nodes/                      # Node component tests
│   │   └── test_node_initialization.py # Basic node initialization and interface
│   └── integrations/               # Integration component tests (placeholder)
├── integration/                    # Integration tests
│   └── test_agent_system_startup.py   # System initialization and component integration
└── README.md                       # This documentation
```

## Running Tests

### Run All Tests
```bash
uv run python -m pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
uv run python -m pytest tests/unit/

# Integration tests only
uv run python -m pytest tests/integration/

# Core infrastructure tests (agent configuration)
uv run python -m pytest tests/unit/core/

# Node initialization tests
uv run python -m pytest tests/unit/nodes/
```

### Run with Coverage
```bash
uv run python -m pytest --cov=src --cov-report=html
```

### Run Specific Test File
```bash
uv run python -m pytest tests/unit/core/test_agent_config_system.py -v
```

### Run Specific Test Function
```bash
uv run python -m pytest tests/unit/core/test_agent_config_system.py::TestAgentConfigManager::test_initialization_success -v
```

## Test Features

### Current Coverage
- **Agent Configuration System**: Comprehensive tests for agent-centric configuration management including loading, validation, model preferences, and environment overrides
- **Node Initialization**: Basic tests for all node types ensuring proper initialization and interface compliance
- **System Integration**: End-to-end system startup testing with proper component integration

### Test Strategy
- **Focused Testing**: Tests concentrate on public interfaces and core functionality
- **Mock External Dependencies**: LLM providers, external APIs, and heavy operations are mocked
- **Temporary Resources**: Tests use temporary directories and files for isolation
- **Environment Agnostic**: Tests work regardless of API key availability or external services

### Key Test Areas
- **Configuration Loading**: Agent configs, system configs, model preferences, and environment overrides
- **Component Integration**: Proper initialization of core system components
- **Error Handling**: Graceful handling of missing configurations and initialization failures
- **Interface Compliance**: All nodes implement expected interfaces and return proper state objects

## Test Development Guidelines

### Writing New Tests
1. **Isolation**: Each test should be independent and not rely on external state
2. **Mocking**: Mock external dependencies to ensure tests are fast and reliable
3. **Coverage**: Test both happy path and error conditions
4. **Clarity**: Use descriptive test names and clear assertions

### Test Naming Convention
- Test files: `test_<component>_<system>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<functionality>_<scenario>`

### Fixtures and Utilities
- Use pytest fixtures for reusable test setup
- Create temporary files and directories for file system tests
- Mock external API calls and heavy operations
- Validate both positive and negative test cases

## Debugging Tests

### Verbose Output
```bash
uv run python -m pytest -v --tb=short
```

### Debug Specific Test
```bash
uv run python -m pytest tests/unit/core/test_config_system.py::TestConfigManager::test_initialization_success -v -s
```

### Show Test Coverage
```bash
uv run python -m pytest --cov=src --cov-report=term-missing
```

## Continuous Integration

These tests are designed to run in CI/CD environments:
- No external dependencies (all properly mocked)
- Fast execution (< 10 seconds for full suite)
- Reliable (focused on stable public interfaces)
- Clean and maintainable (minimal legacy clutter)

## Test Philosophy

This test suite follows a **lean testing approach** suitable for a system in development:

### What We Test
- **Core Infrastructure**: Agent configuration system that powers the entire application
- **Public Interfaces**: Node initialization and basic call patterns
- **System Integration**: End-to-end component integration and startup

### What We Don't Test
- Private implementation details that may change during development
- Complex business logic that isn't yet finalized
- Legacy components that aren't part of the current system

### Benefits
- **Fast feedback**: Tests run quickly and provide immediate validation
- **Maintainable**: Focused tests that don't break when internal implementations change
- **Clear purpose**: Each test has a specific, important function
- **Development friendly**: Tests support rapid iteration without being overly constraining