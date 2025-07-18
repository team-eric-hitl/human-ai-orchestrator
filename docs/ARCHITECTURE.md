# System Architecture Documentation

## Overview

The Human-in-the-Loop (HITL) AI System is a modular LangGraph-based workflow orchestration platform designed to improve both customer and employee experience through intelligent AI-human collaboration. The system intercepts all customer-AI interactions to ensure quality, detect frustration, and route escalations appropriately while protecting employee wellbeing. This document provides a comprehensive technical overview of the updated system architecture.

## Core Design Principles

### 1. Modular Architecture
- **Separation of Concerns**: Each component has a single responsibility
- **Interface Contracts**: Clear interfaces define component interactions
- **Testability**: Each component can be tested in isolation
- **Extensibility**: New agents and workflows can be added easily

### 2. Human-in-the-Loop Integration
- **Quality Interception**: All AI responses reviewed before customer delivery
- **Frustration Detection**: Real-time monitoring of customer emotional state
- **Intelligent Routing**: Smart assignment considering both customer needs and employee wellbeing
- **Employee Protection**: Workload balancing and burnout prevention
- **Context Preservation**: Full conversation context maintained across all handoffs

### 3. Agent-Centric Configuration Design
- **Agent Isolation**: Each agent has its own configuration namespace
- **Shared Resources**: Global models, providers, and system settings
- **Environment Overrides**: Environment-specific configuration layers
- **Hot-Reloading**: Dynamic configuration updates without restart
- **Multi-Provider Support**: Multiple LLM providers with automatic fallback

## System Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        HUMAN-IN-THE-LOOP AI SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐  │
│  │  Chatbot Agent  │    │  Quality Agent  │    │  Frustration Agent      │  │
│  │                 │    │                 │    │                         │  │
│  │ • Customer      │    │ • Response      │    │ • Sentiment Analysis    │  │
│  │   Service Focus │────│   Review        │────│ • Pattern Detection     │  │
│  │ • Empathy       │    │ • Improvement   │    │ • Escalation Triggers   │  │
│  │ • Multi-Provider│    │ • Escalation    │    │ • Employee Protection   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────────────┘  │
│           │                       │                          │              │
│           └───────────────────────┼──────────────────────────┘              │
│                                   │                                         │
│  ┌─────────────────────────────────┼─────────────────────────────────────────┐ │
│  │     ┌─────────────────────────┐ │ ┌─────────────────────────────────────┐ │ │
│  │     │    Routing Agent        │ │ │    Context Manager Agent            │ │ │
│  │     │                         │ │ │                                     │ │ │
│  │     │ • Employee Wellbeing    │ │ │ • SQL Database Context              │ │ │
│  │     │ • Skill Matching        │─┼─│ • Interaction History               │ │ │
│  │     │ • Workload Balancing    │ │ │ • Similar Cases                     │ │ │
│  │     │ • Strategic Routing     │ │ │ • Web Search (Optional)             │ │ │
│  │     └─────────────────────────┘ │ └─────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                         CORE INFRASTRUCTURE                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  ┌──────────────┐ │ │
│  │  │Agent Config │  │ Context     │  │Session        │  │ Simulation   │ │ │
│  │  │Manager      │  │ Manager     │  │Tracking       │  │ Framework    │ │ │
│  │  │• Quality    │  │• SQLite     │  │• Performance  │  │• Customer    │ │ │
│  │  │• Frustration│  │• History    │  │• Metrics      │  │  Simulator   │ │ │
│  │  │• Routing    │  │• Memory     │  │• Cost Track   │  │• Employee    │ │ │
│  │  │• Context    │  │• Privacy    │  │• Error Mon    │  │  Simulator   │ │ │
│  │  └─────────────┘  └─────────────┘  └───────────────┘  └──────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                            INTEGRATIONS                                 │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │ │
│  │  │ LLM         │  │ LangSmith   │  │ Human Agent │  │ Demo            │ │ │
│  │  │ Providers   │  │ Tracing     │  │ Interface   │  │ Orchestration   │ │ │
│  │  │• OpenAI     │  │• Monitoring │  │• Workload   │  │• Scenarios      │ │ │
│  │  │• Anthropic  │  │• Analytics  │  │  Management │  │• Real-time      │ │ │
│  │  │• Local      │  │• Debugging  │  │• Performance│  │  Interaction    │ │ │
│  │  │• Fallback   │  │• Quality    │  │• Wellbeing  │  │• Multi-window   │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
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

