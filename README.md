# Human-in-the-Loop AI System: Improving Customer AND Employee Experience

A sophisticated AI workflow orchestration platform that enhances both customer support quality and employee wellbeing through intelligent human-AI collaboration. The system intercepts all customer-AI interactions to ensure quality, detect frustration, and route escalations while protecting employee mental health and job satisfaction.

## 🎯 Overview

This system implements a **Human-in-the-Loop (HITL) Architecture** that goes beyond simple escalation - it actively improves the entire support experience for customers while protecting employees from burnout and frustration overload. Every AI response is quality-checked, customer frustration is monitored in real-time, and human routing considers both customer needs and employee wellbeing.

### Key Features

- **🛡️ Quality Interception**: All AI responses reviewed before customer delivery
- **😤 Frustration Detection**: Real-time sentiment analysis with escalation triggers  
- **👥 Employee Protection**: Workload balancing and burnout prevention
- **🎯 Intelligent Routing**: Smart assignment considering customer needs and employee wellbeing
- **📊 Comprehensive Analytics**: Customer satisfaction and employee performance metrics
- **🎭 Realistic Simulation**: Complete customer/employee interaction simulation for testing and demos

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
│   ├── chatbot_agent.py           # Customer service-focused chatbot
│   ├── quality_agent.py           # Response quality assessment & improvement
│   ├── frustration_agent.py       # Customer frustration detection & analysis
│   ├── routing_agent.py           # Employee wellbeing-aware routing
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

**Note**: The `.env` file is automatically loaded by the system and contains only environment variables. System configuration uses an agent-centric approach in the `/config/` directory with separate configurations for each agent and shared global settings.

### Run the System

```bash
# Run the main application
make run

# Or with custom configuration
uv run python -m src.main --config-path config/custom_config.json
```

### Try the Demo Scenarios

The system includes a comprehensive simulation framework for testing and demonstration:

```python
from src.simulation.demo_orchestrator import DemoOrchestrator

# Create demo orchestrator
demo = DemoOrchestrator()

# List available scenarios
scenarios = demo.list_available_scenarios()
print("Available scenarios:", [s["name"] for s in scenarios])

# Start a specific demo scenario
demo_session = demo.start_demo_scenario("Frustrated Customer")

# Step through the interaction
chatbot_response = demo.simulate_chatbot_response(demo_session["demo_id"])
quality_check = demo.simulate_quality_assessment(demo_session["demo_id"])
frustration_analysis = demo.simulate_frustration_analysis(demo_session["demo_id"])

# If escalation needed, route to human
if frustration_analysis["intervention_needed"]:
    routing = demo.simulate_routing_decision(demo_session["demo_id"])
    human_response = demo.simulate_human_agent_response(demo_session["demo_id"])

# Complete the interaction
resolution = demo.simulate_resolution(demo_session["demo_id"])
```

**Available Demo Scenarios:**
1. **Happy Path**: Polite customer → Quality response → Direct resolution
2. **Technical Escalation**: Complex query → Quality assessment → Specialist routing  
3. **Frustrated Customer**: Poor experience → Frustration detection → Empathetic human
4. **Manager Escalation**: Explicit complaint → Direct management routing
5. **Quality Adjustment**: Inadequate response → Quality improvement → Re-delivery
6. **Employee Wellbeing**: Multiple difficult cases → Intelligent rotation

## 🎓 Learning Guide

### For Beginners: Start with the Tutorial

We've created comprehensive Jupyter notebooks for different learning paths:

```bash
# Launch Jupyter to access the notebooks
jupyter lab
```

### 📚 AI Agents Tutorial (`notebooks/AI_Agents_Tutorial.ipynb`)
**The tutorial covers:**
- What are AI agents? (with real-world analogies)
- How do they work together?
- Hands-on examples with working code
- Build your own simple agent
- Understanding the real system architecture

### 🧪 Chatbot Agent Tester (`notebooks/chatbot_tester.ipynb`)
Interactive notebook for testing and optimizing the Chatbot Agent:
- **Configuration Editor**: Edit agent settings, prompts, and model preferences
- **Internal Logic Explanation**: Understand how configuration changes affect chatbot behavior
- **Question Testing**: Load test questions and process them through the agent
- **Full Conversations**: Simulate realistic customer-AI interactions until resolution
- **Performance Analysis**: Export results and analyze conversation patterns
- **Optimization Guidelines**: Learn how to tune settings for different use cases

### For Developers: Explore the Implementation

1. **Core Concepts**: Start with `/src/interfaces/` to understand the system contracts
2. **Agent Implementation**: Look at `/src/nodes/` for actual agent logic
3. **Configuration**: Examine `/config/` for agent-centric configuration structure
4. **Testing**: Review `/tests/` for comprehensive examples

## 🤖 The Five Core HITL Agents

### 1. Chatbot Agent (`chatbot_agent.py`)
**Purpose**: Customer service-focused response generation with emotional intelligence
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

### 4. Routing Agent (`routing_agent.py`)
**Purpose**: Route escalations while optimizing customer outcomes AND employee experience
- Multi-strategy routing (skill-based, workload-balanced, employee wellbeing)
- Prevents agent burnout through consecutive difficult case limits
- Frustration tolerance matching and cooldown period management
- Real-time capacity management with priority optimization

### 5. Context Manager Agent (`context_manager_agent.py`)
**Purpose**: Provide comprehensive context to support all decision-making
- Multi-source context aggregation (SQL database, interaction history, similar cases)
- Audience-specific summarization (AI agents, human agents, quality assessment)
- Privacy-aware cross-user pattern analysis
- Optional web search integration for external knowledge

## ⚙️ Configuration System

