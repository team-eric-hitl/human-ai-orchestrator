"""
Gradio Demo App for HITL System
Behind the scenes look at the agents working together.
Demonstrates ChatbotAgent, FrustrationAgent, and QualityAgent working together
Optimized processing logic with early escalation detection
"""

import json
import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import uuid
from dotenv import load_dotenv
import html
import gradio as gr
import concurrent.futures

# Load environment variables from .env file  
load_dotenv()

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

# Global system components (initialized once)
system = None
field_mapper = AgentFieldMapper()
human_agents_repo = SQLiteHumanAgentRepository()

def safe_html_escape(text: Any) -> str:
    """Safely escape HTML characters in text"""
    if text is None:
        return ""
    return html.escape(str(text))

def initialize_system():
    """Initialize the HITL system components"""
    global system
    if system is not None:
        return system
        
    try:
        # Initialize configuration
        config_dir = os.path.join(os.path.dirname(__file__), 'config')
        config_manager = AgentConfigManager(config_dir)
        
        # Use configuration files as intended - no hardcoded overrides
        # Initialize context manager  
        context_manager = SQLiteContextProvider(config_manager=config_manager)
        
        # Initialize agents
        context_manager_agent = ContextManagerAgentNode(config_manager, context_manager)
        chatbot_agent = ChatbotAgentNode(config_manager, context_manager)
        frustration_agent = FrustrationAgentNode(config_manager, context_manager)
        quality_agent = QualityAgentNode(config_manager, context_manager)
        human_routing_agent = HumanRoutingAgentNode(config_manager, context_manager)
        
        system = {
            'config_manager': config_manager,
            'context_manager': context_manager,
            'context_manager_agent': context_manager_agent,
            'chatbot_agent': chatbot_agent,
            'frustration_agent': frustration_agent,
            'quality_agent': quality_agent,
            'human_routing_agent': human_routing_agent,
            'initialized': True
        }
        
        logger.info("HITL system initialized successfully")
        return system
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {str(e)}")
        return {'initialized': False, 'error': str(e)}

async def ensure_database_populated():
    """Ensure the human agents database is populated with mock data"""
    try:
        # Check if database is empty
        agents = await human_agents_repo.get_all()
        if len(agents) == 0:
            logger.info("Database is empty, populating with mock agents...")
            
            # Import and run population logic
            from src.data.populate_agents_db import populate_database
            await populate_database(reset=True)  # Reset to avoid constraint conflicts
            logger.info("Database populated successfully")
        else:
            logger.info(f"Database already contains {len(agents)} agents")
    except Exception as e:
        logger.error(f"Failed to ensure database population: {e}")

def get_human_agents() -> List[Dict[str, Any]]:
    """Fetch all human agents from the database"""
    try:
        async def get_agents():
            # Ensure database is populated before fetching
            await ensure_database_populated()
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
            agents.append(agent_dict)
        
        return agents
    except Exception as e:
        logger.error(f"Failed to fetch human agents: {e}")
        return []

def check_early_escalation(frustration_analysis: Dict[str, Any]) -> bool:
    """Check if frustration level requires immediate escalation (no chatbot/quality needed)"""
    frustration_level = frustration_analysis.get('overall_level', 'low')
    
    # Critical frustration always escalates immediately
    if frustration_level == 'critical':
        return True
    
    # High frustration with high confidence also escalates immediately
    if frustration_level == 'high' and frustration_analysis.get('confidence', 0) > 0.8:
        return True
        
    return False

def check_final_escalation(frustration_analysis: Dict[str, Any], quality_analysis: Dict[str, Any]) -> bool:
    """Check if conditions are met for escalating to human agent after quality analysis"""
    
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

def create_state(query: str, user_id: str, session_id: str, conversation_history: List[Dict]) -> HybridSystemState:
    """Create a state object for the agents"""
    return {
        'query': query,
        'user_id': user_id,
        'session_id': session_id,
        'query_id': str(uuid.uuid4()),
        'timestamp': datetime.now(),
        'messages': conversation_history,
        'next_action': 'process_query'
    }

def get_agent_model_info(agent_name: str) -> str:
    """Get model information for a specific agent"""
    global system
    if not system or not system.get('initialized'):
        return "Model: Loading..."
    
    try:
        config_manager = system.get('config_manager')
        if not config_manager:
            return "Model: Not available"
        
        # Get the agent's preferred model with alias resolution
        preferred_model = config_manager.get_agent_preferred_model(agent_name)
        
        # Get the actual model name by resolving aliases
        resolved_model = config_manager.resolve_model_name(preferred_model)
        
        if preferred_model != resolved_model:
            return f"Model: {resolved_model} (alias: {preferred_model})"
        else:
            return f"Model: {resolved_model}"
    except Exception as e:
        return f"Model: Error loading ({str(e)})"

