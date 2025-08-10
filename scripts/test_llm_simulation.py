#!/usr/bin/env python3
"""
Test LLM-Enhanced Simulation
Tests the simulation with real LLM agents instead of mock responses
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import asyncio
import os
from src.core.config import ConfigManager
from src.core.context_manager import SQLiteContextProvider
from src.simulation.demo_orchestrator import DemoOrchestrator
from src.simulation.test_runner import SimulationTestRunner, TestRunConfig


def check_api_keys():
    """Check if required API keys are available"""
    required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    available_keys = []
    
    for key in required_keys:
        if os.getenv(key):
            available_keys.append(key)
            print(f"✅ {key} is available")
        else:
            print(f"❌ {key} is NOT available")
    
    return len(available_keys) > 0, available_keys


def test_basic_llm_integration():
    """Test basic LLM agent integration"""
    print("\n🧪 Testing Basic LLM Integration")
    print("=" * 50)
    
    try:
        # Initialize config manager
        config_manager = ConfigManager("config")
        context_provider = SQLiteContextProvider(config_manager=config_manager)
        
        # Create orchestrator with real agents enabled
        orchestrator = DemoOrchestrator(
            config_manager=config_manager,
            context_provider=context_provider,
            use_real_agents=True
        )
        
        print("✅ DemoOrchestrator initialized with real agents")
        
        # Test a simple scenario
        print("\nStarting a simple scenario...")
        demo_result = orchestrator.start_demo_scenario("Happy Path - Simple Question")
        print(f"Demo started: {demo_result['demo_id']}")
        print(f"Customer query: {demo_result['customer_query']}")
        
        # Test chatbot response with real LLM (with progressive display)
        print("\n📍 Step 1: Chatbot Response")
        print("-" * 40)
        chatbot_result = orchestrator.simulate_chatbot_response(demo_result['demo_id'], show_progress=True)
        
        # Test quality assessment with real LLM (with progressive display)
        print("\n📍 Step 2: Quality Assessment")
        print("-" * 40)
        quality_result = orchestrator.simulate_quality_assessment(demo_result['demo_id'], show_progress=True)
        
        # Test frustration analysis with real LLM (with progressive display)
        print("\n📍 Step 3: Frustration Analysis")
        print("-" * 40)
        frustration_result = orchestrator.simulate_frustration_analysis(demo_result['demo_id'], show_progress=True)
        
        print("\n✅ Basic LLM integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Basic LLM integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simulation_with_llm_agents():
    """Test full simulation with LLM agents"""
    print("\n🎯 Testing Full Simulation with LLM Agents")
    print("=" * 50)
    
    try:
        # Create a custom test config for LLM testing
        llm_test_config = TestRunConfig(
            name="LLM Integration Test",
            cycles=3,  # Small number for testing
            delay_between_cycles=0.5,  # Slower for LLM calls
            output_dir="simulation_results/llm_test"
        )
        
        # Initialize test runner
        runner = SimulationTestRunner("config")
        
        # Add our custom config
        runner.test_configs["llm_test"] = llm_test_config
        
        # Modify the orchestrator to use real agents
        original_orchestrator = runner.orchestrator
        runner.orchestrator = DemoOrchestrator(
            config_manager=runner.config_manager,
            context_provider=runner.context_provider,
            use_real_agents=True
        )
        
        print("Running simulation with real LLM agents...")
        result = runner.run_test_suite("llm_test")
        
        print(f"✅ Simulation completed!")
        print(f"- Completed cycles: {result['completed_cycles']}/{result['total_cycles']}")
        print(f"- Customer satisfaction: {result['system_metrics'].avg_customer_satisfaction:.2f}")
        print(f"- Escalation rate: {result['system_metrics'].escalation_rate:.1%}")
        print(f"- Total time: {result['total_time']:.1f} seconds")
        print(f"- Results file: {result['results_file']}")
        
        if result['errors']:
            print(f"- Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:  # Show first 3 errors
                print(f"  - {error}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Full simulation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function"""
    print("🚀 LLM-Enhanced Simulation Test")
    print("=" * 60)
    
    # Check API keys
    has_keys, available_keys = check_api_keys()
    
    if not has_keys:
        print("\n⚠️  Warning: No API keys found. Testing fallback simulation mode.")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test real LLM integration.")
        print("Proceeding with fallback testing...\n")
    
    print(f"\n📋 Testing with available providers: {', '.join(available_keys)}")
    
    # Run tests
    test_results = []
    
    # Test 1: Basic integration
    test_results.append(test_basic_llm_integration())
    
    # Test 2: Full simulation (only if basic test passes)
    if test_results[-1]:
        test_results.append(test_simulation_with_llm_agents())
    else:
        print("\n⏭️  Skipping full simulation test due to basic test failure")
        test_results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    tests = ["Basic LLM Integration", "Full Simulation with LLM"]
    for i, (test_name, passed) in enumerate(zip(tests, test_results)):
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{i+1}. {test_name}: {status}")
    
    overall_success = all(test_results)
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 The simulation now successfully uses real LLM agents!")
        print("You can run full simulations with: python src/simulation/test_runner.py --config llm_test")
    else:
        print("\n🔧 Check the errors above and ensure your API keys and configuration are correct.")


if __name__ == "__main__":
    main()