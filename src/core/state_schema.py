"""
Centralized state schema for all LangGraph nodes
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, NotRequired

from typing_extensions import TypedDict


@dataclass
class EscalationData:
    """Structured escalation information"""

    priority: str  # "low", "medium", "high"
    required_expertise: str  # "technical", "financial", "general", etc.
    estimated_resolution_time: int | None  # minutes
    suggested_human_id: str | None
    context_summary: str
    escalation_reason: str


@dataclass
class EvaluationResult:
    """Structured evaluation result"""

    overall_score: float
    accuracy: float
    completeness: float
    clarity: float
    user_satisfaction: float
    confidence: float
    reasoning: str
    context_factors: dict[str, Any]


class HybridSystemState(TypedDict):
    """Complete state schema for the hybrid system workflow"""

    # Core identification
    query_id: str
    user_id: str
    session_id: str
    timestamp: datetime

    # User input
    query: str
    additional_context: NotRequired[str]

    # LangChain message compatibility
    messages: Annotated[list, "add_messages"]

    # Node outputs
    initial_assessment: NotRequired[dict[str, Any]]  # Module 1 output
    ai_response: NotRequired[str]  # Module 1 output
    evaluation_result: NotRequired[EvaluationResult]  # Module 2 output
    escalation_decision: NotRequired[bool]  # Module 2 output
    escalation_data: NotRequired[EscalationData]  # Module 3 output
    human_assignment: NotRequired[dict[str, Any]]  # Module 3 output
    human_response: NotRequired[str]  # Module 4 output
    feedback_data: NotRequired[dict[str, Any]]  # Module 5 input
    quality_metrics: NotRequired[dict[str, Any]]  # Module 6 output

    # Workflow control
    next_action: NotRequired[str]  # "evaluate", "escalate", "respond", "get_feedback"
    workflow_complete: NotRequired[bool]
    final_response: NotRequired[str]

    # Performance tracking (auto-populated)
    node_execution_times: NotRequired[dict[str, float]]
    total_tokens_used: NotRequired[int]
    total_cost_usd: NotRequired[float]

    # Context and configuration
    conversation_context: NotRequired[dict[str, Any]]
    user_preferences: NotRequired[dict[str, Any]]
    system_config: NotRequired[dict[str, Any]]