def format_analysis_display(analysis: Dict[str, Any], title: str, agent_name: str = None) -> str:
    """Format analysis results for display"""
    result = f"**{title}**\n"
    
    # Add model information if agent name is provided
    if agent_name:
        model_info = get_agent_model_info(agent_name)
        result += f"*{model_info}*\n"
    
    result += "\n"
    
    if not analysis:
        return result + "No analysis available"
    
    # Handle loading state
    if analysis.get('status') == 'Analyzing...':
        return result + "🔍 Analyzing..."
    
    # Extract key metrics
    if 'overall_score' in analysis:
        score = analysis['overall_score']
        result += f"**Score:** {score:.1f}/10.0\n"
    elif 'current_query_score' in analysis:
        score = analysis['current_query_score'] 
        result += f"**Score:** {score:.1f}/10.0\n"
        
    if 'overall_level' in analysis:
        level = analysis['overall_level']
        result += f"**Level:** {level.title()}\n"
        
    if 'confidence' in analysis:
        confidence = analysis['confidence']
        result += f"**Confidence:** {confidence:.0%}\n"
        
    if 'decision' in analysis:
        decision = analysis['decision']
        result += f"**Decision:** {decision.title()}\n"
        
    # Show reasoning/analysis
    if 'reasoning' in analysis:
        result += f"\n**Reasoning:**\n{analysis['reasoning']}\n"
    elif 'llm_analysis' in analysis and analysis['llm_analysis']:
        result += f"\n**Analysis:**\n{analysis['llm_analysis']}\n"
    
    return result

def format_logs_display(logs: List[str]) -> str:
    """Format logs for display"""
    if not logs:
        return "No logs yet..."
    
    # Show last 20 logs to keep display manageable
    recent_logs = logs[-20:]
    return "\n".join(recent_logs)

def format_human_roster(agents: List[Dict], selected_agent_id: Optional[str] = None) -> str:
    """Format human agent roster for display - simple list without ranking"""
    if not agents:
        return "No agents available"
    
    result = "**👥 Human Agent Roster**\n\n"
    
    # Simple agent list display
    for agent in agents:
        selected_marker = "►" if agent['id'] == selected_agent_id else " "
        status_emoji = _get_status_with_emoji(agent['status'])
        
        # Get workload info
        current_load = _parse_current_workload(agent)
        max_load = agent.get('max_concurrent_conversations', 5)
        
        result += f"{selected_marker} **{agent['name']}** - {status_emoji} ({current_load}/{max_load})\n"
        result += f"   Specializations: {', '.join(agent.get('specializations', []))}\n"
        result += f"   Experience: Level {agent.get('experience_level', 1)}/5\n\n"
    
    # Show detailed view only for selected agent
    if selected_agent_id:
        selected_agent = next((agent for agent in agents if agent['id'] == selected_agent_id), None)
        if selected_agent:
            result += f"**🎯 Selected Agent Details**\n"
            result += f"**{selected_agent['name']}**\n"
            result += f"Status: {_get_status_with_emoji(selected_agent['status'])}\n"
            result += f"Email: {selected_agent['email']}\n"
            result += f"Specializations: {', '.join(selected_agent.get('specializations', []))}\n"
            result += f"Experience: Level {selected_agent.get('experience_level', 1)}/5\n"
            result += f"Languages: {', '.join(selected_agent.get('languages', ['English']))}\n"
            
            # Add performance insights
            metadata = selected_agent.get('metadata', {})
            if 'certifications' in metadata and metadata['certifications']:
                result += f"Certifications: {', '.join(metadata['certifications'][:2])}\n"
    
    return result

def _parse_current_workload(agent: Dict[str, Any]) -> int:
    """Helper function to parse current workload from various formats"""
    workload = agent.get('current_workload', 0)
    if isinstance(workload, str) and '/' in workload:
        try:
            return int(workload.split('/')[0])
        except (ValueError, IndexError):
            return 0
    elif isinstance(workload, (int, float)):
        return int(workload)
    return 0

