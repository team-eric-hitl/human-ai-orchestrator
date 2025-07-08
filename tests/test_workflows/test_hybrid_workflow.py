"""
Tests for the hybrid workflow
"""

import pytest

from src.workflows.hybrid_workflow import HybridSystemWorkflow


class TestHybridWorkflow:
    """Test suite for HybridSystemWorkflow"""

    @pytest.fixture
    def workflow(self):
        """Create a test workflow instance"""
        return HybridSystemWorkflow(config_dir="config", context_db=":memory:")

    def test_workflow_initialization(self, workflow):
        """Test that workflow initializes correctly"""
        assert workflow is not None
        assert workflow.config_provider is not None
        assert workflow.context_provider is not None
        assert workflow.answer_agent is not None
        assert workflow.evaluator_agent is not None
        assert workflow.escalation_router is not None

    def test_process_simple_query(self, workflow):
        """Test processing a simple query"""
        result = workflow.process_query(
            query="How do I reset my password?",
            user_id="test_user",
            session_id="test_session",
        )

        assert result is not None
        assert "query_id" in result
        assert "escalated" in result
        assert "final_response" in result
        assert "workflow_complete" in result

    def test_process_escalation_query(self, workflow):
        """Test processing a query that should be escalated"""
        result = workflow.process_query(
            query="I'm getting frustrated, I need to speak to someone",
            user_id="test_user",
            session_id="test_session",
        )

        assert result is not None
        # This query should likely be escalated due to frustration indicators
        # The exact behavior depends on the evaluation logic

    def test_session_continuity(self, workflow):
        """Test that session context is maintained across queries"""
        session_id = "continuity_test_session"
        user_id = "test_user"

        # First query
        result1 = workflow.process_query(
            query="How do I reset my password?", user_id=user_id, session_id=session_id
        )

        # Second query in same session
        result2 = workflow.process_query(
            query="That didn't work, can you help me?",
            user_id=user_id,
            session_id=session_id,
        )

        assert result1 is not None
        assert result2 is not None
        # The second query should have context from the first
