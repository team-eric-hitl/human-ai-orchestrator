"""
Tests for the Answer Agent node
"""

from datetime import datetime

import pytest

from src.core.config.agent_config_manager import AgentConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.interfaces.core.state_schema import HybridSystemState
from src.nodes.answer_agent import AnswerAgentNode


class TestAnswerAgentNode:
    """Test suite for AnswerAgentNode"""

    @pytest.fixture
    def config_manager(self):
        """Create a test configuration manager"""
        return AgentConfigManager(config_dir="config")

    @pytest.fixture
    def context_provider(self):
        """Create a test context provider"""
        return SQLiteContextProvider(db_path=":memory:")

    @pytest.fixture
    def answer_agent(self, config_manager, context_provider):
        """Create an AnswerAgentNode instance"""
        return AnswerAgentNode(config_manager, context_provider)

    @pytest.fixture
    def sample_state(self):
        """Create a sample state for testing"""
        return HybridSystemState(
            query_id="test_query_123",
            user_id="test_user",
            session_id="test_session",
            query="How do I reset my password?",
            timestamp=datetime.now(),
            messages=[],
        )

    def test_answer_agent_initialization(self, answer_agent):
        """Test that AnswerAgentNode initializes correctly"""
        assert answer_agent is not None
        assert answer_agent.config_manager is not None
        assert answer_agent.context_provider is not None
        assert answer_agent.agent_config is not None

    def test_generate_response(self, answer_agent):
        """Test response generation"""
        query = "How do I reset my password?"
        context_prompt = ""
        system_prompt = "You are a helpful AI assistant."

        response = answer_agent._generate_response(query, context_prompt, system_prompt)

        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_build_context_prompt_no_context(self, answer_agent, sample_state):
        """Test context prompt building with no previous context"""
        context_prompt = answer_agent._build_context_prompt(sample_state)

        assert context_prompt == ""

    def test_node_execution(self, answer_agent, sample_state):
        """Test the main node execution"""
        result = answer_agent(sample_state)

        assert result is not None
        assert "ai_response" in result
        assert "initial_assessment" in result
        assert "next_action" in result
        assert result["next_action"] == "evaluate"

    def test_context_integration(self, answer_agent, sample_state, context_provider):
        """Test that context is properly integrated"""
        # First, save some context
        from src.core.context_manager import ContextEntry

        context_entry = ContextEntry(
            entry_id="prev_query_1",
            user_id=sample_state["user_id"],
            session_id=sample_state["session_id"],
            timestamp=datetime.now(),
            entry_type="query",
            content="Previous question about account",
            metadata={"query_id": "prev_1"},
        )
        context_provider.save_context_entry(context_entry)

        # Now test context building
        context_prompt = answer_agent._build_context_prompt(sample_state)

        assert "CONVERSATION CONTEXT" in context_prompt
        assert "recent interactions" in context_prompt
