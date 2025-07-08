"""
State schema interfaces for the hybrid system

This module defines the data structures and type schemas used
throughout the hybrid AI-human system for state management.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any, NotRequired

from typing_extensions import TypedDict


@dataclass
class EscalationData:
    """Structured escalation information

    Contains all necessary information for routing and handling
    escalations to human agents.

    Attributes:
        priority: Priority level (low, medium, high)
        required_expertise: Type of expertise needed
        estimated_resolution_time: Expected resolution time in minutes
        suggested_human_id: ID of recommended human agent
        context_summary: Brief summary of the context
        escalation_reason: Reason for escalation
    """

    priority: str
    required_expertise: str
    estimated_resolution_time: int | None
    suggested_human_id: str | None
    context_summary: str
    escalation_reason: str


@dataclass
class EvaluationResult:
    """Structured evaluation result for AI responses

    Contains comprehensive evaluation metrics for assessing
    the quality and appropriateness of AI-generated responses.

    Attributes:
        overall_score: Overall quality score (0-1)
        accuracy: Accuracy of the response (0-1)
        completeness: Completeness of the response (0-1)
        clarity: Clarity and readability (0-1)
        user_satisfaction: Predicted user satisfaction (0-1)
        confidence: System confidence in the response (0-1)
        reasoning: Explanation of the evaluation
        context_factors: Additional context factors considered
    """

    overall_score: float
    accuracy: float
    completeness: float
    clarity: float
    user_satisfaction: float
    confidence: float
    reasoning: str
    context_factors: dict[str, Any]


class HybridSystemState(TypedDict):
    """Complete state schema for the hybrid system workflow

    This TypedDict defines the complete state structure that flows
    through the hybrid system workflow. It includes all data needed
    for processing user queries through AI and human agents.

    The schema is designed to be:
    - Compatible with LangChain/LangGraph message handling
    - Comprehensive enough to support all workflow decisions
    - Structured for efficient AI processing and analysis
    - Extensible for future enhancements
    """

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
    initial_assessment: NotRequired[dict[str, Any]]
    ai_response: NotRequired[str]
    evaluation_result: NotRequired[EvaluationResult]
    escalation_decision: NotRequired[bool]
    escalation_data: NotRequired[EscalationData]
    human_assignment: NotRequired[dict[str, Any]]
    human_response: NotRequired[str]
    feedback_data: NotRequired[dict[str, Any]]
    quality_metrics: NotRequired[dict[str, Any]]

    # Workflow control
    next_action: NotRequired[str]
    workflow_complete: NotRequired[bool]
    final_response: NotRequired[str]

    # Performance tracking
    node_execution_times: NotRequired[dict[str, float]]
    total_tokens_used: NotRequired[int]
    total_cost_usd: NotRequired[float]

    # Context and configuration
    conversation_context: NotRequired[dict[str, Any]]
    user_preferences: NotRequired[dict[str, Any]]
    system_config: NotRequired[dict[str, Any]]