### 1. Chatbot Agent (`src/nodes/chatbot_agent.py`)

**Responsibility**: Generate customer service-focused AI responses with enhanced empathy and service orientation

**Key Features**:
- Customer service-focused response generation with emotional intelligence
- Real-time customer state analysis (urgency, frustration, politeness detection)
- Context-aware personalization based on customer history
- Multi-LLM provider support with automatic fallback
- Response enhancement for customer service standards

**Customer Analysis**:
- **Sentiment Detection**: Urgency, frustration, politeness indicators
- **Communication Style**: Matching customer tone appropriately
- **Service Scoring**: Automated assessment of response quality
- **Empathy Integration**: Adding appropriate emotional responses

**State Flow**:
```
Input: {query, user_id, session_id}
Process: Customer analysis → Context building → Service-focused generation → Enhancement
Output: {ai_response, customer_analysis, response_metadata, next_action: "quality_check"}
```

### 2. Quality Agent (`src/nodes/quality_agent.py`)

**Responsibility**: Review all chatbot responses and decide if adequate, needs adjustment, or requires human intervention

**Key Features**:
- Comprehensive response quality assessment using LLM and rule-based methods
- Response improvement and adjustment capabilities
- Context-aware evaluation considering customer history and patterns
- Configurable quality thresholds for different scenarios
- Automatic escalation triggers for low-quality responses

**Quality Assessment Dimensions**:
- **Accuracy**: Factual correctness and information reliability
- **Completeness**: How fully the customer's needs are addressed
- **Clarity**: Understandability and communication effectiveness
- **Customer Service Standards**: Professional tone and helpfulness
- **Contextual Appropriateness**: Matching customer state and history

**Decision Framework**:
```python
def assess_quality(query, response, context):
    score = llm_assessment + rule_based_assessment + context_adjustment
    if score >= adequate_threshold: return "ADEQUATE"
    elif score >= adjustment_threshold: return "NEEDS_ADJUSTMENT"
    else: return "HUMAN_INTERVENTION"
```

**State Flow**:
```
Input: {query, ai_response, customer_context}
Process: Quality assessment → Decision making → Response adjustment (if needed)
Output: {quality_assessment, next_action, adjusted_response (optional)}
```

### 3. Frustration Agent (`src/nodes/frustration_agent.py`)

**Responsibility**: Analyze customer communications to detect frustration levels and trigger appropriate interventions

**Key Features**:
- Real-time sentiment analysis with pattern detection over interaction history
- Escalating frustration trend identification
- Employee protection through intelligent workload distribution
- Configurable intervention thresholds
- Cultural and linguistic sensitivity in emotion detection

**Frustration Detection Methods**:
- **Keyword Analysis**: Extensive frustration indicator database
- **Pattern Recognition**: Escalation trends over multiple interactions
- **Behavioral Signals**: Caps usage, punctuation patterns, urgency indicators
- **LLM Analysis**: Sophisticated sentiment evaluation
- **Context Integration**: Previous escalations and interaction frequency

**Employee Protection Features**:
- **Consecutive Case Limits**: Prevents agent burnout from difficult customers
- **Cooldown Periods**: Ensures breaks between frustrated customer interactions
- **Tolerance Matching**: Routes based on agent frustration handling capacity
- **Wellbeing Monitoring**: Tracks agent stress and workload impact

**State Flow**:
```
Input: {query, interaction_history, customer_context}
Process: Frustration analysis → Pattern detection → Intervention decision
Output: {frustration_analysis, intervention_needed, next_action}
```

### 4. Routing Agent (`src/nodes/routing_agent.py`)

**Responsibility**: Intelligently route escalations to human agents while optimizing both customer outcomes and employee experience

**Key Features**:
- Multi-strategy routing (skill-based, workload-balanced, employee wellbeing)
- Comprehensive skill matching with complexity assessment
- Real-time workload balancing and capacity management
- Employee wellbeing protection and burnout prevention
- Queue management with priority optimization

**Routing Strategies**:
- **Skill-Based**: Match complex cases to specialized expertise
- **Workload-Balanced**: Distribute work evenly across available agents
- **Employee Wellbeing**: Prioritize agent mental health and job satisfaction
- **Priority-Based**: Route urgent cases to most capable agents

