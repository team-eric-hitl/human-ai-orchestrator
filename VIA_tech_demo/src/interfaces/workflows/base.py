"""
Base interfaces for workflow orchestration

This module defines the fundamental contracts for workflows that
orchestrate multiple nodes and manage the overall system execution.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..core.state_schema import HybridSystemState


@dataclass
class WorkflowResult:
    """Result returned by a workflow execution

    Attributes:
        success: Whether the workflow completed successfully
        final_state: The final system state after execution
        execution_path: List of nodes executed in order
        total_execution_time: Total time for workflow execution
        error_message: Error message if workflow failed
        metadata: Additional metadata about the execution
    """

    success: bool
    final_state: "HybridSystemState"
    execution_path: list[str]
    total_execution_time: float
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class WorkflowInterface(ABC):
    """Abstract base class for workflow orchestration

    Workflows coordinate multiple nodes to implement complete business
    processes. They handle:
    - Node sequencing and routing
    - State management and validation
    - Error handling and recovery
    - Performance monitoring
    - Parallel execution where appropriate

    Implementations should handle:
    - Dynamic workflow routing based on state
    - Graceful error handling and rollback
    - Resource management and cleanup
    - Metrics collection and reporting
    """

    @abstractmethod
    def execute(self, initial_state: "HybridSystemState") -> WorkflowResult:
        """Execute the complete workflow

        Args:
            initial_state: Starting state for the workflow

        Returns:
            WorkflowResult containing final state and execution metadata
        """
        pass

    @abstractmethod
    def validate_initial_state(self, state: "HybridSystemState") -> bool:
        """Validate that initial state is suitable for this workflow

        Args:
            state: Initial state to validate

        Returns:
            True if state is valid for this workflow
        """
        pass

    @abstractmethod
    def get_next_node(self, state: "HybridSystemState") -> str | None:
        """Determine the next node to execute based on current state

        Args:
            state: Current system state

        Returns:
            Name of next node to execute, or None if workflow is complete
        """
        pass

    @property
    @abstractmethod
    def workflow_name(self) -> str:
        """Get the name of this workflow

        Returns:
            Human-readable name for this workflow
        """
        pass

    @property
    @abstractmethod
    def available_nodes(self) -> list[str]:
        """Get list of nodes available in this workflow

        Returns:
            List of node names that can be executed
        """
        pass

    @property
    @abstractmethod
    def required_initial_state_keys(self) -> list[str]:
        """Get the initial state keys required by this workflow

        Returns:
            List of state keys that must be present initially
        """
        pass
