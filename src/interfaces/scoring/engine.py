"""Scoring engine interface."""

from abc import ABC, abstractmethod
from typing import List
from ..human_agents import HumanAgent
from .models import ScoringContext, ScoringResult, ScoringWeights


class ScoringEngine(ABC):
    """Abstract interface for agent scoring engines."""

    @abstractmethod
    async def score_agents(
        self,
        agents: List[HumanAgent],
        context: ScoringContext,
        weights: ScoringWeights
    ) -> ScoringResult:
        """
        Score a list of agents for a given context.
        
        Args:
            agents: List of agents to score
            context: Scoring context with customer factors and requirements
            weights: Weights for different scoring categories
            
        Returns:
            Complete scoring result with ranked agents
        """
        pass

    @abstractmethod
    async def score_single_agent(
        self,
        agent: HumanAgent,
        context: ScoringContext,
        weights: ScoringWeights
    ) -> float:
        """
        Score a single agent for a given context.
        
        Args:
            agent: Agent to score
            context: Scoring context
            weights: Scoring weights
            
        Returns:
            Final composite score (0.0 to 1.0)
        """
        pass

    @abstractmethod
    def explain_score(
        self,
        agent: HumanAgent,
        context: ScoringContext,
        weights: ScoringWeights
    ) -> List[str]:
        """
        Provide human-readable explanation of score calculation.
        
        Args:
            agent: Agent that was scored
            context: Scoring context used
            weights: Weights used
            
        Returns:
            List of explanation strings
        """
        pass

    @abstractmethod
    def validate_configuration(self, weights: ScoringWeights) -> List[str]:
        """
        Validate scoring configuration.
        
        Args:
            weights: Scoring weights to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass