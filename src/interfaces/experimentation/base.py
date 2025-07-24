"""
Base interfaces for experimentation systems

This module defines the fundamental contracts for all experimentation
implementations in the hybrid AI system.
"""

from abc import ABC, abstractmethod

from .models import (
    ExperimentResults,
    OptimizationTarget,
    PromptVariant,
    ThresholdExperiment,
)


class ExperimentationInterface(ABC):
    """Abstract base class for experimentation systems
    
    Experimentation systems are responsible for:
    - Running A/B tests on prompts and configurations
    - Optimizing agent parameters through systematic testing
    - Evaluating performance across different scenarios
    - Providing insights and recommendations
    
    Implementations should handle:
    - Integration with existing agent infrastructure
    - Parallel execution of experiments for efficiency
    - Robust error handling and recovery
    - Detailed metrics collection and analysis
    """

    @abstractmethod
    def run_prompt_experiments(
        self,
        variants: list[PromptVariant],
        test_cases: list[str],
        agent_type: str = "answer_agent",
        iterations: int = 1
    ) -> ExperimentResults:
        """Run experiments with different prompt variants
        
        Tests multiple prompt variants against a set of test cases to
        determine which prompts produce the best results.
        
        Args:
            variants: List of prompt variants to test
            test_cases: List of test inputs to evaluate
            agent_type: Type of agent to test (answer_agent, evaluator_agent, etc.)
            iterations: Number of iterations per variant-test_case combination
            
        Returns:
            ExperimentResults containing analysis of all experiments
            
        Raises:
            ExperimentationError: If experiments cannot be run
        """
        pass

    @abstractmethod
    def run_threshold_experiments(
        self,
        experiments: list[ThresholdExperiment],
        agent_type: str = "evaluator_agent"
    ) -> ExperimentResults:
        """Run experiments with different threshold values
        
        Tests different threshold values (e.g., escalation thresholds,
        confidence thresholds) to find optimal settings.
        
        Args:
            experiments: List of threshold experiments to run
            agent_type: Type of agent to test thresholds for
            
        Returns:
            ExperimentResults containing threshold optimization results
            
        Raises:
            ExperimentationError: If experiments cannot be run
        """
        pass

    @abstractmethod
    def run_continuous_optimization(
        self,
        target: OptimizationTarget,
        test_cases: list[str],
        iterations: int = 10,
        agent_type: str = "answer_agent"
    ) -> ExperimentResults:
        """Run continuous optimization loop
        
        Continuously optimizes agent performance by iteratively testing
        and refining configurations based on performance feedback.
        
        Args:
            target: What to optimize for (quality, speed, cost, etc.)
            test_cases: Test cases to use for optimization
            iterations: Number of optimization iterations
            agent_type: Type of agent to optimize
            
        Returns:
            ExperimentResults containing optimization progress and final results
            
        Raises:
            ExperimentationError: If optimization cannot be run
        """
        pass

    @abstractmethod
    def run_model_comparison(
        self,
        model_names: list[str],
        test_cases: list[str],
        agent_type: str = "answer_agent"
    ) -> ExperimentResults:
        """Compare performance across different LLM models
        
        Tests the same prompts and configurations across different
        LLM models to determine the best model for specific use cases.
        
        Args:
            model_names: List of model names to compare
            test_cases: Test cases to evaluate
            agent_type: Type of agent to test
            
        Returns:
            ExperimentResults containing model comparison analysis
            
        Raises:
            ExperimentationError: If comparison cannot be run
        """
        pass

    @abstractmethod
    def run_configuration_sweep(
        self,
        parameter_ranges: dict[str, list[float]],
        test_cases: list[str],
        agent_type: str = "answer_agent"
    ) -> ExperimentResults:
        """Run systematic sweep of configuration parameters
        
        Tests all combinations of parameter values to find optimal
        configurations through grid search or similar approaches.
        
        Args:
            parameter_ranges: Dictionary mapping parameter names to value ranges
            test_cases: Test cases to evaluate
            agent_type: Type of agent to test
            
        Returns:
            ExperimentResults containing configuration optimization results
            
        Raises:
            ExperimentationError: If parameter sweep cannot be run
        """
        pass

    @abstractmethod
    def get_experiment_history(
        self,
        experiment_type: str | None = None,
        limit: int | None = None
    ) -> list[ExperimentResults]:
        """Get history of past experiments
        
        Retrieves historical experiment results for analysis and comparison.
        
        Args:
            experiment_type: Filter by experiment type (optional)
            limit: Maximum number of results to return (optional)
            
        Returns:
            List of ExperimentResults from past experiments
        """
        pass

    @abstractmethod
    def get_best_configurations(
        self,
        target: OptimizationTarget,
        agent_type: str = "answer_agent"
    ) -> dict[str, any]:
        """Get best configurations for a specific optimization target
        
        Returns the best known configurations based on historical
        experiment results for a given optimization target.
        
        Args:
            target: What was optimized for
            agent_type: Type of agent
            
        Returns:
            Dictionary containing best configuration parameters
        """
        pass

    @property
    @abstractmethod
    def supported_agent_types(self) -> list[str]:
        """Get list of supported agent types for experimentation
        
        Returns:
            List of agent type names that can be experimented with
        """
        pass

    @property
    @abstractmethod
    def experimenter_name(self) -> str:
        """Get name of this experimenter implementation
        
        Returns:
            Human-readable name for this experimenter
        """
        pass
