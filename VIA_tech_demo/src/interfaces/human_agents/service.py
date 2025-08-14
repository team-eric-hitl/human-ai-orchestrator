"""Human agent service interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from .models import HumanAgent, HumanAgentStatus, Specialization, WorkloadMetrics


class HumanAgentService(ABC):
    """Abstract service interface for human agent business logic."""

    @abstractmethod
    async def assign_conversation(self, agent_id: str, conversation_id: str) -> bool:
        """Assign a conversation to an agent."""
        pass

    @abstractmethod
    async def complete_conversation(self, agent_id: str, conversation_id: str) -> bool:
        """Mark a conversation as completed for an agent."""
        pass

    @abstractmethod
    async def find_best_agent(
        self, 
        specialization: Optional[Specialization] = None,
        urgency_level: int = 1,
        exclude_agents: Optional[List[str]] = None
    ) -> Optional[HumanAgent]:
        """Find the best agent for assignment based on various criteria."""
        pass

    @abstractmethod
    async def get_agent_availability(self, agent_id: str) -> bool:
        """Check if agent is available for new conversations."""
        pass

    @abstractmethod
    async def update_agent_metrics(
        self, 
        agent_id: str, 
        response_time: Optional[float] = None,
        satisfaction_score: Optional[float] = None,
        stress_level: Optional[float] = None
    ) -> bool:
        """Update agent performance metrics."""
        pass

    @abstractmethod
    async def get_workload_summary(self) -> dict:
        """Get overall team workload summary."""
        pass

    @abstractmethod
    async def rebalance_workload(self) -> List[str]:
        """Attempt to rebalance workload across agents."""
        pass

    @abstractmethod
    async def set_agent_break(self, agent_id: str, duration_minutes: int) -> bool:
        """Set agent on break for specified duration."""
        pass

    @abstractmethod
    async def escalate_to_senior(self, conversation_id: str, current_agent_id: str) -> Optional[HumanAgent]:
        """Escalate conversation to a senior agent."""
        pass