# Hybrid AI-Human System: LangGraph Multi-Agent Workflow

A sophisticated AI workflow orchestration platform that combines intelligent agents with human-in-the-loop capabilities. Built with LangGraph, this system demonstrates how to create scalable, maintainable AI applications that seamlessly integrate AI automation with human expertise.

## 🎯 Overview

This system showcases a **Modular LangGraph Hybrid Architecture** where specialized AI agents work together to process user queries, evaluate responses, and escalate to human experts when needed. It's designed as both a production-ready system and an educational resource for learning AI agent development.

### Key Features

- **🤖 Multi-Agent Workflow**: Specialized agents for answering, evaluation, and escalation
- **🔄 Human-in-the-Loop**: Seamless handoffs between AI and human agents
- **📊 Advanced Monitoring**: LangSmith integration for tracing and analytics
- **⚙️ Flexible Configuration**: Support for multiple LLM providers with fallback strategies
- **🎓 Educational**: Comprehensive tutorial for learning AI agent concepts
- **🧪 Test-Driven**: >90% test coverage with comprehensive test suite

## 🏗️ Architecture

```
src/
├── core/                          # Core infrastructure
│   ├── config/                    # Configuration management system
│   ├── logging/                   # Structured logging and error handling
│   ├── context_manager.py         # Conversation context with SQLite
│   └── session_tracker.py         # Performance metrics tracking
├── interfaces/                    # Clean separation of concerns
│   ├── core/                      # Core system interfaces
│   ├── nodes/                     # Node behavior contracts
│   └── workflows/                 # Workflow orchestration interfaces
├── nodes/                         # LangGraph agent implementations
│   ├── answer_agent.py            # AI response generation
│   ├── evaluator_agent.py         # Quality assessment and escalation
│   └── escalation_router.py       # Human agent routing
├── integrations/                  # External service integrations
│   └── llm_providers.py           # Multi-provider LLM abstraction
└── workflows/                     # Complete workflow orchestration
    └── hybrid_workflow.py         # Main system orchestration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- uv (recommended) or pip for dependency management

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd hybrid-ai-system

# Setup with uv (recommended)
make setup

# Or manually with uv
uv sync --dev
```

### Configuration

Create a `.env` file in the project root with your configuration:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your API keys
nano .env
```

**.env file contents:**
```bash
# LLM Provider API Keys (optional - system works with local models)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Monitoring and Tracing (optional)
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=hybrid-ai-system

# Environment Setting
ENVIRONMENT=development
```

**Note**: The `.env` file is automatically loaded by the system and contains only environment variables. System configuration is handled through the files in the `/config/` directory.

### Run the System

```bash
# Run the main application
make run

# Or with custom configuration
uv run python -m src.main --config-path config/custom_config.json
```

## 🎓 Learning Guide

### For Beginners: Start with the Tutorial

We've created a comprehensive Jupyter notebook that explains AI agents from the ground up:

```bash
# Launch Jupyter to access the tutorial
jupyter lab notebooks/AI_Agents_Tutorial.ipynb
```

**The tutorial covers:**
- What are AI agents? (with real-world analogies)
- How do they work together?
- Hands-on examples with working code
- Build your own simple agent
- Understanding the real system architecture

### For Developers: Explore the Implementation

1. **Core Concepts**: Start with `/src/interfaces/` to understand the system contracts
2. **Agent Implementation**: Look at `/src/nodes/` for actual agent logic
3. **Configuration**: Examine `/config/` for system setup
4. **Testing**: Review `/tests/` for comprehensive examples

## 🤖 The Four Core Agents

### 1. Answer Agent (`answer_agent.py`)
**Purpose**: Generate intelligent responses to user queries
- Uses multiple LLM providers with automatic fallback
- Integrates conversation context for personalized responses
- Tracks performance metrics and token usage

### 2. Evaluator Agent (`evaluator_agent.py`)
**Purpose**: Assess response quality and determine escalation needs
- Scores responses on accuracy, completeness, and clarity
- Considers user history and interaction patterns
- Makes intelligent escalation decisions

### 3. Escalation Router (`escalation_router.py`)
**Purpose**: Route complex issues to appropriate human experts
- Analyzes query complexity and required expertise
- Assigns priority levels and estimates resolution time
- Manages human agent availability and workload

### 4. Human Interface (planned)
**Purpose**: Facilitate smooth AI-to-human handoffs
- Provides context summaries for human agents
- Manages conversation state during human interactions
- Captures feedback for system improvement

## ⚙️ Configuration System

The system uses a hierarchical configuration approach:

### Model Configuration (`config/models.yaml`)
```yaml
models:
  llama-7b:
    path: "models/llama-7b.gguf"
    type: "llama"
    context_length: 2048
    temperature: 0.7
  gpt-4:
    type: "openai"
    model_name: "gpt-4"
    temperature: 0.7

