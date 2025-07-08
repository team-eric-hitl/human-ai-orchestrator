# Configuration Guide

## Overview

The Hybrid AI-Human System uses a flexible, hierarchical configuration system that allows customization without code changes. This guide covers all configuration options, best practices, and common scenarios.

## Configuration Hierarchy

The system loads configuration in the following priority order:

```
1. Environment Variables (.env file)    [Highest Priority]
2. Configuration Files (/config/)
3. Default Values (in code)             [Lowest Priority]
```

Higher priority sources override lower priority ones.

## Environment Variables (.env)

### Purpose
Environment variables handle:
- **Secrets**: API keys, tokens
- **Environment settings**: Development vs Production
- **Runtime overrides**: Temporary configuration changes

### Setup
```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

### Available Variables

#### LLM Provider API Keys
```bash
# OpenAI (optional - system works with local models)
OPENAI_API_KEY=sk-your_openai_api_key_here

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
```

#### Monitoring and Tracing
```bash
# LangSmith for monitoring (optional but recommended)
LANGCHAIN_API_KEY=ls__your_langsmith_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=hybrid-ai-system
```

#### Environment Settings
```bash
# Environment type affects logging, performance tuning
ENVIRONMENT=development  # development, staging, production

# Python environment
PYTHONPATH=.
PYTHONDONTWRITEBYTECODE=1
```

## Configuration Files (/config/)

### models.yaml - LLM Model Configuration

Controls which AI models are available and how they're configured.

```yaml
# Model definitions
models:
  # Local models (no API key required)
  llama-7b:
    path: "models/llama-7b.gguf"        # Path to model file
    type: "llama"                       # Provider type
    context_length: 2048                # Maximum context window
    gpu_layers: 0                       # GPU acceleration layers
    temperature: 0.7                    # Sampling temperature
    max_tokens: 2000                    # Maximum tokens to generate
    description: "Llama 7B - fast local model"
    
  mistral-7b:
    path: "models/mistral-7b-instruct.gguf"
    type: "mistral"
    context_length: 4096
    gpu_layers: 0
    temperature: 0.7
    max_tokens: 2000
    description: "Mistral 7B - excellent instruction following"
    
  # Cloud models (require API keys)
  gpt-4:
    type: "openai"                      # Provider identifier
    model_name: "gpt-4"                 # Provider-specific model name
    temperature: 0.7
    max_tokens: 2000
    description: "OpenAI GPT-4 - highest quality"
    
  claude-3-sonnet:
    type: "anthropic"
    model_name: "claude-3-sonnet-20240229"
    temperature: 0.7
    max_tokens: 2000
    description: "Anthropic Claude 3 Sonnet - balanced performance"

# Default model selection
default_model: "llama-7b"

# Fallback chain (tried in order if primary fails)
fallback_models:
  - "mistral-7b"
  - "claude-3-sonnet"    # Only if ANTHROPIC_API_KEY is set
  - "gpt-4"              # Only if OPENAI_API_KEY is set

# Model categories for different use cases
use_cases:
  general:
    recommended: "llama-7b"
    alternatives: ["mistral-7b", "claude-3-sonnet", "gpt-4"]
    
  code:
    recommended: "codellama-7b"
    alternatives: ["gpt-4", "claude-3-sonnet"]
    
  fast:
    recommended: "claude-3-haiku"
    alternatives: ["gpt-3.5-turbo", "llama-7b"]
    
  high_quality:
    recommended: "gpt-4"
    alternatives: ["claude-3-sonnet", "mistral-7b"]
