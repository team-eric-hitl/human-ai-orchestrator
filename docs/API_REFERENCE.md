# API Reference Documentation

## Overview

This document provides a comprehensive API reference for the Hybrid AI-Human System. It covers all public interfaces, data structures, and integration points for developers working with or extending the system.

## Core Interfaces

### Node Interface (`src/interfaces/nodes/base.py`)

The fundamental contract for all processing nodes in the system.

```python
class NodeInterface(ABC):
    """Abstract base class for all processing nodes"""
    
    @abstractmethod
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """Process the state and return updated state"""
        pass
    
    @abstractmethod
    def validate_state(self, state: HybridSystemState) -> bool:
        """Validate that the state is suitable for this node"""
        pass
    
    @property
    @abstractmethod
    def node_name(self) -> str:
        """Get the name of this node"""
        pass
    
    @property
    @abstractmethod
    def required_state_keys(self) -> List[str]:
        """Get the state keys required by this node"""
        pass
    
    @property
    @abstractmethod
    def output_state_keys(self) -> List[str]:
        """Get the state keys this node will add/modify"""
        pass
```

#### Usage Example
```python
class CustomNode(NodeInterface):
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        # Process the state
        return updated_state
    
    def validate_state(self, state: HybridSystemState) -> bool:
        return "query" in state and "user_id" in state
    
    @property
    def node_name(self) -> str:
        return "CustomNode"
    
    @property
    def required_state_keys(self) -> List[str]:
        return ["query", "user_id"]
    
    @property
    def output_state_keys(self) -> List[str]:
        return ["custom_result"]
```

## Data Structures

### HybridSystemState (`src/core/state_schema.py`)

The central state object that flows through all system components.

```python
class HybridSystemState(TypedDict):
    # Core identification
    query_id: str                                    # Unique query identifier
    user_id: str                                     # User identifier
    session_id: str                                  # Session identifier
    timestamp: datetime                              # Query timestamp
    
    # User input
    query: str                                       # User's question/request
    additional_context: NotRequired[str]             # Optional additional context
    messages: Annotated[List, "add_messages"]        # LangChain message list
    
    # Node outputs
    initial_assessment: NotRequired[Dict[str, Any]]  # Answer Agent output
    ai_response: NotRequired[str]                    # Generated AI response
    evaluation_result: NotRequired[EvaluationResult] # Evaluator output
    escalation_decision: NotRequired[bool]           # Escalation decision
    escalation_data: NotRequired[EscalationData]     # Escalation details
    human_assignment: NotRequired[Dict[str, Any]]    # Human agent assignment
    human_response: NotRequired[str]                 # Human agent response
    
    # Workflow control
    next_action: NotRequired[str]                    # Next workflow step
    workflow_complete: NotRequired[bool]             # Workflow completion flag
    final_response: NotRequired[str]                 # Final user response
    
    # Performance tracking
    node_execution_times: NotRequired[Dict[str, float]]  # Node execution times
    total_tokens_used: NotRequired[int]                  # Total tokens consumed
    total_cost_usd: NotRequired[float]                   # Total cost in USD
```

### EvaluationResult (`src/core/state_schema.py`)

Quality assessment results from the Evaluator Agent.

```python
@dataclass
class EvaluationResult:
    overall_score: float                    # Overall quality score (1-10)
    accuracy: float                         # Accuracy score (1-10)
    completeness: float                     # Completeness score (1-10)
    clarity: float                          # Clarity score (1-10)
    user_satisfaction: float                # Predicted satisfaction (1-10)
    confidence: float                       # Confidence in evaluation (0-1)
    reasoning: str                          # Explanation of evaluation
    context_factors: Dict[str, Any]         # Context factors considered
```

### EscalationData (`src/core/state_schema.py`)

Escalation information for human agent routing.

```python
@dataclass
class EscalationData:
    priority: str                           # "low", "medium", "high"
    required_expertise: str                 # "technical", "billing", "general"
    estimated_resolution_time: int | None   # Estimated time in minutes
    suggested_human_id: str | None          # Assigned human agent ID
    context_summary: str                    # Summary for human agent
    escalation_reason: str                  # Reason for escalation
```

