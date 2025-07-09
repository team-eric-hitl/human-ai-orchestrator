# Configuration Guide

## Overview

The Modular LangGraph Hybrid System uses an **agent-centric configuration approach** that provides maximum modularity and flexibility. Each agent has its own configuration namespace while sharing global settings through a structured hierarchy.

## Agent-Centric Configuration Architecture

The system uses a three-tier configuration structure:

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

## Configuration Loading Priority

The system loads configuration in the following priority order:

```
1. Environment Variables (.env file)    [Highest Priority]
2. Environment-specific overrides       [config/environments/]
3. Agent-specific configurations        [config/agents/]
4. Shared configurations               [config/shared/]
5. Default Values (in code)            [Lowest Priority]
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

#### Environment and System Settings
```bash
# Environment type affects configuration loading
HYBRID_SYSTEM_ENV=development  # development, testing, production

# LangSmith for monitoring (optional but recommended)
LANGCHAIN_API_KEY=ls__your_langsmith_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=hybrid-ai-system

# Python environment
PYTHONPATH=.
PYTHONDONTWRITEBYTECODE=1
```

## Shared Configuration Files

### shared/models.yaml - Global Model Definitions

Defines all available models and their configurations:

```yaml
models:
  # Local models (no API key required)
  llama-7b:
    provider: "ollama"
    model_name: "llama2:7b"
    context_length: 4096
    temperature: 0.7
    max_tokens: 2000
    description: "Llama 7B - fast local model"
    
  mistral-7b:
    provider: "ollama"
    model_name: "mistral:7b"
    context_length: 8192
    temperature: 0.7
    max_tokens: 2000
    description: "Mistral 7B - excellent instruction following"
    
  # Cloud models (require API keys)
  gpt-4:
    provider: "openai"
    model_name: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
    description: "OpenAI GPT-4 - highest quality"
    
  claude-3-sonnet:
    provider: "anthropic"
    model_name: "claude-3-sonnet-20240229"
    temperature: 0.7
    max_tokens: 2000
    description: "Anthropic Claude 3 Sonnet - balanced performance"

# Model categories for different use cases
use_cases:
  general:
    recommended: "llama-7b"
    alternatives: ["mistral-7b", "claude-3-sonnet", "gpt-4"]
    
  code:
    recommended: "mistral-7b"
    alternatives: ["gpt-4", "claude-3-sonnet"]
    
  fast:
    recommended: "llama-7b"
    alternatives: ["mistral-7b"]
    
  high_quality:
    recommended: "gpt-4"
    alternatives: ["claude-3-sonnet", "mistral-7b"]
```

### shared/providers.yaml - Provider Configurations

Defines LLM provider settings:

```yaml
llm_providers:
  openai:
    base_url: "https://api.openai.com/v1"
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
    
  anthropic:
    base_url: "https://api.anthropic.com"
    timeout: 30
    max_retries: 3
    retry_delay: 1.0
    
  ollama:
    base_url: "http://localhost:11434"
    timeout: 60
    max_retries: 2
    retry_delay: 2.0
```

### shared/system.yaml - System-wide Settings

Global system configuration:

```yaml
system:
  name: "Modular LangGraph Hybrid System"
  version: "1.0.0"
  description: "Agent-centric AI workflow orchestration platform"

# Performance and behavior thresholds
thresholds:
  response_time_warning: 10.0
  response_time_error: 30.0
  quality_score_minimum: 0.7
  escalation_threshold: 0.5
  context_length_warning: 0.8
  retry_attempts: 3

# Monitoring and observability
monitoring:
  enable_langsmith: true
  enable_metrics: true
  log_level: "INFO"
  trace_requests: true

# Security settings
security:
  validate_inputs: true
  sanitize_outputs: true
  rate_limiting: true
  max_requests_per_minute: 60

# Performance settings
performance:
  enable_caching: true
  cache_ttl: 3600
  max_concurrent_requests: 5
  request_timeout: 30
```

## Agent-Specific Configuration

Each agent has its own configuration directory with three files:

### agents/{agent_name}/config.yaml - Agent Settings

Example for `answer_agent`:

```yaml
agent:
  name: "Answer Agent"
  description: "Handles direct query responses using configured LLMs"
  type: "llm_agent"
  enabled: true

# Agent behavior settings
behavior:
  max_thinking_time: 30
  enable_reasoning: true
  use_chain_of_thought: true
  context_retention: "full"

# Agent-specific settings
settings:
  response_format: "markdown"
  include_confidence: true
  max_response_length: 2000
  enable_citations: false

# Evaluation criteria for this agent
evaluation:
  quality_threshold: 0.8
  response_time_target: 5.0
  accuracy_weight: 0.6
  helpfulness_weight: 0.4
```

### agents/{agent_name}/models.yaml - Model Preferences

```yaml
# Primary model for this agent
preferred: "llama-7b"

# Fallback models (tried in order)
fallback:
  - "mistral-7b"
  - "claude-3-sonnet"

# Model-specific overrides for this agent
model_overrides:
  llama-7b:
    temperature: 0.5  # More conservative for answers
    max_tokens: 1500
  
  gpt-4:
    temperature: 0.3  # Very conservative for high-quality answers
    max_tokens: 2000