**Employee Wellbeing Considerations**:
```python
def select_agent_with_wellbeing(requirements, available_agents):
    # Filter agents who've had too many difficult cases
    suitable_agents = filter_by_consecutive_difficult_cases(available_agents)
    # Consider frustration tolerance for frustrated customers
    if customer_frustrated: suitable_agents = filter_by_frustration_tolerance(suitable_agents)
    # Apply cooldown periods for recent difficult interactions
    suitable_agents = apply_cooldown_filters(suitable_agents)
    return optimize_selection(suitable_agents, requirements)
```

**State Flow**:
```
Input: {escalation_requirements, available_agents, customer_context}
Process: Strategy selection → Agent scoring → Wellbeing validation → Assignment
Output: {routing_decision, assigned_agent, estimated_metrics}
```

### 5. Context Manager Agent (`src/nodes/context_manager_agent.py`)

**Responsibility**: Gather, analyze, and summarize comprehensive context from multiple sources to support decision-making

**Key Features**:
- Multi-source context aggregation (SQL database, interaction history, similar cases)
- Intelligent relevance scoring and prioritization
- Audience-specific context summarization
- Privacy-aware cross-user pattern analysis
- Optional web search integration for external knowledge

**Context Sources**:
- **Interaction History**: Customer's previous conversations and resolutions
- **User Profile**: Behavioral patterns, escalation history, preferences
- **Similar Cases**: Anonymized patterns from other customers with similar issues
- **Product Context**: Related service areas and known issues
- **Knowledge Base**: Internal documentation and FAQ matching
- **System Status**: Current service health and known problems

**Context Analysis Pipeline**:
```python
def gather_context(query, user_id, session_id):
    raw_context = gather_from_all_sources(query, user_id, session_id)
    relevance_scores = analyze_relevance(query, raw_context)
    priority_context = filter_by_relevance(raw_context, relevance_scores)
    return create_audience_summaries(priority_context)
```

**Audience-Specific Summaries**:
- **AI Agents**: Structured data for algorithmic processing
- **Human Agents**: Narrative summaries for quick human comprehension
- **Quality Assessment**: Risk factors and quality considerations
- **Routing Decisions**: Complexity and expertise requirements

**State Flow**:
```
Input: {query, user_id, session_id, context_requirements}
Process: Multi-source gathering → Relevance analysis → Audience summarization
Output: {context_data, context_analysis, context_summaries}
```

### 6. Simulation Framework (`src/simulation/`)

**Responsibility**: Provide realistic testing and demonstration capabilities for the HITL system

#### Human Customer Simulator (`src/simulation/human_customer_simulator.py`)
- **Multiple Personalities**: Polite, impatient, technical, frustrated, confused, business
- **Diverse Scenarios**: Simple questions, technical issues, billing problems, escalation requests
- **Dynamic Frustration**: Real-time frustration level tracking based on interactions
- **Realistic Responses**: Context-aware customer responses to chatbot and human agents

#### Employee Simulator (`src/simulation/employee_simulator.py`)
- **Diverse Employee Roster**: Junior/senior support, specialists, managers with different skills
- **Personality Traits**: Empathetic, direct, thorough, efficient, patient approaches
- **Workload Management**: Realistic capacity tracking and availability modeling
- **Performance Metrics**: Customer satisfaction, resolution times, escalation rates

#### Demo Orchestrator (`src/simulation/demo_orchestrator.py`)
- **Complete Scenario Management**: End-to-end conversation flow simulation
- **Predefined Scenarios**: 6 demonstration scenarios covering various outcomes
- **Real-time Interaction**: Step-by-step progression through HITL workflow
- **Analytics Integration**: Complete logging and metrics collection

**Demo Scenarios**:
1. **Happy Path**: Polite customer → Quality response → Direct resolution
2. **Technical Escalation**: Complex query → Quality assessment → Specialist routing
3. **Frustrated Customer**: Poor experience → Frustration detection → Empathetic human
4. **Manager Escalation**: Explicit complaint → Direct management routing
5. **Quality Adjustment**: Inadequate response → Quality improvement → Re-delivery
6. **Employee Wellbeing**: Multiple difficult cases → Intelligent rotation

### 7. Core Infrastructure

#### Configuration Management (`src/core/config/`)
- **Hierarchical Configuration**: Environment → File → Defaults
- **Agent-Specific Configs**: Individual configurations for each agent type
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