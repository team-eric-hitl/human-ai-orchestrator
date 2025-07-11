"""
Comprehensive tests for session tracking system.
Tests SessionTracker, metrics calculation, and session lifecycle management.
"""

import time
from datetime import datetime, timedelta

import pytest

from src.core.logging.exceptions import ValidationError
from src.core.session_tracker import SessionTracker
from src.interfaces.core.session import SessionMetrics


class TestSessionMetrics:
    """Test suite for SessionMetrics data model"""

    def test_session_metrics_creation(self):
        """Test SessionMetrics creation and initialization"""
        metrics = SessionMetrics(
            session_id="test_session",
            user_id="test_user",
            start_time=datetime.now(),
            query_count=5,
            escalation_count=1,
            total_response_time=10.5,
            total_tokens_used=1000,
            total_cost_usd=0.05,
        )

        assert metrics.session_id == "test_session"
        assert metrics.user_id == "test_user"
        assert metrics.query_count == 5
        assert metrics.escalation_count == 1
        assert metrics.total_response_time == 10.5
        assert metrics.total_tokens_used == 1000
        assert metrics.total_cost_usd == 0.05

    def test_session_metrics_calculations(self):
        """Test SessionMetrics calculated properties"""
        start_time = datetime.now() - timedelta(minutes=30)
        end_time = datetime.now()

        metrics = SessionMetrics(
            session_id="test_session",
            user_id="test_user",
            start_time=start_time,
            end_time=end_time,
            query_count=10,
            escalation_count=3,
            total_response_time=25.0,
            total_tokens_used=2000,
            total_cost_usd=0.10,
        )

        # Test calculated properties (using interface property names)
        assert metrics.escalation_rate == 30.0  # 3/10 * 100 (percentage)
        assert metrics.average_response_time == 2.5  # 25.0/10
        assert abs(metrics.duration_seconds - 1800) < 1  # 30 minutes in seconds, allow small variance

    def test_session_metrics_edge_cases(self):
        """Test SessionMetrics with edge cases"""
        # Session with no queries
        metrics = SessionMetrics(
            session_id="empty_session",
            user_id="test_user",
            start_time=datetime.now(),
            query_count=0,
            escalation_count=0,
            total_response_time=0.0,
            total_tokens_used=0,
            total_cost_usd=0.0,
        )

        assert metrics.escalation_rate == 0.0
        assert metrics.average_response_time == 0.0

    def test_session_metrics_serialization(self):
        """Test SessionMetrics serialization"""
        metrics = SessionMetrics(
            session_id="test_session",
            user_id="test_user",
            start_time=datetime(2023, 1, 1, 12, 0, 0),
            end_time=datetime(2023, 1, 1, 12, 30, 0),
            query_count=5,
            escalation_count=1,
            total_response_time=10.5,
            total_tokens_used=1000,
            total_cost_usd=0.05,
        )

        from dataclasses import asdict
        metrics_dict = asdict(metrics)

        assert metrics_dict["session_id"] == "test_session"
        assert metrics_dict["user_id"] == "test_user"
        assert metrics_dict["query_count"] == 5
        assert metrics_dict["escalation_count"] == 1
        assert metrics_dict["total_response_time"] == 10.5
        assert metrics_dict["total_tokens_used"] == 1000
        assert metrics_dict["total_cost_usd"] == 0.05

    def test_session_metrics_validation(self):
        """Test SessionMetrics validation"""
        # Create metrics with negative values - should work (no validation in dataclass)
        metrics = SessionMetrics(
            session_id="test_session",
            user_id="test_user",
            start_time=datetime.now(),
            query_count=-1,  # Negative value allowed in dataclass
            escalation_count=0,
            total_response_time=0.0,
            total_tokens_used=0,
            total_cost_usd=0.0,
        )
        assert metrics.query_count == -1

        # Create metrics with escalated > total - should work (no validation)
        metrics2 = SessionMetrics(
            session_id="test_session",
            user_id="test_user",
            start_time=datetime.now(),
            query_count=5,
            escalation_count=10,  # More escalated than total (allowed)
            total_response_time=10.0,
            total_tokens_used=1000,
            total_cost_usd=0.05,
        )
        assert metrics2.escalation_count == 10


