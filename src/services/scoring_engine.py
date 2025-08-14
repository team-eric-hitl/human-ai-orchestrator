"""Default implementation of the agent scoring engine."""

import time
from datetime import datetime
from typing import List, Dict
import math

from ..core.logging import get_logger
from ..interfaces.scoring import ScoringEngine, AgentScore, ScoreBreakdown, ScoringContext, ScoringResult, ScoringWeights
from ..interfaces.human_agents import HumanAgent, HumanAgentStatus, Specialization


class DefaultScoringEngine(ScoringEngine):
    """Default implementation of agent scoring engine."""

    def __init__(self):
        """Initialize scoring engine."""
        self.logger = get_logger(__name__)

    async def score_agents(
        self,
        agents: List[HumanAgent],
        context: ScoringContext,
        weights: ScoringWeights
    ) -> ScoringResult:
        """Score a list of agents for a given context."""
        start_time = time.time()
        
        # Validate configuration
        validation_errors = self.validate_configuration(weights)
        if validation_errors:
            raise ValueError(f"Invalid scoring configuration: {validation_errors}")

        scored_agents = []
        selection_reasoning = []
        
        for agent in agents:
            try:
                # Skip excluded agents
                if agent.id in context.exclude_agent_ids:
                    continue
                
                # Calculate detailed score
                score_breakdown = await self._calculate_detailed_score(agent, context, weights)
                
                # Determine availability and capability
                is_available = await self._check_availability(agent, context)
                can_handle = await self._check_capability(agent, context)
                
                # Create agent score
                agent_score = AgentScore(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    final_score=score_breakdown.composite_score,
                    is_available=is_available,
                    can_handle_request=can_handle,
                    score_breakdown=score_breakdown,
                    blocking_factors=self._get_blocking_factors(agent, context),
                    recommendation_reasons=self._get_recommendation_reasons(agent, context, score_breakdown)
                )
                
                scored_agents.append(agent_score)
                
            except Exception as e:
                self.logger.error(f"Failed to score agent {agent.id}: {e}")
                continue

        # Sort by score and assign ranks
        available_capable_agents = [
            agent for agent in scored_agents 
            if agent.is_available and agent.can_handle_request
        ]
        available_capable_agents.sort(key=lambda a: a.final_score, reverse=True)
        
        for i, agent in enumerate(available_capable_agents):
            agent.rank = i + 1
            if len(available_capable_agents) > 1:
                agent.relative_score = agent.final_score / available_capable_agents[0].final_score

        # Select best agent and alternatives
        best_agent = available_capable_agents[0] if available_capable_agents else None
        alternatives = available_capable_agents[1:4] if len(available_capable_agents) > 1 else []

        # Add selection reasoning
        if best_agent:
            selection_reasoning.append(f"Selected {best_agent.agent_name} with score {best_agent.final_score:.3f}")
            selection_reasoning.extend(best_agent.recommendation_reasons[:3])
        else:
            selection_reasoning.append("No suitable agents found")

        duration_ms = (time.time() - start_time) * 1000

        return ScoringResult(
            context=context,
            weights_used=weights,
            scored_agents=scored_agents,
            best_agent=best_agent,
            alternative_agents=alternatives,
            total_agents_evaluated=len(agents),
            scoring_duration_ms=duration_ms,
            selection_reasoning=selection_reasoning
        )

    async def score_single_agent(
        self,
        agent: HumanAgent,
        context: ScoringContext,
        weights: ScoringWeights
    ) -> float:
        """Score a single agent for a given context."""
        score_breakdown = await self._calculate_detailed_score(agent, context, weights)
        return score_breakdown.composite_score

    def explain_score(
        self,
        agent: HumanAgent,
        context: ScoringContext,
        weights: ScoringWeights
    ) -> List[str]:
        """Provide human-readable explanation of score calculation."""
        explanations = []
        
        # Basic info
        explanations.append(f"Scoring agent: {agent.name} (ID: {agent.id})")
        explanations.append(f"Status: {agent.status}, Experience: Level {agent.experience_level}")
        
        # Weight information
        explanations.append(f"Scoring weights: Skill Match {weights.skill_match:.1%}, "
                           f"Availability {weights.availability:.1%}, "
                           f"Performance {weights.performance_history:.1%}")
        
        # Context factors
        if context.specialization_required:
            has_spec = context.specialization_required in [s.value if hasattr(s, 'value') else str(s) for s in agent.specializations]
            explanations.append(f"Required specialization '{context.specialization_required}': {'✓' if has_spec else '✗'}")
        
        if context.customer_factors.language_preference:
            has_lang = context.customer_factors.language_preference in agent.languages
            explanations.append(f"Language preference '{context.customer_factors.language_preference}': {'✓' if has_lang else '✗'}")
        
        # Workload factors
        utilization = agent.workload.active_conversations / agent.max_concurrent_conversations
        explanations.append(f"Current utilization: {utilization:.1%} ({agent.workload.active_conversations}/{agent.max_concurrent_conversations})")
        explanations.append(f"Stress level: {agent.workload.stress_level}/10")
        explanations.append(f"Satisfaction score: {agent.workload.satisfaction_score}/10")
        
        return explanations

    def validate_configuration(self, weights: ScoringWeights) -> List[str]:
        """Validate scoring configuration."""
        errors = []
        
        # Check weight sum
        if not weights.validate_weights():
            total = (weights.skill_match + weights.availability + weights.performance_history +
                    weights.wellbeing_factor + weights.customer_factor + weights.workload_balance)
            errors.append(f"Weights do not sum to 1.0 (actual sum: {total:.3f})")
        
        # Check individual weight ranges
        weight_fields = ["skill_match", "availability", "performance_history", 
                        "wellbeing_factor", "customer_factor", "workload_balance"]
        for field in weight_fields:
            value = getattr(weights, field)
            if not (0.0 <= value <= 1.0):
                errors.append(f"Weight {field} must be between 0.0 and 1.0 (actual: {value})")
        
        return errors

    async def _calculate_detailed_score(
        self,
        agent: HumanAgent,
        context: ScoringContext,
        weights: ScoringWeights
    ) -> ScoreBreakdown:
        """Calculate detailed score breakdown for an agent."""
        
        # Individual category scores (0.0 to 1.0)
        skill_score = self._calculate_skill_match_score(agent, context)
        availability_score = self._calculate_availability_score(agent, context)
        performance_score = self._calculate_performance_score(agent, context)
        wellbeing_score = self._calculate_wellbeing_score(agent, context)
        customer_factor_score = self._calculate_customer_factor_score(agent, context)
        workload_score = self._calculate_workload_balance_score(agent, context)
        
        # Apply weights
        weighted_skill = skill_score * weights.skill_match
        weighted_availability = availability_score * weights.availability
        weighted_performance = performance_score * weights.performance_history
        weighted_wellbeing = wellbeing_score * weights.wellbeing_factor
        weighted_customer = customer_factor_score * weights.customer_factor
        weighted_workload = workload_score * weights.workload_balance
        
        # Calculate composite score
        composite_score = (
            weighted_skill + weighted_availability + weighted_performance +
            weighted_wellbeing + weighted_customer + weighted_workload
        )
        
        # Apply urgency multiplier
        if context.urgency_multiplier != 1.0 and composite_score > 0:
            composite_score = min(1.0, composite_score * context.urgency_multiplier)
        
        # Calculate confidence (higher when all factors align)
        score_variance = self._calculate_score_variance([
            skill_score, availability_score, performance_score,
            wellbeing_score, customer_factor_score, workload_score
        ])
        confidence = max(0.1, 1.0 - (score_variance * 2))  # Lower variance = higher confidence
        
        # Collect calculation notes
        notes = []
        if context.urgency_multiplier != 1.0:
            notes.append(f"Applied urgency multiplier: {context.urgency_multiplier}")
        if agent.workload.stress_level > 7.0:
            notes.append("High stress level detected")
        if agent.workload.active_conversations >= agent.max_concurrent_conversations:
            notes.append("At maximum capacity")
        
        return ScoreBreakdown(
            skill_match_score=skill_score,
            availability_score=availability_score,
            performance_score=performance_score,
            wellbeing_score=wellbeing_score,
            customer_factor_score=customer_factor_score,
            workload_balance_score=workload_score,
            weighted_skill_match=weighted_skill,
            weighted_availability=weighted_availability,
            weighted_performance=weighted_performance,
            weighted_wellbeing=weighted_wellbeing,
            weighted_customer_factor=weighted_customer,
            weighted_workload_balance=weighted_workload,
            composite_score=composite_score,
            confidence_level=confidence,
            calculation_notes=notes
        )

    def _calculate_skill_match_score(self, agent: HumanAgent, context: ScoringContext) -> float:
        """Calculate skill match score (0.0 to 1.0)."""
        base_score = 0.5  # Base score for general capability
        
        # Check required specialization
        if context.specialization_required:
            agent_specializations = [
                s.value if hasattr(s, 'value') else str(s) 
                for s in agent.specializations
            ]
            if context.specialization_required in agent_specializations:
                base_score = 0.9  # High score for exact match
            elif "general" in agent_specializations:
                base_score = 0.6  # Medium score for general capability
            else:
                base_score = 0.1  # Low score for no match
        
        # Experience level bonus
        experience_bonus = (agent.experience_level - 1) * 0.1  # 0.0 to 0.4
        
        # Specialization breadth bonus
        specialization_count = len(agent.specializations)
        breadth_bonus = min(0.2, specialization_count * 0.05)
        
        final_score = min(1.0, base_score + experience_bonus + breadth_bonus)
        return final_score

    def _calculate_availability_score(self, agent: HumanAgent, context: ScoringContext) -> float:
        """Calculate availability score (0.0 to 1.0)."""
        if agent.status == HumanAgentStatus.OFFLINE:
            return 0.0
        elif agent.status == HumanAgentStatus.BREAK:
            return 0.1
        elif agent.status == HumanAgentStatus.BUSY:
            # Still available if not at max capacity
            if agent.workload.active_conversations < agent.max_concurrent_conversations:
                utilization = agent.workload.active_conversations / agent.max_concurrent_conversations
                return max(0.2, 1.0 - utilization)
            else:
                return 0.0
        elif agent.status == HumanAgentStatus.AVAILABLE:
            # Score based on current workload
            if agent.max_concurrent_conversations == 0:
                return 1.0
            
            utilization = agent.workload.active_conversations / agent.max_concurrent_conversations
            return max(0.3, 1.0 - (utilization * 0.7))
        
        return 0.5  # Default fallback

    def _calculate_performance_score(self, agent: HumanAgent, context: ScoringContext) -> float:
        """Calculate performance history score (0.0 to 1.0)."""
        # Satisfaction score component (0-10 scale)
        satisfaction_component = agent.workload.satisfaction_score / 10.0
        
        # Response time component (inverse relationship)
        if agent.workload.avg_response_time_minutes > 0:
            # Assume target response time is 5 minutes
            target_response_time = 5.0
            response_time_component = max(0.0, min(1.0, target_response_time / agent.workload.avg_response_time_minutes))
        else:
            response_time_component = 1.0  # No data, assume good
        
        # Experience level component
        experience_component = (agent.experience_level - 1) / 4.0  # Normalize to 0-1
        
        # Weighted average
        performance_score = (
            satisfaction_component * 0.5 +
            response_time_component * 0.3 +
            experience_component * 0.2
        )
        
        return min(1.0, performance_score)

    def _calculate_wellbeing_score(self, agent: HumanAgent, context: ScoringContext) -> float:
        """Calculate wellbeing factor score (0.0 to 1.0)."""
        # Stress level component (inverse relationship, 1-10 scale)
        stress_component = max(0.0, (10.0 - agent.workload.stress_level) / 9.0)
        
        # Workload pressure component
        if agent.max_concurrent_conversations > 0:
            utilization = agent.workload.active_conversations / agent.max_concurrent_conversations
            workload_component = max(0.0, 1.0 - utilization)
        else:
            workload_component = 1.0
        
        # Queue pressure component
        queue_pressure = min(1.0, agent.workload.queue_length / 5.0)  # Normalize to 0-1
        queue_component = max(0.0, 1.0 - queue_pressure)
        
        # Weighted average
        wellbeing_score = (
            stress_component * 0.5 +
            workload_component * 0.3 +
            queue_component * 0.2
        )
        
        return wellbeing_score

    def _calculate_customer_factor_score(self, agent: HumanAgent, context: ScoringContext) -> float:
        """Calculate customer factor score (0.0 to 1.0)."""
        score = 0.5  # Base score
        
        customer = context.customer_factors
        
        # Language preference match
        if customer.language_preference:
            if customer.language_preference in agent.languages:
                score += 0.3
            else:
                score -= 0.2
        
        # Previous agent continuity
        if customer.previous_agent_id:
            if customer.previous_agent_id == agent.id:
                score += 0.4  # Strong bonus for continuity
            else:
                score -= 0.1  # Small penalty for switching
        
        # Experience level vs issue complexity
        if customer.issue_complexity:
            complexity_match = agent.experience_level / customer.issue_complexity
            if complexity_match >= 1.0:
                score += 0.2  # Agent can handle complexity
            else:
                score -= 0.3  # May struggle with complexity
        
        # Customer tier handling
        if customer.customer_tier == "vip" and agent.experience_level >= 4:
            score += 0.2
        elif customer.customer_tier == "premium" and agent.experience_level >= 3:
            score += 0.1
        
        return max(0.0, min(1.0, score))

    def _calculate_workload_balance_score(self, agent: HumanAgent, context: ScoringContext) -> float:
        """Calculate workload balance score (0.0 to 1.0)."""
        if agent.max_concurrent_conversations == 0:
            return 1.0
        
        # Current utilization
        utilization = agent.workload.active_conversations / agent.max_concurrent_conversations
        utilization_score = max(0.0, 1.0 - utilization)
        
        # Queue length factor
        queue_factor = max(0.0, 1.0 - (agent.workload.queue_length / 10.0))
        
        # Balanced scoring
        workload_score = (utilization_score * 0.7) + (queue_factor * 0.3)
        
        return workload_score

    async def _check_availability(self, agent: HumanAgent, context: ScoringContext) -> bool:
        """Check if agent is available for assignment."""
        if agent.status == HumanAgentStatus.OFFLINE:
            return False
        if agent.status == HumanAgentStatus.BREAK:
            return False
        if agent.workload.active_conversations >= agent.max_concurrent_conversations:
            return False
        return True

    async def _check_capability(self, agent: HumanAgent, context: ScoringContext) -> bool:
        """Check if agent can handle the request."""
        # Check required specialization
        if context.specialization_required:
            agent_specializations = [
                s.value if hasattr(s, 'value') else str(s) 
                for s in agent.specializations
            ]
            if (context.specialization_required not in agent_specializations and 
                "general" not in agent_specializations):
                return False
        
        # Check language requirements
        if context.customer_factors.language_preference:
            if context.customer_factors.language_preference not in agent.languages:
                return False
        
        # Check experience level for complex issues
        if (context.customer_factors.issue_complexity >= 4 and 
            agent.experience_level < 3):
            return False
        
        return True

    def _get_blocking_factors(self, agent: HumanAgent, context: ScoringContext) -> List[str]:
        """Get list of factors that block agent selection."""
        factors = []
        
        if agent.status == HumanAgentStatus.OFFLINE:
            factors.append("Agent is offline")
        elif agent.status == HumanAgentStatus.BREAK:
            factors.append("Agent is on break")
        
        if agent.workload.active_conversations >= agent.max_concurrent_conversations:
            factors.append("At maximum conversation capacity")
        
        if agent.workload.stress_level > 8.0:
            factors.append("High stress level (>8.0)")
        
        # Check required specialization
        if context.specialization_required:
            agent_specializations = [
                s.value if hasattr(s, 'value') else str(s) 
                for s in agent.specializations
            ]
            if (context.specialization_required not in agent_specializations and 
                "general" not in agent_specializations):
                factors.append(f"Missing required specialization: {context.specialization_required}")
        
        return factors

    def _get_recommendation_reasons(
        self, 
        agent: HumanAgent, 
        context: ScoringContext, 
        breakdown: ScoreBreakdown
    ) -> List[str]:
        """Get reasons why this agent is recommended."""
        reasons = []
        
        if breakdown.skill_match_score > 0.8:
            reasons.append("Excellent skill match")
        elif breakdown.skill_match_score > 0.6:
            reasons.append("Good skill match")
        
        if breakdown.availability_score > 0.8:
            reasons.append("Highly available")
        
        if breakdown.performance_score > 0.8:
            reasons.append("Strong performance history")
        
        if breakdown.wellbeing_score > 0.8:
            reasons.append("Good wellbeing indicators")
        
        if agent.experience_level >= 4:
            reasons.append("Senior experience level")
        
        if agent.workload.satisfaction_score > 8.5:
            reasons.append("High customer satisfaction")
        
        return reasons

    def _calculate_score_variance(self, scores: List[float]) -> float:
        """Calculate variance in scores to determine confidence."""
        if not scores:
            return 1.0
        
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        return math.sqrt(variance)  # Standard deviation