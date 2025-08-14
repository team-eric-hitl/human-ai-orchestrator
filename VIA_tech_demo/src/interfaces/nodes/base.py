"""
Base interfaces for processing nodes

This module defines the fundamental contracts for all processing nodes
in the hybrid AI-human system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..core.state_schema import HybridSystemState


@dataclass
class NodeResult:
    """Result returned by a node execution

    Attributes:
        success: Whether the node executed successfully
        updated_state: The updated system state
        error_message: Error message if execution failed
        execution_time: Time taken to execute (seconds)
        metadata: Additional metadata about the execution
    """

    success: bool
    updated_state: "HybridSystemState"
    error_message: str | None = None
    execution_time: float | None = None
    metadata: dict[str, Any] | None = None


class NodeInterface(ABC):
    """Abstract base class for all processing nodes

    All nodes in the hybrid system should implement this interface.
    Nodes are responsible for specific processing tasks such as:
    - Handling routine automation tasks
    - Generating AI responses
    - Evaluating response quality
    - Routing escalations
    - Managing context

    Implementations should handle:
    - State validation and transformation
    - Error handling and recovery
    - Performance monitoring
    - Resource management
    """

    @abstractmethod
    def __call__(self, state: "HybridSystemState") -> "HybridSystemState":
        """Process the state and return updated state

        This is the main entry point for node execution. Nodes should
        be implemented as callable objects that take the current system
        state and return an updated state.

        Args:
            state: Current system state

        Returns:
            Updated system state

        Raises:
            NodeProcessingError: If processing fails
        """
        pass

    @abstractmethod
    def validate_state(self, state: "HybridSystemState") -> bool:
        """Validate that the state is suitable for this node

        Args:
            state: System state to validate

        Returns:
            True if state is valid for this node
        """
        pass

    @property
    @abstractmethod
    def node_name(self) -> str:
        """Get the name of this node

        Returns:
            Human-readable name for this node
        """
        pass

    @property
    @abstractmethod
    def required_state_keys(self) -> list[str]:
        """Get the state keys required by this node

        Returns:
            List of state keys that must be present
        """
        pass

    @property
    @abstractmethod
    def output_state_keys(self) -> list[str]:
        """Get the state keys this node will add/modify

        Returns:
            List of state keys this node produces
        """
        pass
