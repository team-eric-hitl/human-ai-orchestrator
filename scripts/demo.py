#!/usr/bin/env python3
"""
Demo script showcasing the modular LangGraph hybrid system

Run with: uv run python scripts/demo.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.workflows.hybrid_workflow import HybridSystemWorkflow

def run_demo():
    """Run a comprehensive demo of the system"""
    
    print("🚀 Modular LangGraph Hybrid System Demo")
    print("=" * 50)
    
    # Initialize the system
    print("\n📦 Initializing system components...")
    hybrid_system = HybridSystemWorkflow(
        config_dir="config",
        context_db="demo_system.db"
    )
    print("✅ System initialized successfully!")
    
    # Demo conversation scenarios
    scenarios = [
        {
            "name": "Simple Query",
            "query": "How do I reset my password?",
            "expected": "AI should handle this easily"
        },
        {
            "name": "Follow-up Query", 
            "query": "That didn't work, can you help me with a different approach?",
            "expected": "Should use context from previous query"
        },
        {
            "name": "Frustration Query",
            "query": "I'm getting frustrated, I need to speak to someone",
            "expected": "Should be escalated to human agent"
        },
        {
            "name": "Technical Query",
            "query": "I'm getting a 500 error when calling the API",
            "expected": "Should be routed to technical agent if escalated"
        }
    ]
    
    user_id = "demo_user"
    session_id = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\n👤 User: {user_id}")
    print(f"🆔 Session: {session_id}")
    print("\n" + "=" * 50)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📝 Scenario {i}: {scenario['name']}")
        print(f"❓ Query: {scenario['query']}")
        print(f"🎯 Expected: {scenario['expected']}")
        
        # Process the query
        start_time = datetime.now()
        result = hybrid_system.process_query(
            query=scenario['query'],
            user_id=user_id,
            session_id=session_id
        )
        end_time = datetime.now()
        
        # Display results
        print(f"⏱️  Processing time: {(end_time - start_time).total_seconds():.2f}s")
        print(f"🆔 Query ID: {result['query_id']}")
        print(f"🤖 Escalated: {'Yes' if result['escalated'] else 'No'}")
        
        if result['escalated']:
            escalation = result['escalation_data']
            print(f"🚨 Priority: {escalation.priority}")
            print(f"👨‍💼 Assigned to: {escalation.suggested_human_id or 'Queue'}")
            print(f"⏰ Est. resolution: {escalation.estimated_resolution_time} minutes")
        else:
            print(f"💬 Response: {result['final_response']}")
        
        if result.get('evaluation_result'):
            eval_result = result['evaluation_result']
            print(f"📊 Evaluation Score: {eval_result.overall_score:.1f}/10")
            print(f"🎯 Confidence: {eval_result.confidence:.2f}")
        
        print("-" * 30)
    
    print("\n🎉 Demo completed!")
    print("\n📊 Key Features Demonstrated:")
    print("✅ Modular node architecture")
    print("✅ Context-aware responses")
    print("✅ Intelligent escalation decisions")
    print("✅ Human agent routing")
    print("✅ Session continuity")
    print("✅ Performance tracking")

if __name__ == "__main__":
    run_demo() 