## Agent APIs

### Answer Agent (`src/nodes/answer_agent.py`)

Generates AI responses to user queries.

```python
class AnswerAgentNode:
    def __init__(
        self,
        config_provider: ConfigProvider,
        context_provider: ContextProvider
    ):
        """Initialize Answer Agent with providers"""
        
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """Generate AI response and update state"""
        
    def _build_context_prompt(self, state: HybridSystemState) -> str:
        """Build context-aware prompt from conversation history"""
        
    def _generate_response(
        self, 
        query: str, 
        context_prompt: str, 
        system_prompt: str
    ) -> str:
        """Generate AI response using LLM"""
```

#### Input Requirements
- `state["query"]`: User's question
- `state["user_id"]`: User identifier
- `state["session_id"]`: Session identifier

#### Output Additions
- `state["ai_response"]`: Generated response
- `state["initial_assessment"]`: Response metadata
- `state["messages"]`: Updated message history
- `state["next_action"]`: Set to "evaluate"

### Evaluator Agent (`src/nodes/evaluator_agent.py`)

Evaluates response quality and determines escalation needs.

```python
class EvaluatorAgentNode:
    def __init__(
        self,
        config_provider: ConfigProvider,
        context_provider: ContextProvider
    ):
        """Initialize Evaluator Agent with providers"""
        
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """Evaluate response and determine escalation"""
        
    def _evaluate_response(
        self, 
        state: HybridSystemState, 
        context_factors: Dict[str, Any]
    ) -> EvaluationResult:
        """Evaluate response quality using LLM or heuristics"""
        
    def _decide_escalation(
        self, 
        evaluation: EvaluationResult
    ) -> Tuple[bool, str]:
        """Decide if escalation is needed"""
```

#### Input Requirements
- `state["query"]`: Original user query
- `state["ai_response"]`: AI-generated response
- `state["user_id"]`: For context lookup

#### Output Additions
- `state["evaluation_result"]`: Quality assessment
- `state["escalation_decision"]`: Boolean escalation decision
- `state["escalation_reason"]`: Reason for escalation
- `state["next_action"]`: "escalate" or "respond"

### Escalation Router (`src/nodes/escalation_router.py`)

Routes escalations to appropriate human agents.

```python
class EscalationRouterNode:
    def __init__(self, config_provider: ConfigProvider):
        """Initialize Escalation Router with configuration"""
        
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """Route escalation to human agent"""
        
    def _identify_required_expertise(self, state: HybridSystemState) -> str:
        """Determine expertise needed for the query"""
        
    def _calculate_priority(self, state: HybridSystemState) -> str:
        """Calculate escalation priority"""
        
    def _assign_human_agent(
        self, 
        expertise: str, 
        priority: str
    ) -> Dict[str, Any] | None:
        """Find and assign best available human agent"""
```

#### Input Requirements
- `state["query"]`: Original user query
- `state["evaluation_result"]`: Quality assessment
- `state["escalation_reason"]`: Reason for escalation

#### Output Additions
- `state["escalation_data"]`: Escalation details
- `state["human_assignment"]`: Assigned human agent
- `state["next_action"]`: "await_human" or "queue_escalation"

## Configuration APIs

### ConfigProvider (`src/interfaces/core/config.py`)

Interface for accessing system configuration.

```python
class ConfigProvider(Protocol):
    @property
    def models(self) -> ModelConfigManager:
        """Get model configuration manager"""
        
    @property
    def prompts(self) -> Dict[str, Any]:
        """Get prompt configurations"""
        
    @property
    def thresholds(self) -> Any:
        """Get threshold configurations"""
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
```

#### Usage Example
```python
# Access model configuration
model_config = config_provider.models.get_model("gpt-4")

# Access prompts
system_prompt = config_provider.prompts.answer_agent["system_prompt"]

# Access thresholds
escalation_threshold = config_provider.thresholds.escalation_score
```

