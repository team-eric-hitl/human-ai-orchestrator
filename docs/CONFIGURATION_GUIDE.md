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

### shared/models.yaml - Global Model Definitions with Semantic Aliases

The system uses semantic model aliases that allow easy model management and updates:

```yaml
# Semantic model aliases - update these when new models are released
# This allows changing model mappings in one place when newer models become available
model_aliases:
  # Anthropic models - organized by use case and performance tier
  anthropic_general_budget: "claude-3-5-haiku-20241022"
  anthropic_general_standard: "claude-3-5-sonnet-20241022"
  anthropic_reasoning_premium: "claude-3-5-sonnet-20241022"
  anthropic_coding_premium: "claude-3-5-sonnet-20241022"
  anthropic_flagship: "claude-3-5-sonnet-20241022"
  
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
    gpu_layers: 40
    temperature: 0.7
    max_tokens: 2000
    description: "Llama 7B model - good balance of speed and quality"
    
  llama-13b:
    path: "models/llama-13b.gguf"
    type: "llama"
    context_length: 4096
    gpu_layers: 40
    temperature: 0.7
    max_tokens: 2000
    description: "Llama 13B model - higher quality, slower inference"
    
  # Local Mistral models
  mistral-7b:
    path: "models/mistral-7b.gguf"
    type: "mistral"
    context_length: 4096
    gpu_layers: 40
    temperature: 0.7
    max_tokens: 2000
    description: "Mistral 7B Instruct - excellent instruction following"
    
  # Code-focused models
  codellama-7b:
    path: "models/codellama-7b.gguf"
    type: "llama"
    context_length: 2048
    gpu_layers: 40
    temperature: 0.2
    max_tokens: 2000
    description: "CodeLlama 7B - optimized for code generation"
    
  # OpenAI models (cloud)
  gpt-4:
    type: "openai"
    model_name: "gpt-4"
    temperature: 0.7
    max_tokens: 2000
    description: "OpenAI GPT-4 - highest quality, requires API key"
    
  gpt-3.5-turbo:
    type: "openai"
    model_name: "gpt-3.5-turbo"
    temperature: 0.7
    max_tokens: 2000
    description: "OpenAI GPT-3.5 Turbo - fast and cost-effective"
    
  # Anthropic models (cloud)
  claude-3-5-sonnet-20241022:
    type: "anthropic"
    model_name: "claude-3-5-sonnet-20241022"
    temperature: 0.7
    max_tokens: 2000
    description: "Anthropic Claude 3.5 Sonnet - balanced performance and reasoning"
    
  claude-3-5-haiku-20241022:
    type: "anthropic"
    model_name: "claude-3-5-haiku-20241022"
    temperature: 0.7
    max_tokens: 2000
    description: "Anthropic Claude 3.5 Haiku - fast and efficient"

# Global model categories for different use cases
use_cases:
  general:
    recommended: "local_general_standard"
    alternatives: ["local_general_budget", "anthropic_general_standard", "openai_general_standard"]
    
  code:
    recommended: "local_coding_standard"
    alternatives: ["anthropic_coding_premium", "openai_coding_standard", "local_general_budget"]
    
  fast:
    recommended: "anthropic_general_budget"
    alternatives: ["openai_general_budget", "local_general_standard"]
    
  high_quality:
    recommended: "openai_general_standard"
    alternatives: ["anthropic_reasoning_premium", "anthropic_general_standard", "local_general_budget", "local_general_premium"]

# Global fallback strategy
fallback_strategy:
  enabled: true
  max_retries: 3
  retry_delay: 5  # seconds
  
  # Global fallback chain
  default_fallback:
    - "local_general_budget"
    - "anthropic_general_budget"  # Only if ANTHROPIC_API_KEY is set
    - "gpt-3.5-turbo"  # Only if OPENAI_API_KEY is set
```

#### Benefits of Semantic Aliases

1. **Easy Model Updates**: When a new model version is released, update the alias mapping in one place
2. **Consistent Naming**: Semantic names like `anthropic_general_budget` are clearer than version numbers
3. **Provider Independence**: Switch between providers without changing agent configurations
4. **Environment Flexibility**: Different environments can use different models by updating aliases

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
  config_schema_version: "1.0.0"
  description: "Agent-centric AI workflow orchestration platform"

# Version management
versioning:
  enabled: true
  schema_version: "1.0.0"
  agent_version_required: true
  strict_validation: true
  
  # Version compatibility rules
  compatibility:
    min_agent_version: "1.0.0"
    max_agent_version: "2.0.0"
    breaking_changes_allowed: false

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
  name: "answer_agent"
  version: "1.0.0"
  description: "Handles direct query responses using configured LLMs"
  type: "llm_agent"
  created: "2025-01-17"
  last_modified: "2025-01-17"
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

### agents/{agent_name}/models.yaml - Model Preferences with Semantic Aliases

```yaml
# Primary model alias for this agent (uses semantic aliases from shared/models.yaml)
primary_model: "local_general_standard"

# Model preferences for different query types
model_preferences:
  general_queries:
    primary: "anthropic_general_budget"
    fallback: ["local_general_budget", "local_general_standard"]
    
  code_queries:
    primary: "anthropic_coding_premium"
    fallback: ["local_coding_standard", "local_general_budget"]
    
  complex_reasoning:
    primary: "anthropic_reasoning_premium"
    fallback: ["local_general_premium", "local_general_budget"]

# Model-specific overrides for this agent
model_overrides:
  temperature: 0.7
  max_tokens: 2000
  
  # Model-specific overrides (using actual model names)
  per_model:
    codellama-7b:
      temperature: 0.2
      max_tokens: 3000
      
    gpt-4:
      temperature: 0.6
      max_tokens: 2500
```

**Note**: Agent configurations use semantic aliases (like `anthropic_general_budget`) which are resolved to actual model names (like `claude-3-5-haiku-20241022`) automatically by the system. This allows for easy model management and updates.

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

## Agent Versioning

The system supports semantic versioning for all agents to track evolution and ensure compatibility:

### Version Format
All agents use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes to agent interface or behavior
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Version Management
```yaml
# Required fields in agent config
agent:
  name: "agent_name"
  version: "1.2.3"              # Semantic version
  created: "2025-01-17"         # Creation date
  last_modified: "2025-01-17"   # Last update date
```

### Version Validation
- Automatic validation on config load
- Ensures proper semantic version format
- Tracks version compatibility across system
- Enables version-specific features and migrations

### Benefits
- **Evolution Tracking**: Monitor agent development over time
- **Compatibility Management**: Ensure system compatibility
- **Rollback Support**: Revert to previous working versions
- **A/B Testing**: Run different agent versions simultaneously

## Migration from Legacy Configuration

If migrating from the old configuration system:

1. **Move model definitions** from `models.json` to `shared/models.yaml`
2. **Split agent settings** into individual agent directories
3. **Add version fields** to all agent configurations
4. **Create environment overrides** for dev/test/prod differences
5. **Update import statements** to use `AgentConfigManager`
6. **Test thoroughly** to ensure all functionality is preserved