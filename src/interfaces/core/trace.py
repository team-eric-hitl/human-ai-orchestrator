"""
Trace collection interfaces

This module defines the contracts for collecting and outputting full interaction traces
in the Human-in-the-Loop AI system. Traces capture complete workflows including
agent interactions, response times, system decisions, and performance metrics.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class OutputFormat(Enum):
    """Supported trace output formats"""
    DETAILED_JSON = "detailed_json"
    SUMMARY_JSON = "summary_json"
    CSV_TIMELINE = "csv_timeline"
    PERFORMANCE_ONLY = "performance_only"


@dataclass
class AgentInteraction:
    """Data structure for a single agent interaction within a trace
    
    Captures all details about an agent's processing including input,
    output, timing, and metadata for analysis and debugging.
    
    Attributes:
        agent_name: Name of the agent (e.g., 'frustration_agent', 'chatbot_agent')
        interaction_id: Unique identifier for this specific interaction
        sequence_number: Order of this interaction in the workflow
        start_time: When the agent processing began
        end_time: When the agent processing completed
        duration_ms: Processing time in milliseconds
        input_data: Data provided to the agent
        output_data: Data returned by the agent
        response_metadata: Agent-specific metadata (model, tokens, cost, etc.)
        next_action: What the system decided to do after this agent
    """
    
    agent_name: str
    interaction_id: str
    sequence_number: int
    start_time: datetime
    end_time: datetime
    duration_ms: float
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    response_metadata: dict[str, Any] = field(default_factory=dict)
    next_action: str = ""


@dataclass
class SystemDecision:
    """Data structure for a key system decision point
    
    Captures critical decision points where the system chose a specific
    path based on agent outputs and business logic.
    
    Attributes:
        decision_point: Type of decision (e.g., 'frustration_intervention', 'quality_gate')
        timestamp: When the decision was made
        decision: What the system decided to do
        reasoning: Explanation of why this decision was made
        factors: Key factors that influenced the decision
        confidence: Confidence score for the decision (0.0-1.0)
    """
    
    decision_point: str
    timestamp: datetime
    decision: str
    reasoning: str
    factors: list[str] = field(default_factory=list)
    confidence: Optional[float] = None


@dataclass
class WorkflowStage:
    """Data structure for workflow progression tracking
    
    Captures major milestones in the workflow progression for
    timing analysis and bottleneck identification.
    
    Attributes:
        stage: Name of the workflow stage
        timestamp: When this stage was reached
        duration_from_start_ms: Time from workflow start to this stage
    """
    
    stage: str
    timestamp: datetime
    duration_from_start_ms: float


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics for the entire trace
    
    Provides summary metrics for performance analysis and optimization.
    
    Attributes:
        total_processing_time_ms: Total time from start to finish
        ai_processing_time_ms: Time spent in AI agent processing
        routing_time_ms: Time spent on routing decisions
        queue_wait_time_ms: Time spent waiting in queues
        total_tokens_used: Total AI tokens consumed
        total_cost_usd: Total cost of processing
        agents_involved: Number of agents that processed this request
        escalation_occurred: Whether escalation to human occurred
        quality_interventions: Number of quality-based interventions
        customer_satisfaction_predicted: Predicted customer satisfaction
    """
    
    total_processing_time_ms: float
    ai_processing_time_ms: float = 0.0
    routing_time_ms: float = 0.0
    queue_wait_time_ms: float = 0.0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    agents_involved: int = 0
    escalation_occurred: bool = False
    quality_interventions: int = 0
    customer_satisfaction_predicted: Optional[float] = None


