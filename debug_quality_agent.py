#!/usr/bin/env python3
"""
Debug script to test Quality Agent LLM assessment
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.config import ConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.nodes.quality_agent import QualityAgentNode
from src.interfaces.core.state_schema import HybridSystemState
from datetime import datetime

def test_quality_agent():
    """Test the quality agent with a simple example"""
    
    # Initialize components
    config_manager = ConfigManager(config_dir=Path(__file__).parent / "config")
    context_provider = SQLiteContextProvider(db_path=":memory:")
    quality_agent = QualityAgentNode(config_manager, context_provider)
    
    print("🔧 Quality Agent Debug Test")
    print("=" * 50)
    
    # Print configuration info
    print(f"Agent config loaded: {quality_agent.agent_config is not None}")
    print(f"LLM provider loaded: {quality_agent.llm_provider is not None}")
    
    if quality_agent.llm_provider:
        print(f"LLM model: {quality_agent.llm_provider.model_name}")
        print(f"Provider type: {quality_agent.llm_provider.provider_type}")
    
    # Test prompt retrieval and debug the structure
    try:
        print(f"\n🔍 Debug: Agent config prompts structure:")
        print(f"Prompts object: {quality_agent.agent_config.prompts}")
        print(f"Prompts keys: {list(quality_agent.agent_config.prompts.keys())}")
        
        system_prompt = quality_agent.agent_config.get_prompt("system")
        assessment_prompt = quality_agent.agent_config.get_prompt("quality_assessment")
        
        print(f"\nSystem prompt length: {len(system_prompt)}")
        print(f"Assessment prompt length: {len(assessment_prompt)}")
        print(f"System prompt preview: {system_prompt[:100]}...")
        print(f"Assessment prompt preview: {assessment_prompt[:100]}...")
        
    except Exception as e:
        print(f"❌ Error getting prompts: {e}")
        return
    
    # Test with a simple case
    test_query = "Why did my premium increase?"
    test_response = "Your premium increased due to market factors and claims experience."
    
    # Create test state
    test_state = HybridSystemState({
        "query_id": "debug_test_001",
        "user_id": "debug_user",
        "session_id": "debug_session",
        "timestamp": datetime.now(),
        "query": test_query,
        "ai_response": test_response,
    })
    
    print(f"\n🧪 Test Case:")
    print(f"Query: {test_query}")
    print(f"Response: {test_response}")
    
    # Format the assessment prompt to see what gets sent to LLM
    formatted_prompt = assessment_prompt.format(
        customer_query=test_query,
        chatbot_response=test_response
    )
    
    print(f"\n📝 Formatted Prompt to LLM:")
    print(f"{formatted_prompt}")
    print(f"\n📝 System Prompt:")
    print(f"{system_prompt}")
    
    # Test LLM call directly
    if quality_agent.llm_provider:
        print(f"\n🤖 Testing direct LLM call...")
        try:
            llm_response = quality_agent.llm_provider.generate_response(
                prompt=formatted_prompt,
                system_prompt=system_prompt
            )
            
            print(f"LLM Response:")
            print(f"{llm_response}")
            print(f"Response length: {len(llm_response)}")
            
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Test the full quality agent
    print(f"\n🔍 Testing full Quality Agent assessment...")
    try:
        result = quality_agent(test_state)
        
        quality_assessment = result.get('quality_assessment', {})
        
        print(f"Quality Decision: {quality_assessment.get('decision', 'N/A')}")
        print(f"Overall Score: {quality_assessment.get('overall_score', 'N/A')}")
        print(f"Confidence: {quality_assessment.get('confidence', 'N/A')}")
        print(f"Reasoning: {quality_assessment.get('reasoning', 'N/A')[:200]}...")
        print(f"Next Action: {result.get('next_action', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Quality agent assessment failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quality_agent()