# Use case mapping for this agent
use_cases:
  simple_questions: "llama-7b"
  complex_analysis: "gpt-4"
  code_questions: "mistral-7b"
```

### agents/{agent_name}/prompts.yaml - Agent Prompts

```yaml
# System prompt for this agent
system_prompt: |
  You are an Answer Agent in a hybrid AI-human system. Your role is to provide
  direct, helpful responses to user queries. Be accurate, concise, and helpful.
  
  If you're uncertain about something, indicate your confidence level.
  If a query is too complex, you may escalate to a human agent.

# Prompt templates for different scenarios
templates:
  standard_response: |
    User Query: {query}
    
    Please provide a helpful and accurate response. Include your confidence level.
  
  complex_query: |
    User Query: {query}
    Context: {context}
    
    This appears to be a complex query. Provide the best response you can,
    or recommend escalation if needed.
  
  follow_up: |
    Previous conversation: {history}
    New query: {query}
    
    Continue the conversation with a helpful response.

# Response formatting templates
response_formats:
  with_confidence: |
    {response}
    
    Confidence: {confidence}/10
  
  with_citations: |
    {response}
    
    Sources: {citations}
```

## Environment-Specific Overrides

### environments/development.yaml

Development environment settings:

```yaml
system:
  environment: "development"

# Development-specific thresholds (more permissive)
thresholds:
  quality_score_minimum: 0.5
  response_time_warning: 15.0
  escalation_threshold: 0.3

# Enhanced logging for development
monitoring:
  log_level: "DEBUG"
  trace_requests: true
  enable_detailed_metrics: true

# Agent overrides for development
agents:
  answer_agent:
    behavior:
      enable_reasoning: true
      max_thinking_time: 60  # More time for debugging
    
    settings:
      include_confidence: true
      enable_debug_info: true
```

### environments/production.yaml

Production environment settings:

```yaml
system:
  environment: "production"

# Stricter thresholds for production
thresholds:
  quality_score_minimum: 0.8
  response_time_warning: 5.0
  escalation_threshold: 0.7

# Production monitoring
monitoring:
  log_level: "WARNING"
  enable_detailed_metrics: false
  alert_on_errors: true

# Security enhancements
security:
  validate_inputs: true
  sanitize_outputs: true
  rate_limiting: true
  max_requests_per_minute: 100

# Performance optimizations
performance:
  enable_caching: true
  cache_ttl: 7200
  max_concurrent_requests: 10
```

## Benefits of Agent-Centric Configuration

### Developer Isolation
- Each agent has its own configuration namespace
- Changes to one agent don't affect others
- Clear separation of concerns

### Modular Testing
- Agents can be tested independently
- Easy to mock or override specific agent configs
- Test scenarios can target individual agents

### Easy Agent Development
- New agents can be added without touching existing configs
- Copy existing agent structure as template
- Clear configuration contract for each agent

### Environment Management
- Clean separation of dev/test/prod settings
- Environment-specific overrides are clearly defined
- Easy to promote configurations across environments

### Hot-Reloading
- Configuration changes can be applied without restart
- Agents can be reconfigured independently
- Dynamic configuration updates during runtime

## Configuration Validation

The system automatically validates all configuration files on startup:

- **Schema validation**: Ensures all required fields are present
- **Model availability**: Verifies referenced models exist
- **Provider connectivity**: Tests LLM provider connections
- **Agent compatibility**: Validates agent configuration consistency

## Best Practices

### Configuration Organization
1. **Keep agent configs focused**: Only include settings specific to that agent
2. **Use shared configs for common settings**: Avoid duplication across agents
3. **Environment overrides should be minimal**: Only override what's different per environment

### Security
1. **Never commit API keys**: Use environment variables for secrets
2. **Validate all inputs**: Enable input validation in production
3. **Use rate limiting**: Protect against abuse in production

### Performance
1. **Enable caching**: Improves response times for similar queries
2. **Set appropriate timeouts**: Balance responsiveness with reliability
3. **Monitor resource usage**: Use the monitoring configuration to track performance

### Development
1. **Use development environment**: More permissive settings for testing
2. **Enable debug logging**: Helps with troubleshooting configuration issues
3. **Test configuration changes**: Validate configs before deploying to production

## Troubleshooting

### Common Issues

1. **Configuration not loading**: Check file permissions and YAML syntax
2. **Model not found**: Verify model is defined in shared/models.yaml
3. **Provider errors**: Check API keys and provider configuration
4. **Agent not responding**: Review agent-specific configuration and logs

### Debugging Tools

```bash
# Validate configuration
uv run python -m src.core.config.agent_config_manager --validate

# Show configuration summary
uv run python -m src.core.config.agent_config_manager --summary

# Test specific agent configuration
uv run python -m src.core.config.agent_config_manager --agent answer_agent
```

## Migration from Legacy Configuration

If migrating from the old configuration system:

1. **Move model definitions** from `models.json` to `shared/models.yaml`
2. **Split agent settings** into individual agent directories
3. **Create environment overrides** for dev/test/prod differences
4. **Update import statements** to use `AgentConfigManager`
5. **Test thoroughly** to ensure all functionality is preserved