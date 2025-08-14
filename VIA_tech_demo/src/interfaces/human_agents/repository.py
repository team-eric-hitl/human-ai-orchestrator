"""Human agent repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from .models import HumanAgent, HumanAgentStatus, Specialization


class HumanAgentRepository(ABC):
    """Abstract base class for human agent data access."""

    @abstractmethod
    async def create(self, agent: HumanAgent) -> HumanAgent:
        """Create a new human agent."""
        pass

    @abstractmethod
    async def get_by_id(self, agent_id: str) -> Optional[HumanAgent]:
        """Get human agent by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[HumanAgent]:
        """Get human agent by email."""
        pass

    @abstractmethod
    async def get_all(self) -> List[HumanAgent]:
        """Get all human agents."""
        pass

    @abstractmethod
    async def get_available_agents(self) -> List[HumanAgent]:
        """Get all available human agents."""
        pass

    @abstractmethod
    async def get_by_specialization(self, specialization: Specialization) -> List[HumanAgent]:
        """Get agents by specialization."""
        pass

    @abstractmethod
    async def get_by_status(self, status: HumanAgentStatus) -> List[HumanAgent]:
        """Get agents by status."""
        pass

    @abstractmethod
    async def update(self, agent: HumanAgent) -> HumanAgent:
        """Update human agent."""
        pass

    @abstractmethod
    async def update_status(self, agent_id: str, status: HumanAgentStatus) -> bool:
        """Update agent status."""
        pass

    @abstractmethod
    async def update_workload(self, agent_id: str, workload_data: dict) -> bool:
        """Update agent workload metrics."""
        pass

    @abstractmethod
    async def delete(self, agent_id: str) -> bool:
        """Delete human agent."""
        pass

    @abstractmethod
    async def get_best_available_agent(
        self, 
        specialization: Optional[Specialization] = None,
        exclude_agents: Optional[List[str]] = None
    ) -> Optional[HumanAgent]:
        """Get the best available agent based on workload and specialization."""
        pass