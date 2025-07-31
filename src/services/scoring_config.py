"""Configuration manager for the scoring system."""

from typing import Dict
from pathlib import Path
import yaml

from ..core.logging import get_logger
from ..interfaces.scoring import ScoringConfigManager, ScoringWeights


class DefaultScoringConfigManager(ScoringConfigManager):
    """Default implementation of scoring configuration manager."""

    def __init__(self, config_base_path: str = "config/agents/routing_agent"):
        """Initialize configuration manager."""
        self.config_base_path = Path(config_base_path)
        self.logger = get_logger(__name__)
        
        # Default configurations
        self._default_weights = {
            "default": ScoringWeights(),
            "emergency": ScoringWeights(
                skill_match=0.30,
                availability=0.35,
                performance_history=0.15,
                wellbeing_factor=0.05,
                customer_factor=0.10,
                workload_balance=0.05
            ),
            "vip": ScoringWeights(
                skill_match=0.35,
                availability=0.20,
                performance_history=0.25,
                wellbeing_factor=0.05,
                customer_factor=0.10,
                workload_balance=0.05
            )
        }
        
        self._wellbeing_thresholds = {
            "max_stress_level": 8.5,
            "max_utilization": 0.9,
            "max_queue_length": 8,
            "min_break_time_hours": 0.25,
            "max_continuous_hours": 6.0
        }
        
        self._performance_targets = {
            "target_satisfaction_score": 8.0,
            "target_response_time_minutes": 5.0,
            "min_experience_for_complex": 3,
            "min_experience_for_vip": 4,
            "max_conversation_duration_minutes": 45
        }

    async def get_scoring_weights(
        self,
        context_type: str = "default",
        priority_level: int = 1
    ) -> ScoringWeights:
        """Get scoring weights for a specific context."""
        try:
            # Determine context type based on priority
            if priority_level >= 4:
                context_type = "emergency"
            elif context_type not in self._default_weights:
                context_type = "default"
            
            # Try to load from file first
            weights_file = self.config_base_path / "scoring_weights.yaml"
            if weights_file.exists():
                with open(weights_file, 'r') as f:
                    config = yaml.safe_load(f)
                    if context_type in config:
                        weights_data = config[context_type]
                        return ScoringWeights(**weights_data)
            
            # Fallback to defaults
            return self._default_weights.get(context_type, self._default_weights["default"])
            
        except Exception as e:
            self.logger.error(f"Failed to load scoring weights for {context_type}: {e}")
            return self._default_weights["default"]

    async def get_wellbeing_thresholds(self) -> Dict[str, float]:
        """Get wellbeing protection thresholds."""
        try:
            thresholds_file = self.config_base_path / "wellbeing_thresholds.yaml"
            if thresholds_file.exists():
                with open(thresholds_file, 'r') as f:
                    config = yaml.safe_load(f)
                    return config
            
            return self._wellbeing_thresholds
            
        except Exception as e:
            self.logger.error(f"Failed to load wellbeing thresholds: {e}")
            return self._wellbeing_thresholds

    async def get_performance_targets(self) -> Dict[str, float]:
        """Get performance targets for scoring."""
        try:
            targets_file = self.config_base_path / "performance_targets.yaml"
            if targets_file.exists():
                with open(targets_file, 'r') as f:
                    config = yaml.safe_load(f)
                    return config
            
            return self._performance_targets
            
        except Exception as e:
            self.logger.error(f"Failed to load performance targets: {e}")
            return self._performance_targets

    async def reload_configuration(self) -> bool:
        """Reload configuration from files."""
        try:
            # In a more sophisticated implementation, this would:
            # 1. Re-read all configuration files
            # 2. Validate the new configuration
            # 3. Update internal caches
            # 4. Notify any listeners of configuration changes
            
            # For now, just log that reload was requested
            self.logger.info("Configuration reload requested - using file-based loading")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            return False

    def validate_configuration(self) -> Dict[str, str]:
        """Validate current configuration."""
        errors = {}
        
        # Validate scoring weights
        for context_type, weights in self._default_weights.items():
            if not weights.validate_weights():
                total = (weights.skill_match + weights.availability + weights.performance_history +
                        weights.wellbeing_factor + weights.customer_factor + weights.workload_balance)
                errors[f"weights_{context_type}"] = f"Weights do not sum to 1.0 (sum: {total:.3f})"
        
        # Validate wellbeing thresholds
        wellbeing = self._wellbeing_thresholds
        if wellbeing["max_stress_level"] < 1.0 or wellbeing["max_stress_level"] > 10.0:
            errors["wellbeing_stress"] = "max_stress_level must be between 1.0 and 10.0"
        
        if wellbeing["max_utilization"] < 0.0 or wellbeing["max_utilization"] > 1.0:
            errors["wellbeing_utilization"] = "max_utilization must be between 0.0 and 1.0"
        
        # Validate performance targets
        performance = self._performance_targets
        if performance["target_satisfaction_score"] < 1.0 or performance["target_satisfaction_score"] > 10.0:
            errors["performance_satisfaction"] = "target_satisfaction_score must be between 1.0 and 10.0"
        
        if performance["target_response_time_minutes"] <= 0:
            errors["performance_response_time"] = "target_response_time_minutes must be positive"
        
        return errors

    def create_sample_configuration_files(self) -> None:
        """Create sample configuration files for reference."""
        try:
            # Ensure directory exists
            self.config_base_path.mkdir(parents=True, exist_ok=True)
            
            # Create scoring weights file
            weights_config = {
                "default": {
                    "skill_match": 0.25,
                    "availability": 0.20,
                    "performance_history": 0.20,
                    "wellbeing_factor": 0.15,
                    "customer_factor": 0.10,
                    "workload_balance": 0.10
                },
                "emergency": {
                    "skill_match": 0.30,
                    "availability": 0.35,
                    "performance_history": 0.15,
                    "wellbeing_factor": 0.05,
                    "customer_factor": 0.10,
                    "workload_balance": 0.05
                },
                "vip": {
                    "skill_match": 0.35,
                    "availability": 0.20,
                    "performance_history": 0.25,
                    "wellbeing_factor": 0.05,
                    "customer_factor": 0.10,
                    "workload_balance": 0.05
                }
            }
            
            weights_file = self.config_base_path / "scoring_weights.yaml"
            with open(weights_file, 'w') as f:
                yaml.dump(weights_config, f, default_flow_style=False, indent=2)
            
            # Create wellbeing thresholds file
            wellbeing_file = self.config_base_path / "wellbeing_thresholds.yaml"
            with open(wellbeing_file, 'w') as f:
                yaml.dump(self._wellbeing_thresholds, f, default_flow_style=False, indent=2)
            
            # Create performance targets file
            targets_file = self.config_base_path / "performance_targets.yaml"
            with open(targets_file, 'w') as f:
                yaml.dump(self._performance_targets, f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Created sample configuration files in {self.config_base_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to create sample configuration files: {e}")
            raise