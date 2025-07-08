# System Architecture Documentation

## Overview

The Hybrid AI-Human System is a modular LangGraph-based workflow orchestration platform that demonstrates intelligent escalation between AI agents and human experts. This document provides a comprehensive technical overview of the system architecture.

## Core Design Principles

### 1. Modular Architecture
- **Separation of Concerns**: Each component has a single responsibility
- **Interface Contracts**: Clear interfaces define component interactions
- **Testability**: Each component can be tested in isolation
- **Extensibility**: New agents and workflows can be added easily

### 2. Human-in-the-Loop Integration
- **Seamless Handoffs**: Smooth transitions between AI and human agents
- **Context Preservation**: Full conversation context maintained across handoffs
- **Intelligent Routing**: Smart assignment of requests to appropriate human experts
- **Feedback Loops**: Continuous learning from human interactions

### 3. Configuration-Driven Design
- **External Configuration**: System behavior controlled through config files
- **Multi-Provider Support**: Multiple LLM providers with automatic fallback
- **Environment Flexibility**: Different configs for dev/staging/production
- **Runtime Adaptation**: Dynamic configuration loading and validation

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        HYBRID AI SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │  Answer Agent   │    │ Evaluator Agent │    │ Escalation   │ │
│  │                 │    │                 │    │ Router       │ │
│  │ • LLM Integration│    │ • Quality Check │    │ • Human      │ │
│  │ • Context Aware │────│ • Score Response│────│   Assignment │ │
│  │ • Multi-Provider│    │ • Escalation    │    │ • Priority   │ │
│  │ • Fallback      │    │   Decision      │    │   Calculation│ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│           │                       │                     │       │
│           └───────────────────────┼─────────────────────┘       │
│                                   │                             │
│  ┌─────────────────────────────────┼─────────────────────────────┐ │
│  │               CORE INFRASTRUCTURE                           │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │ Config      │  │ Context     │  │ Session Tracking    │ │ │
│  │  │ Manager     │  │ Manager     │  │                     │ │ │
│  │  │             │  │             │  │ • Performance       │ │ │
│  │  │ • Models    │  │ • SQLite    │  │ • Metrics           │ │ │
│  │  │ • Prompts   │  │ • History   │  │ • Cost Tracking     │ │ │
│  │  │ • Settings  │  │ • Memory    │  │ • Error Monitoring  │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    INTEGRATIONS                              │ │
│  │                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │ LLM         │  │ LangSmith   │  │ Human Interface     │ │ │
│  │  │ Providers   │  │ Tracing     │  │                     │ │ │
│  │  │             │  │             │  │ • Agent Management  │ │ │
│  │  │ • OpenAI    │  │ • Monitoring│  │ • Handoff Protocol  │ │ │
│  │  │ • Anthropic │  │ • Analytics │  │ • Feedback Collection│ │ │
│  │  │ • Local     │  │ • Debugging │  │ • Quality Assurance │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### State Management
The system uses a centralized state schema (`HybridSystemState`) that flows through all components:

```python
HybridSystemState = {
    # Core identification
    "query_id": str,
    "user_id": str, 
    "session_id": str,
    "timestamp": datetime,
    
    # User input
    "query": str,
    "messages": List[Message],  # LangChain compatible
    
    # Agent outputs
    "ai_response": str,
    "evaluation_result": EvaluationResult,
    "escalation_decision": bool,
    "escalation_data": EscalationData,
    
    # Workflow control
    "next_action": str,
    "workflow_complete": bool,
    
    # Performance tracking
    "node_execution_times": Dict[str, float],
    "total_tokens_used": int,
    "total_cost_usd": float
}
```

### Workflow Execution Pattern

```
User Query → State Initialization → Agent Processing → State Update → Next Agent
     ↓               ↓                     ↓                ↓           ↓
  query_id      HybridSystemState    Node.__call__()   State Merge   Router
```

## Component Deep Dive

### 1. Answer Agent (`src/nodes/answer_agent.py`)

**Responsibility**: Generate intelligent AI responses to user queries

**Key Features**:
- Multi-LLM provider support with automatic fallback
- Context-aware response generation using conversation history
- Performance tracking and token usage monitoring
- Error handling with graceful degradation

**Dependencies**:
- `LLMProviderFactory`: For model access
- `ConfigProvider`: For prompts and settings
- `ContextProvider`: For conversation history

**State Flow**:
```
Input: {query, user_id, session_id}
Process: Context retrieval → LLM generation → Context saving
Output: {ai_response, initial_assessment, messages}
```

### 2. Evaluator Agent (`src/nodes/evaluator_agent.py`)

**Responsibility**: Assess response quality and determine escalation needs

**Key Features**:
- Multi-dimensional quality scoring (accuracy, completeness, clarity)
- Context-aware evaluation considering user history
- Configurable escalation thresholds
- Pattern detection (repeated queries, user frustration)

**Evaluation Metrics**:
- **Accuracy**: Factual correctness of the response
- **Completeness**: How fully the query was addressed
- **Clarity**: Understandability and structure
- **User Satisfaction**: Predicted user satisfaction score

**State Flow**:
```
Input: {query, ai_response, user_history}
Process: Quality analysis → Context factors → Escalation decision
Output: {evaluation_result, escalation_decision, escalation_reason}
```

### 3. Escalation Router (`src/nodes/escalation_router.py`)

**Responsibility**: Route escalations to appropriate human experts