@dataclass
class InteractionTrace:
    """Complete trace of a user interaction through the HITL system
    
    This is the main data structure that captures everything about
    a user interaction from initial query to final resolution.
    
    Attributes:
        trace_id: Unique identifier for this trace
        session_id: Session this trace belongs to
        user_id: User who initiated this interaction
        query_id: Unique identifier for the original query
        start_time: When the interaction began
        end_time: When the interaction completed
        initial_query: The original user query
        agent_interactions: Ordered list of all agent processing steps
        system_decisions: Key decision points in the workflow
        workflow_progression: Timeline of major workflow stages
        performance_metrics: Aggregated performance data
        outcome: Final outcome and resolution details
        context_data: Additional context and metadata
    """
    
    trace_id: str
    session_id: str
    user_id: str
    query_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    initial_query: dict[str, Any] = field(default_factory=dict)
    agent_interactions: list[AgentInteraction] = field(default_factory=list)
    system_decisions: list[SystemDecision] = field(default_factory=list)
    workflow_progression: list[WorkflowStage] = field(default_factory=list)
    performance_metrics: Optional[PerformanceMetrics] = None
    outcome: dict[str, Any] = field(default_factory=dict)
    context_data: dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_duration_ms(self) -> float:
        """Get total trace duration in milliseconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return (datetime.now() - self.start_time).total_seconds() * 1000


class TraceCollectorInterface(ABC):
    """Abstract base class for trace collection
    
    Trace collectors capture complete interaction flows through the HITL system
    for analysis, debugging, and performance monitoring. They provide detailed
    visibility into agent processing, system decisions, and performance metrics.
    
    Implementations should handle:
    - Real-time trace collection during workflow execution
    - Efficient storage and retrieval of trace data
    - Multiple output formats for different use cases
    - Performance optimization for production workloads
    - Integration with existing logging and monitoring systems
    """
    
    @abstractmethod
    def start_trace(
        self, 
        session_id: str, 
        user_id: str, 
        query_id: str, 
        initial_query: dict[str, Any]
    ) -> str:
        """Start a new interaction trace
        
        Args:
            session_id: Session this trace belongs to
            user_id: User who initiated the interaction
            query_id: Unique identifier for the query
            initial_query: The original user query and metadata
            
        Returns:
            trace_id: Unique identifier for the new trace
        """
        pass
    
    @abstractmethod
    def record_agent_interaction(
        self,
        trace_id: str,
        agent_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        metadata: Optional[dict[str, Any]] = None,
        next_action: str = ""
    ) -> str:
        """Record an agent interaction in the trace
        
        Args:
            trace_id: Trace this interaction belongs to
            agent_name: Name of the agent that processed this step
            input_data: Data provided to the agent
            output_data: Data returned by the agent
            start_time: When processing started
            end_time: When processing completed
            metadata: Additional metadata (model info, costs, etc.)
            next_action: What the system will do next
            
        Returns:
            interaction_id: Unique identifier for this interaction
        """
        pass
    
    @abstractmethod
    def record_system_decision(
        self,
        trace_id: str,
        decision_point: str,
        decision: str,
        reasoning: str,
        factors: Optional[list[str]] = None,
        confidence: Optional[float] = None
    ) -> None:
        """Record a system decision point in the trace
        
        Args:
            trace_id: Trace this decision belongs to
            decision_point: Type of decision being made
            decision: What the system decided
            reasoning: Explanation for the decision
            factors: Key factors that influenced the decision
            confidence: Confidence score for the decision
        """
        pass
    
    @abstractmethod
    def record_workflow_stage(
        self,
        trace_id: str,
        stage: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record reaching a workflow stage
        
        Args:
            trace_id: Trace this stage belongs to
            stage: Name of the workflow stage reached
            timestamp: When this stage was reached (defaults to now)
        """
        pass
    
    @abstractmethod
    def finalize_trace(
        self,
        trace_id: str,
        outcome: dict[str, Any],
        end_time: Optional[datetime] = None
    ) -> InteractionTrace:
        """Finalize a trace and calculate performance metrics
        
        Args:
            trace_id: Trace to finalize
            outcome: Final outcome and resolution details
            end_time: When the interaction completed (defaults to now)
            
        Returns:
            Complete InteractionTrace object
        """
        pass
    
    @abstractmethod
    def get_trace(self, trace_id: str) -> Optional[InteractionTrace]:
        """Get a complete trace by ID
        
        Args:
            trace_id: Trace identifier to retrieve
            
        Returns:
            InteractionTrace object or None if not found
        """
        pass
    
    @abstractmethod
    def get_session_traces(self, session_id: str) -> list[InteractionTrace]:
        """Get all traces for a session
        
        Args:
            session_id: Session to get traces for
            
        Returns:
            List of InteractionTrace objects for the session
        """
        pass
    
    @abstractmethod
    def export_trace(
        self, 
        trace_id: str, 
        format: OutputFormat = OutputFormat.DETAILED_JSON
    ) -> str:
        """Export a trace in the specified format
        
        Args:
            trace_id: Trace to export
            format: Output format for the export
            
        Returns:
            Formatted trace data as string
        """
        pass
    
    @abstractmethod
    def export_traces_batch(
        self,
        trace_ids: list[str],
        format: OutputFormat = OutputFormat.DETAILED_JSON,
        output_file: Optional[str] = None
    ) -> str:
        """Export multiple traces in batch
        
        Args:
            trace_ids: List of trace IDs to export
            format: Output format for the export
            output_file: Optional file path to write results
            
        Returns:
            Formatted trace data as string (also written to file if specified)
        """
        pass
    
    @abstractmethod
    def get_performance_summary(
        self, 
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> dict[str, Any]:
        """Get performance summary across traces
        
        Args:
            session_id: Optional session to filter by
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary containing performance summary metrics
        """
        pass
    
    @abstractmethod
    def cleanup_old_traces(self, max_age_days: int = 30) -> int:
        """Clean up old trace data
        
        Args:
            max_age_days: Maximum age of traces to keep
            
        Returns:
            Number of traces cleaned up
        """
        pass