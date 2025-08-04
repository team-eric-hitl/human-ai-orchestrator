"""
Simulation Test Runner
Runs configurable simulation cycles with metrics collection for agent tuning
"""

import asyncio
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from ..core.config import ConfigManager
from ..core.logging import get_logger
from ..core.context_manager import SQLiteContextProvider
from .demo_orchestrator import DemoOrchestrator
from .metrics_collector import MetricsCollector, SystemMetrics


class TestRunConfig:
    """Configuration for simulation test runs"""
    
    def __init__(
        self,
        name: str = "default",
        cycles: int = 10,
        scenarios: Optional[List[str]] = None,
        randomize_scenarios: bool = True,
        delay_between_cycles: float = 0.1,
        max_concurrent_cycles: int = 1,
        output_dir: str = "simulation_results"
    ):
        self.name = name
        self.cycles = cycles
        self.scenarios = scenarios or []  # Empty means use all scenarios
        self.randomize_scenarios = randomize_scenarios
        self.delay_between_cycles = delay_between_cycles
        self.max_concurrent_cycles = max_concurrent_cycles
        self.output_dir = output_dir


class SimulationTestRunner:
    """Runs simulation cycles with comprehensive metrics collection"""
    
    def __init__(self, config_dir: str = "config", use_real_llm_agents: bool = True):
        self.logger = get_logger(__name__)
        self.config_dir = config_dir
        
        # Initialize core components
        self.config_manager = ConfigManager(config_dir)
        self.context_provider = SQLiteContextProvider(config_manager=self.config_manager)
        self.orchestrator = DemoOrchestrator(
            config_manager=self.config_manager,
            context_provider=self.context_provider,
            use_real_agents=use_real_llm_agents
        )
        
        # Test configurations
        self.test_configs = self._create_default_test_configs()
        
    def _create_default_test_configs(self) -> Dict[str, TestRunConfig]:
        """Create default test configurations for different phases"""
        return {
            "quick_validation": TestRunConfig(
                name="Quick Validation",
                cycles=5,
                delay_between_cycles=0.1,
                output_dir="simulation_results/quick"
            ),
            "agent_tuning": TestRunConfig(
                name="Agent Tuning", 
                cycles=20,
                delay_between_cycles=0.2,
                output_dir="simulation_results/tuning"
            ),
            "stress_test": TestRunConfig(
                name="Stress Test",
                cycles=50,
                delay_between_cycles=0.05,
                max_concurrent_cycles=3,
                output_dir="simulation_results/stress"
            ),
            "full_validation": TestRunConfig(
                name="Full Validation",
                cycles=100,
                delay_between_cycles=0.1,
                output_dir="simulation_results/validation"
            ),
            "demo_generation": TestRunConfig(
                name="Demo Data Generation",
                cycles=500,
                delay_between_cycles=0.02,
                max_concurrent_cycles=5,
                output_dir="simulation_results/demo_data"
            )
        }
    
    def list_test_configs(self) -> Dict[str, str]:
        """List available test configurations"""
        return {
            name: f"{config.name} ({config.cycles} cycles)"
            for name, config in self.test_configs.items()
        }
    
    def run_test_suite(self, config_name: str = "quick_validation") -> Dict[str, Any]:
        """Run a complete test suite with the specified configuration"""
        if config_name not in self.test_configs:
            raise ValueError(f"Unknown test config: {config_name}. Available: {list(self.test_configs.keys())}")
        
        config = self.test_configs[config_name]
        
        self.logger.info(
            "Starting simulation test suite",
            extra={
                "config_name": config_name,
                "cycles": config.cycles,
                "operation": "run_test_suite"
            }
        )
        
        # Initialize metrics collector
        metrics_collector = MetricsCollector(config.output_dir)
        run_id = f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metrics_collector.start_run(run_id, config.cycles)
        
        # Get available scenarios
        available_scenarios = self.orchestrator.list_available_scenarios()
        test_scenarios = config.scenarios if config.scenarios else [s["name"] for s in available_scenarios]
        
        # Run simulation cycles
        start_time = time.time()
        completed_cycles = []
        errors = []
        
        try:
            for cycle_num in range(config.cycles):
                cycle_start = time.time()
                
                try:
                    # Select scenario
                    if config.randomize_scenarios:
                        scenario_name = random.choice(test_scenarios)
                    else:
                        scenario_name = test_scenarios[cycle_num % len(test_scenarios)]
                    
                    # Run simulation cycle
                    cycle_result = self._run_single_cycle(
                        cycle_num, 
                        scenario_name, 
                        metrics_collector
                    )
                    
                    completed_cycles.append(cycle_result)
                    
                    # Progress logging
                    if cycle_num % max(1, config.cycles // 10) == 0:
                        progress = (cycle_num + 1) / config.cycles
                        elapsed = time.time() - start_time
                        eta = elapsed / progress - elapsed if progress > 0 else 0
                        
                        self.logger.info(
                            f"Progress: {cycle_num + 1}/{config.cycles} cycles ({progress:.1%}), ETA: {eta:.1f}s"
                        )
                    
                    # Delay between cycles
                    if config.delay_between_cycles > 0:
                        time.sleep(config.delay_between_cycles)
                        
                except Exception as e:
                    error_msg = f"Cycle {cycle_num} failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg, extra={"cycle_num": cycle_num})
                    continue
            
            # Finish metrics collection
            system_metrics = metrics_collector.finish_run()
            
            # Export traces if trace collection is enabled
            traces_exported = self._export_traces(completed_cycles, run_id)
            
            # Generate reports
            results_file = metrics_collector.export_results(system_metrics)
            summary_report = metrics_collector.generate_summary_report(system_metrics)
            
            # Save summary report to file
            summary_file = Path(config.output_dir) / f"summary_{run_id}.txt"
            summary_file.parent.mkdir(parents=True, exist_ok=True)
            with open(summary_file, 'w') as f:
                f.write(summary_report)
            
            total_time = time.time() - start_time
            
            self.logger.info(
                "Completed simulation test suite",
                extra={
                    "run_id": run_id,
                    "completed_cycles": len(completed_cycles),
                    "errors": len(errors),
                    "total_time": total_time,
                    "avg_customer_satisfaction": system_metrics.avg_customer_satisfaction,
                    "escalation_rate": system_metrics.escalation_rate,
                    "operation": "run_test_suite"
                }
            )
            
            return {
                "run_id": run_id,
                "config_name": config_name,
                "system_metrics": system_metrics,
                "completed_cycles": len(completed_cycles),
                "total_cycles": config.cycles,
                "errors": errors,
                "total_time": total_time,
                "results_file": results_file,
                "summary_file": str(summary_file),
                "summary_report": summary_report,
                "traces_exported": traces_exported
            }
            
        except Exception as e:
            self.logger.error(
                "Test suite failed",
                extra={
                    "error": str(e),
                    "completed_cycles": len(completed_cycles),
                    "operation": "run_test_suite"
                }
            )
            raise
    
    def _run_single_cycle(
        self, 
        cycle_num: int, 
        scenario_name: str, 
        metrics_collector: MetricsCollector
    ) -> Dict[str, Any]:
        """Run a single simulation cycle following the complete workflow from simulations.txt"""
        
        cycle_id = f"cycle_{cycle_num:04d}_{scenario_name.replace(' ', '_').lower()}"
        
        # Start cycle metrics
        cycle_result = metrics_collector.record_cycle_start(
            cycle_id=cycle_id,
            scenario_name=scenario_name,
            customer_personality="unknown"  # Will be updated
        )
        
        try:
            # 1. Start demo scenario - simulated user asks a support question
            demo_result = self.orchestrator.start_demo_scenario(scenario_name)
            cycle_result.customer_personality = demo_result["customer_context"]["personality"]
            
            # 2. Frustration agent evaluates the question looking for signs of too much frustration
            frustration_result = self.orchestrator.simulate_frustration_analysis(demo_result["demo_id"])
            metrics_collector.record_frustration_decision(cycle_result, frustration_result["frustration_analysis"])
            
            # If frustration threshold is surpassed, send to escalation router rather than chatbot
            if frustration_result["intervention_needed"]:
                self.logger.info(f"Cycle {cycle_id}: Escalating due to frustration threshold")
                
                routing_result = self.orchestrator.simulate_routing_decision(demo_result["demo_id"])
                metrics_collector.record_routing_decision(cycle_result, routing_result["routing_decision"])
                
                if "assigned_employee" in routing_result["routing_decision"]:
                    human_result = self.orchestrator.simulate_human_agent_response(demo_result["demo_id"])
                    customer_response = self.orchestrator.simulate_customer_response_to_human(demo_result["demo_id"])
                
                # Complete with human resolution
                resolution_result = self.orchestrator.simulate_resolution(demo_result["demo_id"])
                
            else:
                # 3. Chatbot generates a reply to the query (skip automation for simulation focus)
                self.logger.info(f"Cycle {cycle_id}: Processing via chatbot")
                chatbot_result = self.orchestrator.simulate_chatbot_response(demo_result["demo_id"])
                
                # 4. Quality agent evaluates the reply before sending back to user
                quality_result = self.orchestrator.simulate_quality_assessment(demo_result["demo_id"])
                metrics_collector.record_quality_decision(cycle_result, quality_result["quality_assessment"])
                
                # If quality agent detects a problem, direct to escalation agent instead
                if quality_result["quality_assessment"]["next_action"] == "escalate_to_human":
                    self.logger.info(f"Cycle {cycle_id}: Escalating due to quality issues")
                    
                    routing_result = self.orchestrator.simulate_routing_decision(demo_result["demo_id"])
                    metrics_collector.record_routing_decision(cycle_result, routing_result["routing_decision"])
                    
                    if "assigned_employee" in routing_result["routing_decision"]:
                        human_result = self.orchestrator.simulate_human_agent_response(demo_result["demo_id"])
                        customer_response = self.orchestrator.simulate_customer_response_to_human(demo_result["demo_id"])
                    
                    resolution_result = self.orchestrator.simulate_resolution(demo_result["demo_id"])
                
                else:
                    # 5. Quality is adequate - continue with chatbot interaction
                    # TODO: Implement multi-turn conversation capability here
                    # For now, assume single interaction resolves the issue
                    resolution_result = self.orchestrator.simulate_resolution(demo_result["demo_id"])
            
            # Record cycle completion
            metrics_collector.record_cycle_completion(cycle_result, resolution_result)
            
            return {
                "cycle_id": cycle_id,
                "demo_id": demo_result["demo_id"],
                "scenario_name": scenario_name,
                "success": True,
                "final_satisfaction": cycle_result.final_satisfaction,
                "escalated": cycle_result.escalated_to_human,
                "duration": cycle_result.duration_seconds,
                "resolution_method": self._determine_resolution_method(demo_result["demo_id"])
            }
            
        except Exception as e:
            cycle_result.errors.append(str(e))
            metrics_collector.record_cycle_completion(cycle_result, {"resolution_result": {"customer_satisfaction": 0.0}})
            
            self.logger.error(
                "Cycle failed",
                extra={
                    "cycle_id": cycle_id,
                    "scenario_name": scenario_name,
                    "error": str(e),
                    "operation": "_run_single_cycle"
                }
            )
            
            return {
                "cycle_id": cycle_id,
                "scenario_name": scenario_name,
                "success": False,
                "error": str(e),
                "duration": cycle_result.duration_seconds
            }

    def _determine_resolution_method(self, demo_id: str) -> str:
        """Determine how the query was resolved based on demo state"""
        demo = self.orchestrator.active_demonstrations.get(demo_id, {})
        
        if demo.get("automation_response"):
            return "automation"
        elif demo.get("employee_interaction"):
            return "human_agent"
        else:
            return "chatbot"
    
    def run_comparative_test(self, config_names: List[str]) -> Dict[str, Any]:
        """Run multiple test configurations and compare results"""
        results = {}
        
        self.logger.info(
            "Starting comparative test",
            extra={
                "configs": config_names,
                "operation": "run_comparative_test"
            }
        )
        
        for config_name in config_names:
            self.logger.info(f"Running test configuration: {config_name}")
            results[config_name] = self.run_test_suite(config_name)
        
        # Generate comparison report
        comparison_report = self._generate_comparison_report(results)
        
        # Save comparison report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        comparison_file = Path("simulation_results") / f"comparison_{timestamp}.txt"
        comparison_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(comparison_file, 'w') as f:
            f.write(comparison_report)
        
        return {
            "results": results,
            "comparison_report": comparison_report,
            "comparison_file": str(comparison_file)
        }
    
    def _generate_comparison_report(self, results: Dict[str, Any]) -> str:
        """Generate a comparison report across multiple test runs"""
        report = []
        report.append("# Comparative Test Results")
        report.append(f"Generated: {datetime.now()}")
        report.append("")
        
        # Summary table
        report.append("## Summary Comparison")
        report.append("| Config | Cycles | Satisfaction | Escalation Rate | Quality Accuracy | Avg Resolution Time |")
        report.append("|--------|--------|--------------|-----------------|------------------|---------------------|")
        
        for config_name, result in results.items():
            metrics = result["system_metrics"]
            report.append(
                f"| {config_name} | {metrics.total_cycles} | "
                f"{metrics.avg_customer_satisfaction:.2f} | "
                f"{metrics.escalation_rate:.1%} | "
                f"{metrics.quality_agent_accuracy:.1%} | "
                f"{metrics.avg_resolution_time:.1f}s |"
            )
        
        report.append("")
        
        # Detailed analysis
        report.append("## Detailed Analysis")
        
        for config_name, result in results.items():
            report.append(f"### {config_name}")
            report.append(f"- Run ID: {result['run_id']}")
            report.append(f"- Completed: {result['completed_cycles']}/{result['total_cycles']} cycles")
            report.append(f"- Total Time: {result['total_time']:.1f} seconds")
            report.append(f"- Errors: {len(result['errors'])}")
            
            if result['errors']:
                report.append("- Error Details:")
                for error in result['errors'][:5]:  # Show first 5 errors
                    report.append(f"  - {error}")
                if len(result['errors']) > 5:
                    report.append(f"  - ... and {len(result['errors']) - 5} more")
            
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        best_config = max(results.items(), key=lambda x: x[1]["system_metrics"].avg_customer_satisfaction)
        report.append(f"- Best performing configuration: **{best_config[0]}**")
        report.append(f"  - Customer Satisfaction: {best_config[1]['system_metrics'].avg_customer_satisfaction:.2f}/10")
        report.append(f"  - Escalation Rate: {best_config[1]['system_metrics'].escalation_rate:.1%}")
        
        return "\n".join(report)
    
    def get_agent_settings_summary(self) -> Dict[str, Any]:
        """Get current agent settings for reference"""
        try:
            # Get current agent configurations
            chatbot_config = self.config_manager.get_agent_config("chatbot_agent")
            quality_config = self.config_manager.get_agent_config("quality_agent") 
            frustration_config = self.config_manager.get_agent_config("frustration_agent")
            routing_config = self.config_manager.get_agent_config("routing_agent")
            
            return {
                "chatbot_agent": {
                    "settings": chatbot_config.settings,
                    "prompts_available": bool(hasattr(chatbot_config, 'prompts'))
                },
                "quality_agent": {
                    "settings": quality_config.settings,
                    "thresholds": quality_config.settings.get("thresholds", {})
                },
                "frustration_agent": {
                    "settings": frustration_config.settings,
                    "thresholds": frustration_config.settings.get("thresholds", {})
                },
                "routing_agent": {
                    "settings": routing_config.settings,
                    "strategies": routing_config.settings.get("routing_strategies", {})
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Could not get agent settings: {e}")
            return {"error": str(e)}
    
    def _export_traces(self, completed_cycles: list, run_id: str) -> dict:
        """Export traces from completed simulation cycles"""
        from ..interfaces.core.trace import OutputFormat
        
        trace_results = {
            "total_cycles": len(completed_cycles),
            "traces_exported": 0,
            "traces_failed": 0,
            "export_directory": "test_traces",
            "exported_files": []
        }
        
        # Create test_traces directory
        traces_dir = Path("test_traces")
        traces_dir.mkdir(exist_ok=True)
        
        # Create subdirectory for this run
        run_traces_dir = traces_dir / run_id
        run_traces_dir.mkdir(exist_ok=True)
        
        for cycle in completed_cycles:
            if not cycle.get("success", False) or "demo_id" not in cycle:
                continue
                
            demo_id = cycle["demo_id"]
            cycle_id = cycle.get("cycle_id", demo_id)
            
            try:
                # Export detailed JSON trace
                trace_json = self.orchestrator.export_demo_trace(
                    demo_id=demo_id,
                    format="detailed_json"
                )
                
                if "error" not in trace_json:
                    json_file = run_traces_dir / f"{cycle_id}_detailed.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        f.write(trace_json)
                    trace_results["exported_files"].append(str(json_file))
                    
                    # Also export CSV timeline
                    trace_csv = self.orchestrator.export_demo_trace(
                        demo_id=demo_id,
                        format="csv_timeline"
                    )
                    
                    if "error" not in trace_csv:
                        csv_file = run_traces_dir / f"{cycle_id}_timeline.csv"
                        with open(csv_file, 'w', encoding='utf-8') as f:
                            f.write(trace_csv)
                        trace_results["exported_files"].append(str(csv_file))
                    
                    trace_results["traces_exported"] += 1
                    
                else:
                    self.logger.warning(f"Failed to export trace for {demo_id}: {trace_json}")
                    trace_results["traces_failed"] += 1
                    
            except Exception as e:
                self.logger.error(f"Error exporting trace for cycle {cycle_id}: {e}")
                trace_results["traces_failed"] += 1
        
        # Create summary file
        if trace_results["traces_exported"] > 0:
            summary_file = run_traces_dir / "trace_export_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(trace_results, f, indent=2)
            trace_results["summary_file"] = str(summary_file)
            
            self.logger.info(
                f"Exported {trace_results['traces_exported']} traces to {run_traces_dir}",
                extra={
                    "traces_exported": trace_results["traces_exported"],
                    "traces_failed": trace_results["traces_failed"],
                    "export_dir": str(run_traces_dir),
                    "operation": "export_traces"
                }
            )
        
        return trace_results


def main():
    """Main function for running simulation tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run simulation tests")
    parser.add_argument("--config", default="quick_validation", 
                       help="Test configuration to run")
    parser.add_argument("--list-configs", action="store_true",
                       help="List available test configurations")
    parser.add_argument("--compare", nargs="+", 
                       help="Run comparative test with multiple configs")
    
    args = parser.parse_args()
    
    runner = SimulationTestRunner()
    
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
    else:
        print(f"Running test configuration: {args.config}")
        result = runner.run_test_suite(args.config)
        print(f"Test completed! Results saved to: {result['results_file']}")
        print(f"Summary report: {result['summary_file']}")
        print("\nQuick Summary:")
        print(f"- Cycles: {result['completed_cycles']}/{result['total_cycles']}")
        print(f"- Customer Satisfaction: {result['system_metrics'].avg_customer_satisfaction:.2f}/10")
        print(f"- Escalation Rate: {result['system_metrics'].escalation_rate:.1%}")
        print(f"- Total Time: {result['total_time']:.1f} seconds")


if __name__ == "__main__":
    main()