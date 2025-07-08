"""
Session tracking for monitoring user sessions and metrics
"""

from datetime import datetime, timedelta
from typing import Any

from ..core.logging import get_logger
from ..interfaces.core.session import SessionMetrics, SessionTrackerInterface


class SessionTracker(SessionTrackerInterface):
    """Track user sessions and collect metrics"""

    def __init__(self):
        self.active_sessions: dict[str, SessionMetrics] = {}
        self.session_history: dict[str, SessionMetrics] = {}
        self.logger = get_logger(__name__)

    def start_session(self, session_id: str, user_id: str) -> SessionMetrics:
        """Start tracking a new session"""
        session = SessionMetrics(
            session_id=session_id, user_id=user_id, start_time=datetime.now()
        )
        self.active_sessions[session_id] = session

        self.logger.info(
            "Session started",
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "start_time": session.start_time.isoformat(),
                "operation": "start_session",
            },
        )
        return session

    def end_session(self, session_id: str) -> SessionMetrics | None:
        """End a session and move to history"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.end_time = datetime.now()

            # Move to history
            self.session_history[session_id] = session
            del self.active_sessions[session_id]

            self.logger.info(
                "Session ended",
                extra={
                    "session_id": session_id,
                    "user_id": session.user_id,
                    "duration_seconds": session.duration_seconds,
                    "query_count": session.query_count,
                    "escalation_count": session.escalation_count,
                    "total_cost_usd": session.total_cost_usd,
                    "operation": "end_session",
                },
            )
            return session
        return None

    def record_query(
        self,
        session_id: str,
        response_time: float,
        escalated: bool = False,
        tokens_used: int = 0,
        cost_usd: float = 0.0,
        satisfaction: float | None = None,
    ):
        """Record a query in the session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.query_count += 1
            session.total_response_time += response_time
            session.total_tokens_used += tokens_used
            session.total_cost_usd += cost_usd

            if escalated:
                session.escalation_count += 1

            if satisfaction is not None:
                # Update running average
                current_total = session.average_satisfaction * (session.query_count - 1)
                session.average_satisfaction = (
                    current_total + satisfaction
                ) / session.query_count

    def record_node_execution(
        self, session_id: str, node_name: str, execution_time: float
    ):
        """Record node execution time"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if node_name not in session.node_execution_times:
                session.node_execution_times[node_name] = []
            session.node_execution_times[node_name].append(execution_time)

    def get_session_metrics(self, session_id: str) -> SessionMetrics | None:
        """Get metrics for a specific session"""
        return self.active_sessions.get(session_id) or self.session_history.get(
            session_id
        )

    def get_user_sessions(self, user_id: str) -> list[SessionMetrics]:
        """Get all sessions for a user"""
        sessions = []

        # Active sessions
        for session in self.active_sessions.values():
            if session.user_id == user_id:
                sessions.append(session)

        # Historical sessions
        for session in self.session_history.values():
            if session.user_id == user_id:
                sessions.append(session)

        return sessions

    def get_recent_sessions(self, hours: int = 24) -> list[SessionMetrics]:
        """Get sessions from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_sessions = []

        # Check active sessions
        for session in self.active_sessions.values():
            if session.start_time >= cutoff_time:
                recent_sessions.append(session)

        # Check historical sessions
        for session in self.session_history.values():
            if session.start_time >= cutoff_time:
                recent_sessions.append(session)

        return recent_sessions

    def get_system_metrics(self) -> dict[str, Any]:
        """Get overall system metrics"""
        all_sessions = list(self.active_sessions.values()) + list(
            self.session_history.values()
        )

        if not all_sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "average_session_duration": 0,
                "average_queries_per_session": 0,
                "average_escalation_rate": 0,
                "average_response_time": 0,
                "total_tokens_used": 0,
                "total_cost_usd": 0,
            }

        total_sessions = len(all_sessions)
        active_sessions = len(self.active_sessions)

        # Calculate averages
        total_duration = sum(s.duration_seconds for s in all_sessions)
        total_queries = sum(s.query_count for s in all_sessions)
        total_escalations = sum(s.escalation_count for s in all_sessions)
        total_response_time = sum(s.total_response_time for s in all_sessions)
        total_tokens = sum(s.total_tokens_used for s in all_sessions)
        total_cost = sum(s.total_cost_usd for s in all_sessions)

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "average_session_duration": total_duration / total_sessions,
            "average_queries_per_session": total_queries / total_sessions,
            "average_escalation_rate": (total_escalations / max(total_queries, 1))
            * 100,
            "average_response_time": total_response_time / max(total_queries, 1),
            "total_tokens_used": total_tokens,
            "total_cost_usd": total_cost,
        }

    def cleanup_old_sessions(self, days: int = 30):
        """Clean up old session history"""
        cutoff_time = datetime.now() - timedelta(days=days)
        old_sessions = []

        for session_id, session in self.session_history.items():
            if session.start_time < cutoff_time:
                old_sessions.append(session_id)

        for session_id in old_sessions:
            del self.session_history[session_id]

        self.logger.info(
            "Cleaned up old sessions",
            extra={
                "sessions_cleaned": len(old_sessions),
                "cutoff_days": days,
                "cutoff_time": cutoff_time.isoformat(),
                "operation": "cleanup_old_sessions",
            },
        )