default_model: "llama-7b"
fallback_models: ["gpt-4", "claude-3-sonnet"]
```

### Prompts Configuration (`config/prompts.json`)
```json
{
  "answer_agent": {
    "system_prompt": "You are a helpful AI assistant...",
    "context_integration": "Use previous conversation context..."
  },
  "evaluator_agent": {
    "escalation_thresholds": {
      "low_score": 4.0,
      "repeat_query": true
    }
  }
}
```

## 🧪 Testing & Quality

### Run Tests
```bash
# Run all tests with coverage
make test

# Run specific test categories
uv run python -m pytest tests/unit/core/ -v          # Core infrastructure
uv run python -m pytest tests/unit/nodes/ -v         # Agent components
uv run python -m pytest tests/integration/ -v        # End-to-end tests

# Generate coverage report
uv run python -m pytest --cov=src --cov-report=html
```

### Code Quality
```bash
# Run all quality checks
make check

# Individual tools
make format     # Format with ruff
make lint       # Lint with ruff
make type-check # Type check with mypy
```

## 📊 Monitoring & Observability

### LangSmith Integration
- **Automatic Tracing**: All agent interactions are traced
- **Performance Metrics**: Token usage, latency, and costs
- **Error Tracking**: Detailed error context and stack traces
- **Custom Metrics**: Domain-specific performance indicators

### Structured Logging
- **Multi-level Logging**: Debug, info, warning, error levels
- **Contextual Information**: Request IDs, user context, timing
- **Custom Log Types**: Model calls, escalations, system events

## 🔄 Workflow Example

```python
# Simplified workflow demonstration
state = {
    "query": "Help me debug my Python code",
    "user_id": "user_123",
    "session_id": "session_456"
}

# 1. Answer Agent generates response
state = answer_agent(state)
# Result: AI provides initial code debugging advice

# 2. Evaluator assesses quality
state = evaluator_agent(state)
# Result: Determines if response meets quality thresholds

# 3. Router handles escalation (if needed)
if state["escalation_decision"]:
    state = escalation_router(state)
    # Result: Routes to technical support specialist

# 4. Final response delivered
return state["final_response"]
```

## 🛠️ Development

### Adding New Agents

1. **Create the Agent**: Implement the `NodeInterface` in `/src/nodes/`
2. **Add Configuration**: Update `/config/prompts.json`
3. **Integrate Workflow**: Modify `/src/workflows/hybrid_workflow.py`
4. **Add Tests**: Create tests in `/tests/unit/nodes/`

### Extending LLM Support

1. **Provider Implementation**: Add to `/src/integrations/llm_providers.py`
2. **Configuration**: Update `/config/models.yaml`
3. **Factory Integration**: Modify `LLMProviderFactory`

### Custom Configurations

1. **Environment-Specific**: Create configs in `/config/`
2. **Runtime Override**: Use command-line arguments
3. **Dynamic Loading**: Implement custom config providers

## 📈 Production Deployment

### Docker Support
```bash
# Build container
docker build -t hybrid-ai-system .

# Run with .env file
docker run --env-file .env hybrid-ai-system

# Or mount .env file as volume
docker run -v $(pwd)/.env:/app/.env hybrid-ai-system
```

### Environment Configuration
- **Development**: Comprehensive logging, local models
- **Production**: Optimized performance, cloud models, monitoring
- **Testing**: Mock providers, isolated database

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Add tests** for new functionality
4. **Ensure** all tests pass (`make test`)
5. **Check** code quality (`make check`)
6. **Commit** changes (`git commit -m 'Add amazing feature'`)
7. **Submit** a pull request

### Development Guidelines
- Follow the existing code style and patterns
- Add comprehensive tests for new features
- Update documentation for user-facing changes
- Use type hints and docstrings
- Keep components modular and testable

## 📚 Additional Resources

- **[Tutorial Notebook](notebooks/AI_Agents_Tutorial.ipynb)**: Complete beginner's guide
- **[API Documentation](docs/)**: Detailed interface documentation
- **[Test Examples](tests/)**: Comprehensive usage examples
- **[Configuration Guide](config/)**: System setup and customization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 Use Cases

This system architecture is suitable for:
- **Customer Support**: Automated assistance with expert escalation
- **Technical Documentation**: AI-powered help with human validation
- **Educational Platforms**: Tutoring systems with teacher oversight
- **Content Moderation**: AI screening with human review
- **Code Review**: Automated analysis with developer consultation

Built with ❤️ using [LangGraph](https://langchain-ai.github.io/langgraph/), [LangChain](https://langchain.com/), and [LangSmith](https://smith.langchain.com/).