class TestSessionTracker:
    """Test suite for SessionTracker class"""

    @pytest.fixture
    def session_tracker(self):
        """Create SessionTracker instance"""
        return SessionTracker()

    def test_session_tracker_initialization(self, session_tracker):
        """Test SessionTracker initialization"""
        assert session_tracker.sessions == {}
        assert session_tracker.global_metrics is not None
        assert session_tracker.start_time is not None

    def test_start_session(self, session_tracker):
        """Test starting a new session"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)

        assert session_id in session_tracker.sessions
        session = session_tracker.sessions[session_id]
        assert session.session_id == session_id
        assert session.user_id == user_id
        assert session.start_time is not None
        assert session.total_queries == 0

    def test_start_duplicate_session(self, session_tracker):
        """Test starting a session that already exists"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)

        # Starting again should not create duplicate
        session_tracker.start_session(session_id, user_id)

        assert len(session_tracker.sessions) == 1

    def test_record_query(self, session_tracker):
        """Test recording a query in a session"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)

        # Record a query
        session_tracker.record_query(
            session_id=session_id,
            response_time=1.5,
            token_count=150,
            cost=0.01,
            escalated=False,
        )

        session = session_tracker.sessions[session_id]
        assert session.total_queries == 1
        assert session.escalated_queries == 0
        assert session.total_response_time == 1.5
        assert session.total_tokens == 150
        assert session.total_cost == 0.01

    def test_record_escalated_query(self, session_tracker):
        """Test recording an escalated query"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)

        # Record an escalated query
        session_tracker.record_query(
            session_id=session_id,
            response_time=2.3,
            token_count=200,
            cost=0.02,
            escalated=True,
        )

        session = session_tracker.sessions[session_id]
        assert session.total_queries == 1
        assert session.escalated_queries == 1
        assert session.escalation_rate == 1.0

    def test_record_multiple_queries(self, session_tracker):
        """Test recording multiple queries in a session"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)

        # Record multiple queries
        queries = [
            (1.0, 100, 0.005, False),
            (2.0, 200, 0.01, True),
            (1.5, 150, 0.0075, False),
            (3.0, 300, 0.015, True),
        ]

        for response_time, token_count, cost, escalated in queries:
            session_tracker.record_query(
                session_id=session_id,
                response_time=response_time,
                token_count=token_count,
                cost=cost,
                escalated=escalated,
            )

        session = session_tracker.sessions[session_id]
        assert session.total_queries == 4
        assert session.escalated_queries == 2
        assert session.escalation_rate == 0.5
        assert session.total_response_time == 7.5
        assert session.avg_response_time == 1.875
        assert session.total_tokens == 750
        assert session.total_cost == 0.0375

    def test_record_query_nonexistent_session(self, session_tracker):
        """Test recording query for non-existent session"""
        # Should create session automatically
        session_tracker.record_query(
            session_id="nonexistent_session",
            response_time=1.0,
            token_count=100,
            cost=0.01,
            escalated=False,
        )

        assert "nonexistent_session" in session_tracker.sessions
        session = session_tracker.sessions["nonexistent_session"]
        assert session.total_queries == 1

    def test_end_session(self, session_tracker):
        """Test ending a session"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)

        # Record some queries
        session_tracker.record_query(session_id, 1.0, 100, 0.01, False)
        session_tracker.record_query(session_id, 2.0, 200, 0.02, True)

        # End session
        final_metrics = session_tracker.end_session(session_id)

        assert final_metrics is not None
        assert final_metrics.session_id == session_id
        assert final_metrics.end_time is not None
        assert final_metrics.total_queries == 2
        assert final_metrics.escalated_queries == 1

        # Session should be removed from active sessions
        assert session_id not in session_tracker.sessions

    def test_end_nonexistent_session(self, session_tracker):
        """Test ending a non-existent session"""
        final_metrics = session_tracker.end_session("nonexistent_session")
        assert final_metrics is None

    def test_get_session_metrics(self, session_tracker):
        """Test getting current session metrics"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)
        session_tracker.record_query(session_id, 1.5, 150, 0.01, False)

        metrics = session_tracker.get_session_metrics(session_id)

        assert metrics is not None
        assert metrics.session_id == session_id
        assert metrics.user_id == user_id
        assert metrics.total_queries == 1
        assert metrics.escalated_queries == 0
        assert metrics.total_response_time == 1.5
        assert metrics.total_tokens == 150
        assert metrics.total_cost == 0.01

    def test_get_nonexistent_session_metrics(self, session_tracker):
        """Test getting metrics for non-existent session"""
        metrics = session_tracker.get_session_metrics("nonexistent_session")
        assert metrics is None

    def test_get_global_metrics(self, session_tracker):
        """Test getting global system metrics"""
        # Create multiple sessions
        sessions = [("session1", "user1"), ("session2", "user1"), ("session3", "user2")]

        for session_id, user_id in sessions:
            session_tracker.start_session(session_id, user_id)
            # Record some queries
            session_tracker.record_query(session_id, 1.0, 100, 0.01, False)
            session_tracker.record_query(session_id, 2.0, 200, 0.02, True)

        global_metrics = session_tracker.get_global_metrics()

        assert global_metrics["total_sessions"] == 3
        assert global_metrics["total_queries"] == 6  # 2 queries per session
        assert global_metrics["total_escalated_queries"] == 3  # 1 escalated per session
        assert global_metrics["global_escalation_rate"] == 0.5  # 3/6
        assert global_metrics["total_response_time"] == 9.0  # 3.0 per session
        assert global_metrics["avg_response_time"] == 1.5  # 9.0/6
        assert global_metrics["total_tokens"] == 900  # 300 per session
        assert global_metrics["total_cost"] == 0.09  # 0.03 per session

    def test_get_user_metrics(self, session_tracker):
        """Test getting metrics for specific user"""
        # Create sessions for different users
        session_tracker.start_session("session1", "user1")
        session_tracker.start_session("session2", "user1")
        session_tracker.start_session("session3", "user2")

        # Record queries for user1 sessions
        session_tracker.record_query("session1", 1.0, 100, 0.01, False)
        session_tracker.record_query("session1", 2.0, 200, 0.02, True)
        session_tracker.record_query("session2", 1.5, 150, 0.015, False)

        # Record queries for user2 session
        session_tracker.record_query("session3", 2.5, 250, 0.025, True)

        user1_metrics = session_tracker.get_user_metrics("user1")

        assert user1_metrics["total_sessions"] == 2
        assert user1_metrics["total_queries"] == 3
        assert user1_metrics["total_escalated_queries"] == 1
        assert user1_metrics["escalation_rate"] == 1 / 3
        assert user1_metrics["total_response_time"] == 4.5
        assert user1_metrics["avg_response_time"] == 1.5
        assert user1_metrics["total_tokens"] == 450
        assert user1_metrics["total_cost"] == 0.045

    def test_get_active_sessions(self, session_tracker):
        """Test getting list of active sessions"""
        # Start multiple sessions
        session_tracker.start_session("session1", "user1")
        session_tracker.start_session("session2", "user2")
        session_tracker.start_session("session3", "user1")

        active_sessions = session_tracker.get_active_sessions()

        assert len(active_sessions) == 3
        session_ids = [session.session_id for session in active_sessions]
        assert "session1" in session_ids
        assert "session2" in session_ids
        assert "session3" in session_ids

    def test_get_active_sessions_by_user(self, session_tracker):
        """Test getting active sessions for specific user"""
        session_tracker.start_session("session1", "user1")
        session_tracker.start_session("session2", "user2")
        session_tracker.start_session("session3", "user1")

        user1_sessions = session_tracker.get_active_sessions(user_id="user1")

        assert len(user1_sessions) == 2
        session_ids = [session.session_id for session in user1_sessions]
        assert "session1" in session_ids
        assert "session3" in session_ids
        assert "session2" not in session_ids

    def test_session_timeout_handling(self, session_tracker):
        """Test handling of session timeouts"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)

        # Simulate session timeout
        session = session_tracker.sessions[session_id]
        session.start_time = datetime.now() - timedelta(hours=25)  # 25 hours ago

        # Check for expired sessions
        expired_sessions = session_tracker.get_expired_sessions(timeout_hours=24)

        assert len(expired_sessions) == 1
        assert expired_sessions[0].session_id == session_id

    def test_cleanup_expired_sessions(self, session_tracker):
        """Test cleanup of expired sessions"""
        # Create multiple sessions with different ages
        sessions = [
            ("current_session", "user1", timedelta(hours=1)),
            ("old_session1", "user2", timedelta(hours=25)),
            ("old_session2", "user3", timedelta(hours=48)),
        ]

        for session_id, user_id, age in sessions:
            session_tracker.start_session(session_id, user_id)
            session = session_tracker.sessions[session_id]
            session.start_time = datetime.now() - age

        # Cleanup expired sessions (older than 24 hours)
        cleaned_sessions = session_tracker.cleanup_expired_sessions(timeout_hours=24)

        assert len(cleaned_sessions) == 2
        assert "current_session" in session_tracker.sessions
        assert "old_session1" not in session_tracker.sessions
        assert "old_session2" not in session_tracker.sessions

    def test_session_statistics(self, session_tracker):
        """Test session statistics calculation"""
        # Create sessions with various characteristics
        sessions_data = [
            ("session1", "user1", [(1.0, 100, 0.01, False), (2.0, 200, 0.02, True)]),
            ("session2", "user2", [(1.5, 150, 0.015, False)]),
            (
                "session3",
                "user1",
                [
                    (3.0, 300, 0.03, True),
                    (1.0, 100, 0.01, False),
                    (2.5, 250, 0.025, True),
                ],
            ),
        ]

        for session_id, user_id, queries in sessions_data:
            session_tracker.start_session(session_id, user_id)
            for response_time, token_count, cost, escalated in queries:
                session_tracker.record_query(
                    session_id, response_time, token_count, cost, escalated
                )

        stats = session_tracker.get_session_statistics()

        assert stats["total_sessions"] == 3
        assert stats["total_queries"] == 6
        assert stats["total_escalated_queries"] == 3
        assert stats["unique_users"] == 2
        assert stats["avg_queries_per_session"] == 2.0
        assert stats["avg_session_duration"] > 0
        assert stats["escalation_rate"] == 0.5

    def test_performance_metrics_tracking(self, session_tracker):
        """Test performance metrics tracking"""
        session_id = "test_session"
        user_id = "test_user"

        session_tracker.start_session(session_id, user_id)

        # Record queries with timing
        start_time = time.time()
        session_tracker.record_query(session_id, 1.0, 100, 0.01, False)
        time.sleep(0.1)  # Small delay
        session_tracker.record_query(session_id, 2.0, 200, 0.02, True)
        end_time = time.time()

        metrics = session_tracker.get_session_metrics(session_id)

        assert metrics.total_queries == 2
        assert metrics.total_response_time == 3.0
        assert metrics.avg_response_time == 1.5

        # Session should track wall clock time separately from response time
        assert metrics.session_duration < (end_time - start_time)

    def test_concurrent_session_access(self, session_tracker):
        """Test concurrent access to session tracker"""
        import threading

        results = []

        def create_and_use_session(session_id, user_id):
            session_tracker.start_session(session_id, user_id)
            for i in range(10):
                session_tracker.record_query(
                    session_id=session_id,
                    response_time=1.0,
                    token_count=100,
                    cost=0.01,
                    escalated=i % 3 == 0,
                )
            results.append(session_id)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=create_and_use_session, args=(f"session_{i}", f"user_{i}")
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All sessions should be created
        assert len(results) == 5
        assert len(session_tracker.sessions) == 5

        # Each session should have correct metrics
        for i in range(5):
            session_id = f"session_{i}"
            metrics = session_tracker.get_session_metrics(session_id)
            assert metrics.total_queries == 10
            assert metrics.escalated_queries == 4  # Every 3rd query (0, 3, 6, 9)

    def test_memory_usage_optimization(self, session_tracker):
        """Test memory usage optimization with many sessions"""
        # Create many sessions
        num_sessions = 1000
        for i in range(num_sessions):
            session_id = f"session_{i}"
            user_id = f"user_{i % 100}"  # 100 unique users
            session_tracker.start_session(session_id, user_id)
            session_tracker.record_query(session_id, 1.0, 100, 0.01, False)

        # Should handle large number of sessions
        assert len(session_tracker.sessions) == num_sessions

        global_metrics = session_tracker.get_global_metrics()
        assert global_metrics["total_sessions"] == num_sessions
        assert global_metrics["total_queries"] == num_sessions

        # Cleanup should work efficiently
        cleaned = session_tracker.cleanup_expired_sessions(timeout_hours=0)
        assert len(cleaned) == num_sessions
        assert len(session_tracker.sessions) == 0

    def test_session_data_persistence(self, session_tracker):
        """Test session data persistence across operations"""
        session_id = "persistent_session"
        user_id = "test_user"

        # Start session and record data
        session_tracker.start_session(session_id, user_id)
        session_tracker.record_query(session_id, 1.0, 100, 0.01, False)
        session_tracker.record_query(session_id, 2.0, 200, 0.02, True)

        # Get metrics
        metrics_1 = session_tracker.get_session_metrics(session_id)

        # Record more data
        session_tracker.record_query(session_id, 1.5, 150, 0.015, False)

        # Get updated metrics
        metrics_2 = session_tracker.get_session_metrics(session_id)

        # Should show cumulative data
        assert metrics_2.total_queries == metrics_1.total_queries + 1
        assert metrics_2.total_response_time == metrics_1.total_response_time + 1.5
        assert metrics_2.total_tokens == metrics_1.total_tokens + 150
        assert metrics_2.total_cost == metrics_1.total_cost + 0.015

        # Escalation count should remain the same
        assert metrics_2.escalated_queries == metrics_1.escalated_queries
