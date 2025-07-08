# Development Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Code Organization](#code-organization)
4. [Development Workflow](#development-workflow)
5. [Testing Strategy](#testing-strategy)
6. [Code Quality](#code-quality)
7. [Adding New Features](#adding-new-features)
8. [Common Patterns](#common-patterns)
9. [Debugging](#debugging)
10. [Performance Optimization](#performance-optimization)

## Getting Started

### Prerequisites
- Python 3.11+
- Docker Desktop
- VSCode or Cursor with Dev Containers extension
- Git

### Quick Setup
```bash
# Clone and open in dev container
git clone [repository-url]
cd hybrid-ai-system
code .  # Opens VSCode
# When prompted, click "Reopen in Container"

# Verify setup
make test
make run
```

## Development Environment

### Dev Container Configuration
The project includes a fully configured development container with:
- Python 3.11 with uv package manager
- All development tools pre-installed
- VSCode extensions for Python development
- Jupyter Lab for interactive development
- Pre-commit hooks for code quality

### Environment Variables
Create a `.env` file from the template:
```bash
cp .env.example .env
# Edit .env with your API keys (optional for local development)
```

### Available Commands
```bash
# Setup and installation
make setup          # Complete project setup
make install         # Install dependencies
make install-dev     # Install with dev dependencies

# Testing
make test           # Run all tests
make test-unit      # Run unit tests only
make test-integration # Run integration tests
make coverage       # Generate coverage report

# Code quality
make format         # Format code with ruff
make lint           # Lint code
make type-check     # Type checking with mypy
make check          # Run all quality checks

# Running the system
make run            # Run main application
make jupyter        # Start Jupyter Lab
make demo           # Run comprehensive demo

# Utilities
make clean          # Clean generated files
make help           # Show all commands
```

## Code Organization

### Directory Structure
```
src/
├── core/                    # Core infrastructure
│   ├── config/             # Configuration management
│   ├── logging/            # Logging and error handling
│   ├── context_manager.py  # Conversation context
│   └── session_tracker.py  # Performance tracking
├── interfaces/             # Abstract interfaces
│   ├── core/              # Core system interfaces
│   ├── nodes/             # Node behavior contracts
│   └── workflows/         # Workflow interfaces
├── nodes/                 # LangGraph agent implementations
│   ├── answer_agent.py    # AI response generation
│   ├── evaluator_agent.py # Quality assessment
│   └── escalation_router.py # Human routing
├── integrations/          # External service integrations
│   └── llm_providers.py   # Multi-provider LLM access
└── workflows/             # Workflow orchestration
    └── hybrid_workflow.py # Main system workflow
```

### Configuration Structure
```
config/
├── models.yaml           # LLM model configurations
├── prompts.json         # System prompts for each agent
├── config.json          # Core system settings
└── logging.yaml         # Logging configuration
```

### Testing Structure
```
tests/
├── unit/                # Unit tests
│   ├── core/           # Core component tests
│   ├── nodes/          # Agent tests
│   └── integrations/   # Integration tests
├── integration/         # End-to-end tests
├── fixtures/           # Test data and utilities
│   ├── config_files/   # Test configurations
│   ├── mock_responses/ # Mock LLM responses
│   └── test_data/      # Sample data
└── README.md           # Testing documentation
```

## Development Workflow

### 1. Feature Development Process
```bash
# 1. Create feature branch
git checkout -b feature/new-agent

# 2. Develop with TDD approach
# Write tests first, then implementation

# 3. Run tests frequently
make test

# 4. Check code quality
make check

# 5. Commit with clear messages
git commit -m "Add: new sentiment analysis agent"

# 6. Push and create PR
git push origin feature/new-agent
```

### 2. Code Review Checklist
- [ ] Tests written and passing
- [ ] Code follows project patterns
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Error handling implemented
- [ ] Performance considerations addressed
- [ ] Configuration updated if needed

### 3. Integration Testing
```bash
# Test with different model providers
ENVIRONMENT=testing make test

# Test with mock providers
MOCK_LLM_PROVIDERS=true make test

# Performance testing
make test-performance
```

## Testing Strategy

### Testing Levels

#### 1. Unit Tests (`tests/unit/`)
Test individual components in isolation:
```python
def test_answer_agent_generates_response():
    # Arrange
    agent = AnswerAgentNode(mock_config, mock_context)
    state = create_test_state(query="Hello")
    
    # Act
    result = agent(state)
    
    # Assert
    assert "ai_response" in result
    assert result["next_action"] == "evaluate"
```

#### 2. Integration Tests (`tests/integration/`)
Test component interactions:
```python
def test_workflow_end_to_end():
    # Test complete workflow from query to response
    workflow = HybridWorkflow(config, context, tracker)
    result = workflow.process_query("Help me debug my code", "user123", "session456")
    assert result["workflow_complete"] is True
```

#### 3. Mock Strategy
```python
# Mock external dependencies
@patch('src.integrations.llm_providers.ChatOpenAI')
def test_with_mock_llm(mock_openai):
    mock_openai.return_value.invoke.return_value.content = "Mocked response"
    # Test logic without actual API calls
```

### Test Data Management
```python
# Use fixtures for consistent test data
@pytest.fixture
def sample_state():
    return {
        "query_id": "test_123",
        "user_id": "user_123",
        "session_id": "session_123",
        "query": "Test query",
        "timestamp": datetime.now()
    }
```

### Running Tests
```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
uv run pytest tests/unit/nodes/test_answer_agent.py -v

# Run with specific markers
uv run pytest -m "not slow" -v

# Run tests in parallel
uv run pytest -n auto
```

## Code Quality

### Code Formatting
The project uses `ruff` for fast linting and formatting:
```bash
# Format all code
make format

# Lint without fixing
make lint

# Lint with auto-fix
make lint-fix
```

### Type Checking
Use MyPy for static type checking:
```bash
make type-check
```

### Code Style Guidelines

#### 1. Function Documentation
```python
def process_user_query(
    self, 
    query: str, 
    user_id: str, 
    session_id: str
) -> HybridSystemState:
    """Process user query through the complete workflow.
    
    Args:
        query: User's question or request
        user_id: Unique user identifier
        session_id: Session identifier for context
        
    Returns:
        Complete state after workflow processing
        
    Raises:
        ConfigurationError: If system is not properly configured
        ModelError: If all LLM providers fail
    """
```

#### 2. Error Handling
```python
try:
    response = self.llm_provider.generate_response(prompt)
except ModelInferenceError as e:
    self.logger.error(
        "Model inference failed",
        extra={
            "model_name": self.model_config.name,
            "error": str(e),
            "prompt_length": len(prompt)
        }
    )
    raise
```

#### 3. Logging
```python
# Use structured logging
self.logger.info(
    "Processing user query",
    extra={
        "user_id": user_id,
        "query_length": len(query),
        "session_id": session_id,
        "operation": "process_query"
    }
)
```

### Pre-commit Hooks
The project uses pre-commit hooks for quality assurance:
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Adding New Features

### 1. Adding a New Agent

#### Step 1: Create the Agent
```python
# src/nodes/sentiment_agent.py
from ..interfaces.nodes.base import NodeInterface
from ..interfaces.core.state_schema import HybridSystemState

class SentimentAgentNode(NodeInterface):
    def __init__(self, config_provider, context_provider):
        self.config_provider = config_provider
        self.context_provider = context_provider
    
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        sentiment = self._analyze_sentiment(state["query"])
        return {
            **state,
            "sentiment_analysis": sentiment,
            "next_action": "continue"
        }
    
    def validate_state(self, state: HybridSystemState) -> bool:
        return "query" in state
    
    @property
    def node_name(self) -> str:
        return "SentimentAgent"
    
    @property
    def required_state_keys(self) -> List[str]:
        return ["query"]
    
    @property
    def output_state_keys(self) -> List[str]:
        return ["sentiment_analysis"]
```

#### Step 2: Add Configuration
```json
// config/prompts.json
{
    "sentiment_agent": {
        "system_prompt": "Analyze the sentiment of user queries...",
        "confidence_threshold": 0.8
    }
}
```

#### Step 3: Add to Workflow
```python
# src/workflows/hybrid_workflow.py
workflow.add_node("sentiment_agent", SentimentAgentNode(config, context))
workflow.add_edge("sentiment_agent", "answer_agent")
```

#### Step 4: Add Tests
```python
# tests/unit/nodes/test_sentiment_agent.py
def test_sentiment_agent_analyzes_positive():
    agent = SentimentAgentNode(mock_config, mock_context)
    state = {"query": "I love this product!"}
    
    result = agent(state)
    
    assert "sentiment_analysis" in result
    assert result["sentiment_analysis"]["polarity"] > 0
```

### 2. Adding a New LLM Provider

#### Step 1: Implement Provider
```python
# src/integrations/custom_provider.py
class CustomLLMProvider(LLMProvider):
    def _initialize_client(self):
        return CustomLLMClient(
            api_key=os.getenv("CUSTOM_API_KEY"),
            model=self.model_config.model_name
        )
    
    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        # Custom implementation
        pass
```

#### Step 2: Add to Factory
```python
# src/integrations/llm_providers.py
def _initialize_client(self) -> BaseChatModel:
    if self.provider_type == "custom":
        return self._setup_custom()
    # ... existing providers
```

#### Step 3: Update Configuration
```yaml
# config/models.yaml
custom-model:
  type: "custom"
  model_name: "custom-model-v1"
  api_endpoint: "https://api.custom.com/v1"
```

### 3. Adding New Configuration

#### Step 1: Update Schema
```python
# src/core/config/models.py
@dataclass
class CustomConfig:
    feature_enabled: bool
    threshold: float
    options: List[str]
```

#### Step 2: Add to ConfigProvider
```python
# src/core/config/manager.py
@property
def custom_config(self) -> CustomConfig:
    return self._load_custom_config()
```

#### Step 3: Update Configuration Files
```json
// config/config.json
{
    "custom_feature": {
        "feature_enabled": true,
        "threshold": 0.8,
        "options": ["option1", "option2"]
    }
}
```

## Common Patterns

### 1. Error Handling Pattern
```python
from ..core.logging import get_logger
from ..core.logging.exceptions import CustomError

class MyComponent:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def process(self, data):
        try:
            result = self._do_processing(data)
            self.logger.info("Processing completed", extra={"result_size": len(result)})
            return result
        except Exception as e:
            self.logger.error(
                "Processing failed",
                exc_info=True,
                extra={"data_size": len(data), "error": str(e)}
            )
            raise CustomError(f"Processing failed: {e}") from e
```

### 2. Configuration Access Pattern
```python
class ConfigurableComponent:
    def __init__(self, config_provider: ConfigProvider):
        self.config_provider = config_provider
        self.config = self._load_config()
    
    def _load_config(self):
        return {
            "threshold": self.config_provider.get_config("component.threshold", 0.8),
            "enabled": self.config_provider.get_config("component.enabled", True)
        }
```

### 3. State Management Pattern
```python
def process_state(self, state: HybridSystemState) -> HybridSystemState:
    # Validate input
    if not self.validate_state(state):
        raise ValueError("Invalid state for processing")
    
    # Process
    result = self._do_processing(state)
    
    # Return updated state
    return {
        **state,  # Preserve existing state
        "new_field": result,  # Add new data
        "next_action": "next_step"  # Update workflow control
    }
```

### 4. Testing Pattern
```python
class TestMyComponent:
    @pytest.fixture
    def component(self, mock_config_provider):
        return MyComponent(mock_config_provider)
    
    @pytest.fixture
    def sample_state(self):
        return create_test_state(query="test query")
    
    def test_happy_path(self, component, sample_state):
        result = component.process(sample_state)
        assert result["expected_field"] == "expected_value"
    
    def test_error_handling(self, component):
        with pytest.raises(CustomError):
            component.process(invalid_state)
```

## Debugging

### 1. Local Debugging
```python
# Add breakpoints in your IDE or use debugger
import pdb; pdb.set_trace()

# Use logging for runtime debugging
self.logger.debug("Debug info", extra={"variable": value})
```

### 2. LangSmith Tracing
Enable LangSmith for detailed workflow tracing:
```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your_key
```

### 3. Test Debugging
```bash
# Run single test with verbose output
uv run pytest tests/unit/nodes/test_answer_agent.py::test_specific_function -v -s

# Debug test with pdb
uv run pytest --pdb tests/unit/nodes/test_answer_agent.py
```

### 4. Component Isolation
```python
# Test components in isolation
def debug_answer_agent():
    config = create_test_config()
    context = create_test_context()
    agent = AnswerAgentNode(config, context)
    
    state = create_test_state(query="Debug query")
    result = agent(state)
    
    print(f"Result: {result}")
    return result
```

### 5. Log Analysis
```bash
# View real-time logs
tail -f logs/app.log

# Filter specific components
grep "AnswerAgent" logs/app.log

# View structured logs
cat logs/app.log | jq '.message'
```

## Performance Optimization

### 1. Profiling
```python
# Profile code execution
import cProfile
import pstats

def profile_workflow():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run workflow
    workflow.process_query("test", "user", "session")
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative').print_stats(10)
```

### 2. Memory Optimization
```python
# Use context managers for large objects
class LargeResourceManager:
    def __enter__(self):
        self.resource = load_large_resource()
        return self.resource
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.resource
```

### 3. Async Operations
```python
# Use async for I/O bound operations
import asyncio

async def async_llm_call(prompt):
    return await self.async_client.agenerate(prompt)

# Batch operations
async def process_multiple_queries(queries):
    tasks = [async_llm_call(q) for q in queries]
    return await asyncio.gather(*tasks)
```

### 4. Caching Strategies
```python
from functools import lru_cache

class CachedComponent:
    @lru_cache(maxsize=128)
    def expensive_operation(self, input_data):
        # Expensive computation
        return result
```

### 5. Database Optimization
```python
# Batch database operations
def batch_save_context(entries: List[ContextEntry]):
    with self.db.transaction():
        for entry in entries:
            self.db.save(entry)

# Use connection pooling
class DatabaseManager:
    def __init__(self):
        self.pool = create_connection_pool(max_connections=10)
```

### 6. Monitoring Performance
```python
# Add timing decorators
from functools import wraps
import time

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        logger.info(
            f"{func.__name__} execution time",
            extra={"duration": duration, "function": func.__name__}
        )
        return result
    return wrapper

@timing_decorator
def slow_function():
    # Function implementation
    pass
```

## Best Practices Summary

### Code Quality
1. Write tests first (TDD approach)
2. Use type hints consistently
3. Follow the interface contracts
4. Handle errors gracefully
5. Use structured logging
6. Document public APIs

### Performance
1. Profile before optimizing
2. Use async for I/O operations
3. Cache expensive computations
4. Batch database operations
5. Monitor resource usage

### Maintainability
1. Keep components small and focused
2. Use dependency injection
3. Follow established patterns
4. Update documentation
5. Regular refactoring

### Security
1. Validate all inputs
2. Use environment variables for secrets
3. Log security events
4. Regular dependency updates
5. Follow principle of least privilege