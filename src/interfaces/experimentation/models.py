"""
Data models for experimentation results and configurations

This module defines the data structures used throughout the experimentation
system to ensure consistency and type safety.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class OptimizationTarget(Enum):
    """Targets for optimization during experimentation"""
    RESPONSE_QUALITY = "response_quality"
    RESPONSE_TIME = "response_time"
    ESCALATION_RATE = "escalation_rate"
    USER_SATISFACTION = "user_satisfaction"
    COST_EFFICIENCY = "cost_efficiency"
    OVERALL_SCORE = "overall_score"


@dataclass
class PromptVariant:
    """A variant of a prompt for experimentation
    
    Attributes:
        name: Human-readable name for this variant
        system_prompt: System prompt text
        user_prompt_template: Template for user prompts (can include placeholders)
        parameters: Additional parameters for this variant
        metadata: Additional metadata about this variant
    """
    name: str
    system_prompt: str
    user_prompt_template: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThresholdExperiment:
    """Configuration for threshold-based experimentation
    
    Attributes:
        parameter_name: Name of the parameter to vary
        min_value: Minimum value to test
        max_value: Maximum value to test
        step_size: Step size for value increments
        test_cases: List of test cases to evaluate
        metadata: Additional metadata
    """
    parameter_name: str
    min_value: float
    max_value: float
    step_size: float
    test_cases: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Result of a single experiment run
    
    Attributes:
        experiment_id: Unique identifier for this experiment
        variant_name: Name of the variant tested
        test_case: Test case input
        response: Generated response
        metrics: Performance metrics for this run
        execution_time: Time taken for this experiment
        timestamp: When this experiment was run
        error_message: Error message if experiment failed
        metadata: Additional metadata
    """
    experiment_id: str
    variant_name: str
    test_case: str
    response: str
    metrics: Dict[str, float]
    execution_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Whether this experiment completed successfully"""
        return self.error_message is None
    
    @property
    def overall_score(self) -> float:
        """Calculate overall score from metrics"""
        if not self.metrics:
            return 0.0
        return sum(self.metrics.values()) / len(self.metrics)


@dataclass
class ExperimentResults:
    """Collection of experiment results with analysis
    
    Attributes:
        experiment_type: Type of experiment run
        start_time: When the experiment batch started
        end_time: When the experiment batch completed
        total_experiments: Total number of experiments run
        successful_experiments: Number of successful experiments
        results: List of individual experiment results
        best_variant: Name of the best performing variant
        best_score: Score of the best variant
        analysis: Analysis summary of results
        metadata: Additional metadata
    """
    experiment_type: str
    start_time: datetime
    end_time: datetime
    total_experiments: int
    successful_experiments: int
    results: List[ExperimentResult]
    best_variant: str
    best_score: float
    analysis: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.total_experiments == 0:
            return 0.0
        return (self.successful_experiments / self.total_experiments) * 100
    
    @property
    def duration_seconds(self) -> float:
        """Get total duration in seconds"""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def average_execution_time(self) -> float:
        """Get average execution time per experiment"""
        successful_results = [r for r in self.results if r.success]
        if not successful_results:
            return 0.0
        return sum(r.execution_time for r in successful_results) / len(successful_results)
    
    def get_results_by_variant(self, variant_name: str) -> List[ExperimentResult]:
        """Get all results for a specific variant"""
        return [r for r in self.results if r.variant_name == variant_name]
    
    def get_variant_scores(self) -> Dict[str, float]:
        """Get average scores by variant"""
        variant_scores = {}
        for result in self.results:
            if result.success:
                if result.variant_name not in variant_scores:
                    variant_scores[result.variant_name] = []
                variant_scores[result.variant_name].append(result.overall_score)
        
        return {
            variant: sum(scores) / len(scores)
            for variant, scores in variant_scores.items()
            if scores
        }
    
    def get_metric_analysis(self, metric_name: str) -> Dict[str, Any]:
        """Get analysis for a specific metric across all variants"""
        metric_data = {}
        for result in self.results:
            if result.success and metric_name in result.metrics:
                variant = result.variant_name
                if variant not in metric_data:
                    metric_data[variant] = []
                metric_data[variant].append(result.metrics[metric_name])
        
        analysis = {}
        for variant, values in metric_data.items():
            if values:
                analysis[variant] = {
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }
        
        return analysis