def _get_status_with_emoji(status: str) -> str:
    """Helper function to get status with appropriate emoji"""
    status_mapping = {
        "available": "🟢 Available",
        "busy": "🔴 Busy", 
        "break": "🟡 On Break",
        "offline": "⚫ Offline"
    }
    return status_mapping.get(status, f"⚪ {status.title()}")

def format_agent_profile(agent: Dict[str, Any]) -> str:
    """Format selected agent profile for display"""
    if not agent:
        return "**👤 Agent Profile**\n\nNo agent selected"
    
    metadata = agent.get('metadata', {})
    
    result = f"**👤 {agent['name']}**\n\n"
    result += f"**Email:** {agent['email']}\n"
    result += f"**Department:** {metadata.get('department', 'N/A')}\n"
    result += f"**Team:** {metadata.get('team', 'N/A')}\n"
    result += f"**Experience:** Level {agent.get('experience_level', 1)}/5\n"
    result += f"**Languages:** {', '.join(agent.get('languages', []))}\n"
    result += f"**Shift:** {agent.get('shift_start', 'N/A')} - {agent.get('shift_end', 'N/A')}\n"
    result += f"**Status:** {agent['status'].title()}\n\n"
    
    if agent.get('specializations'):
        result += f"**Specializations:**\n{', '.join(agent['specializations'])}\n\n"
    
    if metadata.get('certifications'):
        result += f"**Certifications:**\n{', '.join(metadata['certifications'])}\n"
    
    return result

def format_context_display(context_data: Dict[str, Any], context_summaries: Dict[str, str]) -> str:
    """Format context information being passed to agents"""
    if not context_data and not context_summaries:
        return "**🔍 Context Information**\n\nNo context data available"
    
    result = "**🔍 Context Information**\n\n"
    
    # Display context summaries for different audiences
    if context_summaries:
        result += "**📋 Context Summaries:**\n\n"
        
        if "for_ai_agents" in context_summaries:
            result += f"**🤖 For AI Agents:**\n{context_summaries['for_ai_agents']}\n\n"
        
        if "for_human_agents" in context_summaries:
            result += f"**👤 For Human Agents:**\n{context_summaries['for_human_agents'][:300]}{'...' if len(context_summaries['for_human_agents']) > 300 else ''}\n\n"
        
        if "for_quality_assessment" in context_summaries:
            result += f"**✅ For Quality Assessment:**\n{context_summaries['for_quality_assessment']}\n\n"
        
        if "for_routing_decision" in context_summaries:
            result += f"**🎯 For Routing Decision:**\n{context_summaries['for_routing_decision']}\n\n"
    
    # Display key context data metrics
    if context_data:
        result += "**📊 Context Data Summary:**\n"
        
        # User profile info
        user_profile = context_data.get('user_profile', {})
        if user_profile.get('total_interactions'):
            result += f"• User interactions: {user_profile.get('total_interactions', 0)}\n"
            result += f"• Escalation rate: {user_profile.get('escalation_rate', 0):.1%}\n"
            result += f"• Behavior pattern: {user_profile.get('user_behavior_pattern', 'unknown')}\n"
        
        # Interaction history
        interaction_history = context_data.get('interaction_history', {})
        if interaction_history.get('total_interactions'):
            result += f"• Recent interactions: {interaction_history.get('total_interactions', 0)}\n"
        
        # Similar cases
        similar_cases = context_data.get('similar_cases', [])
        if similar_cases:
            result += f"• Similar cases found: {len(similar_cases)}\n"
            if similar_cases:
                result += f"• Top similarity: {similar_cases[0].get('similarity_score', 0):.0%}\n"
        
        # Product context
        product_context = context_data.get('product_context', {})
        related_products = product_context.get('related_products', [])
        if related_products:
            result += f"• Related products: {', '.join(related_products)}\n"
        
        # Knowledge base results
        knowledge_base = context_data.get('knowledge_base', {})
        relevant_entries = knowledge_base.get('relevant_entries', [])
        if relevant_entries:
            result += f"• Knowledge base matches: {len(relevant_entries)}\n"
            if relevant_entries:
                result += f"• Top relevance: {relevant_entries[0].get('relevance_score', 0):.0%}\n"
        
        # Escalation history
        escalation_history = context_data.get('escalation_history', {})
        if escalation_history.get('total_escalations', 0) > 0:
            result += f"• Previous escalations: {escalation_history.get('total_escalations', 0)}\n"
    
    return result

