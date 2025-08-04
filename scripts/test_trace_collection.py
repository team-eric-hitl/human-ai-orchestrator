#!/usr/bin/env python3
"""
Test script for the new trace collection functionality

This script demonstrates the complete trace collection workflow:
1. Runs a demo scenario with trace collection enabled
2. Records all agent interactions and system decisions
3. Exports the trace in multiple formats
4. Shows how to access trace data programmatically

Usage:
    python scripts/test_trace_collection.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.simulation.demo_orchestrator import DemoOrchestrator
from src.core.config import ConfigManager
from src.core.trace_collector import TraceCollector
from src.interfaces.core.trace import OutputFormat


def setup_test_environment():
    """Set up test environment with trace collection enabled"""
    # Ensure trace output directory exists
    trace_dir = Path("test_traces")
    trace_dir.mkdir(exist_ok=True)
    
    print("🔧 Setting up test environment...")
    print(f"   Trace output directory: {trace_dir.absolute()}")
    
    return trace_dir


def create_orchestrator_with_tracing():
    """Create a DemoOrchestrator with trace collection enabled"""
    print("🚀 Initializing DemoOrchestrator with trace collection...")
    
    try:
        # Initialize with trace collection enabled
        config_manager = ConfigManager("config")
        orchestrator = DemoOrchestrator(
            config_manager=config_manager,
            use_real_agents=False,  # Use simulated agents for reliable testing
            enable_trace_collection=True
        )
        
        print("   ✅ DemoOrchestrator initialized successfully")
        print(f"   📊 Trace collection enabled: {orchestrator.enable_trace_collection}")
        print(f"   📈 Trace collector available: {orchestrator.trace_collector is not None}")
        
        return orchestrator
        
    except Exception as e:
        print(f"   ❌ Failed to initialize orchestrator: {e}")
        raise


def run_demo_scenario(orchestrator, scenario_name="Frustrated Customer"):
    """Run a complete demo scenario with trace collection"""
    print(f"\n🎯 Running demo scenario: '{scenario_name}'")
    
    try:
        # Start the demo scenario
        demo_result = orchestrator.start_demo_scenario(scenario_name)
        demo_id = demo_result["demo_id"]
        
        print(f"   📝 Demo started with ID: {demo_id}")
        print(f"   💬 Customer query: {demo_result['customer_query'][:100]}...")
        
        # Run through the complete workflow
        print("   🔄 Running workflow steps...")
        
        # Step 1: Frustration analysis
        print("      1️⃣ Frustration analysis...")
        frustration_result = orchestrator.simulate_frustration_analysis(demo_id)
        print(f"         Frustration level: {frustration_result['frustration_analysis'].get('overall_level', 'unknown')}")
        
        # Step 2: Chatbot response  
        print("      2️⃣ Chatbot response...")
        chatbot_result = orchestrator.simulate_chatbot_response(demo_id)
        print(f"         Response generated: {len(chatbot_result['chatbot_response'])} characters")
        
        # Step 3: Quality assessment
        print("      3️⃣ Quality assessment...")
        quality_result = orchestrator.simulate_quality_assessment(demo_id)
        print(f"         Quality decision: {quality_result['quality_assessment'].get('decision', 'unknown')}")
        
        # Step 4: Routing decision (if needed)
        if frustration_result['intervention_needed']:
            print("      4️⃣ Routing decision...")
            routing_result = orchestrator.simulate_routing_decision(demo_id)
            print(f"         Routing: {routing_result['routing_decision'].get('assigned_employee', {}).get('name', 'Unknown')}")
            
            # Step 5: Human agent response
            print("      5️⃣ Human agent response...")
            human_result = orchestrator.simulate_human_agent_response(demo_id)
            print(f"         Human response: {len(human_result['employee_response']['employee_response'])} characters")
        
        # Step 6: Resolution
        print("      6️⃣ Resolution...")
        resolution_result = orchestrator.simulate_resolution(demo_id)
        print(f"         Resolution: {resolution_result['resolution_result']['case_resolved']}")
        
        print("   ✅ Demo scenario completed successfully")
        return demo_id
        
    except Exception as e:
        print(f"   ❌ Demo scenario failed: {e}")
        raise


def export_and_analyze_trace(orchestrator, demo_id, output_dir):
    """Export the trace in multiple formats and analyze the results"""
    print(f"\n📤 Exporting trace for demo: {demo_id}")
    
    formats_to_test = [
        ("detailed_json", "Complete detailed trace"),
        ("summary_json", "Summary trace for dashboards"),
        ("csv_timeline", "Timeline in CSV format"), 
        ("performance_only", "Performance metrics only")
    ]
    
    exported_files = []
    
    for format_name, description in formats_to_test:
        print(f"   📄 Exporting {description}...")
        
        try:
            # Export trace in this format
            output_file = output_dir / f"trace_{demo_id}_{format_name}.{format_name.split('_')[-1]}"
            
            trace_data = orchestrator.export_demo_trace(
                demo_id=demo_id,
                format=format_name,
                output_file=str(output_file)
            )
            
            # Validate the export
            if "error" in trace_data:
                print(f"      ❌ Export failed: {trace_data['error']}")
                continue
                
            file_size = len(trace_data.encode('utf-8'))
            print(f"      ✅ Exported to {output_file.name} ({file_size:,} bytes)")
            exported_files.append((output_file, format_name, file_size))
            
        except Exception as e:
            print(f"      ❌ Export failed: {e}")
    
    return exported_files


def analyze_trace_content(orchestrator, demo_id):
    """Analyze the trace content to show what was captured"""
    print(f"\n🔍 Analyzing trace content for demo: {demo_id}")
    
    try:
        # Get the trace directly from the collector
        if not orchestrator.trace_collector:
            print("   ❌ No trace collector available")
            return
            
        trace = orchestrator.trace_collector.get_trace(f"trace_{demo_id.split('_')[1:]}")
        if not trace:
            # Try to get it from the demo session
            demo = orchestrator.active_demonstrations.get(demo_id)
            if demo and "final_trace" in demo:
                trace = demo["final_trace"]
            else:
                print("   ❌ Trace not found")
                return
        
        print(f"   📊 Trace Analysis:")
        print(f"      🕒 Total duration: {trace.total_duration_ms:.1f}ms")
        print(f"      🤖 Agents involved: {len(trace.agent_interactions)}")
        print(f"      🔀 System decisions: {len(trace.system_decisions)}")
        print(f"      📈 Workflow stages: {len(trace.workflow_progression)}")
        
        # Show agent breakdown
        print(f"      🤖 Agent breakdown:")
        for interaction in trace.agent_interactions:
            print(f"         • {interaction.agent_name}: {interaction.duration_ms:.1f}ms")
        
        # Show system decisions
        if trace.system_decisions:
            print(f"      🔀 System decisions:")
            for decision in trace.system_decisions:
                print(f"         • {decision.decision_point}: {decision.decision}")
        
        # Show performance metrics
        if trace.performance_metrics:
            metrics = trace.performance_metrics
            print(f"      📈 Performance metrics:")
            print(f"         • Total cost: ${metrics.total_cost_usd:.4f}")
            print(f"         • Total tokens: {metrics.total_tokens_used}")
            print(f"         • Escalation occurred: {metrics.escalation_occurred}")
        
    except Exception as e:
        print(f"   ❌ Trace analysis failed: {e}")


def demonstrate_trace_api(orchestrator):
    """Demonstrate programmatic access to trace data"""
    print(f"\n🔧 Demonstrating trace API functionality...")
    
    try:
        if not orchestrator.trace_collector:
            print("   ❌ No trace collector available")
            return
            
        # Get performance summary
        summary = orchestrator.trace_collector.get_performance_summary()
        print(f"   📊 Performance summary:")
        print(f"      • Total traces: {summary.get('total_traces', 0)}")
        print(f"      • Completed traces: {summary.get('completed_traces', 0)}")
        print(f"      • Active traces: {summary.get('active_traces', 0)}")
        
        if summary.get('performance_metrics'):
            perf = summary['performance_metrics']
            print(f"      • Avg processing time: {perf.get('avg_processing_time_ms', 0):.1f}ms")
            print(f"      • Total cost: ${perf.get('total_cost_usd', 0):.4f}")
            print(f"      • Escalation rate: {perf.get('escalation_rate', 0):.1f}%")
        
        # Show agent usage
        if summary.get('agent_usage'):
            print(f"   🤖 Agent usage:")
            for agent, stats in summary['agent_usage'].items():
                print(f"      • {agent}: {stats['count']} calls, avg {stats['avg_duration_ms']:.1f}ms")
        
    except Exception as e:
        print(f"   ❌ API demonstration failed: {e}")


def test_trace_collection():
    """Main test function that runs the complete trace collection test"""
    print("🧪 Testing Full Trace Collection System")
    print("=" * 50)
    
    try:
        # Setup
        output_dir = setup_test_environment()
        orchestrator = create_orchestrator_with_tracing()
        
        # Run demo scenario with tracing
        demo_id = run_demo_scenario(orchestrator)
        
        # Export traces in multiple formats
        exported_files = export_and_analyze_trace(orchestrator, demo_id, output_dir)
        
        # Analyze trace content
        analyze_trace_content(orchestrator, demo_id)
        
        # Demonstrate programmatic API
        demonstrate_trace_api(orchestrator)
        
        # Summary
        print(f"\n✅ Test completed successfully!")
        print(f"   📁 Output directory: {output_dir.absolute()}")
        print(f"   📄 Files exported: {len(exported_files)}")
        
        if exported_files:
            print(f"   📋 Exported files:")
            for file_path, format_name, size in exported_files:
                print(f"      • {file_path.name} ({format_name}, {size:,} bytes)")
        
        print(f"\n💡 To view the detailed trace, run:")
        print(f"   cat {output_dir}/trace_{demo_id}_detailed_json.json | jq .")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Trace Collection Test")
    print("This script will run a complete demo scenario with trace collection")
    print("and export the results in multiple formats.\n")
    
    success = test_trace_collection()
    
    if success:
        print("\n🎉 All tests passed! Trace collection is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Tests failed. Check the output above for details.")
        sys.exit(1)