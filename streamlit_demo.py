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
from src.nodes.chatbot_agent import ChatbotAgentNode
from src.nodes.frustration_agent import FrustrationAgentNode
from src.nodes.quality_agent import QualityAgentNode
from src.interfaces.core.state_schema import HybridSystemState

# Initialize logging with a basic config
logging_config = {
    "level": "INFO",
    "console": {"enabled": True, "level": "INFO"},
    "file": {"enabled": False}  # Disable file logging for demo
}
configure_logging(logging_config)
logger = get_logger(__name__)

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
        chatbot_agent = ChatbotAgentNode(config_manager, context_manager)
        frustration_agent = FrustrationAgentNode(config_manager, context_manager)
        quality_agent = QualityAgentNode(config_manager, context_manager)
        
        return {
            'config_manager': config_manager,
            'context_manager': context_manager,
            'chatbot_agent': chatbot_agent,
            'frustration_agent': frustration_agent,
            'quality_agent': quality_agent,
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
            chat_messages_html += f'<div class="chat-message bot-message"><strong>Assistant:</strong> {msg["content"]}</div>'
    
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
        
        st.markdown(f'<div class="analysis-container">{analysis_html}</div>', unsafe_allow_html=True)

def process_user_input_realtime(user_input: str, system: Dict[str, Any], status_placeholder, chat_placeholder, logs_placeholder, frustration_placeholder, quality_placeholder):
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
        # Step 1: Frustration Analysis with real-time updates
        status_placeholder.info("🔍 Analyzing frustration level...")
        add_log_entry("Running FrustrationAgent analysis...")
        add_log_entry(f"LLM Provider: {system['frustration_agent'].llm_provider.model_name if system['frustration_agent'].llm_provider else 'None'}")
        update_logs_display(logs_placeholder)
        
        # Clear previous analysis and show loading state
        st.session_state.current_frustration_analysis = {"status": "Analyzing..."}
        update_frustration_display(frustration_placeholder)
        
        # Run frustration analysis
        frustration_state = system['frustration_agent'](state)
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
        
        # Update bot response in real-time
        st.session_state.conversation_history[-1]['content'] = ai_response
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
            update_chat_display(chat_placeholder)
            
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

def process_user_input_parallel(user_input: str, system: Dict[str, Any], status_placeholder, chat_placeholder, logs_placeholder, frustration_placeholder, quality_placeholder):
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
            # Submit both tasks
            frustration_future = executor.submit(system['frustration_agent'], state)
            chatbot_future = executor.submit(system['chatbot_agent'], state)  # Run on original state
            
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
            update_chat_display(chat_placeholder)
            
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
    st.markdown("Interactive demonstration of ChatbotAgent, FrustrationAgent, and QualityAgent")
    
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
    
    add_log_entry("System initialized successfully")
    add_log_entry(f"User ID: {st.session_state.user_id}")
    add_log_entry(f"Session ID: {st.session_state.session_id}")
    
    # Create layout - 4 windows
    # Top row: Chat (left) and Logging (right)
    col1, col2 = st.columns([2, 1])
    
    # Bottom row: Frustration Analysis (left) and Quality Analysis (right)
    st.markdown("---")
    col3, col4 = st.columns(2)
    
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
                    process_user_input_parallel(user_input, system, status_area, chat_placeholder, logs_placeholder, frustration_placeholder, quality_placeholder)
                else:
                    # For both Standard and Fast modes, use the same function but different prompt selection is handled in agents
                    process_user_input_realtime(user_input, system, status_area, chat_placeholder, logs_placeholder, frustration_placeholder, quality_placeholder)
                    
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


if __name__ == "__main__":
    main()