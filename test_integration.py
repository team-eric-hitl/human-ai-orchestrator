#!/usr/bin/env python3
"""
Integration test for the context display in the HITL demo
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gradio_demo import initialize_system, create_state, format_context_display
import uuid
from datetime import datetime

def test_integration():
    print("Testing Context Display Integration")
    print("=" * 40)
    
    # Initialize the system
    print("Initializing system...")
    system = initialize_system()
    
    if not system.get('initialized'):
        print(f"❌ System initialization failed: {system.get('error', 'Unknown error')}")
        return
    
    print("✅ System initialized successfully")
    
    # Test context manager agent
    print("\nTesting context manager agent...")
    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    query = "I'm having trouble with my billing and need help"
    
    state = create_state(query, user_id, session_id, [])
    
    try:
        # Run context manager agent
        context_state = system['context_manager_agent'](state)
        
        # Extract context information
        context_data = context_state.get('context_data', {})
        context_summaries = context_state.get('context_summaries', {})
        
        print(f"✅ Context manager completed")
        print(f"   - Context data sources: {len(context_data)}")
        print(f"   - Context summaries: {len(context_summaries)}")
        
        # Test display formatting
        print("\nTesting context display formatting...")
        context_display = format_context_display(context_data, context_summaries)
        
        print("✅ Context display generated")
        print(f"   - Display length: {len(context_display)} characters")
        
        # Show sample of the display
        print("\nSample context display:")
        print("-" * 30)
        print(context_display[:500] + "..." if len(context_display) > 500 else context_display)
        print("-" * 30)
        
        print("\n✅ Integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()