**Key Features**:
- Expertise matching based on query analysis
- Priority calculation considering urgency and context
- Human agent availability management
- Estimated resolution time calculation

**Routing Logic**:
```python
def route_escalation(query, evaluation):
    expertise = identify_expertise(query)  # technical, billing, general
    priority = calculate_priority(evaluation.score, query_urgency)
    agent = find_best_agent(expertise, priority, availability)
    return escalation_data
```

### 4. Core Infrastructure

#### Configuration Management (`src/core/config/`)
- **Hierarchical Configuration**: Environment → File → Defaults
- **Type Safety**: Pydantic models for validation
- **Hot Reloading**: Dynamic configuration updates
- **Multi-Format Support**: JSON, YAML, environment variables

#### Context Management (`src/core/context_manager.py`)
- **SQLite Backend**: Persistent conversation storage
- **Efficient Retrieval**: Optimized queries for context lookup
- **Memory Management**: Automatic cleanup of old conversations
- **Privacy Controls**: User data isolation and deletion

#### Session Tracking (`src/core/session_tracker.py`)
- **Real-time Metrics**: Performance monitoring
- **Cost Tracking**: Token usage and API costs
- **Error Analysis**: Failure pattern detection
- **Trend Analysis**: Historical performance trends

## LLM Integration Architecture

### Provider Abstraction
```python
class LLMProvider:
    def generate_response(prompt: str, system_prompt: str) -> str
    def evaluate_response(query: str, response: str) -> Dict
    
class LLMProviderFactory:
    def create_provider(model_name: str) -> LLMProvider
    def create_provider_with_fallback() -> LLMProvider
```

### Fallback Strategy
1. **Primary Model**: Configured default model
2. **Local Fallback**: Available local models
3. **Cloud Fallback**: API-based models (if keys available)
4. **Error Handling**: Graceful degradation with user notification

### Supported Providers
- **OpenAI**: GPT-3.5, GPT-4 series
- **Anthropic**: Claude 3 series
- **Local Models**: Llama, Mistral, CodeLlama via LlamaCpp
- **Optimized Local**: CTransformers for faster inference

## Monitoring and Observability

### LangSmith Integration
- **Automatic Tracing**: All agent interactions traced
- **Performance Metrics**: Latency, token usage, costs
- **Error Tracking**: Detailed error context and stack traces
- **Custom Metrics**: Domain-specific KPIs

### Structured Logging
```python
# Custom log types
logger.model_call(model_name, operation, duration, tokens)
logger.escalation(user_id, reason, priority, metadata)
logger.context_operation(operation, user_id, entries_count)
```

### Health Monitoring
- **System Health**: Component status and availability
- **Performance Alerts**: Threshold-based notifications
- **Resource Usage**: Memory, CPU, disk utilization
- **Quality Metrics**: Response quality trends

## Security and Privacy

### Data Protection
- **User Isolation**: Session and context data segregated by user
- **Encryption**: Sensitive data encrypted at rest
- **Access Controls**: Role-based access to human agents
- **Audit Logging**: All data access logged

### API Security
- **Rate Limiting**: Protection against abuse
- **Input Validation**: Comprehensive input sanitization
- **Error Handling**: No sensitive information in error messages
- **CORS Configuration**: Controlled cross-origin access

## Deployment Architecture

### Container Strategy
```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as base
# Install system dependencies
# Copy and install Python dependencies
# Copy application code
# Configure runtime environment
```

### Environment Configuration
- **Development**: Full logging, debug mode, local models
- **Staging**: Production-like setup with test data
- **Production**: Optimized performance, monitoring, security

### Scaling Considerations
- **Horizontal Scaling**: Multiple container instances
- **Load Balancing**: Request distribution across instances
- **Database Scaling**: Connection pooling and read replicas
- **Cache Layer**: Redis for frequently accessed data

## Extension Points

### Adding New Agents
1. Implement `NodeInterface` in `src/nodes/`
2. Add configuration in `config/prompts.json`
3. Update workflow in `src/workflows/hybrid_workflow.py`
4. Add comprehensive tests

### Custom LLM Providers
1. Extend `LLMProvider` base class
2. Implement required methods
3. Add to `LLMProviderFactory`
4. Update configuration schema

### Workflow Customization
1. Create new workflow in `src/workflows/`
2. Define custom state schema if needed
3. Implement LangGraph workflow logic
4. Add monitoring and error handling

## Performance Characteristics

### Latency Targets
- **Answer Generation**: < 3 seconds (local), < 5 seconds (cloud)
- **Evaluation**: < 1 second
- **Escalation Routing**: < 500ms
- **Context Retrieval**: < 200ms

### Throughput Estimates
- **Concurrent Users**: 50-100 per instance
- **Requests/Second**: 10-20 per instance
- **Database Operations**: 1000+ queries/second

### Resource Requirements
- **Memory**: 2-4GB per instance
- **CPU**: 2-4 cores recommended
- **Storage**: 10GB+ for models and data
- **Network**: Stable internet for cloud LLMs

## Testing Strategy

### Test Levels
1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **End-to-End Tests**: Full workflow testing
4. **Performance Tests**: Load and stress testing

### Test Coverage
- **Core Components**: >95% coverage
- **Agent Logic**: >90% coverage
- **Configuration**: >90% coverage
- **Error Handling**: 100% coverage

### Test Data Management
- **Mock Providers**: Simulated LLM responses
- **Test Fixtures**: Consistent test data
- **Isolated Databases**: Test-specific data stores
- **Cleanup Automation**: Test environment reset