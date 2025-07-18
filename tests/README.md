# Test Suite Documentation

This directory contains comprehensive unit and integration tests for the Modular LangGraph Hybrid System.

## Test Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── core/                       # Core infrastructure tests
│   │   ├── test_config_system.py   # Configuration management
│   │   ├── test_logging_system.py  # Logging and error handling
│   │   ├── test_context_management.py # Context storage and retrieval
│   │   └── test_session_tracking.py   # Session metrics and lifecycle
│   ├── nodes/                      # LangGraph node tests
│   │   ├── test_chatbot_agent.py   # Chatbot generation logic
│   │   ├── test_evaluator_agent.py # Response evaluation
│   │   └── test_escalation_router.py # Human agent routing
│   ├── integrations/               # Integration component tests
│   │   ├── test_llm_providers.py   # LLM provider abstraction
│   │   └── test_langsmith_setup.py # LangSmith integration
│   └── schemas/                    # Data model tests
│       ├── test_state_schema.py    # State validation
│       └── test_config_schemas.py  # Config validation
├── integration/                    # Integration tests
│   ├── test_workflow_orchestration.py # End-to-end workflows
│   ├── test_provider_factory.py      # Provider creation & switching
│   └── test_system_startup.py        # System initialization
├── fixtures/                       # Test data and utilities
│   ├── config_files/              # Test configurations
│   ├── mock_responses/             # LLM response mocks
│   └── test_data/                  # Sample conversations
└── test_*.py                       # Validation and framework tests
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

# Core infrastructure tests
uv run python -m pytest tests/unit/core/

# LLM provider tests
uv run python -m pytest tests/unit/integrations/
```

### Run with Coverage
```bash
uv run python -m pytest --cov=src --cov-report=html
```

### Run Specific Test File
```bash
uv run python -m pytest tests/unit/core/test_config_system.py -v
```

### Run Specific Test Function
```bash
uv run python -m pytest tests/unit/core/test_config_system.py::TestConfigManager::test_initialization_success -v
```

## Test Features

### Comprehensive Coverage
- **Configuration Management**: Tests all aspects of config loading, validation, and management
- **Logging System**: Tests structured logging, error handling, and context management
- **Context Storage**: Tests SQLite-based context storage and retrieval
- **Session Tracking**: Tests session metrics and lifecycle management
- **LLM Providers**: Tests provider abstraction and model integration
- **System Integration**: Tests end-to-end system startup and workflows

### Mock Strategy
- **External Services**: OpenAI API, LangSmith API, file system operations
- **Heavy Operations**: Model loading, database queries, network calls
- **Environment Dependencies**: Environment variables, system time
- **Provider Interfaces**: Test doubles for provider contracts

### Test Data Management
- **Temporary Files**: All tests use temporary directories and files
- **Sample Configurations**: Valid and invalid config examples
- **Mock Responses**: Realistic LLM response data
- **Edge Cases**: Error conditions and boundary values

### Error Testing
- **Configuration Errors**: Missing files, invalid JSON/YAML, validation failures
- **Runtime Errors**: Model failures, network timeouts, database issues
- **Recovery Testing**: Fallback mechanisms and error recovery
- **Performance Testing**: Large datasets and concurrent operations

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
- No external dependencies (all mocked)
- Fast execution (< 30 seconds for full suite)
- Reliable (no flaky tests)
- Comprehensive coverage (>90% code coverage target)

## Replacing Simple Scripts

This comprehensive test suite replaces the previous simple scripts:
- `tests/simple_scripts/test_setup/` → `tests/unit/core/test_config_system.py`
- `tests/simple_scripts/test_logging/` → `tests/unit/core/test_logging_system.py`  
- `tests/simple_scripts/test_local/` → `tests/unit/integrations/test_llm_providers.py`

The new test suite provides:
- **Automated execution** with pytest
- **Proper assertions** and test isolation
- **Coverage reporting** to track completeness
- **CI/CD integration** capability
- **Better maintainability** with structured organization