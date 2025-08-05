"""
Streamlit Demo App for HITL System
Demonstrates ChatbotAgent, FrustrationAgent, and QualityAgent working together
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, Any
import uuid
from dotenv import load_dotenv
import html

import streamlit as st

# Load environment variables from .env file
load_dotenv()

# Configure page
st.set_page_config(
    page_title="HITL System Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Import system components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config.agent_config_manager import AgentConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.core.logging import get_logger, configure_logging
from src.core.agent_field_mapper import AgentFieldMapper
from src.data.human_agents_repository import SQLiteHumanAgentRepository
from src.nodes.chatbot_agent import ChatbotAgentNode
from src.nodes.frustration_agent import FrustrationAgentNode
from src.nodes.quality_agent import QualityAgentNode
from src.nodes.context_manager_agent import ContextManagerAgentNode
from src.nodes.human_routing_agent import HumanRoutingAgentNode
from src.interfaces.core.state_schema import HybridSystemState

# Initialize logging with a basic config
logging_config = {
    "level": "INFO",
    "console": {"enabled": True, "level": "INFO"},
    "file": {"enabled": False}  # Disable file logging for demo
}
configure_logging(logging_config)
logger = get_logger(__name__)

# Initialize field mapper for consistent agent data handling
field_mapper = AgentFieldMapper()

# Initialize human agents repository
human_agents_repo = SQLiteHumanAgentRepository()

def safe_html_escape(text: Any) -> str:
    """Safely escape HTML characters in text"""
    if text is None:
        return ""
    return html.escape(str(text))

def ensure_agent_fields(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure agent data has all expected fields for UI display"""
    if not agent_data:
        return {}
    
    try:
        # Use field mapper to ensure consistent format
        mapped_agent = field_mapper.map_database_to_agent(agent_data, include_computed=True)
        
        # Ensure critical UI fields are present with safe defaults
        ui_defaults = {
            "shift_start": "09:00",
            "shift_end": "17:00",
            "specializations": [],
            "languages": ["english"],
            "experience_level": 1,
            "status": "available"
        }
        
        for field, default_value in ui_defaults.items():
            if field not in mapped_agent or mapped_agent[field] is None:
                mapped_agent[field] = default_value
        
        return mapped_agent
        
    except Exception as e:
        logger.warning(f"Failed to map agent fields: {e}, using fallback")
        # Return fallback with required fields
        return {
            "id": agent_data.get("id", "unknown"),
            "name": agent_data.get("name", "Unknown Agent"),
            "email": agent_data.get("email", "unknown@company.com"),
            "shift_start": "09:00",
            "shift_end": "17:00",
            "specializations": [],
            "languages": ["english"],
            "experience_level": 1,
            "status": "available"
        }

