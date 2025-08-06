#!/usr/bin/env python3
"""
Basic test for Gradio demo functionality
"""

import sys
import os
sys.path.append('.')

from gradio_demo import initialize_system, process_user_input, get_human_agents

def test_system_initialization():
    """Test that the system initializes properly"""
    print("Testing system initialization...")
    system = initialize_system()
    
    if system and system.get('initialized'):
        print("✅ System initialization: PASSED")
        return True
    else:
        print(f"❌ System initialization: FAILED - {system.get('error', 'Unknown error')}")
        return False

def test_human_agents_fetch():
    """Test that human agents can be fetched"""
    print("Testing human agents fetch...")
    try:
        agents = get_human_agents()
        if isinstance(agents, list):
            print(f"✅ Human agents fetch: PASSED - Found {len(agents)} agents")
            if agents:
                print(f"   First agent: {agents[0]['name']} ({agents[0]['id']})")
            return True
        else:
            print("❌ Human agents fetch: FAILED - Not a list")
            return False
    except Exception as e:
        print(f"❌ Human agents fetch: FAILED - {str(e)}")
        return False

def test_basic_processing():
    """Test basic message processing"""
    print("Testing basic message processing...")
    try:
        # Simple test message
        test_message = "Hello, I need help with my account"
        test_history = []
        test_logs = []
        
        result = process_user_input(test_message, test_history, test_logs)
        
        if len(result) == 8:  # Should return 8 values
            response, history, logs, frustration, quality, roster, profile, context = result
            if isinstance(history, list) and len(history) >= 2:
                print("✅ Basic processing: PASSED")
                print(f"   Generated response: {history[-1]['content'][:100]}...")
                return True
            else:
                print("❌ Basic processing: FAILED - Invalid history format")
                return False
        else:
            print(f"❌ Basic processing: FAILED - Expected 8 return values, got {len(result)}")
            return False
            
    except Exception as e:
        print(f"❌ Basic processing: FAILED - {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running Gradio Demo Tests\n")
    
    tests = [
        test_system_initialization,
        test_human_agents_fetch,
        test_basic_processing
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}\n")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Gradio demo is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)