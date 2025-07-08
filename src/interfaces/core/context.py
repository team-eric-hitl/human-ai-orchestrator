"""
Context management interfaces

This module defines the contracts for context providers that handle
storing and retrieving conversation context across user sessions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ContextEntry:
    """Represents a single context entry in the system

    This data class encapsulates all information about a context entry,
    including metadata for tracking and analysis purposes.

    Attributes:
        entry_id: Unique identifier for the context entry
        user_id: Identifier for the user who created this entry
        session_id: Identifier for the session this entry belongs to
        timestamp: When this entry was created
        entry_type: Type of entry (query, response, escalation, feedback, evaluation)
        content: The actual content/text of the entry
        metadata: Additional structured data about the entry
    """

    entry_id: str
    user_id: str
    session_id: str
    timestamp: datetime
    entry_type: str
    content: str
    metadata: dict[str, Any]


class ContextProvider(ABC):
    """Abstract base class for context providers

    Context providers are responsible for persisting and retrieving
    conversation context across user sessions. They enable the system
    to maintain continuity and provide personalized experiences.

    Implementations should handle:
    - Efficient storage and retrieval of context entries
    - Context summarization for quick overview
    - Cleanup of old/irrelevant context
    - Performance optimization for large context histories
    """

    @abstractmethod
    def save_context_entry(self, entry: ContextEntry) -> bool:
        """Save a context entry to the storage system

        Args:
            entry: The context entry to save

        Returns:
            True if saved successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_context_summary(self, user_id: str, session_id: str) -> dict[str, Any]:
        """Get a summary of context for a user session

        This should provide a condensed view of the context that includes
        key metrics and recent activity without returning all entries.

        Args:
            user_id: The user identifier
            session_id: The session identifier

        Returns:
            Dictionary containing:
            - entries_count: Total number of context entries
            - type_breakdown: Count of entries by type
            - recent_queries: List of recent query contents
            - escalation_count: Number of escalations
            - last_activity: Timestamp of last activity
        """
        pass

    @abstractmethod
    def get_recent_context(
        self, user_id: str, session_id: str, limit: int = 10
    ) -> list[ContextEntry]:
        """Get recent context entries for a user session

        Args:
            user_id: The user identifier
            session_id: The session identifier
            limit: Maximum number of entries to return

        Returns:
            List of recent context entries, ordered by timestamp (most recent first)
        """
        pass
