"""Human agent service implementation."""

from datetime import datetime, timedelta
from typing import List, Optional

from ..core.logging import get_logger
from ..interfaces.human_agents import HumanAgent, HumanAgentRepository, HumanAgentService, HumanAgentStatus, Specialization
from ..interfaces.scoring import ScoringEngine, ScoringConfigManager, ScoringContext, CustomerFactors
from .scoring_engine import DefaultScoringEngine
from .scoring_config import DefaultScoringConfigManager


class DefaultHumanAgentService(HumanAgentService):
    """Default implementation of human agent service."""

    def __init__(
        self, 
        repository: HumanAgentRepository,
        scoring_engine: Optional[ScoringEngine] = None,
        scoring_config: Optional[ScoringConfigManager] = None
    ):
        """Initialize service with repository and optional scoring components."""
        self.repository = repository
        self.scoring_engine = scoring_engine or DefaultScoringEngine()
        self.scoring_config = scoring_config or DefaultScoringConfigManager()
        self.logger = get_logger(__name__)

    async def assign_conversation(self, agent_id: str, conversation_id: str) -> bool:
        """Assign a conversation to an agent."""
        try:
            agent = await self.repository.get_by_id(agent_id)
            if not agent:
                self.logger.warning(f"Agent not found: {agent_id}")
                return False

            if agent.status != HumanAgentStatus.AVAILABLE:
                self.logger.warning(f"Agent {agent_id} is not available for assignment")
                return False

            if agent.workload.active_conversations >= agent.max_concurrent_conversations:
                self.logger.warning(f"Agent {agent_id} is at maximum capacity")
                return False

            # Update workload
            new_workload = {
                'active_conversations': agent.workload.active_conversations + 1
            }
            
            success = await self.repository.update_workload(agent_id, new_workload)
            
            if success:
                # Update status to busy if at capacity
                if agent.workload.active_conversations + 1 >= agent.max_concurrent_conversations:
                    await self.repository.update_status(agent_id, HumanAgentStatus.BUSY)
                
                self.logger.info(f"Assigned conversation {conversation_id} to agent {agent_id}")
            
            return success

        except Exception as e:
            self.logger.error(f"Failed to assign conversation {conversation_id} to agent {agent_id}: {e}")
            return False

    async def complete_conversation(self, agent_id: str, conversation_id: str) -> bool:
        """Mark a conversation as completed for an agent."""
        try:
            agent = await self.repository.get_by_id(agent_id)
            if not agent:
                self.logger.warning(f"Agent not found: {agent_id}")
                return False

            if agent.workload.active_conversations == 0:
                self.logger.warning(f"Agent {agent_id} has no active conversations")
                return False

            # Update workload
            new_workload = {
                'active_conversations': max(0, agent.workload.active_conversations - 1)
            }
            
            success = await self.repository.update_workload(agent_id, new_workload)
            
            if success:
                # Update status to available if was at capacity
                if (agent.status == HumanAgentStatus.BUSY and 
                    agent.workload.active_conversations - 1 < agent.max_concurrent_conversations):
                    await self.repository.update_status(agent_id, HumanAgentStatus.AVAILABLE)
                
                self.logger.info(f"Completed conversation {conversation_id} for agent {agent_id}")
            
            return success

        except Exception as e:
            self.logger.error(f"Failed to complete conversation {conversation_id} for agent {agent_id}: {e}")
            return False

    async def find_best_agent(
        self, 
        specialization: Optional[Specialization] = None,
        urgency_level: int = 1,
        exclude_agents: Optional[List[str]] = None,
        customer_factors: Optional[CustomerFactors] = None,
        conversation_id: Optional[str] = None
    ) -> Optional[HumanAgent]:
        """Find the best agent for assignment using advanced scoring algorithm."""
        try:
            # Get all potentially suitable agents
            if urgency_level >= 3:
                # For high urgency, consider more agents
                agents = await self.repository.get_all()
                candidate_agents = [
                    agent for agent in agents 
                    if (agent.status in [HumanAgentStatus.AVAILABLE, HumanAgentStatus.BUSY] and
                        agent.workload.active_conversations < agent.max_concurrent_conversations and
                        (not exclude_agents or agent.id not in exclude_agents))
                ]
            else:
                # Normal priority - focus on available agents
                if specialization:
                    candidate_agents = await self.repository.get_by_specialization(specialization)
                else:
                    candidate_agents = await self.repository.get_available_agents()
                
                # Filter out excluded agents
                if exclude_agents:
                    candidate_agents = [a for a in candidate_agents if a.id not in exclude_agents]
            
            if not candidate_agents:
                self.logger.warning("No candidate agents found for assignment")
                return None
            
            # Create scoring context
            context = ScoringContext(
                specialization_required=specialization.value if specialization else None,
                customer_factors=customer_factors or CustomerFactors(),
                exclude_agent_ids=exclude_agents or [],
                urgency_multiplier=self._calculate_urgency_multiplier(urgency_level),
                conversation_id=conversation_id
            )
            
            # Get scoring weights based on context
            context_type = self._determine_context_type(urgency_level, customer_factors)
            weights = await self.scoring_config.get_scoring_weights(context_type, urgency_level)
            
            # Score all candidate agents
            scoring_result = await self.scoring_engine.score_agents(candidate_agents, context, weights)
            
            # Log scoring decision
            if scoring_result.best_agent:
                self.logger.info(
                    f"Selected agent {scoring_result.best_agent.agent_name} "
                    f"(score: {scoring_result.best_agent.final_score:.3f}) "
                    f"from {scoring_result.total_agents_evaluated} candidates"
                )
                self.logger.debug(f"Selection reasoning: {scoring_result.selection_reasoning}")
                
                # Return the actual HumanAgent object
                return next(
                    agent for agent in candidate_agents 
                    if agent.id == scoring_result.best_agent.agent_id
                )
            else:
                self.logger.warning("Scoring engine found no suitable agents")
                return None

        except Exception as e:
            self.logger.error(f"Failed to find best agent: {e}")
            # Fallback to simple selection
            return await self.repository.get_best_available_agent(specialization, exclude_agents)

    def _calculate_urgency_multiplier(self, urgency_level: int) -> float:
        """Calculate urgency multiplier based on urgency level."""
        # Map urgency levels to multipliers
        multipliers = {1: 1.0, 2: 1.1, 3: 1.3, 4: 1.6, 5: 2.0}
        return multipliers.get(urgency_level, 1.0)

    def _determine_context_type(
        self, 
        urgency_level: int, 
        customer_factors: Optional[CustomerFactors]
    ) -> str:
        """Determine scoring context type based on request characteristics."""
        if urgency_level >= 4:
            return "emergency"
        
        if customer_factors:
            if customer_factors.customer_tier == "vip":
                return "vip"
            elif customer_factors.priority_level >= 4:
                return "emergency"
        
        return "default"

    async def get_agent_availability(self, agent_id: str) -> bool:
        """Check if agent is available for new conversations."""
        try:
            agent = await self.repository.get_by_id(agent_id)
            if not agent:
                return False

            return (agent.status == HumanAgentStatus.AVAILABLE and 
                    agent.workload.active_conversations < agent.max_concurrent_conversations)

        except Exception as e:
            self.logger.error(f"Failed to check availability for agent {agent_id}: {e}")
            return False

    async def update_agent_metrics(
        self, 
        agent_id: str, 
        response_time: Optional[float] = None,
        satisfaction_score: Optional[float] = None,
        stress_level: Optional[float] = None
    ) -> bool:
        """Update agent performance metrics."""
        try:
            agent = await self.repository.get_by_id(agent_id)
            if not agent:
                self.logger.warning(f"Agent not found: {agent_id}")
                return False

            workload_updates = {}
            
            if response_time is not None:
                # Update rolling average response time
                current_avg = agent.workload.avg_response_time_minutes
                if current_avg == 0:
                    workload_updates['avg_response_time_minutes'] = response_time
                else:
                    # Simple rolling average (could be improved with more sophisticated calculation)
                    workload_updates['avg_response_time_minutes'] = (current_avg * 0.8) + (response_time * 0.2)
            
            if satisfaction_score is not None:
                # Update rolling average satisfaction score
                current_score = agent.workload.satisfaction_score
                workload_updates['satisfaction_score'] = (current_score * 0.8) + (satisfaction_score * 0.2)
            
            if stress_level is not None:
                workload_updates['stress_level'] = stress_level

            if workload_updates:
                return await self.repository.update_workload(agent_id, workload_updates)
            
            return True

        except Exception as e:
            self.logger.error(f"Failed to update metrics for agent {agent_id}: {e}")
            return False

    async def get_workload_summary(self) -> dict:
        """Get overall team workload summary."""
        try:
            agents = await self.repository.get_all()
            
            if not agents:
                return {
                    'total_agents': 0,
                    'available_agents': 0,
                    'busy_agents': 0,
                    'offline_agents': 0,
                    'total_active_conversations': 0,
                    'average_stress_level': 0.0,
                    'average_satisfaction': 0.0,
                    'capacity_utilization': 0.0
                }

            status_counts = {status: 0 for status in HumanAgentStatus}
            total_conversations = 0
            total_capacity = 0
            total_stress = 0
            total_satisfaction = 0

            for agent in agents:
                status_counts[agent.status] += 1
                total_conversations += agent.workload.active_conversations
                total_capacity += agent.max_concurrent_conversations
                total_stress += agent.workload.stress_level
                total_satisfaction += agent.workload.satisfaction_score

            agent_count = len(agents)
            capacity_utilization = (total_conversations / total_capacity * 100) if total_capacity > 0 else 0

            return {
                'total_agents': agent_count,
                'available_agents': status_counts[HumanAgentStatus.AVAILABLE],
                'busy_agents': status_counts[HumanAgentStatus.BUSY],
                'on_break_agents': status_counts[HumanAgentStatus.BREAK],
                'offline_agents': status_counts[HumanAgentStatus.OFFLINE],
                'total_active_conversations': total_conversations,
                'total_capacity': total_capacity,
                'capacity_utilization': capacity_utilization,
                'average_stress_level': total_stress / agent_count,
                'average_satisfaction': total_satisfaction / agent_count
            }

        except Exception as e:
            self.logger.error(f"Failed to get workload summary: {e}")
            return {}

    async def rebalance_workload(self) -> List[str]:
        """Attempt to rebalance workload across agents."""
        try:
            agents = await self.repository.get_all()
            if not agents:
                return []

            # Find agents with high stress levels
            high_stress_agents = [
                agent for agent in agents 
                if agent.workload.stress_level > 7.0 and agent.workload.active_conversations > 1
            ]

            # Find agents with low workload who could take on more
            low_workload_agents = [
                agent for agent in agents
                if (agent.status == HumanAgentStatus.AVAILABLE and
                    agent.workload.active_conversations < agent.max_concurrent_conversations - 1 and
                    agent.workload.stress_level < 5.0)
            ]

            rebalanced_agents = []
            
            for stressed_agent in high_stress_agents:
                if not low_workload_agents:
                    break
                
                # Find a suitable agent to transfer work to
                target_agent = min(low_workload_agents, key=lambda a: a.workload.active_conversations)
                
                # Simulate transferring one conversation
                # In a real implementation, this would involve actual conversation transfer
                await self.repository.update_workload(stressed_agent.id, {
                    'active_conversations': stressed_agent.workload.active_conversations - 1,
                    'stress_level': max(1.0, stressed_agent.workload.stress_level - 0.5)
                })
                
                await self.repository.update_workload(target_agent.id, {
                    'active_conversations': target_agent.workload.active_conversations + 1
                })
                
                rebalanced_agents.extend([stressed_agent.id, target_agent.id])
                
                # Remove target agent if they're now at capacity
                if target_agent.workload.active_conversations + 1 >= target_agent.max_concurrent_conversations:
                    low_workload_agents.remove(target_agent)

            return rebalanced_agents

        except Exception as e:
            self.logger.error(f"Failed to rebalance workload: {e}")
            return []

    async def set_agent_break(self, agent_id: str, duration_minutes: int) -> bool:
        """Set agent on break for specified duration."""
        try:
            agent = await self.repository.get_by_id(agent_id)
            if not agent:
                self.logger.warning(f"Agent not found: {agent_id}")
                return False

            success = await self.repository.update_status(agent_id, HumanAgentStatus.BREAK)
            
            if success:
                # In a real implementation, you'd set up a timer to automatically 
                # return the agent to available status after the break
                self.logger.info(f"Agent {agent_id} set on break for {duration_minutes} minutes")
            
            return success

        except Exception as e:
            self.logger.error(f"Failed to set break for agent {agent_id}: {e}")
            return False

    async def escalate_to_senior(self, conversation_id: str, current_agent_id: str) -> Optional[HumanAgent]:
        """Escalate conversation to a senior agent."""
        try:
            current_agent = await self.repository.get_by_id(current_agent_id)
            if not current_agent:
                self.logger.warning(f"Current agent not found: {current_agent_id}")
                return None

            # Find senior agents with same specializations
            all_agents = await self.repository.get_all()
            senior_agents = [
                agent for agent in all_agents
                if (agent.experience_level > current_agent.experience_level and
                    agent.id != current_agent_id and
                    agent.workload.active_conversations < agent.max_concurrent_conversations and
                    any(spec in agent.specializations for spec in current_agent.specializations))
            ]

            if not senior_agents:
                # Fallback to any senior agent with escalation specialization
                senior_agents = [
                    agent for agent in all_agents
                    if (agent.experience_level >= 4 and  # Senior level
                        agent.id != current_agent_id and
                        agent.workload.active_conversations < agent.max_concurrent_conversations and
                        Specialization.ESCALATION in agent.specializations)
                ]

            if not senior_agents:
                self.logger.warning(f"No senior agents available for escalation")
                return None

            # Select best senior agent
            best_senior = min(senior_agents, key=lambda a: (
                a.workload.active_conversations,
                a.workload.stress_level,
                -a.experience_level
            ))

            # Complete conversation for current agent
            await self.complete_conversation(current_agent_id, conversation_id)
            
            # Assign to senior agent
            success = await self.assign_conversation(best_senior.id, conversation_id)
            
            if success:
                self.logger.info(f"Escalated conversation {conversation_id} from {current_agent_id} to {best_senior.id}")
                return best_senior
            
            return None

        except Exception as e:
            self.logger.error(f"Failed to escalate conversation {conversation_id}: {e}")
            return None