def format_escalation_context(context: Dict[str, Any], query: str, conversation_history: List[Dict]) -> str:
    """Format escalation context for human agent with enhanced routing decision transparency"""
    if not context:
        return "**📋 Escalation Context**\n\nNo escalation context available"
    
    result = "**📋 Escalation Context**\n\n"
    
    routing_requirements = context.get('routing_requirements', {})
    
    result += f"**🎯 Escalation Summary**\n"
    result += f"Reason: {routing_requirements.get('escalation_type', 'general_escalation')}\n"
    result += f"Priority: {routing_requirements.get('priority', 'high')}\n"
    result += f"Complexity: {routing_requirements.get('complexity', 'low')}\n"
    result += f"Est. Resolution: {context.get('estimated_resolution_time', 15)} minutes\n\n"
    
    # Add agent ranking information when agent is selected
    agents = get_human_agents()
    if agents:
        result += f"**🏆 Agent Performance Ranking**\n"
        
        # Calculate performance scores for ranking
        agents_with_scores = []
        for agent in agents:
            # Calculate composite performance score
            metadata = agent.get('metadata', {})
            experience_score = agent.get('experience_level', 1) * 20  # 0-100 scale
            workload_available = agent.get('max_concurrent_conversations', 5) - _parse_current_workload(agent)
            workload_score = min(workload_available * 20, 100)  # More availability = higher score
            
            # Mock satisfaction score from metadata or default
            satisfaction_score = metadata.get('customer_satisfaction_score', 4.5) * 20  # Convert 1-5 to 0-100 scale
            
            composite_score = (experience_score * 0.4 + workload_score * 0.3 + satisfaction_score * 0.3)
            agents_with_scores.append((agent, composite_score))
        
        # Sort by performance score (highest first)
        agents_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        result += "```\nRank  Agent                Score  Load    Satisfaction\n"
        result += "----  ------------------- ------ ------- ------------\n"
        
        rank_emojis = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for i, (agent, score) in enumerate(agents_with_scores[:5]):  # Show top 5 agents
            rank_emoji = rank_emojis[i] if i < len(rank_emojis) else f"{i+1}️⃣"
            
            # Format agent name (truncate if too long)
            agent_name = agent['name']
            if len(agent_name) > 18:
                agent_name = agent_name[:15] + "..."
            
            # Get workload info
            current_load = _parse_current_workload(agent)
            max_load = agent.get('max_concurrent_conversations', 5)
            
            # Get satisfaction score
            metadata = agent.get('metadata', {})
            satisfaction = metadata.get('customer_satisfaction_score', 4.5)
            
            result += f" {rank_emoji} {agent_name:<18} {score:5.1f}  {current_load}/{max_load}     {satisfaction:.1f}⭐\n"
        
        result += "```\n\n"
    
    # Enhanced routing decision explanation
    result += f"**🧠 Why This Agent Was Selected**\n"
    agent_match_score = context.get('agent_match_score', 100.0)
    result += f"Overall Match Score: {agent_match_score:.1f}%\n\n"
    
    # Add LLM reasoning if available
    llm_explanation = context.get('llm_explanation', '')
    if llm_explanation:
        result += f"**🤖 AI Routing Analysis**\n{llm_explanation}\n\n"
    
    # Add detailed reasoning factors
    llm_reasoning = context.get('llm_reasoning', [])
    if llm_reasoning:
        result += f"**💡 Key Selection Factors**\n"
        for i, reason in enumerate(llm_reasoning[:4], 1):  # Show top 4 factors
            result += f"{i}. {reason}\n"
        result += "\n"
    
    # Show alternative agents considered
    alternative_agents = context.get('alternative_agents', [])
    if alternative_agents:
        result += f"**🔄 Alternative Agents Considered**\n"
        for alt in alternative_agents[:2]:  # Show top 2 alternatives
            result += f"• {alt.get('name', 'Unknown Agent')} (ID: {alt.get('id', 'N/A')})\n"
        result += "\n"
    
    # Routing strategy and confidence
    routing_strategy = context.get('routing_strategy', 'unknown')
    routing_confidence = context.get('routing_confidence', 0.0)
    if routing_strategy != 'unknown':
        result += f"**⚙️ Routing Method:** {routing_strategy.replace('_', ' ').title()}\n"
    if routing_confidence > 0:
        result += f"**📊 Confidence Level:** {routing_confidence:.0%}\n\n"
    
    result += f"**💬 Current Issue**\n{query}\n\n"
    
    if conversation_history:
        result += f"**📝 Recent Conversation (last 3 messages)**\n"
        for msg in conversation_history[-3:]:
            role = "Customer" if msg['role'] == 'user' else "AI Assistant"
            content = msg['content'][:150] + '...' if len(msg['content']) > 150 else msg['content']
            result += f"**{role}:** {content}\n\n"
    
    return result

