"""
Gradio Demo App for HITL System
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

def get_human_agents() -> List[Dict[str, Any]]:
    """Fetch all human agents from the database"""
    try:
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

def format_analysis_display(analysis: Dict[str, Any], title: str) -> str:
    """Format analysis results for display"""
    if not analysis:
        return f"**{title}**\n\nNo analysis available"
    
    # Handle loading state
    if analysis.get('status') == 'Analyzing...':
        return f"**{title}**\n\n🔍 Analyzing..."
    
    result = f"**{title}**\n\n"
    
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
    
    # Show last 15 logs for readability
    recent_logs = logs[-15:]
    return "\n".join(recent_logs)

def format_human_roster(agents: List[Dict], selected_agent_id: Optional[str] = None) -> str:
    """Format human agent roster for display"""
    if not agents:
        return "No agents available"
    
    result = "**👥 Available Agents**\n\n"
    
    for agent in agents:
        status_emoji = {"available": "🟢", "busy": "🔴", "break": "🟡", "offline": "⚫"}.get(agent['status'], "⚪")
        selected_marker = "👉 " if agent['id'] == selected_agent_id else ""
        
        result += f"{selected_marker}**{agent['name']}** {status_emoji}\n"
        result += f"Status: {agent['status'].title()}\n"
        result += f"Specializations: {', '.join(agent.get('specializations', []))}\n"
        result += f"Experience: Level {agent.get('experience_level', 1)}\n\n"
    
    return result

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

def format_escalation_context(context: Dict[str, Any], query: str, conversation_history: List[Dict]) -> str:
    """Format escalation context for human agent"""
    if not context:
        return "**📋 Escalation Context**\n\nNo escalation context available"
    
    result = "**📋 Escalation Context**\n\n"
    
    routing_requirements = context.get('routing_requirements', {})
    
    result += f"**🎯 Escalation Summary**\n"
    result += f"Reason: {routing_requirements.get('escalation_type', 'general_escalation')}\n"
    result += f"Priority: {routing_requirements.get('priority', 'high')}\n"
    result += f"Complexity: {routing_requirements.get('complexity', 'low')}\n"
    result += f"Est. Resolution: {context.get('estimated_resolution_time', 15)} minutes\n\n"
    
    result += f"**💬 Current Issue**\n{query}\n\n"
    
    if conversation_history:
        result += f"**📝 Recent Conversation (last 3 messages)**\n"
        for msg in conversation_history[-3:]:
            role = "Customer" if msg['role'] == 'user' else "AI Assistant"
            content = msg['content'][:150] + '...' if len(msg['content']) > 150 else msg['content']
            result += f"**{role}:** {content}\n\n"
    
    result += f"**🎯 Match Score:** {context.get('agent_match_score', 100.0):.1f}%\n"
    
    return result

def process_user_input_with_realtime_updates(message: str, history: List[Dict], logs_state: List[str]):
    """
    Process user input through the optimized HITL system with real-time UI updates via generator
    Yields: (msg_input, updated_history, logs, frustration_analysis, quality_analysis, human_roster, agent_profile, escalation_context)
    """
    global system
    
    # Show user input immediately
    new_history = history + [{'role': 'user', 'content': message}]
    yield ("", new_history, "Processing...", "", "", "", "", "")
    
    if not system or not system.get('initialized'):
        system = initialize_system()
        if not system.get('initialized'):
            error_msg = "System initialization failed. Please refresh and try again."
            error_history = new_history + [{'role': 'assistant', 'content': error_msg}]
            yield ("", error_history, format_logs_display(logs_state), "", "", "", "", "")
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
    selected_agent = None
    human_agents = get_human_agents()
    
    try:
        # Add processing start log
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Processing: '{message[:50]}...'")
        yield ("", new_history, format_logs_display(logs_state), "", "", "", "", "")
        
        # Create state for processing
        state = create_state(message, user_id, session_id, conversation_history)
        
        # Step 1: Context Gathering (TEMPORARILY DISABLED FOR PERFORMANCE)
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Context gathering disabled (performance optimization)")
        yield ("", new_history, format_logs_display(logs_state), "", "", "", "", "")
        
        # Skip context gathering - use state directly
        context_state = state.copy()
        context_state['context_summaries'] = {}
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Context step skipped")
        yield ("", new_history, format_logs_display(logs_state), "", "", "", "", "")
        
        # Step 2: Frustration Analysis
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 😠 Analyzing frustration level...")
        yield ("", new_history, format_logs_display(logs_state), "🔍 Analyzing...", "", "", "", "")
        
        frustration_state = system['frustration_agent'](context_state)
        frustration_analysis = frustration_state.get('frustration_analysis', {})
        frustration_level = frustration_analysis.get('overall_level', 'low')
        logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Frustration level: {frustration_level}")
        frustration_display = format_analysis_display(frustration_analysis, "😠 Frustration Analysis")
        yield ("", new_history, format_logs_display(logs_state), frustration_display, "", "", "", "")
        
        # Step 3: Check for Early Escalation (OPTIMIZATION: Skip chatbot/quality if critical frustration)
        if check_early_escalation(frustration_analysis):
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Early escalation triggered - bypassing chatbot/quality")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, "", "", "", "")
            
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
            yield ("", new_history, format_logs_display(logs_state), frustration_display, "", "", "", "")
            
            chatbot_state = system['chatbot_agent'](frustration_state)
            ai_response = chatbot_state.get('ai_response', 'I apologize, but I encountered an error generating a response.')
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Response generated ({len(ai_response)} chars)")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, "", "", "", "")
            
            # Step 5: Quality Analysis
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Assessing response quality...")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, "🔍 Analyzing...", "", "", "")
            
            quality_state = system['quality_agent'](chatbot_state)
            quality_analysis = quality_state.get('quality_assessment', {})
            quality_decision = quality_analysis.get('decision', 'approve')
            logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Quality decision: {quality_decision}")
            quality_display = format_analysis_display(quality_analysis, "✅ Quality Analysis")
            yield ("", new_history, format_logs_display(logs_state), frustration_display, quality_display, "", "", "")
            
            # Use adjusted response if available
            if quality_analysis.get('adjusted_response'):
                response = quality_analysis['adjusted_response']
                logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] Response adjusted by QualityAgent")
            else:
                response = ai_response
            
            # Step 6: Check for Final Escalation
            if check_final_escalation(frustration_analysis, quality_analysis):
                logs_state.append(f"[{datetime.now().strftime('%H:%M:%S')}] 🚨 Final escalation triggered")
                yield ("", new_history, format_logs_display(logs_state), frustration_display, quality_display, "", "", "")
                
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
        selected_agent = None
        response = error_msg
    
    # Format displays
    logs_display = format_logs_display(logs_state)
    frustration_display = format_analysis_display(frustration_analysis, "😠 Frustration Analysis")
    quality_display = format_analysis_display(quality_analysis, "✅ Quality Analysis")
    human_roster_display = format_human_roster(human_agents, selected_agent['id'] if selected_agent else None)
    agent_profile_display = format_agent_profile(selected_agent)
    escalation_context_display = format_escalation_context(escalation_context, message, conversation_history)
    
    # Final yield with all results
    yield ("", final_history, logs_display, frustration_display, quality_display, human_roster_display, agent_profile_display, escalation_context_display)

def process_user_input(message: str, history: List[Dict], logs_state: List[str]) -> Tuple[str, List[Dict], str, str, str, str, str]:
    """
    Wrapper function for synchronous processing with real-time updates
    """
    # This will store intermediate updates
    updates = {}
    
    def progress_callback(msg, hist, logs, frust, qual, roster, prof, esc):
        """Update intermediate results"""
        if logs is not None:
            updates['logs'] = logs
        if frust is not None:
            updates['frustration'] = frust
        if qual is not None:
            updates['quality'] = qual
        if roster is not None:
            updates['roster'] = roster
        if prof is not None:
            updates['profile'] = prof
        if esc is not None:
            updates['escalation'] = esc
    
    return process_user_input_async(message, history, logs_state, progress_callback)

def create_interface():
    """Create the Gradio interface"""
    
    # Custom CSS for better styling
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
        height: 300px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
        background-color: #f0f2f6;
        font-family: monospace;
        font-size: 12px;
    }
    """
    
    with gr.Blocks(css=css, title="HITL System Demo", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🤖 HITL System Demo")
        gr.Markdown("Interactive demonstration of ChatbotAgent, FrustrationAgent, QualityAgent, and HumanRoutingAgent with optimized processing logic")
        
        # State for logs
        logs_state = gr.State([])
        
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
                msg = gr.Textbox(
                    placeholder="Ask a question or describe your issue...",
                    show_label=False,
                    container=False
                )
                
            with gr.Column(scale=1):
                gr.Markdown("### 📋 System Logs")
                logs_display = gr.Textbox(
                    value="System ready...",
                    show_label=False,
                    interactive=False,
                    lines=15,
                    max_lines=15,
                    elem_classes=["logs-panel"]
                )
                clear_logs_btn = gr.Button("Clear Logs", size="sm")
        
        # Analysis panels row
        with gr.Row():
            with gr.Column():
                frustration_display = gr.Textbox(
                    label="😠 Frustration Analysis",
                    value="No analysis yet...",
                    interactive=False,
                    lines=12,
                    max_lines=12,
                    elem_classes=["analysis-panel"]
                )
                
            with gr.Column():
                quality_display = gr.Textbox(
                    label="✅ Quality Analysis", 
                    value="No analysis yet...",
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
        def process_with_updates(message, history, logs_state):
            """Process user input with real-time UI updates"""
            # Use the generator function for real-time updates
            yield from process_user_input_with_realtime_updates(message, history, logs_state)
        
        msg.submit(
            process_with_updates,
            inputs=[msg, chatbot, logs_state],
            outputs=[msg, chatbot, logs_display, frustration_display, quality_display, 
                    human_roster_display, agent_profile_display, escalation_context_display],
            queue=True
        )
        
        def clear_logs(logs_state):
            return [], "Logs cleared..."
        
        clear_logs_btn.click(
            clear_logs,
            inputs=[logs_state],
            outputs=[logs_state, logs_display]
        )
        
        # Initialize human roster on load
        def init_display():
            agents = get_human_agents()
            return format_human_roster(agents)
        
        interface.load(
            init_display,
            outputs=[human_roster_display]
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