### ModelConfig (`src/core/config/models.py`)

Configuration for individual models.

```python
@dataclass
class ModelConfig:
    name: str                      # Model identifier
    type: str                      # Provider type (openai, anthropic, llama)
    model_name: str | None         # Provider-specific model name
    path: str | None               # Local model path
    temperature: float             # Sampling temperature
    max_tokens: int                # Maximum tokens to generate
    context_length: int            # Maximum context length
    gpu_layers: int                # GPU layers for local models
    
    def is_local(self) -> bool:
        """Check if this is a local model"""
        
    def is_available(self) -> bool:
        """Check if model is available for use"""
```

## Context Management APIs

### ContextProvider (`src/interfaces/core/context.py`)

Interface for conversation context management.

```python
class ContextProvider(Protocol):
    def save_context_entry(self, entry: ContextEntry) -> None:
        """Save a context entry"""
        
    def get_context_summary(
        self, 
        user_id: str, 
        session_id: str
    ) -> Dict[str, Any]:
        """Get context summary for user/session"""
        
    def get_recent_context(
        self, 
        user_id: str, 
        session_id: str, 
        limit: int = 10
    ) -> List[ContextEntry]:
        """Get recent context entries"""
        
    def cleanup_old_context(self, days: int = 30) -> int:
        """Clean up context older than specified days"""
```

### ContextEntry (`src/core/context_manager.py`)

Individual context entry structure.

```python
@dataclass
class ContextEntry:
    entry_id: str                  # Unique entry identifier
    user_id: str                   # User identifier
    session_id: str                # Session identifier
    timestamp: datetime            # Entry timestamp
    entry_type: str                # Type: "query", "response", "escalation"
    content: str                   # Entry content
    metadata: Dict[str, Any]       # Additional metadata
```

## LLM Provider APIs

### LLMProvider (`src/integrations/llm_providers.py`)

Base class for all LLM providers.

```python
class LLMProvider:
    def __init__(self, model_config: ModelConfig):
        """Initialize provider with model configuration"""
        
    def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using LLM"""
        
    def evaluate_response(self, query: str, response: str) -> Dict[str, Any]:
        """Evaluate response quality using LLM"""
```

### LLMProviderFactory (`src/integrations/llm_providers.py`)

Factory for creating LLM providers.

```python
class LLMProviderFactory:
    def __init__(self, config_dir: str = "config"):
        """Initialize factory with configuration directory"""
        
    def create_provider(self, model_name: str | None = None) -> LLMProvider:
        """Create provider for specific model"""
        
    def create_auto_provider(self) -> LLMProvider:
        """Auto-select best available provider"""
        
    def create_provider_with_fallback(
        self, 
        preferred_model: str | None = None
    ) -> LLMProvider:
        """Create provider with automatic fallback"""
```

## Workflow APIs

### Hybrid Workflow (`src/workflows/hybrid_workflow.py`)

Main workflow orchestrator.

```python
class HybridWorkflow:
    def __init__(
        self,
        config_provider: ConfigProvider,
        context_provider: ContextProvider,
        session_tracker: SessionTracker
    ):
        """Initialize workflow with providers"""
        
    def process_query(
        self,
        query: str,
        user_id: str,
        session_id: str,
        additional_context: str = ""
    ) -> HybridSystemState:
        """Process user query through complete workflow"""
        
    def create_initial_state(
        self,
        query: str,
        user_id: str,
        session_id: str,
        additional_context: str = ""
    ) -> HybridSystemState:
        """Create initial state for workflow"""
```

## Error Handling

### Custom Exceptions (`src/core/logging/exceptions.py`)

System-specific exception types.

```python
class ModelError(Exception):
    """Base exception for model-related errors"""
    def __init__(
        self, 
        message: str, 
        model_name: str, 
        model_type: str,
        extra: Dict[str, Any] = None
    ):
        
class ModelInferenceError(ModelError):
    """Exception for model inference failures"""
    
class ConfigurationError(Exception):
    """Exception for configuration-related errors"""
    
class ContextError(Exception):
    """Exception for context management errors"""
```

