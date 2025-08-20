# Human-in-the-Loop AI System: Improving Customer AND Employee Experience

A sophisticated AI workflow orchestration platform that enhances both customer support quality and employee wellbeing through intelligent human-AI collaboration. The system intercepts all customer-AI interactions to ensure quality, detect frustration, and route escalations while protecting employee mental health and job satisfaction.

## 🎯 Overview

This system implements a **Human-in-the-Loop (HITL) Architecture** that goes beyond simple escalation - it actively improves the entire support experience for customers while protecting employees from burnout and frustration overload. Every AI response is quality-checked, customer frustration is monitored in real-time, and human routing considers both customer needs and employee wellbeing.

### Key Features

- **🛡️ Quality Interception**: All AI responses reviewed and improved before customer delivery
- **😤 Frustration Detection**: Real-time sentiment analysis with intelligent escalation triggers  
- **👥 Employee Protection**: Workload balancing and burnout prevention with wellbeing metrics
- **🎯 Intelligent Routing**: LLM-powered smart assignment considering customer needs and employee wellbeing
- **📊 Context Management**: Multi-source context aggregation with audience-specific summarization


## 🏗️ Architecture

```
src/
├── core/                          # Core infrastructure
│   ├── config/                    # Agent-centric configuration system
│   ├── logging/                   # Structured logging and error handling
│   ├── context_manager.py         # Conversation context with SQLite
│   └── session_tracker.py         # Performance metrics tracking
├── interfaces/                    # Clean separation of concerns
│   ├── core/                      # Core system interfaces
│   ├── nodes/                     # Node behavior contracts
│   └── workflows/                 # Workflow orchestration interfaces
├── nodes/                         # HITL agent implementations
│   ├── mock_automation_agent.py   # Routine task automation (insurance focused)
│   ├── chatbot_agent.py           # Customer service-focused chatbot
│   ├── quality_agent.py           # Response quality assessment & improvement
│   ├── frustration_agent.py       # Customer frustration detection & analysis
│   ├── human_routing_agent.py     # Employee wellbeing-aware routing
│   └── context_manager_agent.py   # Multi-source context aggregation
├── simulation/                    # Realistic testing framework
│   ├── human_customer_simulator.py # Customer personality simulation
│   ├── employee_simulator.py      # Employee response simulation
│   └── demo_orchestrator.py       # End-to-end scenario management
├── integrations/                  # External service integrations
│   └── llm_providers.py           # Multi-provider LLM abstraction
└── workflows/                     # Complete workflow orchestration
    └── hybrid_workflow.py         # HITL system orchestration
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- uv (recommended) or pip for dependency management

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd human-ai-orchestrator

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
LANGCHAIN_PROJECT=human-ai-orchestrator

# Environment Setting
ENVIRONMENT=development
```

**Note**: The `.env` file is automatically loaded by the system and contains only environment variables. System configuration uses an agent-centric approach in the `/config/` directory with separate configurations for each agent and shared global settings.


1. **Core Concepts**: Start with `/src/interfaces/` to understand the system contracts
2. **Agent Implementation**: Look at `/src/nodes/` for actual agent logic
3. **Configuration**: Examine `/config/` for agent-centric configuration structure
4. **Testing**: Review `/tests/` for comprehensive examples

## 🤖 The Five Core HITL Agents

### 1. Chatbot Agent (`chatbot_agent.py`)
**Purpose**: Customer service-focused response generation - our stand-in for a generic chatbot
- Real-time customer sentiment analysis (urgency, frustration, politeness)
- Context-aware personalization using conversation history
- Service-oriented response enhancement with empathy integration
- Multi-LLM provider support with customer service prompts

### 2. Quality Agent (`quality_agent.py`)
**Purpose**: Intercept and review all chatbot responses before customer delivery
- Comprehensive quality assessment (accuracy, completeness, service standards)
- Response improvement and adjustment capabilities
- Context-aware evaluation considering customer history
- Automatic escalation triggers for inadequate responses

### 3. Frustration Agent (`frustration_agent.py`)
**Purpose**: Monitor customer emotional state and protect employee wellbeing
- Real-time frustration detection with escalating pattern analysis
- Employee protection through intelligent workload distribution
- Cultural sensitivity in emotion detection
- Configurable intervention thresholds based on business needs

### 4. Human Routing Agent (`human_routing_agent.py`)
**Purpose**: Route escalations while optimizing customer outcomes AND employee experience
- LLM-powered intelligent routing with database integration
- Employee wellbeing protection through workload analysis and frustration tolerance matching
- Context-enhanced routing decisions using Context Manager insights
- Real-time capacity management with priority optimization and cooldown periods

### 5. Context Manager Agent (`context_manager_agent.py`)
**Purpose**: Provide comprehensive context to support all decision-making
- Multi-source context aggregation (SQLite database, interaction history, similar cases)
- Audience-specific summarization (for routing decisions, quality assessment, human handoff)
- Privacy-aware cross-user pattern analysis with user behavior profiling
- Web search integration for external knowledge (configurable)

