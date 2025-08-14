"""
Trace collection implementation for HITL system interactions

This module provides concrete implementation of trace collection functionality
to capture complete interaction flows with detailed agent processing, timing,
and system decision information.
"""

import json
import csv
import io
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from ..core.logging import get_logger
from ..interfaces.core.trace import (
    TraceCollectorInterface,
    InteractionTrace,
    AgentInteraction,
    SystemDecision,
    WorkflowStage,
    PerformanceMetrics,
    OutputFormat
)


class TraceCollector(TraceCollectorInterface):
    """Concrete implementation of trace collection for HITL interactions
    
    This collector captures complete interaction traces including agent processing,
    system decisions, timing data, and performance metrics. It provides multiple
    export formats and integrates with the existing logging infrastructure.
    """
    
    def __init__(self, max_traces_in_memory: int = 1000):
        """Initialize the trace collector
        
        Args:
            max_traces_in_memory: Maximum number of traces to keep in memory
        """
        self.active_traces: dict[str, InteractionTrace] = {}
        self.completed_traces: dict[str, InteractionTrace] = {}
        self.max_traces_in_memory = max_traces_in_memory
        self.logger = get_logger(__name__)
        
        # Track next sequence numbers for agent interactions
        self._interaction_counters: dict[str, int] = {}
        
        self.logger.info(
            "TraceCollector initialized",
            extra={
                "max_traces_in_memory": max_traces_in_memory,
                "operation": "trace_collector_init"
            }
        )
    
    def start_trace(
        self, 
        session_id: str, 
        user_id: str, 
        query_id: str, 
        initial_query: dict[str, Any]
    ) -> str:
        """Start a new interaction trace"""
        trace_id = f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        trace = InteractionTrace(
            trace_id=trace_id,
            session_id=session_id,
            user_id=user_id,
            query_id=query_id,
            start_time=start_time,
            initial_query=initial_query
        )
        
        self.active_traces[trace_id] = trace
        self._interaction_counters[trace_id] = 0
        
        # Record initial workflow stage
        self.record_workflow_stage(trace_id, "query_received", start_time)
        
        self.logger.info(
            "Trace started",
            extra={
                "trace_id": trace_id,
                "session_id": session_id,
                "user_id": user_id,
                "query_id": query_id,
                "start_time": start_time.isoformat(),
                "operation": "start_trace"
            }
        )
        
        return trace_id
    
    def record_agent_interaction(
        self,
        trace_id: str,
        agent_name: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        metadata: Optional[dict[str, Any]] = None,
        next_action: str = ""
    ) -> str:
        """Record an agent interaction in the trace"""
        if trace_id not in self.active_traces:
            self.logger.warning(
                "Attempted to record agent interaction for non-existent trace",
                extra={"trace_id": trace_id, "agent_name": agent_name}
            )
            return ""
        
        trace = self.active_traces[trace_id]
        
        # Generate interaction ID and increment sequence
        self._interaction_counters[trace_id] += 1
        sequence_number = self._interaction_counters[trace_id]
        interaction_id = f"{agent_name}_{sequence_number:03d}"
        
        # Calculate duration
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Create interaction record
        interaction = AgentInteraction(
            agent_name=agent_name,
            interaction_id=interaction_id,
            sequence_number=sequence_number,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            input_data=input_data.copy(),
            output_data=output_data.copy(),
            response_metadata=metadata.copy() if metadata else {},
            next_action=next_action
        )
        
        trace.agent_interactions.append(interaction)
        
        # Record workflow stage for agent completion
        stage_name = f"{agent_name}_complete"
        self.record_workflow_stage(trace_id, stage_name, end_time)
        
        self.logger.info(
            "Agent interaction recorded",
            extra={
                "trace_id": trace_id,
                "agent_name": agent_name,
                "interaction_id": interaction_id,
                "duration_ms": duration_ms,
                "next_action": next_action,
                "operation": "record_agent_interaction"
            }
        )
        
        return interaction_id
    
    def record_system_decision(
        self,
        trace_id: str,
        decision_point: str,
        decision: str,
        reasoning: str,
        factors: Optional[list[str]] = None,
        confidence: Optional[float] = None
    ) -> None:
        """Record a system decision point in the trace"""
        if trace_id not in self.active_traces:
            self.logger.warning(
                "Attempted to record system decision for non-existent trace",
                extra={"trace_id": trace_id, "decision_point": decision_point}
            )
            return
        
        trace = self.active_traces[trace_id]
        timestamp = datetime.now()
        
        decision_record = SystemDecision(
            decision_point=decision_point,
            timestamp=timestamp,
            decision=decision,
            reasoning=reasoning,
            factors=factors.copy() if factors else [],
            confidence=confidence
        )
        
        trace.system_decisions.append(decision_record)
        
        self.logger.info(
            "System decision recorded",
            extra={
                "trace_id": trace_id,
                "decision_point": decision_point,
                "decision": decision,
                "confidence": confidence,
                "factors": factors,
                "operation": "record_system_decision"
            }
        )
    
    def record_workflow_stage(
        self,
        trace_id: str,
        stage: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Record reaching a workflow stage"""
        if trace_id not in self.active_traces:
            self.logger.warning(
                "Attempted to record workflow stage for non-existent trace",
                extra={"trace_id": trace_id, "stage": stage}
            )
            return
        
        trace = self.active_traces[trace_id]
        stage_time = timestamp or datetime.now()
        duration_from_start_ms = (stage_time - trace.start_time).total_seconds() * 1000
        
        stage_record = WorkflowStage(
            stage=stage,
            timestamp=stage_time,
            duration_from_start_ms=duration_from_start_ms
        )
        
        trace.workflow_progression.append(stage_record)
        
        self.logger.debug(
            "Workflow stage recorded",
            extra={
                "trace_id": trace_id,
                "stage": stage,
                "duration_from_start_ms": duration_from_start_ms,
                "operation": "record_workflow_stage"
            }
        )
    
    def finalize_trace(
        self,
        trace_id: str,
        outcome: dict[str, Any],
        end_time: Optional[datetime] = None
    ) -> InteractionTrace:
        """Finalize a trace and calculate performance metrics"""
        if trace_id not in self.active_traces:
            raise ValueError(f"Trace {trace_id} not found or already finalized")
        
        trace = self.active_traces[trace_id]
        trace.end_time = end_time or datetime.now()
        trace.outcome = outcome.copy()
        
        # Calculate performance metrics
        trace.performance_metrics = self._calculate_performance_metrics(trace)
        
        # Move to completed traces
        self.completed_traces[trace_id] = trace
        del self.active_traces[trace_id]
        
        # Clean up interaction counter
        if trace_id in self._interaction_counters:
            del self._interaction_counters[trace_id]
        
        # Manage memory usage
        self._manage_memory()
        
        self.logger.info(
            "Trace finalized",
            extra={
                "trace_id": trace_id,
                "total_duration_ms": trace.total_duration_ms,
                "agents_involved": len(trace.agent_interactions),
                "system_decisions": len(trace.system_decisions),
                "escalation_occurred": trace.performance_metrics.escalation_occurred if trace.performance_metrics else False,
                "operation": "finalize_trace"
            }
        )
        
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[InteractionTrace]:
        """Get a complete trace by ID"""
        return (self.active_traces.get(trace_id) or 
                self.completed_traces.get(trace_id))
    
    def get_session_traces(self, session_id: str) -> list[InteractionTrace]:
        """Get all traces for a session"""
        session_traces = []
        
        # Check active traces
        for trace in self.active_traces.values():
            if trace.session_id == session_id:
                session_traces.append(trace)
        
        # Check completed traces
        for trace in self.completed_traces.values():
            if trace.session_id == session_id:
                session_traces.append(trace)
        
        # Sort by start time
        session_traces.sort(key=lambda t: t.start_time)
        return session_traces
    
    def export_trace(
        self, 
        trace_id: str, 
        format: OutputFormat = OutputFormat.DETAILED_JSON
    ) -> str:
        """Export a trace in the specified format"""
        trace = self.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace {trace_id} not found")
        
        if format == OutputFormat.DETAILED_JSON:
            return self._export_detailed_json(trace)
        elif format == OutputFormat.SUMMARY_JSON:
            return self._export_summary_json(trace)
        elif format == OutputFormat.CSV_TIMELINE:
            return self._export_csv_timeline(trace)
        elif format == OutputFormat.PERFORMANCE_ONLY:
            return self._export_performance_only(trace)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def export_traces_batch(
        self,
        trace_ids: list[str],
        format: OutputFormat = OutputFormat.DETAILED_JSON,
        output_file: Optional[str] = None
    ) -> str:
        """Export multiple traces in batch"""
        traces = []
        for trace_id in trace_ids:
            trace = self.get_trace(trace_id)
            if trace:
                traces.append(trace)
            else:
                self.logger.warning(f"Trace {trace_id} not found for batch export")
        
        if format == OutputFormat.DETAILED_JSON:
            result = self._export_batch_detailed_json(traces)
        elif format == OutputFormat.SUMMARY_JSON:
            result = self._export_batch_summary_json(traces)
        elif format == OutputFormat.CSV_TIMELINE:
            result = self._export_batch_csv_timeline(traces)
        elif format == OutputFormat.PERFORMANCE_ONLY:
            result = self._export_batch_performance_only(traces)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            self.logger.info(f"Batch export written to {output_file}")
        
        return result
    
    def get_performance_summary(
        self, 
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> dict[str, Any]:
        """Get performance summary across traces"""
        # Collect relevant traces
        relevant_traces = []
        all_traces = list(self.active_traces.values()) + list(self.completed_traces.values())
        
        for trace in all_traces:
            # Filter by session if specified
            if session_id and trace.session_id != session_id:
                continue
            
            # Filter by time range if specified
            if start_time and trace.start_time < start_time:
                continue
            if end_time and trace.start_time > end_time:
                continue
            
            relevant_traces.append(trace)
        
        if not relevant_traces:
            return {
                "total_traces": 0,
                "time_range": {
                    "start": start_time.isoformat() if start_time else None,
                    "end": end_time.isoformat() if end_time else None
                },
                "session_filter": session_id
            }
        
        # Calculate aggregated metrics
        total_traces = len(relevant_traces)
        completed_traces = [t for t in relevant_traces if t.end_time is not None]
        
        # Timing metrics
        avg_processing_time = 0
        avg_ai_processing_time = 0
        total_cost = 0
        total_tokens = 0
        escalation_count = 0
        quality_intervention_count = 0
        
        if completed_traces:
            processing_times = [t.total_duration_ms for t in completed_traces]
            avg_processing_time = sum(processing_times) / len(processing_times)
            
            for trace in completed_traces:
                if trace.performance_metrics:
                    avg_ai_processing_time += trace.performance_metrics.ai_processing_time_ms
                    total_cost += trace.performance_metrics.total_cost_usd
                    total_tokens += trace.performance_metrics.total_tokens_used
                    if trace.performance_metrics.escalation_occurred:
                        escalation_count += 1
                    quality_intervention_count += trace.performance_metrics.quality_interventions
            
            if completed_traces:
                avg_ai_processing_time /= len(completed_traces)
        
        # Agent usage statistics
        agent_usage = {}
        for trace in relevant_traces:
            for interaction in trace.agent_interactions:
                agent_name = interaction.agent_name
                if agent_name not in agent_usage:
                    agent_usage[agent_name] = {
                        "count": 0,
                        "total_duration_ms": 0,
                        "avg_duration_ms": 0
                    }
                agent_usage[agent_name]["count"] += 1
                agent_usage[agent_name]["total_duration_ms"] += interaction.duration_ms
        
        # Calculate averages for agent usage
        for agent_stats in agent_usage.values():
            if agent_stats["count"] > 0:
                agent_stats["avg_duration_ms"] = agent_stats["total_duration_ms"] / agent_stats["count"]
        
        return {
            "total_traces": total_traces,
            "completed_traces": len(completed_traces),
            "active_traces": total_traces - len(completed_traces),
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None
            },
            "session_filter": session_id,
            "performance_metrics": {
                "avg_processing_time_ms": avg_processing_time,
                "avg_ai_processing_time_ms": avg_ai_processing_time,
                "total_cost_usd": total_cost,
                "avg_cost_per_trace": total_cost / max(len(completed_traces), 1),
                "total_tokens_used": total_tokens,
                "avg_tokens_per_trace": total_tokens / max(len(completed_traces), 1),
                "escalation_rate": (escalation_count / max(len(completed_traces), 1)) * 100,
                "avg_quality_interventions": quality_intervention_count / max(len(completed_traces), 1)
            },
            "agent_usage": agent_usage
        }
    
    def cleanup_old_traces(self, max_age_days: int = 30) -> int:
        """Clean up old trace data"""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        old_trace_ids = []
        
        for trace_id, trace in self.completed_traces.items():
            if trace.start_time < cutoff_time:
                old_trace_ids.append(trace_id)
        
        for trace_id in old_trace_ids:
            del self.completed_traces[trace_id]
        
        self.logger.info(
            "Old traces cleaned up",
            extra={
                "traces_cleaned": len(old_trace_ids),
                "cutoff_days": max_age_days,
                "cutoff_time": cutoff_time.isoformat(),
                "operation": "cleanup_old_traces"
            }
        )
        
        return len(old_trace_ids)
    
    def _calculate_performance_metrics(self, trace: InteractionTrace) -> PerformanceMetrics:
        """Calculate performance metrics for a trace"""
        total_duration_ms = trace.total_duration_ms
        ai_processing_time_ms = sum(i.duration_ms for i in trace.agent_interactions)
        
        # Extract metadata from agent interactions
        total_tokens = 0
        total_cost = 0.0
        for interaction in trace.agent_interactions:
            metadata = interaction.response_metadata
            total_tokens += metadata.get("tokens_input", 0) + metadata.get("tokens_output", 0)
            total_cost += metadata.get("cost_usd", 0.0)
        
        # Determine if escalation occurred
        escalation_occurred = any(
            "escalat" in interaction.next_action.lower() or 
            "human" in interaction.next_action.lower()
            for interaction in trace.agent_interactions
        )
        
        # Count quality interventions
        quality_interventions = sum(
            1 for decision in trace.system_decisions
            if decision.decision_point == "quality_gate" and "intervention" in decision.decision.lower()
        )
        
        return PerformanceMetrics(
            total_processing_time_ms=total_duration_ms,
            ai_processing_time_ms=ai_processing_time_ms,
            routing_time_ms=0.0,  # Could be calculated from routing agent timing
            queue_wait_time_ms=0.0,  # Could be calculated from workflow stages
            total_tokens_used=total_tokens,
            total_cost_usd=total_cost,
            agents_involved=len(trace.agent_interactions),
            escalation_occurred=escalation_occurred,
            quality_interventions=quality_interventions,
            customer_satisfaction_predicted=None  # Could be extracted from outcome
        )
    
    def _manage_memory(self) -> None:
        """Manage memory usage by removing old completed traces"""
        if len(self.completed_traces) > self.max_traces_in_memory:
            # Sort by start time and remove oldest
            sorted_traces = sorted(
                self.completed_traces.items(),
                key=lambda x: x[1].start_time
            )
            
            traces_to_remove = len(self.completed_traces) - self.max_traces_in_memory
            for i in range(traces_to_remove):
                trace_id = sorted_traces[i][0]
                del self.completed_traces[trace_id]
            
            self.logger.info(
                f"Memory management: removed {traces_to_remove} old traces",
                extra={"operation": "memory_management"}
            )
    
    def _export_detailed_json(self, trace: InteractionTrace) -> str:
        """Export trace as detailed JSON"""
        trace_dict = {
            "trace_id": trace.trace_id,
            "session_id": trace.session_id,
            "user_id": trace.user_id,
            "query_id": trace.query_id,
            "trace_metadata": {
                "start_time": trace.start_time.isoformat(),
                "end_time": trace.end_time.isoformat() if trace.end_time else None,
                "total_duration_ms": trace.total_duration_ms,
                "trace_version": "1.0"
            },
            "initial_query": trace.initial_query,
            "agent_interactions": [
                {
                    "agent_name": i.agent_name,
                    "interaction_id": i.interaction_id,
                    "sequence_number": i.sequence_number,
                    "start_time": i.start_time.isoformat(),
                    "end_time": i.end_time.isoformat(),
                    "duration_ms": i.duration_ms,
                    "input": i.input_data,
                    "output": i.output_data,
                    "response_metadata": i.response_metadata,
                    "next_action": i.next_action
                }
                for i in trace.agent_interactions
            ],
            "system_decisions": [
                {
                    "decision_point": d.decision_point,
                    "timestamp": d.timestamp.isoformat(),
                    "decision": d.decision,
                    "reasoning": d.reasoning,
                    "factors": d.factors,
                    "confidence": d.confidence
                }
                for d in trace.system_decisions
            ],
            "workflow_progression": [
                {
                    "stage": w.stage,
                    "timestamp": w.timestamp.isoformat(),
                    "duration_from_start_ms": w.duration_from_start_ms
                }
                for w in trace.workflow_progression
            ],
            "performance_metrics": {
                "total_processing_time_ms": trace.performance_metrics.total_processing_time_ms,
                "ai_processing_time_ms": trace.performance_metrics.ai_processing_time_ms,
                "routing_time_ms": trace.performance_metrics.routing_time_ms,
                "queue_wait_time_ms": trace.performance_metrics.queue_wait_time_ms,
                "total_tokens_used": trace.performance_metrics.total_tokens_used,
                "total_cost_usd": trace.performance_metrics.total_cost_usd,
                "agents_involved": trace.performance_metrics.agents_involved,
                "escalation_occurred": trace.performance_metrics.escalation_occurred,
                "quality_interventions": trace.performance_metrics.quality_interventions,
                "customer_satisfaction_predicted": trace.performance_metrics.customer_satisfaction_predicted
            } if trace.performance_metrics else None,
            "outcome": trace.outcome,
            "context_data": trace.context_data
        }
        
        return json.dumps(trace_dict, indent=2, default=str)
    
    def _export_summary_json(self, trace: InteractionTrace) -> str:
        """Export trace as summary JSON"""
        summary = {
            "trace_id": trace.trace_id,
            "session_id": trace.session_id,
            "user_id": trace.user_id,
            "start_time": trace.start_time.isoformat(),
            "end_time": trace.end_time.isoformat() if trace.end_time else None,
            "total_duration_ms": trace.total_duration_ms,
            "agents_used": [i.agent_name for i in trace.agent_interactions],
            "system_decisions_count": len(trace.system_decisions),
            "escalation_occurred": trace.performance_metrics.escalation_occurred if trace.performance_metrics else False,
            "total_cost_usd": trace.performance_metrics.total_cost_usd if trace.performance_metrics else 0,
            "final_outcome": trace.outcome.get("final_resolution", "unknown")
        }
        
        return json.dumps(summary, indent=2, default=str)
    
    def _export_csv_timeline(self, trace: InteractionTrace) -> str:
        """Export trace as CSV timeline"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "timestamp", "event_type", "duration_ms", "agent_name", 
            "stage", "decision", "details"
        ])
        
        # Write workflow stages
        for stage in trace.workflow_progression:
            writer.writerow([
                stage.timestamp.isoformat(),
                "workflow_stage",
                stage.duration_from_start_ms,
                "",
                stage.stage,
                "",
                ""
            ])
        
        # Write agent interactions
        for interaction in trace.agent_interactions:
            writer.writerow([
                interaction.start_time.isoformat(),
                "agent_interaction",
                interaction.duration_ms,
                interaction.agent_name,
                "",
                "",
                f"Next: {interaction.next_action}"
            ])
        
        # Write system decisions
        for decision in trace.system_decisions:
            writer.writerow([
                decision.timestamp.isoformat(),
                "system_decision",
                "",
                "",
                "",
                decision.decision,
                decision.reasoning
            ])
        
        return output.getvalue()
    
    def _export_performance_only(self, trace: InteractionTrace) -> str:
        """Export performance metrics only"""
        if not trace.performance_metrics:
            return json.dumps({"error": "No performance metrics available"})
        
        performance_data = {
            "trace_id": trace.trace_id,
            "total_processing_time_ms": trace.performance_metrics.total_processing_time_ms,
            "ai_processing_time_ms": trace.performance_metrics.ai_processing_time_ms,
            "total_cost_usd": trace.performance_metrics.total_cost_usd,
            "total_tokens_used": trace.performance_metrics.total_tokens_used,
            "agents_involved": trace.performance_metrics.agents_involved,
            "escalation_occurred": trace.performance_metrics.escalation_occurred,
            "agent_timings": [
                {
                    "agent": i.agent_name,
                    "duration_ms": i.duration_ms,
                    "tokens": i.response_metadata.get("tokens_input", 0) + i.response_metadata.get("tokens_output", 0),
                    "cost": i.response_metadata.get("cost_usd", 0)
                }
                for i in trace.agent_interactions
            ]
        }
        
        return json.dumps(performance_data, indent=2)
    
    def _export_batch_detailed_json(self, traces: list[InteractionTrace]) -> str:
        """Export multiple traces as detailed JSON"""
        batch_data = {
            "export_metadata": {
                "export_time": datetime.now().isoformat(),
                "trace_count": len(traces),
                "format": "detailed_json_batch"
            },
            "traces": [json.loads(self._export_detailed_json(trace)) for trace in traces]
        }
        return json.dumps(batch_data, indent=2, default=str)
    
    def _export_batch_summary_json(self, traces: list[InteractionTrace]) -> str:
        """Export multiple traces as summary JSON"""
        batch_data = {
            "export_metadata": {
                "export_time": datetime.now().isoformat(),
                "trace_count": len(traces),
                "format": "summary_json_batch"
            },
            "traces": [json.loads(self._export_summary_json(trace)) for trace in traces]
        }
        return json.dumps(batch_data, indent=2, default=str)
    
    def _export_batch_csv_timeline(self, traces: list[InteractionTrace]) -> str:
        """Export multiple traces as combined CSV timeline"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "trace_id", "timestamp", "event_type", "duration_ms", 
            "agent_name", "stage", "decision", "details"
        ])
        
        for trace in traces:
            # Parse the single trace CSV and add trace_id column
            single_csv = self._export_csv_timeline(trace)
            lines = single_csv.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                row = [trace.trace_id] + line.split(',')
                writer.writerow(row)
        
        return output.getvalue()
    
    def _export_batch_performance_only(self, traces: list[InteractionTrace]) -> str:
        """Export multiple traces performance metrics"""
        batch_data = {
            "export_metadata": {
                "export_time": datetime.now().isoformat(),
                "trace_count": len(traces),
                "format": "performance_only_batch"
            },
            "traces": [json.loads(self._export_performance_only(trace)) for trace in traces]
        }
        return json.dumps(batch_data, indent=2, default=str)