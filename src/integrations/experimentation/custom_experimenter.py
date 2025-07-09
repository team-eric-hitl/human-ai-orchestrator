"""
Custom experimentation implementation

This module provides a custom implementation of the experimentation interface
that integrates with the existing agent infrastructure.
"""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from itertools import product
from typing import Any, Dict, List, Optional

from ...core.config import ConfigManager
from ...core.logging import get_logger
from ...core.session_tracker import SessionTracker
from ...integrations.llm_providers import LLMProviderFactory
from ...interfaces.experimentation import (
    ExperimentationInterface,
    ExperimentResult,
    ExperimentResults,
    OptimizationTarget,
    PromptVariant,
    ThresholdExperiment,
)
from ...nodes.answer_agent import AnswerAgentNode
from ...nodes.evaluator_agent import EvaluatorAgentNode


class CustomExperimenter(ExperimentationInterface):
    """Custom experimentation implementation using existing infrastructure
    
    This implementation leverages the existing agent nodes, configuration
    management, and session tracking to provide comprehensive experimentation
    capabilities.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        session_tracker: SessionTracker,
        llm_factory: LLMProviderFactory,
        max_workers: int = 4
    ):
        """Initialize the custom experimenter
        
        Args:
            config_manager: Configuration management instance
            session_tracker: Session tracking instance
            llm_factory: LLM provider factory
            max_workers: Maximum number of concurrent experiments
        """
        self.config_manager = config_manager
        self.session_tracker = session_tracker
        self.llm_factory = llm_factory
        self.max_workers = max_workers
        self.logger = get_logger("experimentation.custom")
        
        # Store experiment history
        self.experiment_history: List[ExperimentResults] = []
        
        self.logger.info(
            "Custom experimenter initialized",
            extra={
                "max_workers": max_workers,
                "config_dir": config_manager.config_dir
            }
        )
    
    def run_prompt_experiments(
        self,
        variants: List[PromptVariant],
        test_cases: List[str],
        agent_type: str = "answer_agent",
        iterations: int = 1
    ) -> ExperimentResults:
        """Run experiments with different prompt variants"""
        start_time = datetime.now()
        experiment_id = str(uuid.uuid4())
        
        self.logger.info(
            "Starting prompt experiments",
            extra={
                "experiment_id": experiment_id,
                "variants_count": len(variants),
                "test_cases_count": len(test_cases),
                "agent_type": agent_type,
                "iterations": iterations
            }
        )
        
        results = []
        total_experiments = len(variants) * len(test_cases) * iterations
        
        # Create experiment tasks
        tasks = []
        for variant in variants:
            for test_case in test_cases:
                for iteration in range(iterations):
                    tasks.append((experiment_id, variant, test_case, iteration, agent_type))
        
        # Run experiments in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._run_single_prompt_experiment, *task): task
                for task in tasks
            }
            
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    task = future_to_task[future]
                    self.logger.error(
                        "Experiment failed",
                        exc_info=True,
                        extra={
                            "experiment_id": experiment_id,
                            "variant": task[1].name,
                            "test_case": task[2][:50] + "..." if len(task[2]) > 50 else task[2],
                            "error": str(e)
                        }
                    )
                    # Create error result
                    results.append(ExperimentResult(
                        experiment_id=experiment_id,
                        variant_name=task[1].name,
                        test_case=task[2],
                        response="",
                        metrics={},
                        execution_time=0.0,
                        timestamp=datetime.now(),
                        error_message=str(e)
                    ))
        
        end_time = datetime.now()
        
        # Analyze results
        successful_results = [r for r in results if r.success]
        variant_scores = self._calculate_variant_scores(successful_results)
        best_variant, best_score = self._find_best_variant(variant_scores)
        
        experiment_results = ExperimentResults(
            experiment_type="prompt_experiments",
            start_time=start_time,
            end_time=end_time,
            total_experiments=total_experiments,
            successful_experiments=len(successful_results),
            results=results,
            best_variant=best_variant,
            best_score=best_score,
            analysis=self._analyze_prompt_results(results, variants),
            metadata={
                "agent_type": agent_type,
                "iterations": iterations,
                "experiment_id": experiment_id
            }
        )
        
        self.experiment_history.append(experiment_results)
        
        self.logger.info(
            "Prompt experiments completed",
            extra={
                "experiment_id": experiment_id,
                "total_experiments": total_experiments,
                "successful_experiments": len(successful_results),
                "best_variant": best_variant,
                "best_score": best_score,
                "duration_seconds": experiment_results.duration_seconds
            }
        )
        
        return experiment_results
    
    def run_threshold_experiments(
        self,
        experiments: List[ThresholdExperiment],
        agent_type: str = "evaluator_agent"
    ) -> ExperimentResults:
        """Run experiments with different threshold values"""
        start_time = datetime.now()
        experiment_id = str(uuid.uuid4())
        
        self.logger.info(
            "Starting threshold experiments",
            extra={
                "experiment_id": experiment_id,
                "experiments_count": len(experiments),
                "agent_type": agent_type
            }
        )
        
        results = []
        total_experiments = 0
        
        for experiment in experiments:
            # Generate threshold values
            threshold_values = self._generate_threshold_values(experiment)
            total_experiments += len(threshold_values) * len(experiment.test_cases)
            
            # Run experiments for each threshold value
            for threshold_value in threshold_values:
                for test_case in experiment.test_cases:
                    try:
                        result = self._run_single_threshold_experiment(
                            experiment_id,
                            experiment.parameter_name,
                            threshold_value,
                            test_case,
                            agent_type
                        )
                        results.append(result)
                    except Exception as e:
                        self.logger.error(
                            "Threshold experiment failed",
                            exc_info=True,
                            extra={
                                "experiment_id": experiment_id,
                                "parameter": experiment.parameter_name,
                                "threshold": threshold_value,
                                "error": str(e)
                            }
                        )
                        results.append(ExperimentResult(
                            experiment_id=experiment_id,
                            variant_name=f"{experiment.parameter_name}={threshold_value}",
                            test_case=test_case,
                            response="",
                            metrics={},
                            execution_time=0.0,
                            timestamp=datetime.now(),
                            error_message=str(e)
                        ))
        
        end_time = datetime.now()
        
        # Analyze results
        successful_results = [r for r in results if r.success]
        variant_scores = self._calculate_variant_scores(successful_results)
        best_variant, best_score = self._find_best_variant(variant_scores)
        
        experiment_results = ExperimentResults(
            experiment_type="threshold_experiments",
            start_time=start_time,
            end_time=end_time,
            total_experiments=total_experiments,
            successful_experiments=len(successful_results),
            results=results,
            best_variant=best_variant,
            best_score=best_score,
            analysis=self._analyze_threshold_results(results, experiments),
            metadata={
                "agent_type": agent_type,
                "experiment_id": experiment_id
            }
        )
        
        self.experiment_history.append(experiment_results)
        
        self.logger.info(
            "Threshold experiments completed",
            extra={
                "experiment_id": experiment_id,
                "total_experiments": total_experiments,
                "successful_experiments": len(successful_results),
                "best_variant": best_variant,
                "best_score": best_score
            }
        )
        
        return experiment_results
    
    def run_continuous_optimization(
        self,
        target: OptimizationTarget,
        test_cases: List[str],
        iterations: int = 10,
        agent_type: str = "answer_agent"
    ) -> ExperimentResults:
        """Run continuous optimization loop"""
        start_time = datetime.now()
        experiment_id = str(uuid.uuid4())
        
        self.logger.info(
            "Starting continuous optimization",
            extra={
                "experiment_id": experiment_id,
                "target": target.value,
                "test_cases_count": len(test_cases),
                "iterations": iterations,
                "agent_type": agent_type
            }
        )
        
        results = []
        current_config = self._get_baseline_config(agent_type)
        
        for iteration in range(iterations):
            self.logger.info(
                f"Running optimization iteration {iteration + 1}/{iterations}",
                extra={
                    "experiment_id": experiment_id,
                    "iteration": iteration + 1,
                    "current_config": current_config
                }
            )
            
            # Generate variations of current config
            config_variations = self._generate_config_variations(current_config)
            
            # Test each variation
            iteration_results = []
            for config_name, config in config_variations.items():
                for test_case in test_cases:
                    try:
                        result = self._run_single_optimization_experiment(
                            experiment_id,
                            config_name,
                            config,
                            test_case,
                            agent_type,
                            iteration
                        )
                        iteration_results.append(result)
                        results.append(result)
                    except Exception as e:
                        self.logger.error(
                            "Optimization experiment failed",
                            exc_info=True,
                            extra={
                                "experiment_id": experiment_id,
                                "config_name": config_name,
                                "iteration": iteration,
                                "error": str(e)
                            }
                        )
            
            # Find best configuration for this iteration
            if iteration_results:
                best_config = self._find_best_config_for_target(
                    iteration_results, target
                )
                if best_config:
                    current_config = best_config
                    self.logger.info(
                        f"Updated config for iteration {iteration + 1}",
                        extra={
                            "experiment_id": experiment_id,
                            "iteration": iteration + 1,
                            "new_config": current_config
                        }
                    )
        
        end_time = datetime.now()
        
        # Analyze results
        successful_results = [r for r in results if r.success]
        variant_scores = self._calculate_variant_scores(successful_results)
        best_variant, best_score = self._find_best_variant(variant_scores)
        
        experiment_results = ExperimentResults(
            experiment_type="continuous_optimization",
            start_time=start_time,
            end_time=end_time,
            total_experiments=len(results),
            successful_experiments=len(successful_results),
            results=results,
            best_variant=best_variant,
            best_score=best_score,
            analysis=self._analyze_optimization_results(results, target),
            metadata={
                "agent_type": agent_type,
                "target": target.value,
                "iterations": iterations,
                "experiment_id": experiment_id,
                "final_config": current_config
            }
        )
        
        self.experiment_history.append(experiment_results)
        
        self.logger.info(
            "Continuous optimization completed",
            extra={
                "experiment_id": experiment_id,
                "total_experiments": len(results),
                "successful_experiments": len(successful_results),
                "best_variant": best_variant,
                "best_score": best_score,
                "final_config": current_config
            }
        )
        
        return experiment_results
    
    def run_model_comparison(
        self,
        model_names: List[str],
        test_cases: List[str],
        agent_type: str = "answer_agent"
    ) -> ExperimentResults:
        """Compare performance across different LLM models"""
        start_time = datetime.now()
        experiment_id = str(uuid.uuid4())
        
        self.logger.info(
            "Starting model comparison",
            extra={
                "experiment_id": experiment_id,
                "models_count": len(model_names),
                "test_cases_count": len(test_cases),
                "agent_type": agent_type
            }
        )
        
        results = []
        total_experiments = len(model_names) * len(test_cases)
        
        # Create experiment tasks
        tasks = []
        for model_name in model_names:
            for test_case in test_cases:
                tasks.append((experiment_id, model_name, test_case, agent_type))
        
        # Run experiments in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self._run_single_model_experiment, *task): task
                for task in tasks
            }
            
            for future in as_completed(future_to_task):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    task = future_to_task[future]
                    self.logger.error(
                        "Model experiment failed",
                        exc_info=True,
                        extra={
                            "experiment_id": experiment_id,
                            "model_name": task[1],
                            "test_case": task[2][:50] + "..." if len(task[2]) > 50 else task[2],
                            "error": str(e)
                        }
                    )
                    results.append(ExperimentResult(
                        experiment_id=experiment_id,
                        variant_name=task[1],
                        test_case=task[2],
                        response="",
                        metrics={},
                        execution_time=0.0,
                        timestamp=datetime.now(),
                        error_message=str(e)
                    ))
        
        end_time = datetime.now()
        
        # Analyze results
        successful_results = [r for r in results if r.success]
        variant_scores = self._calculate_variant_scores(successful_results)
        best_variant, best_score = self._find_best_variant(variant_scores)
        
        experiment_results = ExperimentResults(
            experiment_type="model_comparison",
            start_time=start_time,
            end_time=end_time,
            total_experiments=total_experiments,
            successful_experiments=len(successful_results),
            results=results,
            best_variant=best_variant,
            best_score=best_score,
            analysis=self._analyze_model_results(results, model_names),
            metadata={
                "agent_type": agent_type,
                "experiment_id": experiment_id
            }
        )
        
        self.experiment_history.append(experiment_results)
        
        self.logger.info(
            "Model comparison completed",
            extra={
                "experiment_id": experiment_id,
                "total_experiments": total_experiments,
                "successful_experiments": len(successful_results),
                "best_variant": best_variant,
                "best_score": best_score
            }
        )
        
        return experiment_results
    
    def run_configuration_sweep(
        self,
        parameter_ranges: Dict[str, List[float]],
        test_cases: List[str],
        agent_type: str = "answer_agent"
    ) -> ExperimentResults:
        """Run systematic sweep of configuration parameters"""
        start_time = datetime.now()
        experiment_id = str(uuid.uuid4())
        
        self.logger.info(
            "Starting configuration sweep",
            extra={
                "experiment_id": experiment_id,
                "parameters": list(parameter_ranges.keys()),
                "test_cases_count": len(test_cases),
                "agent_type": agent_type
            }
        )
        
        results = []
        
        # Generate all parameter combinations
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        combinations = list(product(*param_values))
        
        total_experiments = len(combinations) * len(test_cases)
        
        self.logger.info(
            f"Generated {len(combinations)} parameter combinations",
            extra={
                "experiment_id": experiment_id,
                "combinations_count": len(combinations),
                "total_experiments": total_experiments
            }
        )
        
        # Run experiments for each combination
        for combination in combinations:
            config = dict(zip(param_names, combination))
            config_name = "_".join(f"{k}={v}" for k, v in config.items())
            
            for test_case in test_cases:
                try:
                    result = self._run_single_config_experiment(
                        experiment_id,
                        config_name,
                        config,
                        test_case,
                        agent_type
                    )
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        "Configuration experiment failed",
                        exc_info=True,
                        extra={
                            "experiment_id": experiment_id,
                            "config": config,
                            "test_case": test_case[:50] + "..." if len(test_case) > 50 else test_case,
                            "error": str(e)
                        }
                    )
                    results.append(ExperimentResult(
                        experiment_id=experiment_id,
                        variant_name=config_name,
                        test_case=test_case,
                        response="",
                        metrics={},
                        execution_time=0.0,
                        timestamp=datetime.now(),
                        error_message=str(e)
                    ))
        
        end_time = datetime.now()
        
        # Analyze results
        successful_results = [r for r in results if r.success]
        variant_scores = self._calculate_variant_scores(successful_results)
        best_variant, best_score = self._find_best_variant(variant_scores)
        
        experiment_results = ExperimentResults(
            experiment_type="configuration_sweep",
            start_time=start_time,
            end_time=end_time,
            total_experiments=total_experiments,
            successful_experiments=len(successful_results),
            results=results,
            best_variant=best_variant,
            best_score=best_score,
            analysis=self._analyze_configuration_results(results, parameter_ranges),
            metadata={
                "agent_type": agent_type,
                "parameter_ranges": parameter_ranges,
                "experiment_id": experiment_id
            }
        )
        
        self.experiment_history.append(experiment_results)
        
        self.logger.info(
            "Configuration sweep completed",
            extra={
                "experiment_id": experiment_id,
                "total_experiments": total_experiments,
                "successful_experiments": len(successful_results),
                "best_variant": best_variant,
                "best_score": best_score
            }
        )
        
        return experiment_results
    
    def get_experiment_history(
        self,
        experiment_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ExperimentResults]:
        """Get history of past experiments"""
        filtered_history = self.experiment_history
        
        if experiment_type:
            filtered_history = [
                exp for exp in filtered_history 
                if exp.experiment_type == experiment_type
            ]
        
        # Sort by start time (most recent first)
        filtered_history.sort(key=lambda x: x.start_time, reverse=True)
        
        if limit:
            filtered_history = filtered_history[:limit]
        
        return filtered_history
    
    def get_best_configurations(
        self,
        target: OptimizationTarget,
        agent_type: str = "answer_agent"
    ) -> Dict[str, Any]:
        """Get best configurations for a specific optimization target"""
        # Find relevant experiments
        relevant_experiments = [
            exp for exp in self.experiment_history
            if exp.metadata.get("agent_type") == agent_type
        ]
        
        if not relevant_experiments:
            self.logger.warning(
                "No relevant experiments found",
                extra={
                    "target": target.value,
                    "agent_type": agent_type
                }
            )
            return {}
        
        # Extract best configurations based on target
        best_configs = {}
        for exp in relevant_experiments:
            if exp.experiment_type == "configuration_sweep":
                # Find best configuration from sweep
                best_result = self._find_best_result_for_target(exp.results, target)
                if best_result:
                    config = self._extract_config_from_variant_name(best_result.variant_name)
                    best_configs[exp.experiment_type] = config
        
        return best_configs
    
    @property
    def supported_agent_types(self) -> List[str]:
        """Get list of supported agent types for experimentation"""
        return ["answer_agent", "evaluator_agent", "escalation_router"]
    
    @property
    def experimenter_name(self) -> str:
        """Get name of this experimenter implementation"""
        return "CustomExperimenter"
    
    # Private helper methods
    
    def _run_single_prompt_experiment(
        self,
        experiment_id: str,
        variant: PromptVariant,
        test_case: str,
        iteration: int,
        agent_type: str
    ) -> ExperimentResult:
        """Run a single prompt experiment"""
        start_time = datetime.now()
        
        # Create temporary configuration with the variant
        temp_config = self._create_temp_config_with_prompt(variant, agent_type)
        
        # Create agent with temporary configuration
        agent = self._create_agent(agent_type, temp_config)
        
        # Create test state
        test_state = self._create_test_state(test_case, experiment_id)
        
        # Run the agent
        result_state = agent(test_state)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract response and calculate metrics
        response = result_state.get("ai_response", "")
        metrics = self._calculate_metrics(test_case, response, result_state)
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_name=variant.name,
            test_case=test_case,
            response=response,
            metrics=metrics,
            execution_time=execution_time,
            timestamp=datetime.now(),
            metadata={
                "iteration": iteration,
                "agent_type": agent_type,
                "variant_parameters": variant.parameters
            }
        )
    
    def _run_single_threshold_experiment(
        self,
        experiment_id: str,
        parameter_name: str,
        threshold_value: float,
        test_case: str,
        agent_type: str
    ) -> ExperimentResult:
        """Run a single threshold experiment"""
        start_time = datetime.now()
        
        # Create temporary configuration with threshold
        temp_config = self._create_temp_config_with_threshold(
            parameter_name, threshold_value, agent_type
        )
        
        # Create agent with temporary configuration
        agent = self._create_agent(agent_type, temp_config)
        
        # Create test state
        test_state = self._create_test_state(test_case, experiment_id)
        
        # Run the agent
        result_state = agent(test_state)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract response and calculate metrics
        response = result_state.get("ai_response", "")
        metrics = self._calculate_metrics(test_case, response, result_state)
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_name=f"{parameter_name}={threshold_value}",
            test_case=test_case,
            response=response,
            metrics=metrics,
            execution_time=execution_time,
            timestamp=datetime.now(),
            metadata={
                "parameter_name": parameter_name,
                "threshold_value": threshold_value,
                "agent_type": agent_type
            }
        )
    
    def _run_single_optimization_experiment(
        self,
        experiment_id: str,
        config_name: str,
        config: Dict[str, Any],
        test_case: str,
        agent_type: str,
        iteration: int
    ) -> ExperimentResult:
        """Run a single optimization experiment"""
        start_time = datetime.now()
        
        # Create temporary configuration
        temp_config = self._create_temp_config_with_values(config, agent_type)
        
        # Create agent with temporary configuration
        agent = self._create_agent(agent_type, temp_config)
        
        # Create test state
        test_state = self._create_test_state(test_case, experiment_id)
        
        # Run the agent
        result_state = agent(test_state)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract response and calculate metrics
        response = result_state.get("ai_response", "")
        metrics = self._calculate_metrics(test_case, response, result_state)
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_name=config_name,
            test_case=test_case,
            response=response,
            metrics=metrics,
            execution_time=execution_time,
            timestamp=datetime.now(),
            metadata={
                "iteration": iteration,
                "agent_type": agent_type,
                "config": config
            }
        )
    
    def _run_single_model_experiment(
        self,
        experiment_id: str,
        model_name: str,
        test_case: str,
        agent_type: str
    ) -> ExperimentResult:
        """Run a single model comparison experiment"""
        start_time = datetime.now()
        
        # Create LLM provider for this model
        llm_provider = self.llm_factory.create_provider(model_name)
        
        # Create temporary configuration with this model
        temp_config = self._create_temp_config_with_model(model_name, agent_type)
        
        # Create agent with temporary configuration
        agent = self._create_agent(agent_type, temp_config, llm_provider)
        
        # Create test state
        test_state = self._create_test_state(test_case, experiment_id)
        
        # Run the agent
        result_state = agent(test_state)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract response and calculate metrics
        response = result_state.get("ai_response", "")
        metrics = self._calculate_metrics(test_case, response, result_state)
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_name=model_name,
            test_case=test_case,
            response=response,
            metrics=metrics,
            execution_time=execution_time,
            timestamp=datetime.now(),
            metadata={
                "model_name": model_name,
                "agent_type": agent_type
            }
        )
    
    def _run_single_config_experiment(
        self,
        experiment_id: str,
        config_name: str,
        config: Dict[str, Any],
        test_case: str,
        agent_type: str
    ) -> ExperimentResult:
        """Run a single configuration experiment"""
        start_time = datetime.now()
        
        # Create temporary configuration
        temp_config = self._create_temp_config_with_values(config, agent_type)
        
        # Create agent with temporary configuration
        agent = self._create_agent(agent_type, temp_config)
        
        # Create test state
        test_state = self._create_test_state(test_case, experiment_id)
        
        # Run the agent
        result_state = agent(test_state)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Extract response and calculate metrics
        response = result_state.get("ai_response", "")
        metrics = self._calculate_metrics(test_case, response, result_state)
        
        return ExperimentResult(
            experiment_id=experiment_id,
            variant_name=config_name,
            test_case=test_case,
            response=response,
            metrics=metrics,
            execution_time=execution_time,
            timestamp=datetime.now(),
            metadata={
                "config": config,
                "agent_type": agent_type
            }
        )
    
    def _create_agent(self, agent_type: str, config: Any, llm_provider: Any = None):
        """Create an agent instance for testing"""
        if agent_type == "answer_agent":
            return AnswerAgentNode(
                config or self.config_manager,
                None,  # context_provider - simplified for experimentation
                llm_provider or self.llm_factory.create_auto_provider()
            )
        elif agent_type == "evaluator_agent":
            return EvaluatorAgentNode(
                config or self.config_manager,
                None,  # context_provider - simplified for experimentation
                llm_provider or self.llm_factory.create_auto_provider()
            )
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
    
    def _create_test_state(self, test_case: str, experiment_id: str) -> Dict[str, Any]:
        """Create a test state for experimentation"""
        return {
            "query_id": f"exp_{experiment_id}_{uuid.uuid4().hex[:8]}",
            "user_id": "experiment_user",
            "session_id": f"exp_session_{experiment_id}",
            "timestamp": datetime.now(),
            "query": test_case,
            "messages": []
        }
    
    def _calculate_metrics(
        self,
        test_case: str,
        response: str,
        result_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate metrics for an experiment result"""
        metrics = {}
        
        # Basic metrics
        metrics["response_length"] = len(response)
        metrics["response_time"] = result_state.get("execution_time", 0.0)
        
        # Quality metrics (simplified - in production, use proper evaluation)
        metrics["accuracy"] = 7.5  # Placeholder
        metrics["completeness"] = 8.0  # Placeholder
        metrics["clarity"] = 7.8  # Placeholder
        metrics["user_satisfaction"] = 8.2  # Placeholder
        
        # Derived metrics
        metrics["overall_score"] = (
            metrics["accuracy"] + 
            metrics["completeness"] + 
            metrics["clarity"] + 
            metrics["user_satisfaction"]
        ) / 4.0
        
        return metrics
    
    def _calculate_variant_scores(
        self,
        results: List[ExperimentResult]
    ) -> Dict[str, float]:
        """Calculate average scores by variant"""
        variant_scores = {}
        for result in results:
            if result.variant_name not in variant_scores:
                variant_scores[result.variant_name] = []
            variant_scores[result.variant_name].append(result.overall_score)
        
        return {
            variant: sum(scores) / len(scores)
            for variant, scores in variant_scores.items()
            if scores
        }
    
    def _find_best_variant(
        self,
        variant_scores: Dict[str, float]
    ) -> tuple[str, float]:
        """Find the best performing variant"""
        if not variant_scores:
            return "none", 0.0
        
        best_variant = max(variant_scores.keys(), key=lambda x: variant_scores[x])
        best_score = variant_scores[best_variant]
        
        return best_variant, best_score
    
    def _generate_threshold_values(
        self,
        experiment: ThresholdExperiment
    ) -> List[float]:
        """Generate threshold values for experimentation"""
        values = []
        current = experiment.min_value
        while current <= experiment.max_value:
            values.append(current)
            current += experiment.step_size
        return values
    
    def _get_baseline_config(self, agent_type: str) -> Dict[str, Any]:
        """Get baseline configuration for optimization"""
        return {
            "temperature": 0.7,
            "max_tokens": 1000,
            "threshold": 0.8
        }
    
    def _generate_config_variations(
        self,
        base_config: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate variations of a configuration"""
        variations = {}
        
        # Temperature variations
        for temp in [0.5, 0.7, 0.9]:
            config = base_config.copy()
            config["temperature"] = temp
            variations[f"temp_{temp}"] = config
        
        # Threshold variations
        for threshold in [0.6, 0.8, 0.9]:
            config = base_config.copy()
            config["threshold"] = threshold
            variations[f"threshold_{threshold}"] = config
        
        return variations
    
    def _find_best_config_for_target(
        self,
        results: List[ExperimentResult],
        target: OptimizationTarget
    ) -> Optional[Dict[str, Any]]:
        """Find best configuration for optimization target"""
        if not results:
            return None
        
        # Find best result based on target
        best_result = self._find_best_result_for_target(results, target)
        if not best_result:
            return None
        
        # Extract configuration from result metadata
        return best_result.metadata.get("config", {})
    
    def _find_best_result_for_target(
        self,
        results: List[ExperimentResult],
        target: OptimizationTarget
    ) -> Optional[ExperimentResult]:
        """Find best result for a specific optimization target"""
        successful_results = [r for r in results if r.success]
        if not successful_results:
            return None
        
        if target == OptimizationTarget.RESPONSE_QUALITY:
            return max(successful_results, key=lambda x: x.overall_score)
        elif target == OptimizationTarget.RESPONSE_TIME:
            return min(successful_results, key=lambda x: x.execution_time)
        elif target == OptimizationTarget.OVERALL_SCORE:
            return max(successful_results, key=lambda x: x.overall_score)
        else:
            return max(successful_results, key=lambda x: x.overall_score)
    
    def _extract_config_from_variant_name(self, variant_name: str) -> Dict[str, Any]:
        """Extract configuration from variant name"""
        # Simple parsing - in production, use proper serialization
        config = {}
        parts = variant_name.split("_")
        for part in parts:
            if "=" in part:
                key, value = part.split("=")
                try:
                    config[key] = float(value)
                except ValueError:
                    config[key] = value
        return config
    
    def _create_temp_config_with_prompt(
        self,
        variant: PromptVariant,
        agent_type: str
    ) -> Any:
        """Create temporary configuration with prompt variant"""
        # In production, create proper configuration object
        return self.config_manager  # Simplified for now
    
    def _create_temp_config_with_threshold(
        self,
        parameter_name: str,
        threshold_value: float,
        agent_type: str
    ) -> Any:
        """Create temporary configuration with threshold"""
        return self.config_manager  # Simplified for now
    
    def _create_temp_config_with_values(
        self,
        config: Dict[str, Any],
        agent_type: str
    ) -> Any:
        """Create temporary configuration with values"""
        return self.config_manager  # Simplified for now
    
    def _create_temp_config_with_model(
        self,
        model_name: str,
        agent_type: str
    ) -> Any:
        """Create temporary configuration with specific model"""
        return self.config_manager  # Simplified for now
    
    def _analyze_prompt_results(
        self,
        results: List[ExperimentResult],
        variants: List[PromptVariant]
    ) -> Dict[str, Any]:
        """Analyze prompt experiment results"""
        return {
            "variants_tested": len(variants),
            "total_results": len(results),
            "successful_results": len([r for r in results if r.success]),
            "analysis_type": "prompt_experiments"
        }
    
    def _analyze_threshold_results(
        self,
        results: List[ExperimentResult],
        experiments: List[ThresholdExperiment]
    ) -> Dict[str, Any]:
        """Analyze threshold experiment results"""
        return {
            "parameters_tested": len(experiments),
            "total_results": len(results),
            "successful_results": len([r for r in results if r.success]),
            "analysis_type": "threshold_experiments"
        }
    
    def _analyze_optimization_results(
        self,
        results: List[ExperimentResult],
        target: OptimizationTarget
    ) -> Dict[str, Any]:
        """Analyze optimization results"""
        return {
            "optimization_target": target.value,
            "total_results": len(results),
            "successful_results": len([r for r in results if r.success]),
            "analysis_type": "continuous_optimization"
        }
    
    def _analyze_model_results(
        self,
        results: List[ExperimentResult],
        model_names: List[str]
    ) -> Dict[str, Any]:
        """Analyze model comparison results"""
        return {
            "models_tested": len(model_names),
            "total_results": len(results),
            "successful_results": len([r for r in results if r.success]),
            "analysis_type": "model_comparison"
        }
    
    def _analyze_configuration_results(
        self,
        results: List[ExperimentResult],
        parameter_ranges: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Analyze configuration sweep results"""
        return {
            "parameters_tested": len(parameter_ranges),
            "total_results": len(results),
            "successful_results": len([r for r in results if r.success]),
            "analysis_type": "configuration_sweep"
        }