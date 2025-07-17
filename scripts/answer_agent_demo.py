#!/usr/bin/env python3
"""
Answer Agent Demo Script

This demo script loads the Answer Agent, sends it a test question,
and displays the AI response along with key agent settings.

Usage:
    python scripts/answer_agent_demo.py
"""

import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.core.config.agent_config_manager import AgentConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.nodes.answer_agent import AnswerAgentNode
from src.interfaces.core.state_schema import HybridSystemState


def create_test_state(query: str) -> HybridSystemState:
    """Create a test state for the demo"""
    return {
        "query_id": str(uuid4()),
        "user_id": "demo_user",
        "session_id": f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "query": query,
        "timestamp": datetime.now(timezone.utc),
        "messages": [],
        "context": {},
        "metadata": {"demo": True},
        "next_action": "answer"
    }


def display_agent_settings(agent_config):
    """Display key agent configuration settings"""
    print("\n" + "="*60)
    print("ANSWER AGENT CONFIGURATION")
    print("="*60)
    
    # Agent info
    print(f"Agent Name: {agent_config.name}")
    print(f"Version: {agent_config.version}")
    print(f"Description: {agent_config.description}")
    print(f"Type: {agent_config.type}")
    
    # Model configuration
    print(f"\nPreferred Model: {agent_config.get_preferred_model()}")
    fallback_models = agent_config.get_fallback_models()
    print(f"Fallback Models: {', '.join(fallback_models) if fallback_models else 'None configured'}")
    
    # Settings
    print(f"\nTemperature: {agent_config.settings.get('temperature', 'Not set')}")
    print(f"Max Tokens: {agent_config.settings.get('max_tokens', 'Not set')}")
    print(f"Timeout: {agent_config.settings.get('timeout', 'Not set')}s")
    print(f"Max Retries: {agent_config.settings.get('max_retries', 'Not set')}")
    
    # Behavior settings
    print(f"\nContext Integration: {agent_config.behavior.get('context_integration', False)}")
    print(f"Response Style: {agent_config.behavior.get('response_style', 'Not set')}")
    print(f"Personalization: {agent_config.behavior.get('personalization', False)}")
    
    # Escalation settings
    print(f"\nConfidence Threshold: {agent_config.escalation.get('confidence_threshold', 'Not set')}")
    print(f"Auto-escalation: {agent_config.escalation.get('enable_auto_escalation', False)}")
    
    print("="*60)


def main():
    """Main demo function"""
    print("Answer Agent Demo")
    print("="*40)
    
    try:
        # Initialize configuration manager
        print("Initializing configuration manager...")
        config_dir = os.path.join(project_root, "config")
        config_manager = AgentConfigManager(config_dir)
        
        # Initialize context manager
        print("Initializing context manager...")
        context_manager = SQLiteContextProvider("demo_system.db")
        
        # Create answer agent
        print("Creating Answer Agent...")
        answer_agent = AnswerAgentNode(config_manager, context_manager)
        
        # Display agent configuration
        display_agent_settings(answer_agent.agent_config)
        
        # Test questions  
        test_questions = [
            "What is the capital of France?"
        ]
        
        print("\n" + "="*60)
        print("DEMO INTERACTIONS")
        print("="*60)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n--- Test Question {i} ---")
            print(f"Question: {question}")
            
            # Create test state
            state = create_test_state(question)
            
            # Get response from agent
            print("\nProcessing...")
            response_state = answer_agent(state)
            
            # Display response
            print(f"\nAI Response:")
            print("-" * 40)
            print(response_state.get("ai_response", "No response generated"))
            print("-" * 40)
            
            # Display assessment info
            assessment = response_state.get("initial_assessment", {})
            print(f"\nResponse Assessment:")
            print(f"  Context Used: {assessment.get('context_used', 'Unknown')}")
            print(f"  Confidence: {assessment.get('confidence', 'Unknown')}")
            print(f"  Response Time: {assessment.get('response_time', 'Unknown')}s")
            print(f"  Next Action: {response_state.get('next_action', 'Unknown')}")
            
            # Brief pause between questions for readability
            if i < len(test_questions):
                print("\n" + "-"*40 + "\n")
        
        print("\n" + "="*60)
        print("Demo completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        print("Please check your configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()