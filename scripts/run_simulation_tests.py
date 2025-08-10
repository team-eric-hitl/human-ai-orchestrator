#!/usr/bin/env python3
"""
Simulation Test Runner Script
Easy command-line interface for running simulation tests and tuning agents
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.simulation.test_runner import SimulationTestRunner
from src.core.logging import get_logger


def main():
    """Main function with enhanced CLI interface"""
    import argparse
    
    logger = get_logger(__name__)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run simulation tests")
    parser.add_argument("--config", default=None, 
                       help="Test configuration to run")
    parser.add_argument("--list-configs", action="store_true",
                       help="List available test configurations")
    parser.add_argument("--compare", nargs="+", 
                       help="Run comparative test with multiple configs")
    parser.add_argument("--no-llm", action="store_true",
                       help="Use simulated responses instead of real LLM calls")
    
    args = parser.parse_args()
    
    # Default to using real LLM agents unless --no-llm is specified
    use_real_agents = not args.no_llm
    runner = SimulationTestRunner(use_real_llm_agents=use_real_agents)
    
    # Handle command line usage
    if args.list_configs:
        print("Available test configurations:")
        for name, desc in runner.list_test_configs().items():
            print(f"  {name}: {desc}")
        return
    
    if args.compare:
        print(f"Running comparative test with configs: {args.compare}")
        results = runner.run_comparative_test(args.compare)
        print(f"Comparison report saved to: {results['comparison_file']}")
        print("\nComparison Summary:")
        print(results['comparison_report'])
        return
    
    if args.config:
        print(f"Running test configuration: {args.config}")
        result = runner.run_test_suite(args.config)
        print(f"Test completed! Results saved to: {result['results_file']}")
        print(f"Summary report: {result['summary_file']}")
        if result.get('traces_exported', {}).get('traces_exported', 0) > 0:
            traces_info = result['traces_exported']
            print(f"Traces exported: {traces_info['traces_exported']} traces saved to {traces_info['export_directory']}/")
        print("\nQuick Summary:")
        print(f"- Cycles: {result['completed_cycles']}/{result['total_cycles']}")
        print(f"- Customer Satisfaction: {result['system_metrics'].avg_customer_satisfaction:.2f}/10")
        print(f"- Escalation Rate: {result['system_metrics'].escalation_rate:.1%}")
        print(f"- Total Time: {result['total_time']:.1f} seconds")
        return
    
    # Interactive mode if no arguments provided
    print("🤖 AI System Simulation Test Runner")
    print("=" * 50)
    
    # Display current agent settings
    print("\n📋 Current Agent Settings:")
    settings = runner.get_agent_settings_summary()
    for agent_name, config in settings.items():
        if "error" not in config:
            print(f"  ✓ {agent_name}: {len(config.get('settings', {}))} settings configured")
        else:
            print(f"  ❌ {agent_name}: {config['error']}")
    
    # Show available configurations
    print("\n⚙️  Available Test Configurations:")
    configs = runner.list_test_configs()
    for i, (name, desc) in enumerate(configs.items(), 1):
        print(f"  {i}. {name}: {desc}")
    
    print("\n🚀 Quick Start Options:")
    print("  q) Quick validation (5 cycles)")
    print("  t) Agent tuning (20 cycles)")
    print("  s) Stress test (50 cycles)")
    print("  f) Full validation (100 cycles)")
    print("  c) Compare multiple configs")
    print("  x) Exit")
    
    while True:
        choice = input("\nSelect option: ").strip().lower()
        
        if choice == 'x':
            print("👋 Goodbye!")
            break
        elif choice == 'q':
            run_test(runner, "quick_validation")
        elif choice == 't':
            run_test(runner, "agent_tuning")
        elif choice == 's':
            run_test(runner, "stress_test")
        elif choice == 'f':
            run_test(runner, "full_validation")
        elif choice == 'c':
            run_comparative_test(runner)
        else:
            print("❌ Invalid choice. Please try again.")


def run_test(runner: SimulationTestRunner, config_name: str):
    """Run a single test configuration"""
    print(f"\n🏃 Running {config_name} test...")
    
    try:
        result = runner.run_test_suite(config_name)
        
        print("\n✅ Test completed successfully!")
        print("=" * 50)
        print(f"📊 Results Summary:")
        print(f"  • Run ID: {result['run_id']}")
        print(f"  • Completed: {result['completed_cycles']}/{result['total_cycles']} cycles")
        print(f"  • Customer Satisfaction: {result['system_metrics'].avg_customer_satisfaction:.2f}/10")
        print(f"  • Escalation Rate: {result['system_metrics'].escalation_rate:.1%}")
        print(f"  • Quality Agent Accuracy: {result['system_metrics'].quality_agent_accuracy:.1%}")
        print(f"  • Frustration Detection: {result['system_metrics'].frustration_detection_precision:.1%}")
        print(f"  • Routing Success: {result['system_metrics'].routing_success_rate:.1%}")
        print(f"  • Total Time: {result['total_time']:.1f} seconds")
        
        if result['errors']:
            print(f"  ⚠️  Errors: {len(result['errors'])}")
            print("    First few errors:")
            for error in result['errors'][:3]:
                print(f"    - {error}")
        
        print(f"\n📁 Files Generated:")
        print(f"  • Detailed Results: {result['results_file']}")
        print(f"  • Summary Report: {result['summary_file']}")
        
        # Show trace export information
        if result.get('traces_exported', {}).get('traces_exported', 0) > 0:
            traces_info = result['traces_exported']
            print(f"  • Traces: {traces_info['traces_exported']} traces exported to {traces_info['export_directory']}/")
        
        # Show key recommendations
        recommendations = _extract_key_recommendations(result['summary_report'])
        if recommendations:
            print(f"\n🎯 Key Recommendations:")
            for rec in recommendations[:3]:  # Show top 3
                print(f"  {rec}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")


def run_comparative_test(runner: SimulationTestRunner):
    """Run comparative test with user selection"""
    configs = list(runner.list_test_configs().keys())
    
    print("\n🔄 Comparative Test Setup")
    print("Available configurations:")
    for i, config in enumerate(configs, 1):
        print(f"  {i}. {config}")
    
    print("\nSelect configurations to compare (e.g., '1,2,3' or 'q,t'):")
    selection = input("Enter selection: ").strip()
    
    # Parse selection
    selected_configs = []
    for item in selection.split(','):
        item = item.strip()
        if item.isdigit():
            idx = int(item) - 1
            if 0 <= idx < len(configs):
                selected_configs.append(configs[idx])
        elif item in configs:
            selected_configs.append(item)
        elif item in ['q', 't', 's', 'f']:
            config_map = {'q': 'quick_validation', 't': 'agent_tuning', 's': 'stress_test', 'f': 'full_validation'}
            selected_configs.append(config_map[item])
    
    if not selected_configs:
        print("❌ No valid configurations selected.")
        return
    
    print(f"\n🏃 Running comparative test with: {selected_configs}")
    
    try:
        result = runner.run_comparative_test(selected_configs)
        
        print("\n✅ Comparative test completed!")
        print("=" * 50)
        print(f"📊 Comparison Results:")
        
        # Show summary table
        for config_name, test_result in result['results'].items():
            metrics = test_result['system_metrics']
            print(f"\n{config_name}:")
            print(f"  • Satisfaction: {metrics.avg_customer_satisfaction:.2f}/10")
            print(f"  • Escalation Rate: {metrics.escalation_rate:.1%}")
            print(f"  • Quality Accuracy: {metrics.quality_agent_accuracy:.1%}")
            print(f"  • Cycles: {test_result['completed_cycles']}")
            print(f"  • Time: {test_result['total_time']:.1f}s")
        
        print(f"\n📁 Comparison report saved to: {result['comparison_file']}")
        
    except Exception as e:
        print(f"\n❌ Comparative test failed: {e}")


def _extract_key_recommendations(summary_report: str) -> list:
    """Extract key recommendations from summary report"""
    lines = summary_report.split('\n')
    recommendations = []
    
    in_recommendations = False
    for line in lines:
        if line.strip() == "## Recommendations":
            in_recommendations = True
            continue
        elif in_recommendations and line.startswith('- '):
            recommendations.append(line.strip())
        elif in_recommendations and line.startswith('#'):
            break
    
    return recommendations


if __name__ == "__main__":
    main()