```

#### Model Configuration Options

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `name` | Model identifier | Yes | - |
| `type` | Provider type (openai, anthropic, llama, mistral) | Yes | - |
| `model_name` | Provider-specific model name | Cloud only | - |
| `path` | Local model file path | Local only | - |
| `temperature` | Sampling temperature (0.0-2.0) | No | 0.7 |
| `max_tokens` | Maximum tokens to generate | No | 2000 |
| `context_length` | Maximum context window | Local only | 2048 |
| `gpu_layers` | GPU acceleration layers | Local only | 0 |
| `description` | Human-readable description | No | - |

### prompts.json - Agent Prompts and Behavior

Controls how each agent behaves through system prompts and parameters.

```json
{
  "answer_agent": {
    "system_prompt": "You are a helpful AI assistant. Provide accurate, helpful responses to user queries. Use context from previous conversations when available to provide more personalized assistance.",
    "context_integration": "When context is available, reference previous interactions to provide continuity and avoid repetition.",
    "response_style": "Clear, concise, and professional while maintaining a helpful tone."
  },
  
  "evaluator_agent": {
    "system_prompt": "You are an evaluation specialist. Assess the quality of AI responses based on accuracy, completeness, clarity, and user satisfaction. Consider context factors when making escalation decisions.",
    
    "evaluation_criteria": {
      "accuracy": "How correct and factual is the response?",
      "completeness": "Does the response address all aspects of the query?", 
      "clarity": "Is the response clear and easy to understand?",
      "user_satisfaction": "How likely is the user to be satisfied with this response?"
    },
    
    "escalation_thresholds": {
      "low_score": 4.0,              # Escalate if overall score below this
      "repeat_query": true,          # Escalate if user repeating similar queries
      "escalation_history": 2        # Escalate if user has 2+ previous escalations
    }
  },
  
  "escalation_router": {
    "system_prompt": "You are an escalation routing specialist. Analyze queries and assign them to the most appropriate human agent based on expertise requirements and priority levels.",
    
    "expertise_mapping": {
      "technical": ["code", "programming", "API", "bug", "error", "technical", "system"],
      "financial": ["billing", "payment", "refund", "price", "cost", "financial", "money"],
      "general": ["general", "help", "support", "question"]
    },
    
    "priority_factors": {
      "high": ["urgent", "critical", "broken", "failed", "error"],
      "medium": ["issue", "problem", "help", "support"],
      "low": ["question", "information", "general"]
    }
  },
  
  "human_interface": {
    "system_prompt": "You are a human agent interface. Present escalated queries to human agents with clear context and facilitate smooth handoffs between AI and human assistance.",
    "handoff_message": "This query has been escalated to a human agent. Please provide the following context to assist the user effectively."
  }
}
```

#### Prompt Configuration Best Practices
1. **Clear Instructions**: Make system prompts specific and actionable
2. **Context Awareness**: Include instructions for using conversation history
3. **Consistent Tone**: Maintain brand voice across all agents
4. **Measurable Criteria**: Define clear evaluation criteria
5. **Flexible Thresholds**: Make numeric thresholds configurable

### config.json - Core System Settings

System-wide configuration and operational parameters.

```json
{
  "system": {
    "name": "Hybrid AI-Human System",
    "version": "1.0.0",
    "description": "Intelligent AI-human workflow orchestration"
  },
  
  "thresholds": {
    "escalation_score": 6.0,           # Global escalation threshold
    "confidence_threshold": 0.7,       # Minimum confidence for responses
    "max_context_entries": 50,         # Maximum context history per user
    "session_timeout_minutes": 30      # Session expiry time
  },
  
  "providers": {
    "config": {
      "type": "file",
      "config_dir": "config"
    },
    "context": {
      "type": "sqlite",
      "db_path": "data/hybrid_system.db",
      "backup_enabled": true,
      "cleanup_days": 30
    },
    "session": {
      "type": "memory",
      "max_sessions": 1000
    }
  },
  
  "performance": {
    "max_concurrent_requests": 10,
    "request_timeout_seconds": 30,
    "retry_attempts": 3,
    "retry_delay_seconds": 1.0
  },
  
  "monitoring": {
    "metrics_enabled": true,
    "health_checks_enabled": true,
    "log_level": "INFO",
    "trace_enabled": false
  }
}
```

### logging.yaml - Logging Configuration

Controls system logging behavior and output formats.

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
  json:
    format: "%(asctime)s %(name)s %(levelname)s %(message)s"
    class: "src.core.logging.formatters.JSONFormatter"
    
  detailed:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
    
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: json
    filename: logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/error.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  src:
    level: DEBUG
    handlers: [console, file]
    propagate: false
    
  src.nodes:
    level: DEBUG
    handlers: [console, file]
    propagate: false
    
  src.integrations.llm_providers:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console, file, error_file]
```

## Environment-Specific Configuration

### Development Environment
```bash
# .env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
MOCK_LLM_PROVIDERS=true
```

```json
// config/config.json (development overrides)
{
  "monitoring": {
    "log_level": "DEBUG",
    "trace_enabled": true
  },
  "performance": {
    "request_timeout_seconds": 60
  }
}
```

### Production Environment
```bash
# .env
ENVIRONMENT=production
LOG_LEVEL=INFO
LANGCHAIN_TRACING_V2=true
```

```json
// config/config.json (production overrides)
{
  "thresholds": {
    "escalation_score": 7.0
  },
  "performance": {
    "max_concurrent_requests": 50,
    "request_timeout_seconds": 15
  },
  "monitoring": {
    "metrics_enabled": true,
    "health_checks_enabled": true
  }
}
```

## Configuration Validation

### Automatic Validation
The system automatically validates configuration on startup:

```python
# Example validation errors
ConfigurationError: Missing required API key for model 'gpt-4'
ConfigurationError: Model file not found: models/missing-model.gguf
ConfigurationError: Invalid escalation_score: must be between 0.0 and 10.0
```

### Manual Validation
```bash
# Test configuration validity
uv run python -c "from src.core.config import ConfigManager; ConfigManager('config')"

# Validate specific model
uv run python -c "
from src.integrations.llm_providers import LLMProviderFactory
factory = LLMProviderFactory()
provider = factory.create_provider('gpt-4')
print('Model validated successfully')
"
```

## Common Configuration Scenarios

### 1. Local-Only Setup (No API Keys)
```yaml
# models.yaml
default_model: "llama-7b"
fallback_models: ["mistral-7b", "codellama-7b"]
```

```bash
# .env (no API keys needed)
ENVIRONMENT=development
```