def process_user_input_with_realtime_updates(message: str, history: List[Dict], logs_state: List[str], use_context_manager: bool = False):
    """
    Process user input through the optimized HITL system with real-time UI updates via generator
    Yields: (msg_input, updated_history, logs, frustration_analysis, quality_analysis, context_display, human_roster, agent_profile, escalation_context)
    """
    global system
    
    # Show user input immediately
    new_history = history + [{'role': 'user', 'content': message}]
    yield ("", new_history, "Processing...", "", "", "", "", "", "")
    
    if not system or not system.get('initialized'):
        system = initialize_system()
        if not system.get('initialized'):
            error_msg = "System initialization failed. Please refresh and try again."
            error_history = new_history + [{'role': 'assistant', 'content': error_msg}]
            yield ("", error_history, format_logs_display(logs_state), "", "", "", "", "", "")
            return
    
    # Generate unique IDs for this session
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Convert Gradio messages format to internal format
    conversation_history = []
    for msg in history:
        conversation_history.append(msg)
    
    # Add current user message
    conversation_history.append({'role': 'user', 'content': message})
    
    # Initialize variables for analysis results
    frustration_analysis = {}
    quality_analysis = {}
    escalation_context = {}
    context_data = {}
    context_summaries = {}
    selected_agent = None
    human_agents = get_human_agents()
    
    try:
        # Add processing start log
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Processing: '{message[:50]}...'")
        yield ("", new_history, format_logs_display(logs_state), "", "", "", "", "", "")
        
        # Create state for processing
        state = create_state(message, user_id, session_id, conversation_history)
        
        # Step 1: Context Gathering (configurable via toggle)
        if use_context_manager:
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Gathering context information...")
            yield ("", new_history, format_logs_display(logs_state), "", "", "", "", "", "")
            
            # Use context manager agent
            context_state = system['context_manager_agent'](state)
            context_summaries = context_state.get('context_summaries', {})
            context_data = context_state.get('context_data', {})
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Context gathered ({len(context_summaries)} sources)")
        else:
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Context gathering disabled (toggle off)")
            yield ("", new_history, format_logs_display(logs_state), "", "", "", "", "", "")
            
            # Skip context gathering - use state directly
            context_state = state.copy()
            context_state['context_summaries'] = {}
            context_summaries = {}
            context_data = {}
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Context step skipped")
        
        yield ("", new_history, format_logs_display(logs_state), "", "", "", "", "", "")
        
        # Step 2: Frustration Analysis
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 😠 Analyzing frustration level...")
        analyzing_frustration = format_analysis_display({"status": "Analyzing..."}, "😠 Frustration Analysis", "frustration_agent")
        context_display = format_context_display(context_data, context_summaries)
        yield ("", new_history, format_logs_display(logs_state), analyzing_frustration, "", context_display, "", "", "")
        
        frustration_state = system['frustration_agent'](context_state)
        frustration_analysis = frustration_state.get('frustration_analysis', {})
        frustration_level = frustration_analysis.get('overall_level', 'low')
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Frustration level: {frustration_level}")
        frustration_display = format_analysis_display(frustration_analysis, "😠 Frustration Analysis", "frustration_agent")
        yield ("", new_history, format_logs_display(logs_state), frustration_display, "", context_display, "", "", "")
        
        # Step 3: Check for Early Escalation (OPTIMIZATION: Skip chatbot/quality if critical frustration)
        if check_early_escalation(frustration_analysis):
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Early escalation triggered - bypassing chatbot/quality")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, "", context_display, "", "", "")
            
            # Skip chatbot and quality analysis, go straight to human routing
            routing_state = system['human_routing_agent'](frustration_state)
            escalation_context = routing_state.get('routing_decision', {})
            selected_agent = routing_state.get('assigned_human_agent')
            
            # Convert agent object to dict if needed
            if selected_agent and hasattr(selected_agent, '__dict__'):
                selected_agent = {
                    'id': getattr(selected_agent, 'id', ''),
                    'name': getattr(selected_agent, 'name', ''),
                    'email': getattr(selected_agent, 'email', ''),
                    'status': getattr(selected_agent, 'status', 'available'),
                    'specializations': getattr(selected_agent, 'specializations', []),
                    'max_concurrent_conversations': getattr(selected_agent, 'max_concurrent_conversations', 5),
                    'experience_level': getattr(selected_agent, 'experience_level', 1),
                    'languages': getattr(selected_agent, 'languages', ['en']),
                    'shift_start': getattr(selected_agent, 'shift_start', 'N/A'),
                    'shift_end': getattr(selected_agent, 'shift_end', 'N/A'),
                    'metadata': getattr(selected_agent, 'metadata', {})
                }
            
            if selected_agent:
                logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 👤 Assigned to: {selected_agent['name']}")
                response = f"I understand you're experiencing significant frustration. I'm immediately connecting you with {selected_agent['name']}, one of our human specialists who can provide the personalized assistance you need."
            else:
                logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No agents available - customer queued")
                response = "I understand your frustration and want to help immediately. I'm placing you in priority queue for our next available human specialist. You should be connected within the next few minutes."
            
        else:
            # Step 4: Generate Chatbot Response (only if no early escalation)
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 Generating AI response...")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, "", context_display, "", "", "")
            
            chatbot_state = system['chatbot_agent'](frustration_state)
            ai_response = chatbot_state.get('ai_response', 'I apologize, but I encountered an error generating a response.')
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Response generated ({len(ai_response)} chars)")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, "", context_display, "", "", "")
            
            # Step 5: Quality Analysis
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Assessing response quality...")
            analyzing_quality = format_analysis_display({"status": "Analyzing..."}, "✅ Quality Analysis", "quality_agent")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, analyzing_quality, context_display, "", "", "")
            
            quality_state = system['quality_agent'](chatbot_state)
            quality_analysis = quality_state.get('quality_assessment', {})
            quality_decision = quality_analysis.get('decision', 'approve')
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Quality decision: {quality_decision}")
            quality_display = format_analysis_display(quality_analysis, "✅ Quality Analysis", "quality_agent")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, quality_display, context_display, "", "", "")
            
            # Use adjusted response if available
            if quality_analysis.get('adjusted_response'):
                response = quality_analysis['adjusted_response']
                logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Response adjusted by QualityAgent")
            else:
                response = ai_response
            
            # Step 6: Check for Final Escalation
            if check_final_escalation(frustration_analysis, quality_analysis):
                logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Final escalation triggered")
                yield ("", new_history, format_logs_display(logs_state), frustration_display, quality_display, context_display, "", "", "")
                
                # Run human routing
                routing_state = system['human_routing_agent'](quality_state)
                escalation_context = routing_state.get('routing_decision', {})
                selected_agent = routing_state.get('assigned_human_agent')
                
                # Convert agent object to dict if needed
                if selected_agent and hasattr(selected_agent, '__dict__'):
                    selected_agent = {
                        'id': getattr(selected_agent, 'id', ''),
                        'name': getattr(selected_agent, 'name', ''),
                        'email': getattr(selected_agent, 'email', ''),
                        'status': getattr(selected_agent, 'status', 'available'),
                        'specializations': getattr(selected_agent, 'specializations', []),
                        'max_concurrent_conversations': getattr(selected_agent, 'max_concurrent_conversations', 5),
                        'experience_level': getattr(selected_agent, 'experience_level', 1),
                        'languages': getattr(selected_agent, 'languages', ['en']),
                        'shift_start': getattr(selected_agent, 'shift_start', 'N/A'),
                        'shift_end': getattr(selected_agent, 'shift_end', 'N/A'),
                        'metadata': getattr(selected_agent, 'metadata', {})
                    }
                
                if selected_agent:
                    logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 👤 Assigned to: {selected_agent['name']}")
                    # Append escalation notice to the response
                    response += f"\n\nI'm also connecting you with {selected_agent['name']}, one of our human specialists, to ensure you receive the best possible assistance."
                else:
                    logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No agents available - customer queued")
                    response += "\n\nI'm also placing you in our priority queue to connect with a human specialist who can provide additional assistance."
        
        # Add the AI response to history
        final_history = new_history + [{'role': 'assistant', 'content': response}]
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Processing complete")
        
        # Keep logs manageable
        if len(logs_state) > 50:
            logs_state = logs_state[-50:]
        
    except Exception as e:
        error_msg = f"I apologize, but I encountered an error processing your request: {str(e)}"
        final_history = new_history + [{'role': 'assistant', 'content': error_msg}]
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Error: {str(e)}")
        frustration_analysis = {}
        quality_analysis = {}
        escalation_context = {}
        context_data = {}
        context_summaries = {}
        selected_agent = None
        response = error_msg
    
    # Format displays
    logs_display = format_logs_display(logs_state)
    frustration_display = format_analysis_display(frustration_analysis, "😠 Frustration Analysis", "frustration_agent")
    quality_display = format_analysis_display(quality_analysis, "✅ Quality Analysis", "quality_agent")
    context_display = format_context_display(context_data, context_summaries)
    human_roster_display = format_human_roster(human_agents, selected_agent['id'] if selected_agent else None)
    agent_profile_display = format_agent_profile(selected_agent)
    escalation_context_display = format_escalation_context(escalation_context, message, conversation_history)
    
    # Final yield with all results
    yield ("", final_history, logs_display, frustration_display, quality_display, context_display, human_roster_display, agent_profile_display, escalation_context_display)

