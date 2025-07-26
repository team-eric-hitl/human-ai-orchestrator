"""
Unit tests for MockAutomationAgent node
"""

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.core.config import ConfigManager
from src.interfaces.core.state_schema import HybridSystemState
from src.nodes.mock_automation_agent import MockAutomationAgent


class TestMockAutomationAgent:
    """Test suite for MockAutomationAgent"""

    @pytest.fixture
    def mock_config_manager(self):
        """Mock ConfigManager for testing"""
        config_manager = Mock(spec=ConfigManager)
        config_manager.config_dir = "config"

        # Mock agent config
        agent_config = Mock()
        agent_config.get_all_prompts.return_value = {
            "system_templates": {
                "success_response": "Task completed successfully. Reference ID: {reference_id}",
                "failure_response": "Task failed. Error: {error_message}. Reference ID: {reference_id}"
            }
        }
        config_manager.get_agent_config.return_value = agent_config

        return config_manager

    @pytest.fixture
    def mock_context_provider(self):
        """Mock ContextProvider for testing"""
        context_provider = Mock()
        context_provider.store_context.return_value = None
        return context_provider

    @pytest.fixture
    def sample_automation_repertoire(self):
        """Sample automation repertoire for testing"""
        return {
            "automation_tasks": {
                "test_task": {
                    "category": "test_category",
                    "keywords": ["test", "sample"],
                    "success_rate": 0.95,
                    "avg_response_time": 0.5,
                    "response_template": "system_templates.success_response"
                }
            },
            "escalation_triggers": {
                "complexity_keywords": ["frustrated", "manager", "complaint"]
            },
            "mock_data": {
                "policies": {
                    "POL-TEST-001": {
                        "policy_number": "POL-TEST-001",
                        "status": "Active",
                        "premium": 100.00
                    }
                }
            }
        }

    @pytest.fixture
    def automation_agent(self, mock_config_manager, mock_context_provider, sample_automation_repertoire):
        """Create MockAutomationAgent instance for testing"""
        with patch.object(MockAutomationAgent, '_load_automation_repertoire', return_value=sample_automation_repertoire):
            agent = MockAutomationAgent(mock_config_manager, mock_context_provider)
            return agent

    @pytest.fixture
    def sample_state(self):
        """Sample HybridSystemState for testing"""
        return HybridSystemState(
            query_id="test_query_001",
            user_id="test_user",
            session_id="test_session",
            query="test query",
            timestamp=datetime.now(),
            messages=[]
        )

    def test_initialization(self, automation_agent):
        """Test agent initialization"""
        assert automation_agent is not None
        assert automation_agent.logger is not None
        assert automation_agent.automation_repertoire is not None
        assert automation_agent.response_templates is not None

    def test_get_supported_tasks(self, automation_agent):
        """Test getting supported tasks"""
        tasks = automation_agent.get_supported_tasks()
        assert isinstance(tasks, list)
        assert "test_task" in tasks

    def test_get_task_categories(self, automation_agent):
        """Test getting task categories"""
        categories = automation_agent.get_task_categories()
        assert isinstance(categories, list)
        assert "test_category" in categories

    def test_detect_automation_intent_success(self, automation_agent):
        """Test successful intent detection"""
        query = "This is a test query"
        result = automation_agent._detect_automation_intent(query)

        assert result is not None
        task_name, task_config = result
        assert task_name == "test_task"
        assert task_config["category"] == "test_category"

    def test_detect_automation_intent_no_match(self, automation_agent):
        """Test intent detection with no match"""
        query = "This query has no matching keywords"
        result = automation_agent._detect_automation_intent(query)

        assert result is None

    def test_check_escalation_triggers_true(self, automation_agent):
        """Test escalation trigger detection - should escalate"""
        query = "I'm frustrated with this service"
        should_escalate = automation_agent._check_escalation_triggers(query)

        assert should_escalate is True

    def test_check_escalation_triggers_false(self, automation_agent):
        """Test escalation trigger detection - should not escalate"""
        query = "What is my policy status?"
        should_escalate = automation_agent._check_escalation_triggers(query)

        assert should_escalate is False

    def test_simulate_processing_time(self, automation_agent):
        """Test processing time simulation"""
        task_config = {"avg_response_time": 0.5}
        processing_time = automation_agent._simulate_processing_time(task_config)

        assert isinstance(processing_time, float)
        assert processing_time > 0
        # Should be roughly around 0.5 with some variance
        assert 0.1 <= processing_time <= 1.0

    def test_simulate_success_rate_high(self, automation_agent):
        """Test success rate simulation with high success rate"""
        task_config = {"success_rate": 1.0}  # 100% success

        # Test multiple times to ensure consistency
        successes = sum(automation_agent._simulate_success_rate(task_config) for _ in range(10))
        assert successes == 10  # Should always succeed

    def test_simulate_success_rate_low(self, automation_agent):
        """Test success rate simulation with low success rate"""
        task_config = {"success_rate": 0.0}  # 0% success

        # Test multiple times to ensure consistency
        successes = sum(automation_agent._simulate_success_rate(task_config) for _ in range(10))
        assert successes == 0  # Should always fail

    def test_format_response_success(self, automation_agent):
        """Test response formatting with valid template"""
        template_path = "system_templates.success_response"
        data = {"test_field": "test_value"}
        reference_id = "TEST-123"
        processing_time = 0.5

        response = automation_agent._format_response(
            template_path, data, reference_id, processing_time
        )

        assert reference_id in response
        # The processing time gets formatted as "0.5" in the template
        assert "Task completed successfully" in response

    def test_format_response_invalid_template(self, automation_agent):
        """Test response formatting with invalid template"""
        template_path = "nonexistent.template"
        data = {}
        reference_id = "TEST-123"
        processing_time = 0.5

        response = automation_agent._format_response(
            template_path, data, reference_id, processing_time
        )

        # Should return fallback response
        assert reference_id in response
        assert "Automated response completed" in response

    def test_automation_success_flow(self, automation_agent, sample_state):
        """Test successful automation processing flow"""
        sample_state["query"] = "This is a test query"

        result_state = automation_agent(sample_state)

        # Should have automation response
        assert result_state.get("automation_response") is not None
        assert result_state.get("requires_escalation") is False

        metadata = result_state.get("automation_metadata", {})
        assert metadata.get("automation_result") == "success"
        assert metadata.get("task_name") == "test_task"

    def test_escalation_trigger_flow(self, automation_agent, sample_state):
        """Test escalation trigger flow"""
        sample_state["query"] = "I'm frustrated and want to speak to a manager"

        result_state = automation_agent(sample_state)

        # Should escalate
        assert result_state.get("automation_response") is None
        assert result_state.get("requires_escalation") is True

        metadata = result_state.get("automation_metadata", {})
        assert metadata.get("automation_result") == "escalated"
        assert metadata.get("escalation_reason") == "trigger_keyword_detected"

    def test_no_match_flow(self, automation_agent, sample_state):
        """Test no automation match flow"""
        sample_state["query"] = "What's the weather like today?"

        result_state = automation_agent(sample_state)

        # Should escalate due to no match
        assert result_state.get("automation_response") is None
        assert result_state.get("requires_escalation") is True

        metadata = result_state.get("automation_metadata", {})
        assert metadata.get("automation_result") == "no_match"
        assert metadata.get("escalation_reason") == "no_automation_task_matched"

    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_processing_includes_timing(self, mock_sleep, automation_agent, sample_state):
        """Test that processing includes timing metadata"""
        sample_state["query"] = "This is a test query"

        start_time = time.time()
        result_state = automation_agent(sample_state)
        end_time = time.time()

        metadata = result_state.get("automation_metadata", {})
        processing_time = metadata.get("processing_time")

        assert processing_time is not None
        assert isinstance(processing_time, float)
        # Processing time should be reasonable (allowing for test overhead)
        assert processing_time <= (end_time - start_time) + 1.0

    def test_context_saving_called(self, automation_agent, sample_state, mock_context_provider):
        """Test that context saving is attempted"""
        sample_state["query"] = "This is a test query"

        automation_agent(sample_state)

        # Should attempt to save context (even if it fails in this mock)
        # We verify this by checking the mock was called
        assert mock_context_provider.store_context.called
