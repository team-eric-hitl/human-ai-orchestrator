"""Scoring configuration management interface."""

from abc import ABC, abstractmethod
from typing import Dict, Optional
from .models import ScoringWeights


class ScoringConfigManager(ABC):
    """Abstract interface for scoring configuration management."""

    @abstractmethod
    async def get_scoring_weights(
        self,
        context_type: str = "default",
        priority_level: int = 1
    ) -> ScoringWeights:
        """
        Get scoring weights for a specific context.
        
        Args:
            context_type: Type of context (e.g., "default", "emergency", "vip")
            priority_level: Priority level (1-5)
            
        Returns:
            Scoring weights configuration
        """
        pass

    @abstractmethod
    async def get_wellbeing_thresholds(self) -> Dict[str, float]:
        """
        Get wellbeing protection thresholds.
        
        Returns:
            Dictionary of threshold values
        """
        pass

    @abstractmethod
    async def get_performance_targets(self) -> Dict[str, float]:
        """
        Get performance targets for scoring.
        
        Returns:
            Dictionary of performance target values
        """
        pass

    @abstractmethod
    async def reload_configuration(self) -> bool:
        """
        Reload configuration from files.
        
        Returns:
            True if reload successful, False otherwise
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> Dict[str, str]:
        """
        Validate current configuration.
        
        Returns:
            Dictionary of validation errors (empty if valid)
        """
        pass