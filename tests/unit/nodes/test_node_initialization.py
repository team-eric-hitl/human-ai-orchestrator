"""
Simple tests for node initialization and basic functionality.
Tests only the public interface without relying on private methods.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import uuid

from src.core.config.agent_config_manager import AgentConfigManager


class TestNodeInitialization:
    """Test basic node initialization and public interface"""

    @pytest.fixture
    def mock_config_manager(self):
        """Create mock configuration manager"""
        config_manager = Mock()
        agent_config = Mock()
        agent_config.get_preferred_model.return_value = "gpt-3.5-turbo"
        agent_config.settings = {}
        agent_config.prompts = {}
        config_manager.get_agent_config.return_value = agent_config
        config_manager.config_dir = "/mock/config"
        return config_manager

    @pytest.fixture
    def mock_context_provider(self):
        """Create mock context provider"""
        context_provider = Mock()
        return context_provider

    @pytest.fixture
    def sample_state(self):
        """Create sample state for testing"""
        return {
            'query': 'Test query',
            'user_id': str(uuid.uuid4()),
            'session_id': str(uuid.uuid4()),
            'query_id': str(uuid.uuid4()),
            'timestamp': datetime.now(),
            'messages': []
        }

    def test_chatbot_agent_initialization(self, mock_config_manager, mock_context_provider):
        """Test ChatbotAgentNode can be initialized"""
        with patch('src.nodes.chatbot_agent.LLMProviderFactory'):
            from src.nodes.chatbot_agent import ChatbotAgentNode
            
            agent = ChatbotAgentNode(mock_config_manager, mock_context_provider)
            assert agent is not None
            assert agent.config_manager == mock_config_manager
            assert agent.context_provider == mock_context_provider

    def test_frustration_agent_initialization(self, mock_config_manager, mock_context_provider):
        """Test FrustrationAgentNode can be initialized"""
        with patch('src.nodes.frustration_agent.LLMProviderFactory'):
            from src.nodes.frustration_agent import FrustrationAgentNode
            
            agent = FrustrationAgentNode(mock_config_manager, mock_context_provider)
            assert agent is not None
            assert agent.config_manager == mock_config_manager
            assert agent.context_provider == mock_context_provider

    def test_quality_agent_initialization(self, mock_config_manager, mock_context_provider):
        """Test QualityAgentNode can be initialized"""
        with patch('src.nodes.quality_agent.LLMProviderFactory'):
            from src.nodes.quality_agent import QualityAgentNode
            
            agent = QualityAgentNode(mock_config_manager, mock_context_provider)
            assert agent is not None
            assert agent.config_manager == mock_config_manager
            assert agent.context_provider == mock_context_provider

    def test_context_manager_agent_initialization(self, mock_config_manager, mock_context_provider):
        """Test ContextManagerAgentNode can be initialized"""
        with patch('src.nodes.context_manager_agent.LLMProviderFactory'):
            from src.nodes.context_manager_agent import ContextManagerAgentNode
            
            agent = ContextManagerAgentNode(mock_config_manager, mock_context_provider)
            assert agent is not None
            assert agent.config_manager == mock_config_manager
            assert agent.context_provider == mock_context_provider

    def test_human_routing_agent_initialization(self, mock_config_manager, mock_context_provider):
        """Test HumanRoutingAgentNode can be initialized"""
        with patch('src.nodes.human_routing_agent.LLMProviderFactory'):
            with patch('src.nodes.human_routing_agent.SyncLLMRoutingAgent'):
                with patch('src.nodes.human_routing_agent.AgentFieldMapper'):
                    from src.nodes.human_routing_agent import HumanRoutingAgentNode
                    
                    agent = HumanRoutingAgentNode(mock_config_manager, mock_context_provider)
                    assert agent is not None
                    assert agent.config_manager == mock_config_manager
                    assert agent.context_provider == mock_context_provider

    def test_node_interfaces_exist(self):
        """Test that all nodes implement the expected interface"""
        from src.nodes.chatbot_agent import ChatbotAgentNode
        from src.nodes.frustration_agent import FrustrationAgentNode
        from src.nodes.quality_agent import QualityAgentNode
        from src.nodes.context_manager_agent import ContextManagerAgentNode
        from src.nodes.human_routing_agent import HumanRoutingAgentNode
        
        # All nodes should have a __call__ method
        assert callable(ChatbotAgentNode.__call__)
        assert callable(FrustrationAgentNode.__call__)
        assert callable(QualityAgentNode.__call__)
        assert callable(ContextManagerAgentNode.__call__)
        assert callable(HumanRoutingAgentNode.__call__)

    def test_all_agents_can_be_imported(self):
        """Test that all agent nodes can be imported without errors"""
        from src.nodes.chatbot_agent import ChatbotAgentNode
        from src.nodes.frustration_agent import FrustrationAgentNode
        from src.nodes.quality_agent import QualityAgentNode
        from src.nodes.context_manager_agent import ContextManagerAgentNode
        from src.nodes.human_routing_agent import HumanRoutingAgentNode
        
        # All imports successful
        assert True