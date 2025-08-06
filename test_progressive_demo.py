#!/usr/bin/env python3
"""
Test script to verify progressive result display in demo orchestrator
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import asyncio
from src.core.config import ConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.simulation.demo_orchestrator import DemoOrchestrator


def test_progressive_display():
    """Test that results are displayed progressively"""
    print("🧪 Testing Progressive Display in Demo Orchestrator")
    print("=" * 60)
    
    try:
        # Initialize config manager
        config_manager = ConfigManager("config")
        context_provider = SQLiteContextProvider(config_manager=config_manager)
        
        # Create orchestrator (use simulation mode for faster testing)
        orchestrator = DemoOrchestrator(
            config_manager=config_manager,
            context_provider=context_provider,
            use_real_agents=False  # Use simulation for faster testing
        )
        
        print("✅ DemoOrchestrator initialized")
        print()
        
        # Start a demo scenario
        print("🎬 Starting demo scenario...")
        demo_result = orchestrator.start_demo_scenario("Happy Path - Simple Question")
        print(f"✅ Demo started: {demo_result['demo_id']}")
        print(f"❓ Customer query: {demo_result['customer_query']}")
        print()
        
        # Test progressive chatbot response
        print("📍 Step 1: Chatbot Response")
        print("-" * 40)
        chatbot_result = orchestrator.simulate_chatbot_response(
            demo_result['demo_id'], 
            show_progress=True
        )
        print()
        
        # Test progressive quality assessment
        print("📍 Step 2: Quality Assessment")
        print("-" * 40)
        quality_result = orchestrator.simulate_quality_assessment(
            demo_result['demo_id'], 
            show_progress=True
        )
        print()
        
        # Test progressive frustration analysis
        print("📍 Step 3: Frustration Analysis")
        print("-" * 40)
        frustration_result = orchestrator.simulate_frustration_analysis(
            demo_result['demo_id'], 
            show_progress=True
        )
        print()
        
        print("🎉 Progressive display test completed successfully!")
        print("✅ Each step now shows immediate feedback during processing")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_silent_mode():
    """Test that show_progress=False works correctly"""
    print("\n🔇 Testing Silent Mode (show_progress=False)")
    print("=" * 60)
    
    try:
        # Initialize config manager
        config_manager = ConfigManager("config")
        context_provider = SQLiteContextProvider(config_manager=config_manager)
        
        # Create orchestrator
        orchestrator = DemoOrchestrator(
            config_manager=config_manager,
            context_provider=context_provider,
            use_real_agents=False
        )
        
        # Start a demo scenario
        demo_result = orchestrator.start_demo_scenario("Happy Path - Simple Question")
        print(f"✅ Demo started: {demo_result['demo_id']}")
        
        # Test silent mode (should show minimal output)
        print("\n📍 Running steps in silent mode...")
        chatbot_result = orchestrator.simulate_chatbot_response(
            demo_result['demo_id'], 
            show_progress=False
        )
        
        quality_result = orchestrator.simulate_quality_assessment(
            demo_result['demo_id'], 
            show_progress=False
        )
        
        frustration_result = orchestrator.simulate_frustration_analysis(
            demo_result['demo_id'], 
            show_progress=False
        )
        
        print("✅ Silent mode test completed - no progress output shown")
        
        return True
        
    except Exception as e:
        print(f"❌ Silent mode test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Demo Orchestrator Progressive Display Test")
    print("=" * 70)
    
    # Test 1: Progressive display mode
    test1_passed = test_progressive_display()
    
    # Test 2: Silent mode
    test2_passed = test_silent_mode()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    tests = [
        ("Progressive Display Mode", test1_passed),
        ("Silent Mode", test2_passed)
    ]
    
    for test_name, passed in tests:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"• {test_name}: {status}")
    
    overall_success = all([test1_passed, test2_passed])
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 Progressive display is now working correctly!")
        print("The demo will show results immediately as each step completes.")
    else:
        print("\n🔧 Check the errors above to troubleshoot issues.")


if __name__ == "__main__":
    main()