## ⚙️ Configuration System

The system uses an **agent-centric configuration approach** with streamlined model management:

### Configuration Structure
```
config/
├── agents/                    # Agent-specific configurations
│   ├── chatbot_agent/
│   │   ├── config.yaml       # Agent settings & behavior (NO model config)
│   │   ├── prompts.yaml      # Agent prompts & templates
│   │   └── models.yaml       # Agent model preferences (SINGLE SOURCE)
│   └── ...
├── shared/                    # Global configurations
│   ├── models.yaml           # Master model definitions & aliases
│   ├── system.yaml           # System-wide settings
│   └── providers.yaml        # Provider configurations
└── environments/             # Environment-specific overrides
    ├── development.yaml
    ├── testing.yaml
    └── production.yaml
```


### Agent Configuration Example
```yaml
# config/agents/chatbot_agent/config.yaml
version: "1.2.0"
settings:
  customer_service_focus: true
  empathy_level: "high"
  response_length: "medium"
  
# config/agents/chatbot_agent/models.yaml  
primary_model: "fast_model"
model_preferences:
  temperature: 0.7
  max_tokens: 1500
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

## 🔄 HITL Workflow Example

```python
# Human-in-the-Loop workflow demonstration
state = {
    "query": "I'm frustrated! Your API is broken and I can't get help!",
    "user_id": "user_123", 
    "session_id": "session_456"
}

# 1. Chatbot Agent generates empathetic response
state = chatbot_agent(state)
# Result: Customer service-focused response with sentiment analysis
# Output: {ai_response, customer_analysis, response_metadata}

# 2. Quality Agent reviews response before delivery
state = quality_agent(state)
# Result: Assesses response quality, may improve or escalate
# Output: {quality_assessment, next_action, adjusted_response?}

# 3. Frustration Agent analyzes customer emotional state
state = frustration_agent(state)
# Result: Detects high frustration, triggers intervention
# Output: {frustration_analysis, intervention_needed: true}

# 4. Context Manager gathers comprehensive background
state = context_manager_agent(state)
# Result: Provides context for human agent
# Output: {context_summaries, user_history, similar_cases}

# 5. Human Routing Agent selects appropriate human (protecting employee wellbeing)
state = human_routing_agent(state)
# Result: Routes to available agent with high frustration tolerance
# Output: {assigned_human_agent, routing_strategy, employee_protection_applied}

# 6. Human agent handles with full context
# Result: Empathetic resolution with employee wellbeing maintained
```

## 🛠️ Development

### Adding New Agents

1. **Create the Agent**: Implement the `NodeInterface` in `/src/nodes/`
2. **Add Configuration**: Create agent config files in `/config/agents/<agent_name>/`
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
docker build -t human-ai-orchestrator .

# Run with .env file
docker run --env-file .env human-ai-orchestrator

# Or mount .env file as volume
docker run -v $(pwd)/.env:/app/.env human-ai-orchestrator

# For GPU support
docker build -f Dockerfile.gpu -t human-ai-orchestrator:gpu .
docker run --gpus all --env-file .env human-ai-orchestrator:gpu
```

### Dev Container Support
For development with VSCode/Cursor:
- **Standard devcontainer**: `.devcontainer/devcontainer.json`
- **GPU-enabled devcontainer**: `.devcontainer/devcontainer.gpu.json` 

The GPU devcontainer automatically configures NVIDIA GPU access for local LLM models.

### Development Guidelines
- Follow the existing code style and patterns
- Add comprehensive tests for new features
- Update documentation for user-facing changes
- Use type hints and docstrings
- Keep components modular and testable

## 📚 Additional Resources

- **[CLAUDE.md](CLAUDE.md)**: Complete development guide and architecture documentation
- **[API Documentation](docs/)**: Detailed interface documentation
- **[Test Examples](tests/)**: Comprehensive unit and integration tests
- **[Configuration Guide](config/)**: Agent-centric configuration examples
- **[Demo Scripts](scripts/)**: Experimentation and demo tools

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 Use Cases

This Human-in-the-Loop system architecture is ideal for:

### Customer Support Excellence
- **Quality-First Support**: Every AI response quality-checked before delivery
- **Frustrated Customer Recovery**: Real-time frustration detection and empathetic routing
- **Employee Burnout Prevention**: Workload balancing and stress management
- **Performance Analytics**: Customer satisfaction and employee wellbeing metrics


### Key Benefits
- **Improved Customer Experience**: Higher quality responses, faster frustration resolution
- **Enhanced Employee Experience**: Better workload distribution, burnout prevention, job satisfaction
- **Operational Excellence**: Comprehensive analytics, quality metrics, performance optimization
- **Scalable Growth**: AI handles routine cases, humans focus on complex and high-value interactions

