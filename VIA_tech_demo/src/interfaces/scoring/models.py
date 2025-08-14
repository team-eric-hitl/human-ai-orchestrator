"""Scoring system models and types."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ScoreCategory(str, Enum):
    """Categories for agent scoring."""
    SKILL_MATCH = "skill_match"
    AVAILABILITY = "availability" 
    PERFORMANCE_HISTORY = "performance_history"
    WELLBEING_FACTOR = "wellbeing_factor"
    CUSTOMER_FACTOR = "customer_factor"
    WORKLOAD_BALANCE = "workload_balance"


class ScoringWeights(BaseModel):
    """Weights for different scoring categories."""
    skill_match: float = Field(default=0.25, ge=0.0, le=1.0)
    availability: float = Field(default=0.20, ge=0.0, le=1.0)
    performance_history: float = Field(default=0.20, ge=0.0, le=1.0)
    wellbeing_factor: float = Field(default=0.15, ge=0.0, le=1.0)
    customer_factor: float = Field(default=0.10, ge=0.0, le=1.0)
    workload_balance: float = Field(default=0.10, ge=0.0, le=1.0)
    
    def validate_weights(self) -> bool:
        """Validate that weights sum to 1.0."""
        total = (
            self.skill_match + self.availability + self.performance_history +
            self.wellbeing_factor + self.customer_factor + self.workload_balance
        )
        return abs(total - 1.0) < 0.001


class CustomerFactors(BaseModel):
    """Customer-specific factors that influence agent selection."""
    priority_level: int = Field(default=1, ge=1, le=5, description="1=Low, 5=Critical")
    language_preference: Optional[str] = Field(default=None)
    previous_agent_id: Optional[str] = Field(default=None)
    issue_complexity: int = Field(default=1, ge=1, le=5, description="1=Simple, 5=Very Complex")
    customer_tier: str = Field(default="standard", description="standard, premium, vip")
    estimated_duration_minutes: Optional[int] = Field(default=None, ge=1)
    requires_escalation: bool = Field(default=False)


class ScoringContext(BaseModel):
    """Context information for scoring agents."""
    specialization_required: Optional[str] = None
    customer_factors: CustomerFactors = Field(default_factory=CustomerFactors)
    exclude_agent_ids: List[str] = Field(default_factory=list)
    urgency_multiplier: float = Field(default=1.0, ge=0.1, le=3.0)
    conversation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of an agent's score."""
    skill_match_score: float = Field(ge=0.0, le=1.0)
    availability_score: float = Field(ge=0.0, le=1.0)
    performance_score: float = Field(ge=0.0, le=1.0)
    wellbeing_score: float = Field(ge=0.0, le=1.0)
    customer_factor_score: float = Field(ge=0.0, le=1.0)
    workload_balance_score: float = Field(ge=0.0, le=1.0)
    
    # Weighted scores
    weighted_skill_match: float = Field(ge=0.0, le=1.0)
    weighted_availability: float = Field(ge=0.0, le=1.0)
    weighted_performance: float = Field(ge=0.0, le=1.0)
    weighted_wellbeing: float = Field(ge=0.0, le=1.0)
    weighted_customer_factor: float = Field(ge=0.0, le=1.0)
    weighted_workload_balance: float = Field(ge=0.0, le=1.0)
    
    # Final composite score
    composite_score: float = Field(ge=0.0, le=1.0)
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in score accuracy")
    
    # Additional metadata
    calculation_notes: List[str] = Field(default_factory=list)
    penalties_applied: Dict[str, float] = Field(default_factory=dict)
    bonuses_applied: Dict[str, float] = Field(default_factory=dict)


class AgentScore(BaseModel):
    """Complete scoring result for an agent."""
    agent_id: str
    agent_name: str
    final_score: float = Field(ge=0.0, le=1.0)
    is_available: bool
    can_handle_request: bool
    
    # Detailed breakdown
    score_breakdown: ScoreBreakdown
    
    # Ranking information
    rank: Optional[int] = None
    relative_score: Optional[float] = None  # Score relative to other candidates
    
    # Decision factors
    blocking_factors: List[str] = Field(default_factory=list)
    recommendation_reasons: List[str] = Field(default_factory=list)
    
    # Metadata
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    scoring_version: str = Field(default="1.0")


class ScoringResult(BaseModel):
    """Complete result of the scoring process."""
    context: ScoringContext
    weights_used: ScoringWeights
    
    # Results
    scored_agents: List[AgentScore]
    best_agent: Optional[AgentScore] = None
    alternative_agents: List[AgentScore] = Field(default_factory=list)
    
    # Process metadata
    total_agents_evaluated: int
    scoring_duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Decision trail
    selection_reasoning: List[str] = Field(default_factory=list)
    fallback_strategies_applied: List[str] = Field(default_factory=list)
    
    def get_top_n_agents(self, n: int = 3) -> List[AgentScore]:
        """Get top N agents by score."""
        available_agents = [agent for agent in self.scored_agents if agent.is_available and agent.can_handle_request]
        return sorted(available_agents, key=lambda a: a.final_score, reverse=True)[:n]
    
    def get_score_distribution(self) -> Dict[str, float]:
        """Get distribution statistics of scores."""
        scores = [agent.final_score for agent in self.scored_agents if agent.can_handle_request]
        if not scores:
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "std": 0.0}
        
        return {
            "min": min(scores),
            "max": max(scores),
            "avg": sum(scores) / len(scores),
            "count": len(scores)
        }