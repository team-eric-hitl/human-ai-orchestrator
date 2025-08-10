"""
Metrics Collector for Simulation Testing
Collects and analyzes key performance metrics from simulation runs
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from ..core.logging import get_logger


@dataclass
class AgentMetrics:
    """Metrics for individual agent performance"""
    agent_id: str
    agent_name: str
    agent_type: str
    
    # Performance metrics
    cases_handled: int = 0
    avg_resolution_time: float = 0.0
    customer_satisfaction: float = 0.0
    escalation_rate: float = 0.0
    
    # Workload metrics
    max_concurrent: int = 0
    avg_utilization: float = 0.0
    stress_level: float = 0.0
    
    # Quality metrics
    successful_resolutions: int = 0
    total_resolution_attempts: int = 0


@dataclass
class SystemMetrics:
    """Overall system performance metrics"""
    
    # Simulation run info
    run_id: str
    start_time: datetime
    end_time: datetime
    total_cycles: int
    
    # Customer experience
    avg_customer_satisfaction: float = 0.0
    total_escalations: int = 0
    escalation_rate: float = 0.0
    
    # Agent performance
    quality_agent_accuracy: float = 0.0
    frustration_detection_precision: float = 0.0
    routing_success_rate: float = 0.0
    
    # System efficiency
    avg_resolution_time: float = 0.0
    system_utilization: float = 0.0
    
    # Issue counts
    failed_routes: int = 0
    quality_interventions: int = 0
    frustration_interventions: int = 0


@dataclass
class CycleResult:
    """Results from a single simulation cycle"""
    cycle_id: str
    scenario_name: str
    customer_personality: str
    
    # Timing
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    
    # Outcomes
    escalated_to_human: bool = False
    final_satisfaction: float = 0.0
    resolution_method: str = "unknown"
    
    # Agent decisions
    quality_score: float = 0.0
    frustration_score: float = 0.0
    routing_decision: str = "none"
    assigned_agent: Optional[str] = None
    
    # Issues
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class MetricsCollector:
    """Collects and analyzes metrics from simulation runs"""
    
    def __init__(self, output_dir: str = "simulation_results"):
        self.logger = get_logger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Current run data
        self.current_run_id: Optional[str] = None
        self.run_start_time: Optional[datetime] = None
        self.cycle_results: List[CycleResult] = []
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        
        # Tracking data
        self.quality_decisions = []
        self.frustration_decisions = []
        self.routing_decisions = []
        
    def start_run(self, run_id: str, expected_cycles: int = 0) -> str:
        """Start a new metrics collection run"""
        self.current_run_id = run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.run_start_time = datetime.now()
        self.cycle_results = []
        self.agent_metrics = {}
        
        self.logger.info(
            "Started metrics collection run",
            extra={
                "run_id": self.current_run_id,
                "expected_cycles": expected_cycles,
                "operation": "start_run"
            }
        )
        
        return self.current_run_id
    
    def record_cycle_start(self, cycle_id: str, scenario_name: str, customer_personality: str) -> CycleResult:
        """Record the start of a simulation cycle"""
        cycle_result = CycleResult(
            cycle_id=cycle_id,
            scenario_name=scenario_name,
            customer_personality=customer_personality,
            start_time=datetime.now(),
            end_time=datetime.now(),  # Will be updated
            duration_seconds=0.0
        )
        
        return cycle_result
    
    def record_quality_decision(self, cycle_result: CycleResult, decision_data: Dict[str, Any]):
        """Record quality agent decision"""
        cycle_result.quality_score = decision_data.get("overall_score", 0.0)
        
        self.quality_decisions.append({
            "cycle_id": cycle_result.cycle_id,
            "decision": decision_data.get("decision", "unknown"),
            "score": cycle_result.quality_score,
            "confidence": decision_data.get("confidence", 0.0),
            "next_action": decision_data.get("next_action", "unknown")
        })
        
    def record_frustration_decision(self, cycle_result: CycleResult, decision_data: Dict[str, Any]):
        """Record frustration agent decision"""
        cycle_result.frustration_score = decision_data.get("overall_score", 0.0)
        
        self.frustration_decisions.append({
            "cycle_id": cycle_result.cycle_id,
            "score": cycle_result.frustration_score,
            "level": decision_data.get("overall_level", "unknown"),
            "intervention_needed": decision_data.get("intervention_needed", False),
            "confidence": decision_data.get("confidence", 0.0)
        })
        
    def record_routing_decision(self, cycle_result: CycleResult, decision_data: Dict[str, Any]):
        """Record routing agent decision"""
        cycle_result.escalated_to_human = True
        cycle_result.routing_decision = decision_data.get("routing_strategy", "unknown")
        
        if "assigned_employee" in decision_data:
            cycle_result.assigned_agent = decision_data["assigned_employee"]["id"]
        
        self.routing_decisions.append({
            "cycle_id": cycle_result.cycle_id,
            "strategy": cycle_result.routing_decision,
            "agent_id": cycle_result.assigned_agent,
            "match_score": decision_data.get("match_score", 0.0),
            "confidence": decision_data.get("routing_confidence", 0.0)
        })
        
    def record_cycle_completion(self, cycle_result: CycleResult, resolution_data: Dict[str, Any]):
        """Record completion of a simulation cycle"""
        cycle_result.end_time = datetime.now()
        cycle_result.duration_seconds = (cycle_result.end_time - cycle_result.start_time).total_seconds()
        
        # Extract resolution metrics
        if "resolution_result" in resolution_data:
            res_data = resolution_data["resolution_result"]
            cycle_result.final_satisfaction = res_data.get("customer_satisfaction", 0.0)
            cycle_result.resolution_method = res_data.get("resolution_method", "unknown")
        
        self.cycle_results.append(cycle_result)
        
        # Update agent metrics if agent was involved
        if cycle_result.assigned_agent:
            self._update_agent_metrics(cycle_result, resolution_data)
            
        self.logger.debug(
            "Recorded cycle completion",
            extra={
                "cycle_id": cycle_result.cycle_id,
                "duration": cycle_result.duration_seconds,
                "satisfaction": cycle_result.final_satisfaction,
                "operation": "record_cycle_completion"
            }
        )
    
    def _update_agent_metrics(self, cycle_result: CycleResult, resolution_data: Dict[str, Any]):
        """Update metrics for the assigned agent"""
        agent_id = cycle_result.assigned_agent
        
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics(
                agent_id=agent_id,
                agent_name=f"Agent {agent_id}",
                agent_type="unknown"
            )
        
        agent = self.agent_metrics[agent_id]
        agent.cases_handled += 1
        
        # Update resolution time
        if agent.cases_handled == 1:
            agent.avg_resolution_time = cycle_result.duration_seconds
        else:
            agent.avg_resolution_time = (
                (agent.avg_resolution_time * (agent.cases_handled - 1) + cycle_result.duration_seconds) 
                / agent.cases_handled
            )
        
        # Update satisfaction
        if agent.cases_handled == 1:
            agent.customer_satisfaction = cycle_result.final_satisfaction
        else:
            agent.customer_satisfaction = (
                (agent.customer_satisfaction * (agent.cases_handled - 1) + cycle_result.final_satisfaction)
                / agent.cases_handled
            )
        
        # Track successful resolutions
        agent.total_resolution_attempts += 1
        if cycle_result.final_satisfaction >= 7.0:  # Threshold for success
            agent.successful_resolutions += 1
    
    def finish_run(self) -> SystemMetrics:
        """Complete the metrics collection run and calculate final metrics"""
        if not self.current_run_id or not self.run_start_time:
            raise ValueError("No active run to finish")
        
        end_time = datetime.now()
        
        # Calculate system metrics
        system_metrics = SystemMetrics(
            run_id=self.current_run_id,
            start_time=self.run_start_time,
            end_time=end_time,
            total_cycles=len(self.cycle_results)
        )
        
        if self.cycle_results:
            # Customer experience metrics
            satisfactions = [c.final_satisfaction for c in self.cycle_results if c.final_satisfaction > 0]
            system_metrics.avg_customer_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else 0.0
            
            system_metrics.total_escalations = sum(1 for c in self.cycle_results if c.escalated_to_human)
            system_metrics.escalation_rate = system_metrics.total_escalations / len(self.cycle_results)
            
            # System performance metrics
            durations = [c.duration_seconds for c in self.cycle_results]
            system_metrics.avg_resolution_time = sum(durations) / len(durations)
            
            # Agent decision accuracy
            system_metrics.quality_agent_accuracy = self._calculate_quality_accuracy()
            system_metrics.frustration_detection_precision = self._calculate_frustration_precision()
            system_metrics.routing_success_rate = self._calculate_routing_success()
            
            # Count interventions
            system_metrics.quality_interventions = len([d for d in self.quality_decisions if d["decision"] != "adequate"])
            system_metrics.frustration_interventions = len([d for d in self.frustration_decisions if d["intervention_needed"]])
            system_metrics.failed_routes = len([d for d in self.routing_decisions if d["match_score"] < 0.7])
        
        self.logger.info(
            "Finished metrics collection run",
            extra={
                "run_id": self.current_run_id,
                "total_cycles": system_metrics.total_cycles,
                "avg_satisfaction": system_metrics.avg_customer_satisfaction,
                "escalation_rate": system_metrics.escalation_rate,
                "operation": "finish_run"
            }
        )
        
        return system_metrics
    
    def _calculate_quality_accuracy(self) -> float:
        """Calculate quality agent decision accuracy"""
        if not self.quality_decisions:
            return 0.0
        
        # Simple heuristic: good decisions have confidence > 0.7 and appropriate scores
        good_decisions = 0
        for decision in self.quality_decisions:
            confidence = decision.get("confidence", 0.0)
            score = decision.get("score", 0.0)
            
            # Consider it accurate if high confidence and score aligns with decision
            if confidence > 0.7:
                if (score >= 7.0 and decision["decision"] == "adequate") or \
                   (score < 7.0 and decision["decision"] in ["needs_adjustment", "human_intervention"]):
                    good_decisions += 1
        
        return good_decisions / len(self.quality_decisions)
    
    def _calculate_frustration_precision(self) -> float:
        """Calculate frustration detection precision"""
        if not self.frustration_decisions:
            return 0.0
        
        # Precision: interventions that were likely needed
        interventions = [d for d in self.frustration_decisions if d["intervention_needed"]]
        if not interventions:
            return 1.0  # No false positives
        
        # High frustration scores (>6) with intervention are likely correct
        correct_interventions = len([d for d in interventions if d["score"] > 6.0])
        return correct_interventions / len(interventions)
    
    def _calculate_routing_success(self) -> float:
        """Calculate routing decision success rate"""
        if not self.routing_decisions:
            return 0.0
        
        # Success: high match scores and confidence
        successful = len([
            d for d in self.routing_decisions 
            if d["match_score"] >= 0.8 and d["confidence"] >= 0.7
        ])
        
        return successful / len(self.routing_decisions)
    
    def export_results(self, system_metrics: SystemMetrics, filename: Optional[str] = None) -> str:
        """Export metrics to JSON file"""
        if not filename:
            filename = f"simulation_results_{system_metrics.run_id}.json"
        
        output_file = self.output_dir / filename
        
        export_data = {
            "system_metrics": asdict(system_metrics),
            "agent_metrics": {aid: asdict(metrics) for aid, metrics in self.agent_metrics.items()},
            "cycle_results": [asdict(cycle) for cycle in self.cycle_results],
            "decision_details": {
                "quality_decisions": self.quality_decisions,
                "frustration_decisions": self.frustration_decisions,
                "routing_decisions": self.routing_decisions
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.logger.info(
            "Exported simulation results",
            extra={
                "output_file": str(output_file),
                "total_cycles": len(self.cycle_results),
                "operation": "export_results"
            }
        )
        
        return str(output_file)
    
    def generate_summary_report(self, system_metrics: SystemMetrics) -> str:
        """Generate a human-readable summary report"""
        report = []
        report.append(f"# Simulation Test Results - {system_metrics.run_id}")
        report.append(f"Run Time: {system_metrics.start_time} to {system_metrics.end_time}")
        report.append(f"Duration: {(system_metrics.end_time - system_metrics.start_time).total_seconds():.1f} seconds")
        report.append("")
        
        # System Performance
        report.append("## System Performance")
        report.append(f"- Total Cycles: {system_metrics.total_cycles}")
        report.append(f"- Average Customer Satisfaction: {system_metrics.avg_customer_satisfaction:.2f}/10")
        report.append(f"- Escalation Rate: {system_metrics.escalation_rate:.1%}")
        report.append(f"- Average Resolution Time: {system_metrics.avg_resolution_time:.1f} seconds")
        report.append("")
        
        # Agent Performance
        report.append("## Agent Decision Quality")
        report.append(f"- Quality Agent Accuracy: {system_metrics.quality_agent_accuracy:.1%}")
        report.append(f"- Frustration Detection Precision: {system_metrics.frustration_detection_precision:.1%}")
        report.append(f"- Routing Success Rate: {system_metrics.routing_success_rate:.1%}")
        report.append("")
        
        # Intervention Counts
        report.append("## System Interventions")
        report.append(f"- Quality Interventions: {system_metrics.quality_interventions}")
        report.append(f"- Frustration Interventions: {system_metrics.frustration_interventions}")
        report.append(f"- Failed Routes: {system_metrics.failed_routes}")
        report.append("")
        
        # Individual Agent Performance
        if self.agent_metrics:
            report.append("## Individual Agent Performance")
            for agent_id, metrics in self.agent_metrics.items():
                report.append(f"### {metrics.agent_name} ({agent_id})")
                report.append(f"- Cases Handled: {metrics.cases_handled}")
                report.append(f"- Avg Resolution Time: {metrics.avg_resolution_time:.1f} seconds")
                report.append(f"- Customer Satisfaction: {metrics.customer_satisfaction:.2f}/10")
                if metrics.total_resolution_attempts > 0:
                    success_rate = metrics.successful_resolutions / metrics.total_resolution_attempts
                    report.append(f"- Success Rate: {success_rate:.1%}")
                report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        recommendations = self._generate_recommendations(system_metrics)
        for rec in recommendations:
            report.append(f"- {rec}")
        
        return "\n".join(report)
    
    def _generate_recommendations(self, system_metrics: SystemMetrics) -> List[str]:
        """Generate recommendations based on metrics"""
        recommendations = []
        
        # Customer satisfaction
        if system_metrics.avg_customer_satisfaction < 7.0:
            recommendations.append("🔴 Customer satisfaction below target (7.0). Consider tuning chatbot quality or agent training.")
        elif system_metrics.avg_customer_satisfaction > 9.0:
            recommendations.append("🟡 Very high satisfaction - may indicate insufficient challenge in test scenarios.")
        
        # Escalation rate
        if system_metrics.escalation_rate > 0.6:
            recommendations.append("🔴 High escalation rate. Consider improving chatbot responses or quality thresholds.")
        elif system_metrics.escalation_rate < 0.2:
            recommendations.append("🟡 Low escalation rate - ensure quality and frustration agents are properly calibrated.")
        
        # Agent accuracy
        if system_metrics.quality_agent_accuracy < 0.7:
            recommendations.append("🔴 Quality agent accuracy low. Review quality assessment thresholds.")
        
        if system_metrics.frustration_detection_precision < 0.7:
            recommendations.append("🔴 Frustration detection precision low. Review frustration indicators and thresholds.")
        
        if system_metrics.routing_success_rate < 0.8:
            recommendations.append("🔴 Routing success rate low. Review agent specialization matching.")
        
        # System efficiency
        if system_metrics.avg_resolution_time > 60:
            recommendations.append("🟡 Average resolution time high. Consider optimizing agent response generation.")
        
        if not recommendations:
            recommendations.append("✅ All metrics within acceptable ranges!")
        
        return recommendations