The system uses an **agent-centric configuration approach** with comprehensive versioning support:

### Agent Versioning
All agents use semantic versioning (MAJOR.MINOR.PATCH) for evolution tracking:
- **Version validation** on config load
- **Compatibility management** across system updates
- **Rollback support** for stable deployments
- **A/B testing** capabilities for agent improvements

### Configuration Structure
```
config/
├── agents/                    # Agent-specific configurations
│   ├── chatbot_agent/
│   │   ├── config.yaml       # Agent settings & version info (NO model config)
│   │   ├── prompts.yaml      # Agent prompts & templates
│   │   └── models.yaml       # Agent model preferences (SINGLE SOURCE)
│   └── ...
├── shared/                    # Global configurations
│   ├── models.yaml           # Master model definitions & aliases
│   ├── system.yaml           # System-wide settings & versioning
│   └── providers.yaml        # Provider configurations
└── environments/             # Environment-specific overrides
    ├── development.yaml
    ├── testing.yaml
    └── production.yaml
```

### 🔄 Model Configuration Consolidation (Latest Update)
**IMPORTANT CHANGE**: Model configuration has been consolidated for clarity and consistency:
- **✅ SINGLE SOURCE**: All model preferences now in `models.yaml` files only
- **❌ REMOVED**: Model sections from all `config.yaml` files (eliminated duplication)
- **🔧 STANDARDIZED**: Consistent `primary_model` + `model_preferences` structure
- **🚫 NO CONFLICTS**: No more confusion between config.yaml and models.yaml model settings

### Hierarchical Configuration Loading:

### Model Configuration (`config/shared/models.yaml`)
```yaml
# Semantic model aliases - update these when new models are released
model_aliases:
  # Anthropic models - organized by use case and performance tier
  anthropic_general_budget: "claude-3-5-haiku-20241022"
  anthropic_general_standard: "claude-3-5-sonnet-20241022"
  anthropic_reasoning_premium: "claude-3-5-sonnet-20241022"
  anthropic_coding_premium: "claude-3-5-sonnet-20241022"
  
  # OpenAI models
  openai_general_standard: "gpt-4"
  openai_general_budget: "gpt-3.5-turbo"
  openai_coding_standard: "gpt-4"
  
  # Local models
  local_general_standard: "llama-7b"
  local_general_premium: "llama-13b"
  local_coding_standard: "codellama-7b"
  local_general_budget: "mistral-7b"

models:
  # Local Llama models
  llama-7b:
    path: "models/llama-7b.gguf"
    type: "llama"
    context_length: 2048
    temperature: 0.7
    description: "Llama 7B model - good balance of speed and quality"
    
  # OpenAI models (cloud)
  gpt-4:
    type: "openai"
    model_name: "gpt-4"
    temperature: 0.7
    description: "OpenAI GPT-4 - highest quality, requires API key"
    
  # Anthropic models (cloud)
  claude-3-5-sonnet-20241022:
    type: "anthropic"
    model_name: "claude-3-5-sonnet-20241022"
    temperature: 0.7
    description: "Anthropic Claude 3.5 Sonnet - balanced performance and reasoning"

# Global model categories for different use cases
use_cases:
  general:
    recommended: "local_general_standard"
    alternatives: ["local_general_budget", "anthropic_general_standard", "openai_general_standard"]
```

### Prompts Configuration (`config/prompts.json`)
```json
{
  "chatbot_agent": {
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

# 5. Routing Agent selects appropriate human (protecting employee wellbeing)
state = routing_agent(state)
# Result: Routes to available agent with high frustration tolerance
# Output: {assigned_human_agent, routing_strategy, employee_protection_applied}

# 6. Human agent handles with full context
# Result: Empathetic resolution with employee wellbeing maintained
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

# For GPU support
docker build -f Dockerfile.gpu -t hybrid-ai-system:gpu .
docker run --gpus all --env-file .env hybrid-ai-system:gpu
```

### Dev Container Support
For development with VSCode/Cursor:
- **Standard devcontainer**: `.devcontainer/devcontainer.json`
- **GPU-enabled devcontainer**: `.devcontainer/devcontainer.gpu.json` 

The GPU devcontainer automatically configures NVIDIA GPU access for local LLM models. See [SETUP.md](SETUP.md) for detailed setup instructions.

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

- **[Tutorial Notebook](notebooks/AI_Agents_Tutorial.ipynb)**: Complete beginner's guide to AI agents
- **[Chatbot Tester](notebooks/chatbot_tester.ipynb)**: Interactive testing and optimization tool
- **[API Documentation](docs/)**: Detailed interface documentation
- **[Test Examples](tests/)**: Comprehensive usage examples
- **[Configuration Guide](config/)**: System setup and customization

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

### Beyond Customer Support
- **Technical Documentation**: AI-powered help with expert validation and context
- **Educational Platforms**: Tutoring systems with teacher oversight and student frustration monitoring
- **Content Moderation**: AI screening with human review and moderator wellbeing protection  
- **Code Review**: Automated analysis with developer consultation and workload distribution
- **Healthcare Support**: Patient interaction with medical professional oversight
- **Financial Advisory**: AI guidance with human expert validation and compliance

### Key Benefits
- **Improved Customer Experience**: Higher quality responses, faster frustration resolution
- **Enhanced Employee Experience**: Better workload distribution, burnout prevention, job satisfaction
- **Operational Excellence**: Comprehensive analytics, quality metrics, performance optimization
- **Scalable Growth**: AI handles routine cases, humans focus on complex and high-value interactions

Built with ❤️ using [LangGraph](https://langchain-ai.github.io/langgraph/), [LangChain](https://langchain.com/), and [LangSmith](https://smith.langchain.com/).