# Custom CSS for better layout
st.markdown("""
<style>
    .stApp > div > div > div > div > section > div {padding-top: 1rem;}
    .log-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
        height: 300px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 12px;
    }
    .analysis-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #ddd;
        height: 300px;
        overflow-y: auto;
    }
    .chat-container {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
        height: 400px;
        overflow-y: auto;
    }
    .chat-message {
        margin-bottom: 15px;
        padding: 10px;
        border-radius: 5px;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
    .context-info {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 8px;
        margin-top: 5px;
        font-size: 11px;
        color: #666;
        border-radius: 3px;
    }
    .human-roster-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #ddd;
        height: 300px;
        overflow-y: auto;
    }
    .human-profile-container {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #ddd;
        height: 300px;
        overflow-y: auto;
    }
    .human-context-container {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #ddd;
        height: 300px;
        overflow-y: auto;
    }
    .agent-card {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .agent-card:hover {
        background-color: #e3f2fd;
    }
    .agent-card.selected {
        background-color: #c8e6c9;
        border-color: #4caf50;
    }
    .agent-status {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 10px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-available { background-color: #c8e6c9; color: #2e7d32; }
    .status-busy { background-color: #ffcdd2; color: #c62828; }
    .status-break { background-color: #fff3e0; color: #f57c00; }
    .status-offline { background-color: #e0e0e0; color: #424242; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="Initializing HITL system...")
def initialize_system():
    """Initialize the HITL system components"""
    try:
        # Initialize configuration
        config_dir = os.path.join(os.path.dirname(__file__), 'config')
        config_manager = AgentConfigManager(config_dir)
        
        # Override model selections for demo
        # Chatbot agent - use anthropic general budget (claude-3-5-haiku-20241022)
        try:
            chatbot_config = config_manager.get_agent_config('chatbot_agent')
            if hasattr(chatbot_config, 'models') and isinstance(chatbot_config.models, dict):
                chatbot_config.models['primary_model'] = 'anthropic_general_budget'
            
            # Frustration agent - use anthropic general standard (claude-3-5-sonnet-20241022)
            frustration_config = config_manager.get_agent_config('frustration_agent')
            if hasattr(frustration_config, 'models') and isinstance(frustration_config.models, dict):
                frustration_config.models['primary_model'] = 'anthropic_general_standard'
            
            # Quality agent - use anthropic general standard (claude-3-5-sonnet-20241022)
            quality_config = config_manager.get_agent_config('quality_agent')
            if hasattr(quality_config, 'models') and isinstance(quality_config.models, dict):
                quality_config.models['primary_model'] = 'anthropic_general_standard'
        except Exception as e:
            logger.warning(f"Failed to override model configurations: {e}")
            # Continue with default configurations
        
        # Initialize context manager  
        context_manager = SQLiteContextProvider(config_manager=config_manager)
        
        # Initialize agents
        context_manager_agent = ContextManagerAgentNode(config_manager, context_manager)
        chatbot_agent = ChatbotAgentNode(config_manager, context_manager)
        frustration_agent = FrustrationAgentNode(config_manager, context_manager)
        quality_agent = QualityAgentNode(config_manager, context_manager)
        human_routing_agent = HumanRoutingAgentNode(config_manager, context_manager)
        
        return {
            'config_manager': config_manager,
            'context_manager': context_manager,
            'context_manager_agent': context_manager_agent,
            'chatbot_agent': chatbot_agent,
            'frustration_agent': frustration_agent,
            'quality_agent': quality_agent,
            'human_routing_agent': human_routing_agent,
            'initialized': True
        }
    except Exception as e:
        st.error(f"Failed to initialize system: {str(e)}")
        return {'initialized': False, 'error': str(e)}

def add_log_entry(message: str, level: str = "INFO"):
    """Add entry to the logging display"""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    st.session_state.logs.append(log_entry)
    
    # Keep only last 50 log entries
    if len(st.session_state.logs) > 50:
        st.session_state.logs = st.session_state.logs[-50:]

def fetch_human_agents_from_db():
    """Fetch all human agents from the database using repository abstraction"""
    try:
        # Use async repository in sync context by running in event loop
        import asyncio
        
        async def get_agents():
            return await human_agents_repo.get_all()
        
        # Get agents using repository
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        agents_objects = loop.run_until_complete(get_agents())
        
        # Convert agent objects to dictionaries for UI display
        agents = []
        for agent in agents_objects:
            # Convert agent object to dictionary format expected by UI
            agent_dict = {
                'id': agent.id,
                'name': agent.name,
                'email': agent.email,
                'status': agent.status.value if hasattr(agent.status, 'value') else str(agent.status),
                'specializations': [s.value if hasattr(s, 'value') else str(s) for s in agent.specializations],
                'max_concurrent_conversations': agent.max_concurrent_conversations,
                'experience_level': agent.experience_level,
                'languages': agent.languages,
                'shift_start': agent.shift_start,
                'shift_end': agent.shift_end,
                'metadata': agent.metadata
            }
            
            # Use field mapper to get properly formatted agent
            mapped_agent = ensure_agent_fields(agent_dict)
            agents.append(mapped_agent)
        
        return agents
    except Exception as e:
        st.error(f"Failed to fetch human agents: {e}")
        return []

def get_current_workload(agent_id: str) -> int:
    """Get current workload for an agent using repository abstraction"""
    try:
        import asyncio
        
        async def get_agent():
            return await human_agents_repo.get_by_id(agent_id)
        
        # Get agent using repository
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        agent = loop.run_until_complete(get_agent())
        
        if agent and agent.workload:
            return agent.workload.active_conversations
        return 0
    except Exception:
        return 0

def update_human_roster_display(placeholder):
    """Update the human roster display"""
    agents = fetch_human_agents_from_db()
    
    # Debug info
    add_log_entry(f"Roster update: Found {len(agents)} agents")
    if agents:
        add_log_entry(f"First agent: {agents[0]['id']} - {agents[0]['name']}")
    
    roster_html = ""
    for i, agent in enumerate(agents):
        current_workload = get_current_workload(agent['id'])
        max_concurrent = agent.get('max_concurrent_conversations', agent.get('max_concurrent', 1))
        workload_ratio = current_workload / max_concurrent if max_concurrent > 0 else 0
        
        # Status styling
        status_class = f"status-{agent['status']}"
        
        # Selected styling
        selected_class = "selected" if st.session_state.get('selected_agent_id') == agent['id'] else ""
        
        agent_card_html = f'''
        <div class="agent-card {selected_class}" data-agent-id="{agent['id']}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong>{safe_html_escape(agent['name'])}</strong>
                <span class="agent-status {status_class}">{safe_html_escape(agent['status'])}</span>
            </div>
            <div style="font-size: 12px; color: #666; margin-top: 5px;">
                {safe_html_escape(', '.join(agent.get('specializations', [])))}
            </div>
            <div style="font-size: 11px; color: #888; margin-top: 3px;">
                Workload: {current_workload}/{max_concurrent} 
                ({workload_ratio:.0%} capacity)
            </div>
            <div style="font-size: 11px; color: #888;">
                Experience: Level {safe_html_escape(agent.get('experience_level', 1))} | 
                Languages: {safe_html_escape(', '.join(agent.get('languages', [])))}
            </div>
        </div>'''
        
        roster_html += agent_card_html
        
        # Debug first agent
        if i == 0:
            add_log_entry(f"First agent HTML length: {len(agent_card_html)}")
    
    if not roster_html:
        roster_html = '<div style="text-align: center; color: #666; margin-top: 20px;">No agents available</div>'
    
    final_html = f'<div class="human-roster-container">{roster_html}</div>'
    add_log_entry(f"Total roster HTML length: {len(final_html)}")
    
    placeholder.markdown(final_html, unsafe_allow_html=True)

def update_human_profile_display(placeholder):
    """Update the human profile display for selected agent"""
    selected_agent_id = st.session_state.get('selected_agent_id')
    selected_agent = st.session_state.get('selected_agent')
    
    if not selected_agent:
        profile_html = '<div style="text-align: center; color: #666; margin-top: 20px;">Select an agent to view profile</div>'
    else:
        metadata = selected_agent.get('metadata', {})
        profile_html = f'''
        <div style="text-align: center; margin-bottom: 15px;">
            <h4 style="margin: 0; color: #2196f3;">{safe_html_escape(selected_agent['name'])}</h4>
            <p style="margin: 5px 0; color: #666;">{safe_html_escape(selected_agent['email'])}</p>
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Department:</strong> {safe_html_escape(metadata.get('department', 'N/A'))}<br>
            <strong>Team:</strong> {safe_html_escape(metadata.get('team', 'N/A'))}<br>
            <strong>Experience Level:</strong> {safe_html_escape(selected_agent['experience_level'])}/5<br>
            <strong>Specializations:</strong> {safe_html_escape(', '.join(selected_agent.get('specializations', [])))}
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Languages:</strong> {safe_html_escape(metadata.get('languages_spoken', ', '.join(selected_agent.get('languages', []))))}<br>
            <strong>Shift:</strong> {safe_html_escape(selected_agent.get('shift_start', 'N/A'))} - {safe_html_escape(selected_agent.get('shift_end', 'N/A'))}
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Certifications:</strong><br>
            {safe_html_escape(', '.join(metadata.get('certifications', [])) if metadata.get('certifications') else 'None listed')}
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Specialties:</strong><br>
            <small>{safe_html_escape(metadata.get('specialties', 'General customer service'))}</small>
        </div>
        
        <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd;">
            <strong>Current Status:</strong> 
            <span class="agent-status status-{selected_agent.get('status', 'unknown')}">{safe_html_escape(selected_agent.get('status', 'unknown'))}</span>
        </div>'''
    
    placeholder.markdown(f'<div class="human-profile-container">{profile_html}</div>', unsafe_allow_html=True)

def update_human_context_display(placeholder):
    """Update the human context display with information for the agent"""
    context_html = ""
    
    if not st.session_state.get('routing_decision'):
        context_html = '<div style="text-align: center; color: #666; margin-top: 20px;">No escalation context available</div>'
    else:
        routing_decision = st.session_state.routing_decision
        current_query = st.session_state.get('current_query', 'No current query')
        conversation_history = st.session_state.get('conversation_history', [])
        
        # Build conversation summary for human agent
        conversation_summary = ""
        for i, msg in enumerate(conversation_history[-5:]):  # Last 5 messages
            role = "Customer" if msg['role'] == 'user' else "AI Assistant"
            content_preview = safe_html_escape(msg['content'][:100])
            if len(msg['content']) > 100:
                content_preview += '...'
            conversation_summary += f"<strong>{safe_html_escape(role)}:</strong> {content_preview}<br><br>"
        
        routing_requirements = routing_decision.get('routing_requirements', {})
        required_skills = routing_requirements.get('required_skills', ['general'])
        
        context_html = f'''
        <div style="margin-bottom: 15px;">
            <h4 style="color: #f57c00; margin: 0 0 10px 0;">🎯 Escalation Summary</h4>
            <strong>Reason:</strong> {safe_html_escape(routing_requirements.get('escalation_type', 'general_escalation'))}<br>
            <strong>Priority:</strong> {safe_html_escape(routing_requirements.get('priority', 'high'))}<br>
            <strong>Complexity:</strong> {safe_html_escape(routing_requirements.get('complexity', 'low'))}<br>
            <strong>Est. Resolution:</strong> {safe_html_escape(routing_decision.get('estimated_resolution_time', 15))} minutes
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #2196f3; margin: 0 0 10px 0;">💬 Current Issue</h4>
            <div style="background: #f0f8ff; padding: 10px; border-radius: 5px; font-size: 13px;">
                {safe_html_escape(current_query)}
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #4caf50; margin: 0 0 10px 0;">📋 Recent Conversation</h4>
            <div style="max-height: 120px; overflow-y: auto; font-size: 12px;">
                {conversation_summary if conversation_summary else "No conversation history"}
            </div>
        </div>
        
        <div style="margin-bottom: 15px;">
            <h4 style="color: #9c27b0; margin: 0 0 10px 0;">🔍 Analysis Results</h4>
            <strong>Frustration Level:</strong> {safe_html_escape(st.session_state.get('current_frustration_analysis', {}).get('overall_level', 'critical'))}<br>
            <strong>Quality Score:</strong> {safe_html_escape(st.session_state.get('current_quality_analysis', {}).get('overall_score', '9.0'))}<br>
            <strong>Match Score:</strong> {routing_decision.get('agent_match_score', 100.0):.1f}%
        </div>
        
        <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd;">
            <strong>🎯 Recommended Actions:</strong><br>
            <ul style="margin: 5px 0; padding-left: 20px; font-size: 12px;">
                <li>Review customer's escalation history</li>
                <li>Focus on {safe_html_escape(', '.join(required_skills))}</li>
                <li>Expected resolution in {safe_html_escape(routing_decision.get('estimated_resolution_time', 15))} minutes</li>
            </ul>
        </div>'''
    
    placeholder.markdown(f'<div class="human-context-container">{context_html}</div>', unsafe_allow_html=True)

def check_escalation_conditions(frustration_analysis: Dict[str, Any], quality_analysis: Dict[str, Any]) -> bool:
    """Check if conditions are met for escalating to human agent"""
    
    # High frustration levels trigger escalation
    frustration_level = frustration_analysis.get('overall_level', 'low')
    if frustration_level in ['high', 'critical']:
        return True
    
    # Low quality scores trigger escalation
    quality_score = quality_analysis.get('overall_score', 7.0)
    if quality_score < 5.0:
        return True
    
    # Quality agent decision to escalate
    quality_decision = quality_analysis.get('decision', 'approve')
    if quality_decision == 'escalate':
        return True
    
    # Moderate frustration + adjusted response triggers escalation
    if frustration_level == 'moderate' and quality_analysis.get('adjusted_response'):
        return True
    
    return False

def create_state(query: str, user_id: str, session_id: str) -> HybridSystemState:
    """Create a state object for the agents"""
    return {
        'query': query,
        'user_id': user_id,
        'session_id': session_id,
        'query_id': str(uuid.uuid4()),
        'timestamp': datetime.now(),
        'messages': st.session_state.get('conversation_history', []),
        'next_action': 'process_query'
    }

def display_analysis_results(title: str, analysis: Dict[str, Any], container):
    """Display analysis results in a formatted way"""
    with container:
        st.markdown(f"### {title}")
        
        if not analysis:
            analysis_html = '<div style="text-align: center; color: #666; margin-top: 20px;">No analysis available</div>'
            st.markdown(f'<div class="analysis-container">{analysis_html}</div>', unsafe_allow_html=True)
            return
            
        # Build HTML content for scrollable container
        analysis_html = ""
        
        # Extract key metrics
        if 'overall_score' in analysis:
            score = analysis['overall_score']
            analysis_html += f'<div style="margin-bottom: 15px;"><strong>Score:</strong> {score:.1f}/10.0</div>'
        elif 'current_query_score' in analysis:
            score = analysis['current_query_score'] 
            analysis_html += f'<div style="margin-bottom: 15px;"><strong>Score:</strong> {score:.1f}/10.0</div>'
            
        if 'confidence' in analysis:
            confidence = analysis['confidence']
            analysis_html += f'<div style="margin-bottom: 15px;"><strong>Confidence:</strong> {confidence:.0%}</div>'
            
        # Show reasoning/analysis
        if 'reasoning' in analysis:
            analysis_html += f'<div style="margin-bottom: 15px;"><strong>Reasoning:</strong><br>{analysis["reasoning"]}</div>'
        elif 'llm_analysis' in analysis and analysis['llm_analysis']:
            analysis_html += f'<div style="margin-bottom: 15px;"><strong>Analysis:</strong><br>{analysis["llm_analysis"]}</div>'
            
        # Show key details
        for key, value in analysis.items():
            if key not in ['reasoning', 'llm_analysis', 'overall_score', 'current_query_score', 'confidence']:
                if isinstance(value, (str, int, float, bool)):
                    analysis_html += f'<div style="margin-bottom: 10px;"><strong>{key.replace("_", " ").title()}:</strong> {value}</div>'
        
        st.markdown(f'<div class="analysis-container">{analysis_html}</div>', unsafe_allow_html=True)

def update_chat_display(placeholder):
    """Update the chat display in real-time"""
    chat_messages_html = ""
    for i, msg in enumerate(st.session_state.conversation_history):
        if msg['role'] == 'user':
            chat_messages_html += f'<div class="chat-message user-message"><strong>You:</strong> {msg["content"]}</div>'
        else:
            chat_messages_html += f'<div class="chat-message bot-message"><strong>Assistant:</strong> {msg["content"]}'
            
            # Add context information if available for this message
            if 'context' in msg and msg['context']:
                context_text = msg['context'][:200] + '...' if len(msg['context']) > 200 else msg['context']
                chat_messages_html += f'<div class="context-info"><strong>Context:</strong> {context_text}</div>'
            
            chat_messages_html += '</div>'
    
    if not chat_messages_html:
        chat_messages_html = '<div style="text-align: center; color: #666; margin-top: 20px;">No messages yet. Start a conversation!</div>'
    
    placeholder.markdown(f'<div class="chat-container">{chat_messages_html}</div>', unsafe_allow_html=True)

def update_logs_display(placeholder):
    """Update the logs display in real-time"""
    logs_text = "\n".join(st.session_state.logs[-20:])  # Show last 20 logs
    placeholder.markdown(f'<div class="log-container">{logs_text}</div>', unsafe_allow_html=True)

def update_frustration_display(placeholder):
    """Update the frustration analysis display in real-time"""
    with placeholder.container():
        
        analysis = st.session_state.current_frustration_analysis
        if not analysis:
            analysis_html = '<div style="text-align: center; color: #666; margin-top: 20px;">No analysis available</div>'
            st.markdown(f'<div class="analysis-container">{analysis_html}</div>', unsafe_allow_html=True)
            return
            
        # Build HTML content for scrollable container
        analysis_html = ""
        
        # Handle loading state
        if analysis.get('status') == 'Analyzing...':
            analysis_html = '<div style="text-align: center; color: #2196f3; margin-top: 20px;">🔍 Analyzing frustration level...</div>'
        else:
            # Extract key metrics
            if 'overall_score' in analysis:
                score = analysis['overall_score']
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Score:</strong> {score:.1f}/10.0</div>'
            elif 'current_query_score' in analysis:
                score = analysis['current_query_score'] 
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Score:</strong> {score:.1f}/10.0</div>'
                
            if 'confidence' in analysis:
                confidence = analysis['confidence']
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Confidence:</strong> {confidence:.0%}</div>'
                
            # Show reasoning/analysis
            if 'reasoning' in analysis:
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Reasoning:</strong><br>{analysis["reasoning"]}</div>'
            elif 'llm_analysis' in analysis and analysis['llm_analysis']:
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Analysis:</strong><br>{analysis["llm_analysis"]}</div>'
                
            # Show key details
            for key, value in analysis.items():
                if key not in ['reasoning', 'llm_analysis', 'overall_score', 'current_query_score', 'confidence', 'status']:
                    if isinstance(value, (str, int, float, bool)):
                        analysis_html += f'<div style="margin-bottom: 10px;"><strong>{key.replace("_", " ").title()}:</strong> {value}</div>'
                        
            # Add context information if available
            if hasattr(st.session_state, 'current_context_for_frustration') and st.session_state.current_context_for_frustration:
                context_text = st.session_state.current_context_for_frustration
                analysis_html += f'<div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd;"><strong>Context:</strong><br><small>{context_text}</small></div>'
        
        st.markdown(f'<div class="analysis-container">{analysis_html}</div>', unsafe_allow_html=True)

def update_quality_display(placeholder):
    """Update the quality analysis display in real-time"""
    with placeholder.container():
        
        analysis = st.session_state.current_quality_analysis
        if not analysis:
            analysis_html = '<div style="text-align: center; color: #666; margin-top: 20px;">No analysis available</div>'
            st.markdown(f'<div class="analysis-container">{analysis_html}</div>', unsafe_allow_html=True)
            return
            
        # Build HTML content for scrollable container
        analysis_html = ""
        
        # Handle loading state
        if analysis.get('status') == 'Analyzing...':
            analysis_html = '<div style="text-align: center; color: #2196f3; margin-top: 20px;">🔍 Assessing response quality...</div>'
        else:
            # Extract key metrics
            if 'overall_score' in analysis:
                score = analysis['overall_score']
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Score:</strong> {score:.1f}/10.0</div>'
            elif 'current_query_score' in analysis:
                score = analysis['current_query_score'] 
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Score:</strong> {score:.1f}/10.0</div>'
                
            if 'confidence' in analysis:
                confidence = analysis['confidence']
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Confidence:</strong> {confidence:.0%}</div>'
                
            # Show reasoning/analysis
            if 'reasoning' in analysis:
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Reasoning:</strong><br>{analysis["reasoning"]}</div>'
            elif 'llm_analysis' in analysis and analysis['llm_analysis']:
                analysis_html += f'<div style="margin-bottom: 15px;"><strong>Analysis:</strong><br>{analysis["llm_analysis"]}</div>'
                
            # Show key details
            for key, value in analysis.items():
                if key not in ['reasoning', 'llm_analysis', 'overall_score', 'current_query_score', 'confidence', 'status']:
                    if isinstance(value, (str, int, float, bool)):
                        analysis_html += f'<div style="margin-bottom: 10px;"><strong>{key.replace("_", " ").title()}:</strong> {value}</div>'
                        
            # Add context information if available
            if hasattr(st.session_state, 'current_context_for_quality') and st.session_state.current_context_for_quality:
                context_text = st.session_state.current_context_for_quality
                analysis_html += f'<div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd;"><strong>Context:</strong><br><small>{context_text}</small></div>'
        
        st.markdown(f'<div class="analysis-container">{analysis_html}</div>', unsafe_allow_html=True)

def process_user_input_realtime(user_input: str, system: Dict[str, Any], status_placeholder, chat_placeholder, logs_placeholder, frustration_placeholder, quality_placeholder, human_roster_placeholder, human_profile_placeholder, human_context_placeholder):
    """Process user input through the HITL system with real-time updates"""
    
    # Add user message to conversation immediately
    st.session_state.conversation_history.append({
        'role': 'user',
        'content': user_input
    })
    
    # Update all displays immediately
    update_chat_display(chat_placeholder)
    
    add_log_entry(f"Processing user query: '{user_input[:50]}...'")
    update_logs_display(logs_placeholder)
    
    # Create state for processing
    state = create_state(user_input, st.session_state.user_id, st.session_state.session_id)
    
    try:
        # Step 0: Context Gathering with real-time updates
        status_placeholder.info("🔍 Gathering context...")
        add_log_entry("Running ContextManager analysis...")
        add_log_entry(f"LLM Provider: {system['context_manager_agent'].llm_provider.model_name if system['context_manager_agent'].llm_provider else 'None'}")
        update_logs_display(logs_placeholder)
        
        # Gather context
        context_state = system['context_manager_agent'](state)
        context_summaries = context_state.get('context_summaries', {})
        
        # Store context for display in different components
        st.session_state.current_context_for_frustration = context_summaries.get('for_ai_agents', '')
        st.session_state.current_context_for_quality = context_summaries.get('for_quality_assessment', '')
        st.session_state.current_context_for_chatbot = context_summaries.get('for_ai_agents', '')
        
        add_log_entry("Context gathering complete")
        update_logs_display(logs_placeholder)
        
        # Step 1: Frustration Analysis with real-time updates
        status_placeholder.info("🔍 Analyzing frustration level...")
        add_log_entry("Running FrustrationAgent analysis...")
        add_log_entry(f"LLM Provider: {system['frustration_agent'].llm_provider.model_name if system['frustration_agent'].llm_provider else 'None'}")
        update_logs_display(logs_placeholder)
        
        # Clear previous analysis and show loading state
        st.session_state.current_frustration_analysis = {"status": "Analyzing..."}
        update_frustration_display(frustration_placeholder)
        
        # Run frustration analysis with context
        frustration_state = system['frustration_agent'](context_state)
        frustration_analysis = frustration_state.get('frustration_analysis', {})
        
        # Update frustration analysis in real-time
        st.session_state.current_frustration_analysis = frustration_analysis
        update_frustration_display(frustration_placeholder)
        add_log_entry(f"Frustration level: {frustration_analysis.get('overall_level', 'unknown')}")
        add_log_entry("✅ Frustration analysis complete")
        update_logs_display(logs_placeholder)
        
        # Step 2: Chatbot Response with real-time updates
        status_placeholder.info("🤖 Generating response...")
        add_log_entry("Generating ChatbotAgent response...")
        add_log_entry(f"LLM Provider: {system['chatbot_agent'].llm_provider.model_name if system['chatbot_agent'].llm_provider else 'None'}")
        update_logs_display(logs_placeholder)
        
        # Add placeholder for bot response
        st.session_state.conversation_history.append({
            'role': 'assistant',
            'content': '🤖 Thinking...'
        })
        update_chat_display(chat_placeholder)
        
        # Generate actual response
        chatbot_state = system['chatbot_agent'](frustration_state)
        ai_response = chatbot_state.get('ai_response', 'Sorry, I encountered an error.')
        
        # Update bot response in real-time with context
        st.session_state.conversation_history[-1]['content'] = ai_response
        st.session_state.conversation_history[-1]['context'] = st.session_state.current_context_for_chatbot
        update_chat_display(chat_placeholder)
        
        add_log_entry(f"Generated response ({len(ai_response)} chars)")
        update_logs_display(logs_placeholder)
        
        # Step 3: Quality Analysis with real-time updates
        status_placeholder.info("🔍 Assessing response quality...")
        add_log_entry("Running QualityAgent assessment...")
        add_log_entry(f"LLM Provider: {system['quality_agent'].llm_provider.model_name if system['quality_agent'].llm_provider else 'None'}")
        update_logs_display(logs_placeholder)
        
        # Clear previous quality analysis and show loading state
        st.session_state.current_quality_analysis = {"status": "Analyzing..."}
        update_quality_display(quality_placeholder)
        
        # Run quality analysis
        quality_state = system['quality_agent'](chatbot_state)
        quality_analysis = quality_state.get('quality_assessment', {})
        
        # Update quality analysis in real-time
        st.session_state.current_quality_analysis = quality_analysis
        update_quality_display(quality_placeholder)
        add_log_entry(f"Quality decision: {quality_analysis.get('decision', 'unknown')}")
        
        # Check for adjusted response and update chat in real-time
        if quality_analysis.get('adjusted_response'):
            add_log_entry("Response was adjusted by QualityAgent")
            adjusted_response = quality_analysis['adjusted_response']
            
            # Update the conversation with adjusted response immediately
            st.session_state.conversation_history[-1]['content'] = adjusted_response
            st.session_state.conversation_history[-1]['context'] = st.session_state.current_context_for_chatbot
            update_chat_display(chat_placeholder)
        
        # Step 4: Check for Human Escalation
        escalation_needed = check_escalation_conditions(frustration_analysis, quality_analysis)
        
        if escalation_needed:
            # Store current query for human context
            st.session_state.current_query = user_input
            
            status_placeholder.info("🚨 Escalating to human agent...")
            add_log_entry("Escalation conditions met - routing to human agent")
            add_log_entry(f"LLM Provider: {system['human_routing_agent'].llm_provider.model_name if system['human_routing_agent'].llm_provider else 'None'}")
            update_logs_display(logs_placeholder)
            
            # Run human routing
            routing_state = system['human_routing_agent'](quality_state)
            st.session_state.routing_decision = routing_state.get('routing_decision', {})
            
            # Select the agent that was chosen by the routing system
            assigned_agent = routing_state.get('assigned_human_agent')
            if assigned_agent:
                # Ensure agent data has all expected fields for UI display
                mapped_agent = ensure_agent_fields(assigned_agent)
                st.session_state.selected_agent_id = mapped_agent['id']
                st.session_state.selected_agent = mapped_agent
                st.session_state.escalation_triggered = True
                
                add_log_entry(f"Assigned to agent: {assigned_agent['name']}")
                add_log_entry(f"Match score: {st.session_state.routing_decision.get('agent_match_score', 0):.1f}%")
                
                # Update human routing displays
                update_human_roster_display(human_roster_placeholder)
                update_human_profile_display(human_profile_placeholder)
                update_human_context_display(human_context_placeholder)
                
                add_log_entry("✅ Human routing complete")
            else:
                add_log_entry("⚠️ No agents available - customer queued")
            
            update_logs_display(logs_placeholder)
            
        add_log_entry("Processing completed successfully")
        update_logs_display(logs_placeholder)
        status_placeholder.success("✅ All processing complete!")
        
        # Clear status after a brief moment
        time.sleep(1)
        status_placeholder.empty()
        
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        add_log_entry(error_msg)
        update_logs_display(logs_placeholder)
        status_placeholder.error(f"❌ Error: {str(e)}")
        
        # Add error response to conversation and update display
        if st.session_state.conversation_history and st.session_state.conversation_history[-1]['content'] == '🤖 Thinking...':
            st.session_state.conversation_history[-1]['content'] = 'I apologize, but I encountered an error processing your request. Please try again.'
        else:
            st.session_state.conversation_history.append({
                'role': 'assistant',
                'content': 'I apologize, but I encountered an error processing your request. Please try again.'
            })
        
        update_chat_display(chat_placeholder)
        
        # Clear error status after a brief moment  
        time.sleep(2)
        status_placeholder.empty()

def process_user_input_parallel(user_input: str, system: Dict[str, Any], status_placeholder, chat_placeholder, logs_placeholder, frustration_placeholder, quality_placeholder, human_roster_placeholder, human_profile_placeholder, human_context_placeholder):
    """Process user input with parallel frustration/quality analysis for speed"""
    import concurrent.futures
    import threading
    
    # Add user message to conversation immediately
    st.session_state.conversation_history.append({
        'role': 'user',
        'content': user_input
    })
    
    # Update all displays immediately
    update_chat_display(chat_placeholder)
    
    add_log_entry(f"Processing user query (parallel mode): '{user_input[:50]}...'")
    update_logs_display(logs_placeholder)
    
    # Create state for processing
    state = create_state(user_input, st.session_state.user_id, st.session_state.session_id)
    
    try:
        # Step 0: Context Gathering 
        status_placeholder.info("🔍 Gathering context...")
        add_log_entry("Running ContextManager analysis...")
        add_log_entry(f"LLM Provider: {system['context_manager_agent'].llm_provider.model_name if system['context_manager_agent'].llm_provider else 'None'}")
        update_logs_display(logs_placeholder)
        
        # Gather context
        context_state = system['context_manager_agent'](state)
        context_summaries = context_state.get('context_summaries', {})
        
        # Store context for display in different components
        st.session_state.current_context_for_frustration = context_summaries.get('for_ai_agents', '')
        st.session_state.current_context_for_quality = context_summaries.get('for_quality_assessment', '')
        st.session_state.current_context_for_chatbot = context_summaries.get('for_ai_agents', '')
        
        add_log_entry("Context gathering complete")
        update_logs_display(logs_placeholder)
        
        # Step 1: Parallel Frustration Analysis + Chatbot Response
        status_placeholder.info("🚀 Running parallel analysis...")
        add_log_entry("Running parallel FrustrationAgent analysis and ChatbotAgent response...")
        update_logs_display(logs_placeholder)
        
        # Clear previous analysis and show loading state
        st.session_state.current_frustration_analysis = {"status": "Analyzing..."}
        update_frustration_display(frustration_placeholder)
        
        # Add placeholder for bot response
        st.session_state.conversation_history.append({
            'role': 'assistant',
            'content': '🤖 Thinking...'
        })
        update_chat_display(chat_placeholder)
        
        # Run frustration analysis and chatbot response in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks using context state
            frustration_future = executor.submit(system['frustration_agent'], context_state)
            chatbot_future = executor.submit(system['chatbot_agent'], context_state)
            
            # Wait for both to complete
            frustration_state = frustration_future.result()
            chatbot_state_initial = chatbot_future.result()
            
            # Merge results - use frustration analysis in chatbot state
            chatbot_state = {**chatbot_state_initial, **frustration_state}
        
        # Update displays with results
        frustration_analysis = frustration_state.get('frustration_analysis', {})
        ai_response = chatbot_state.get('ai_response', 'Sorry, I encountered an error.')
        
        st.session_state.current_frustration_analysis = frustration_analysis
        update_frustration_display(frustration_placeholder)
        
        st.session_state.conversation_history[-1]['content'] = ai_response
        st.session_state.conversation_history[-1]['context'] = st.session_state.current_context_for_chatbot
        update_chat_display(chat_placeholder)
        
        add_log_entry(f"Frustration level: {frustration_analysis.get('overall_level', 'unknown')}")
        add_log_entry(f"Generated response ({len(ai_response)} chars)")
        add_log_entry("✅ Parallel analysis complete")
        update_logs_display(logs_placeholder)
        
        # Step 2: Quality Analysis
        status_placeholder.info("🔍 Assessing response quality...")
        add_log_entry("Running QualityAgent assessment...")
        update_logs_display(logs_placeholder)
        
        st.session_state.current_quality_analysis = {"status": "Analyzing..."}
        update_quality_display(quality_placeholder)
        
        # Run quality analysis
        quality_state = system['quality_agent'](chatbot_state)
        quality_analysis = quality_state.get('quality_assessment', {})
        
        # Update quality analysis in real-time
        st.session_state.current_quality_analysis = quality_analysis
        update_quality_display(quality_placeholder)
        add_log_entry(f"Quality decision: {quality_analysis.get('decision', 'unknown')}")
        
        # Check for adjusted response and update chat in real-time
        if quality_analysis.get('adjusted_response'):
            add_log_entry("Response was adjusted by QualityAgent")
            adjusted_response = quality_analysis['adjusted_response']
            
            # Update the conversation with adjusted response immediately
            st.session_state.conversation_history[-1]['content'] = adjusted_response
            st.session_state.conversation_history[-1]['context'] = st.session_state.current_context_for_chatbot
            update_chat_display(chat_placeholder)
        
        # Step 3: Check for Human Escalation (parallel mode)
        escalation_needed = check_escalation_conditions(frustration_analysis, quality_analysis)
        
        if escalation_needed:
            # Store current query for human context
            st.session_state.current_query = user_input
            
            status_placeholder.info("🚨 Escalating to human agent...")
            add_log_entry("Escalation conditions met - routing to human agent")
            add_log_entry(f"LLM Provider: {system['human_routing_agent'].llm_provider.model_name if system['human_routing_agent'].llm_provider else 'None'}")
            update_logs_display(logs_placeholder)
            
            # Run human routing
            routing_state = system['human_routing_agent'](quality_state)
            st.session_state.routing_decision = routing_state.get('routing_decision', {})
            
            # Select the agent that was chosen by the routing system
            assigned_agent = routing_state.get('assigned_human_agent')
            if assigned_agent:
                # Ensure agent data has all expected fields for UI display
                mapped_agent = ensure_agent_fields(assigned_agent)
                st.session_state.selected_agent_id = mapped_agent['id']
                st.session_state.selected_agent = mapped_agent
                st.session_state.escalation_triggered = True
                
                add_log_entry(f"Assigned to agent: {assigned_agent['name']}")
                add_log_entry(f"Match score: {st.session_state.routing_decision.get('agent_match_score', 0):.1f}%")
                
                # Update human routing displays
                update_human_roster_display(human_roster_placeholder)
                update_human_profile_display(human_profile_placeholder)
                update_human_context_display(human_context_placeholder)
                
                add_log_entry("✅ Human routing complete")
            else:
                add_log_entry("⚠️ No agents available - customer queued")
            
            update_logs_display(logs_placeholder)
            
        add_log_entry("Processing completed successfully")
        update_logs_display(logs_placeholder)
        status_placeholder.success("✅ All processing complete!")
        
        # Clear status after a brief moment
        time.sleep(1)
        status_placeholder.empty()
        
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        add_log_entry(error_msg)
        update_logs_display(logs_placeholder)
        status_placeholder.error(f"❌ Error: {str(e)}")
        
        # Add error response to conversation and update display
        if st.session_state.conversation_history and st.session_state.conversation_history[-1]['content'] == '🤖 Thinking...':
            st.session_state.conversation_history[-1]['content'] = 'I apologize, but I encountered an error processing your request. Please try again.'
        else:
            st.session_state.conversation_history.append({
                'role': 'assistant',
                'content': 'I apologize, but I encountered an error processing your request. Please try again.'
            })
        
        update_chat_display(chat_placeholder)
        
        # Clear error status after a brief moment  
        time.sleep(2)
        status_placeholder.empty()

def main():
    st.title("🤖 HITL System Demo")
    st.markdown("Interactive demonstration of ChatbotAgent, FrustrationAgent, QualityAgent, and HumanRoutingAgent")
    
    # Initialize system
    system = initialize_system()
    
    if not system.get('initialized', False):
        st.error("System initialization failed. Please check the configuration and try again.")
        if 'error' in system:
            st.error(f"Error details: {system['error']}")
        return
    
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'current_frustration_analysis' not in st.session_state:
        st.session_state.current_frustration_analysis = {}
    if 'current_quality_analysis' not in st.session_state:
        st.session_state.current_quality_analysis = {}
    if 'current_context_for_frustration' not in st.session_state:
        st.session_state.current_context_for_frustration = ""
    if 'current_context_for_quality' not in st.session_state:
        st.session_state.current_context_for_quality = ""
    if 'current_context_for_chatbot' not in st.session_state:
        st.session_state.current_context_for_chatbot = ""
    if 'selected_agent_id' not in st.session_state:
        st.session_state.selected_agent_id = None
    if 'selected_agent' not in st.session_state:
        st.session_state.selected_agent = None
    if 'routing_decision' not in st.session_state:
        st.session_state.routing_decision = None
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'escalation_triggered' not in st.session_state:
        st.session_state.escalation_triggered = False
    
    add_log_entry("System initialized successfully")
    add_log_entry(f"User ID: {st.session_state.user_id}")
    add_log_entry(f"Session ID: {st.session_state.session_id}")
    
    # Create layout - 4 windows
    # Top row: Chat (left) and Logging (right)
    col1, col2 = st.columns([2, 1])
    
    # Bottom row: Frustration Analysis (left) and Quality Analysis (right)
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    # Human Routing row: Human Roster, Profile, and Context
    st.markdown("---")
    col5, col6, col7 = st.columns(3)
    
    # Create all placeholders that will be used across columns
    with col2:
        st.markdown("### 📋 System Logs")
        logs_placeholder = st.empty()
    
    with col3:
        st.markdown("### 😠 Frustration Analysis")
        frustration_placeholder = st.empty()
    
    with col4:
        st.markdown("### ✅ Quality Analysis")
        quality_placeholder = st.empty()
    
    with col5:
        st.markdown("### 👥 Human Agent Roster")
        human_roster_placeholder = st.empty()
    
    with col6:
        st.markdown("### 👤 Selected Agent Profile")
        human_profile_placeholder = st.empty()
    
    with col7:
        st.markdown("### 📋 Human Context & Briefing")
        human_context_placeholder = st.empty()
    
    with col1:
        st.markdown("### 💬 Chat Window")
        
        # Performance mode selector
        col1a, col1b = st.columns([2, 1])
        with col1a:
            pass  # Keep space for chat
        with col1b:
            performance_mode = st.selectbox(
                "Performance Mode:",
                ["Standard", "Fast (Compact)", "Fastest (Parallel)"],
                index=1,  # Default to Fast mode
                help="Standard: Full analysis, Fast: Compact responses, Fastest: Parallel processing"
            )
        
        # Create placeholder for dynamic chat updates
        chat_placeholder = st.empty()
        update_chat_display(chat_placeholder)
        
        # Input for new message
        user_input = st.text_input("Enter your message:", key="user_input", placeholder="Ask a question or describe your issue...")
        
        # Status area for showing processing progress
        status_area = st.empty()
        
        # Send button with processing mode selection
        col_send1, col_send2 = st.columns([1, 3])
        with col_send1:
            send_clicked = st.button("Send", type="primary")
        with col_send2:
            if performance_mode == "Fast (Compact)":
                st.caption("⚡ Using compact responses for speed")
            elif performance_mode == "Fastest (Parallel)":
                st.caption("🚀 Using parallel processing for maximum speed")
            else:
                st.caption("🔄 Using standard detailed responses")
        
        if send_clicked:
            add_log_entry(f"Send button clicked. Input: '{user_input}' Mode: {performance_mode}")
            if user_input and user_input.strip():
                add_log_entry(f"Processing input: '{user_input}'")
                
                # Store performance mode in session state for agents to access
                st.session_state.performance_mode = performance_mode
                
                # Select processing function based on mode
                if performance_mode == "Fastest (Parallel)":
                    process_user_input_parallel(user_input, system, status_area, chat_placeholder, logs_placeholder, frustration_placeholder, quality_placeholder, human_roster_placeholder, human_profile_placeholder, human_context_placeholder)
                else:
                    # For both Standard and Fast modes, use the same function but different prompt selection is handled in agents
                    process_user_input_realtime(user_input, system, status_area, chat_placeholder, logs_placeholder, frustration_placeholder, quality_placeholder, human_roster_placeholder, human_profile_placeholder, human_context_placeholder)
                    
                # Clear the input field after processing by triggering a rerun
                st.rerun()
            else:
                st.warning("Please enter a message before sending.")
                add_log_entry("No input provided")
    
    with col2:
        update_logs_display(logs_placeholder)
        
        if st.button("Clear Logs"):
            st.session_state.logs = []
            st.rerun()
    
    # Update analysis displays
    update_frustration_display(frustration_placeholder)
    update_quality_display(quality_placeholder)
    
    # Update human routing displays
    update_human_roster_display(human_roster_placeholder)
    update_human_profile_display(human_profile_placeholder)
    update_human_context_display(human_context_placeholder)


if __name__ == "__main__":
    main()