### 2. Cloud-Only Setup
```yaml
# models.yaml
default_model: "gpt-4"
fallback_models: ["claude-3-sonnet", "gpt-3.5-turbo"]
```

```bash
# .env
OPENAI_API_KEY=sk-your_key_here
ANTHROPIC_API_KEY=sk-ant-your_key_here
```

### 3. Hybrid Setup (Local Primary, Cloud Fallback)
```yaml
# models.yaml
default_model: "llama-7b"
fallback_models: ["mistral-7b", "gpt-4", "claude-3-sonnet"]
```

```bash
# .env
OPENAI_API_KEY=sk-your_key_here  # For fallback only
```

### 4. High-Performance Setup
```yaml
# models.yaml - Use GPU acceleration
llama-7b:
  path: "models/llama-7b.gguf"
  type: "llama"
  gpu_layers: 35  # GPU acceleration
  context_length: 4096
```

```json
// config.json - Increase limits
{
  "performance": {
    "max_concurrent_requests": 100,
    "request_timeout_seconds": 10
  }
}
```

### 5. Conservative Escalation Setup
```json
// prompts.json - Lower escalation threshold
{
  "evaluator_agent": {
    "escalation_thresholds": {
      "low_score": 7.0,  // Higher threshold = more escalations
      "repeat_query": true,
      "escalation_history": 1  // Escalate after 1 previous escalation
    }
  }
}
```

## Configuration Management Best Practices

### 1. Version Control
- **Commit configuration files** to version control
- **Never commit .env files** with secrets
- **Use .env.example** for documentation
- **Document configuration changes** in commit messages

### 2. Environment Separation
```bash
# Different config directories for environments
config/
├── development/
│   ├── models.yaml
│   └── prompts.json
├── staging/
│   ├── models.yaml
│   └── prompts.json
└── production/
    ├── models.yaml
    └── prompts.json
```

### 3. Secret Management
```bash
# Use environment-specific secret management
# Development
export OPENAI_API_KEY="dev_key_here"

# Production (use secure secret management)
kubectl create secret generic ai-system-secrets \
  --from-literal=openai-api-key="prod_key_here"
```

### 4. Configuration Testing
```python
# Test configuration changes
def test_configuration_loads():
    config = ConfigManager("config")
    assert config.models.default_model == "llama-7b"
    assert config.thresholds.escalation_score == 6.0

def test_model_availability():
    factory = LLMProviderFactory()
    provider = factory.create_provider_with_fallback()
    assert provider is not None
```

### 5. Documentation
- **Document all configuration options** in this guide
- **Include examples** for common scenarios
- **Explain the impact** of each setting
- **Provide troubleshooting** for common issues

## Troubleshooting Configuration Issues

### Common Problems and Solutions

#### Problem: "Model file not found"
```bash
# Check model file exists
ls -la models/llama-7b.gguf

# Download if missing
curl -L "https://huggingface.co/model/resolve/main/model.gguf" -o models/llama-7b.gguf
```

#### Problem: "API key not found"
```bash
# Check environment variable is set
echo $OPENAI_API_KEY

# Verify .env file is loaded
grep OPENAI_API_KEY .env
```

#### Problem: "Configuration validation failed"
```python
# Debug configuration loading
from src.core.config import ConfigManager
config = ConfigManager("config")
print(config.models.get_available_models())
```

#### Problem: "No working models available"
```bash
# Test each model individually
uv run python -c "
from src.integrations.llm_providers import LLMProviderFactory
factory = LLMProviderFactory()
for model in ['llama-7b', 'gpt-4', 'claude-3-sonnet']:
    try:
        provider = factory.create_provider(model)
        print(f'{model}: OK')
    except Exception as e:
        print(f'{model}: ERROR - {e}')
"
```

### Debug Commands
```bash
# Show effective configuration
uv run python -c "
from src.core.config import ConfigManager
import json
config = ConfigManager('config')
print(json.dumps(config.get_all_config(), indent=2, default=str))
"

# Test model creation
uv run python -c "
from src.integrations.llm_providers import LLMProviderFactory
factory = LLMProviderFactory()
provider = factory.create_provider_with_fallback()
print(f'Using model: {provider.model_config.name}')
"

# Validate all configuration files
make check-config
```

## Configuration Schema Reference

### Complete Schema
See `src/core/config/schemas.py` for the complete configuration schema with:
- Type definitions for all configuration objects
- Validation rules and constraints
- Default values and examples
- Documentation for each field

### Configuration API
```python
# Access configuration in code
from src.core.config import ConfigManager

config = ConfigManager("config")

# Model configuration
model_config = config.models.get_model("gpt-4")
available_models = config.models.get_available_models()

# Prompts
system_prompt = config.prompts.answer_agent["system_prompt"]

# Thresholds
escalation_threshold = config.thresholds.escalation_score

# Custom settings
custom_value = config.get_config("custom.setting", default_value)
```

This configuration guide provides comprehensive coverage of all system configuration options, best practices, and troubleshooting guidance for the Hybrid AI-Human System.