### Error Response Format

```python
{
    "error": {
        "type": "ModelInferenceError",
        "message": "Failed to generate response",
        "details": {
            "model_name": "gpt-4",
            "model_type": "openai",
            "duration": 5.2,
            "retry_count": 3
        },
        "timestamp": "2024-01-01T10:00:00Z",
        "request_id": "req_123"
    }
}
```

## Monitoring APIs

### SessionTracker (`src/core/session_tracker.py`)

Performance and metrics tracking.

```python
class SessionTracker:
    def start_session(self, user_id: str, session_id: str) -> None:
        """Start tracking a new session"""
        
    def track_node_execution(
        self, 
        session_id: str, 
        node_name: str, 
        duration: float
    ) -> None:
        """Track node execution time"""
        
    def track_token_usage(
        self, 
        session_id: str, 
        tokens: int, 
        cost: float
    ) -> None:
        """Track token usage and cost"""
        
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get metrics for a session"""
```

### Logger (`src/core/logging/logger.py`)

Structured logging interface.

```python
def get_logger(name: str) -> Logger:
    """Get logger instance with structured logging"""

# Custom log methods
logger.model_call(
    model_name: str,
    operation: str,
    duration: float,
    prompt_length: int = None,
    response_length: int = None
)

logger.escalation(
    user_id: str,
    reason: str,
    priority: str,
    extra: Dict[str, Any] = None
)

logger.context_operation(
    operation: str,
    user_id: str,
    entries_count: int = None,
    extra: Dict[str, Any] = None
)
```

## Integration Points

### Adding Custom Nodes

1. **Implement NodeInterface**:
```python
from src.interfaces.nodes.base import NodeInterface

class MyCustomNode(NodeInterface):
    # Implement required methods
```

2. **Add to Workflow**:
```python
# In hybrid_workflow.py
workflow = StateGraph(HybridSystemState)
workflow.add_node("my_custom_node", MyCustomNode())
```

3. **Configure**:
```json
// In config/prompts.json
{
    "my_custom_node": {
        "system_prompt": "Custom instructions...",
        "parameters": {...}
    }
}
```

### Adding LLM Providers

1. **Extend LLMProvider**:
```python
class MyLLMProvider(LLMProvider):
    def _initialize_client(self):
        # Custom initialization
        
    def generate_response(self, prompt, system_prompt=""):
        # Custom generation logic
```

2. **Add to Factory**:
```python
# In LLMProviderFactory._initialize_client()
elif self.provider_type == "my_provider":
    return self._setup_my_provider()
```

3. **Update Configuration**:
```yaml
# In config/models.yaml
my_model:
  type: "my_provider"
  custom_param: "value"
```

## Testing APIs

### Test Utilities

```python
# Test fixtures
from tests.fixtures import mock_config_provider, mock_context_provider

# Mock LLM responses
from tests.fixtures.mock_responses import SAMPLE_RESPONSES

# Test data
from tests.fixtures.test_data import SAMPLE_QUERIES, SAMPLE_STATES
```

### Testing Patterns

```python
def test_node_processing():
    # Arrange
    node = MyNode(mock_config_provider, mock_context_provider)
    state = create_test_state()
    
    # Act
    result = node(state)
    
    # Assert
    assert result["expected_output"] == "expected_value"
    assert node.validate_state(result)
```

## Rate Limits and Quotas

### API Limits
- **OpenAI**: Configured per API key
- **Anthropic**: Configured per API key
- **Local Models**: Hardware-limited
- **Context Storage**: 10,000 entries per user (configurable)

### Performance Guidelines
- **Concurrent Requests**: 50-100 per instance
- **Response Timeout**: 30 seconds default
- **Token Limits**: Model-specific maximums
- **Cost Monitoring**: Real-time tracking with alerts