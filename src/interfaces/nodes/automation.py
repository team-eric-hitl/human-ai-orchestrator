"""
Automation agent interface

This module defines the interface contract for automation agents
in the hybrid AI-human system.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from ..core.state_schema import HybridSystemState


class AutomationAgentInterface(ABC):
    """Interface for automation agents
    
    Automation agents handle routine tasks automatically without requiring
    LLM processing. They provide fast, cost-effective responses for common
    customer inquiries while intelligently escalating complex cases.
    """

    @abstractmethod
    def __call__(self, state: "HybridSystemState") -> "HybridSystemState":
        """Process the state and return updated state with automation results
        
        Args:
            state: Current system state containing the customer query
            
        Returns:
            Updated state with automation response or escalation flag
        """
        pass

    @abstractmethod
    def get_supported_tasks(self) -> List[str]:
        """Get list of tasks this automation agent can handle
        
        Returns:
            List of task names/identifiers
        """
        pass

    @abstractmethod
    def get_task_categories(self) -> List[str]:
        """Get list of task categories this agent supports
        
        Returns:
            List of category names (e.g., "billing", "policy_lookup")
        """
        pass

    @abstractmethod
    def detect_automation_intent(self, query: str) -> Optional[Tuple[str, Dict]]:
        """Detect if a query can be handled by automation
        
        Args:
            query: Customer query text
            
        Returns:
            Tuple of (task_name, task_config) if automatable, None otherwise
        """
        pass

    @abstractmethod
    def check_escalation_triggers(self, query: str) -> bool:
        """Check if query should be escalated immediately
        
        Args:
            query: Customer query text
            
        Returns:
            True if should escalate, False if can attempt automation
        """
        pass

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Get the name of this automation agent
        
        Returns:
            Human-readable agent name
        """
        pass

    @property
    @abstractmethod
    def response_time_range(self) -> Tuple[float, float]:
        """Get the expected response time range for this agent
        
        Returns:
            Tuple of (min_seconds, max_seconds)
        """
        pass

    @property
    @abstractmethod
    def success_rate(self) -> float:
        """Get the overall success rate for this agent
        
        Returns:
            Success rate as float between 0.0 and 1.0
        """
        pass


class AutomationResult:
    """Structured result from automation processing
    
    Attributes:
        success: Whether automation was successful
        response: The automation response text (if successful)
        task_name: Name of the task that was attempted
        task_category: Category of the task
        processing_time: Time taken to process
        reference_id: Unique reference ID for the automation
        escalation_required: Whether escalation is needed
        escalation_reason: Reason for escalation (if applicable)
        metadata: Additional metadata about the processing
    """
    
    def __init__(
        self,
        success: bool,
        response: Optional[str] = None,
        task_name: Optional[str] = None,
        task_category: Optional[str] = None,
        processing_time: Optional[float] = None,
        reference_id: Optional[str] = None,
        escalation_required: bool = False,
        escalation_reason: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ):
        self.success = success
        self.response = response
        self.task_name = task_name
        self.task_category = task_category
        self.processing_time = processing_time
        self.reference_id = reference_id
        self.escalation_required = escalation_required
        self.escalation_reason = escalation_reason
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        """Convert to dictionary for state storage"""
        return {
            "automation_result": "success" if self.success else "failed",
            "task_name": self.task_name,
            "task_category": self.task_category,
            "processing_time": self.processing_time,
            "reference_id": self.reference_id,
            "escalation_required": self.escalation_required,
            "escalation_reason": self.escalation_reason,
            **self.metadata,
        }