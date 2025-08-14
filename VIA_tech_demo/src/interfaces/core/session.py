"""
Session tracking interfaces

This module defines the contracts for session tracking and metrics collection
to monitor user interactions and system performance.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SessionMetrics:
    """Metrics collected for a user session

    This data class captures comprehensive metrics about a user session
    including performance, cost, and user satisfaction data.

    Attributes:
        session_id: Unique identifier for the session
        user_id: Identifier for the user
        start_time: When the session started
        end_time: When the session ended (None if still active)
        query_count: Number of queries processed
        escalation_count: Number of escalations to human
        total_response_time: Total time spent responding (seconds)
        average_satisfaction: Average user satisfaction rating
        total_tokens_used: Total AI tokens consumed
        total_cost_usd: Total cost in USD
        node_execution_times: Execution times by node type
    """

    session_id: str
    user_id: str
    start_time: datetime
    end_time: datetime | None = None
    query_count: int = 0
    escalation_count: int = 0
    total_response_time: float = 0.0
    average_satisfaction: float = 0.0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    node_execution_times: dict[str, float] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        """Get session duration in seconds"""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def average_response_time(self) -> float:
        """Get average response time per query"""
        return self.total_response_time / max(self.query_count, 1)

    @property
    def escalation_rate(self) -> float:
        """Get escalation rate as percentage"""
        return (self.escalation_count / max(self.query_count, 1)) * 100


class SessionTrackerInterface(ABC):
    """Abstract base class for session tracking

    Session trackers monitor user sessions and collect metrics for:
    - Performance monitoring and optimization
    - Cost tracking and budgeting
    - User satisfaction analysis
    - System capacity planning
    - Quality assurance and debugging

    Implementations should handle:
    - Real-time session monitoring
    - Efficient metrics storage and retrieval
    - Aggregation and reporting capabilities
    - Cleanup of old session data
    """

    @abstractmethod
    def start_session(self, session_id: str, user_id: str) -> SessionMetrics:
        """Start tracking a new session

        Args:
            session_id: Unique identifier for the session
            user_id: Identifier for the user

        Returns:
            SessionMetrics object for the new session
        """
        pass

    @abstractmethod
    def end_session(self, session_id: str) -> SessionMetrics | None:
        """End a session and finalize metrics

        Args:
            session_id: The session to end

        Returns:
            Final SessionMetrics object, or None if session not found
        """
        pass

    @abstractmethod
    def record_query(
        self,
        session_id: str,
        response_time: float,
        escalated: bool = False,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        satisfaction: float | None = None,
    ):
        """Record a query and its associated metrics

        Args:
            session_id: The session this query belongs to
            response_time: Time taken to respond (seconds)
            escalated: Whether this query was escalated to human
            tokens_used: Number of AI tokens consumed
            cost_usd: Cost of processing this query
            satisfaction: User satisfaction rating (0-10)
        """
        pass

    @abstractmethod
    def record_node_execution(
        self, session_id: str, node_name: str, execution_time: float
    ):
        """Record execution time for a specific node

        Args:
            session_id: The session this execution belongs to
            node_name: Name/type of the node that was executed
            execution_time: Time taken to execute (seconds)
        """
        pass

    @abstractmethod
    def get_session_metrics(self, session_id: str) -> SessionMetrics | None:
        """Get metrics for a specific session

        Args:
            session_id: The session to get metrics for

        Returns:
            SessionMetrics object, or None if not found
        """
        pass

    @abstractmethod
    def get_user_sessions(self, user_id: str) -> list[SessionMetrics]:
        """Get all sessions for a specific user

        Args:
            user_id: The user to get sessions for

        Returns:
            List of SessionMetrics objects for the user
        """
        pass

    @abstractmethod
    def get_system_metrics(self) -> dict[str, Any]:
        """Get overall system metrics across all sessions

        Returns:
            Dictionary containing system-wide metrics including:
            - total_sessions: Total number of sessions
            - active_sessions: Number of currently active sessions
            - average_session_duration: Average session length
            - average_queries_per_session: Average queries per session
            - average_escalation_rate: System-wide escalation rate
            - average_response_time: System-wide response time
            - total_tokens_used: Total tokens consumed
            - total_cost_usd: Total system cost
        """
        pass