def process_user_input(message: str, history: List[Dict], logs_state: List[str], use_context_manager: bool = False) -> Tuple[str, List[Dict], str, str, str, str, str, str, str]:
    """
    Wrapper function for synchronous processing with real-time updates
    """
    # Get the final result from the generator
    final_result = None
    for result in process_user_input_with_realtime_updates(message, history, logs_state, use_context_manager):
        final_result = result
    
    return final_result

def create_interface():
    """Create the Gradio interface"""
    
    # Custom CSS for better styling with auto-scrolling logs
    css = """
    .chatbot-container .message-wrap .message {
        font-size: 14px !important;
    }
    .analysis-panel {
        height: 300px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
        background-color: #f8f9fa;
    }
    .logs-panel {
        height: 420px;
        overflow-y: scroll;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
        background-color: #f0f2f6;
        font-family: monospace;
        font-size: 12px;
    }
    .logs-panel textarea {
        height: 100% !important;
        overflow-y: scroll !important;
        scrollbar-width: thin;
        scrollbar-color: #888 #f0f2f6;
    }
    .logs-panel textarea::-webkit-scrollbar {
        width: 8px;
    }
    .logs-panel textarea::-webkit-scrollbar-track {
        background: #f0f2f6;
    }
    .logs-panel textarea::-webkit-scrollbar-thumb {
        background-color: #888;
        border-radius: 4px;
    }
    """
    
    
    with gr.Blocks(css=css, title="HITL System Demo", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🤖 VIA - Agent Technical Demo")
        gr.Markdown("A 'Behind the Scenes' look at the agents working together.")
        gr.Markdown("As proof of concept, foundation LLM models are used to simulate custom models.")
        gr.Markdown("These are not as performant as what specialized, custom models would be.")

        # State for logs
        logs_state = gr.State([])
        
        # Configuration controls
        with gr.Row():
            with gr.Column():
                context_toggle = gr.Checkbox(
                    label="🔍 Enable Context Manager Agent",
                    value=False,
                    info="Toggle to enable/disable context gathering for enhanced responses (may increase response time)"
                )
            with gr.Column():
                restart_btn = gr.Button("🔄 Restart New Conversation", size="sm", variant="secondary")
        
        # Main layout: Chat + Logs on top row
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 💬 Chat Window")
                chatbot = gr.Chatbot(
                    height=400,
                    show_label=False,
                    container=True,
                    type="messages"
                )
                with gr.Row():
                    msg = gr.Textbox(
                        placeholder="Ask a question or describe your issue...",
                        show_label=False,
                        container=False,
                        scale=4
                    )
                    submit_btn = gr.Button("Send", variant="primary", size="sm", scale=1)
                
            with gr.Column(scale=1):
                gr.Markdown("### 📋 System Logs")
                logs_display = gr.Textbox(
                    value="System ready...",
                    show_label=False,
                    interactive=False,
                    lines=20,
                    max_lines=65,
                    elem_classes=["logs-panel"]
                )
                clear_logs_btn = gr.Button("Clear Logs", size="sm")
        
        # Analysis panels row
        with gr.Row():
            with gr.Column():
                frustration_display = gr.Textbox(
                    label="😠 Frustration Analysis",
                    value=format_analysis_display({}, "😠 Frustration Analysis", "frustration_agent"),
                    interactive=False,
                    lines=12,
                    max_lines=12,
                    elem_classes=["analysis-panel"]
                )
                
            with gr.Column():
                quality_display = gr.Textbox(
                    label="✅ Quality Analysis", 
                    value=format_analysis_display({}, "✅ Quality Analysis", "quality_agent"),
                    interactive=False,
                    lines=12,
                    max_lines=12,
                    elem_classes=["analysis-panel"]
                )
                
            with gr.Column():
                context_display = gr.Textbox(
                    label="🔍 Context Information",
                    value=format_context_display({}, {}),
                    interactive=False,
                    lines=12,
                    max_lines=12,
                    elem_classes=["analysis-panel"]
                )
        
        # Human routing panels row
        with gr.Row():
            with gr.Column():
                human_roster_display = gr.Textbox(
                    label="👥 Human Agent Roster",
                    value="Loading agents...",
                    interactive=False,
                    lines=12,
                    max_lines=12,
                    elem_classes=["analysis-panel"]
                )
                
            with gr.Column():
                agent_profile_display = gr.Textbox(
                    label="👤 Selected Agent Profile",
                    value="No agent selected",
                    interactive=False,
                    lines=12,
                    max_lines=12,
                    elem_classes=["analysis-panel"]
                )
                
            with gr.Column():
                escalation_context_display = gr.Textbox(
                    label="📋 Escalation Context",
                    value="No escalation context",
                    interactive=False,
                    lines=12,
                    max_lines=12,
                    elem_classes=["analysis-panel"]
                )
        
        # Event handlers with real-time updates
        def process_with_updates(message, history, logs_state, use_context_manager):
            """Process user input with real-time UI updates"""
            # Use the generator function for real-time updates
            yield from process_user_input_with_realtime_updates(message, history, logs_state, use_context_manager)
        
        # Handle both submit (Enter) and button click
        msg.submit(
            process_with_updates,
            inputs=[msg, chatbot, logs_state, context_toggle],
            outputs=[msg, chatbot, logs_display, frustration_display, quality_display, 
                    context_display, human_roster_display, agent_profile_display, escalation_context_display],
            queue=True
        )
        
        submit_btn.click(
            process_with_updates,
            inputs=[msg, chatbot, logs_state, context_toggle],
            outputs=[msg, chatbot, logs_display, frustration_display, quality_display, 
                    context_display, human_roster_display, agent_profile_display, escalation_context_display],
            queue=True
        )
        
        def clear_logs(_logs_state):
            return [], "Logs cleared..."
        
        clear_logs_btn.click(
            clear_logs,
            inputs=[logs_state],
            outputs=[logs_state, logs_display]
        )
        
        def restart_conversation():
            """Restart the conversation by clearing all state and displays"""
            # Clear logs state
            empty_logs = []
            
            # Reset all analysis displays
            frustration_init = format_analysis_display({}, "😠 Frustration Analysis", "frustration_agent")
            quality_init = format_analysis_display({}, "✅ Quality Analysis", "quality_agent")
            context_init = format_context_display({}, {})
            
            # Reset human agent displays
            agents = get_human_agents()
            human_roster_init = format_human_roster(agents)
            agent_profile_init = format_agent_profile(None)
            escalation_context_init = format_escalation_context({}, "", [])
            
            return (
                [],  # Clear chatbot history
                empty_logs,  # Clear logs state
                "System ready...",  # Reset logs display
                frustration_init,
                quality_init,
                context_init,
                human_roster_init,
                agent_profile_init,
                escalation_context_init
            )
        
        restart_btn.click(
            restart_conversation,
            outputs=[
                chatbot, 
                logs_state, 
                logs_display, 
                frustration_display, 
                quality_display,
                context_display,
                human_roster_display, 
                agent_profile_display, 
                escalation_context_display
            ]
        )
        
        # Initialize displays on load
        def init_display():
            agents = get_human_agents()
            # Also refresh the analysis panels with model information once system is initialized
            frustration_init = format_analysis_display({}, "😠 Frustration Analysis", "frustration_agent")
            quality_init = format_analysis_display({}, "✅ Quality Analysis", "quality_agent")
            context_init = format_context_display({}, {})
            return format_human_roster(agents), frustration_init, quality_init, context_init
        
        interface.load(
            init_display,
            outputs=[human_roster_display, frustration_display, quality_display, context_display]
        )
    
    return interface

if __name__ == "__main__":
    # Initialize system on startup
    print("Initializing HITL system...")
    system = initialize_system()
    
    if system.get('initialized'):
        print("✅ System initialized successfully")
        interface = create_interface()
        interface.queue(max_size=10)
        interface.launch(
            share=False,
            server_name="0.0.0.0",
            server_port=7860,
            show_error=True
        )
    else:
        print(f"❌ System initialization failed: {system.get('error', 'Unknown error')}")