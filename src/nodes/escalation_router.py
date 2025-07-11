"""
Module 3: Escalation Router Node
Responsibility: Route escalations to appropriate human agents
"""

from typing import Any

from ..core.logging import get_logger
from ..interfaces.core.state_schema import EscalationData, HybridSystemState
from ..core.config import ConfigManager


class EscalationRouterNode:
    """LangGraph node for routing escalations to human agents"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("escalation_router")
        self.logger = get_logger(__name__)
        self.human_availability = self._load_human_availability()

    def _load_human_availability(self) -> dict[str, Any]:
        """Load current human agent availability"""
        # This would connect to your human agent management system
        return {
            "technical_agents": [
                {
                    "id": "tech_001",
                    "name": "Alice",
                    "available": True,
                    "skill_level": "senior",
                },
                {
                    "id": "tech_002",
                    "name": "Bob",
                    "available": False,
                    "skill_level": "junior",
                },
            ],
            "general_agents": [
                {
                    "id": "gen_001",
                    "name": "Carol",
                    "available": True,
                    "skill_level": "senior",
                },
                {
                    "id": "gen_002",
                    "name": "David",
                    "available": True,
                    "skill_level": "junior",
                },
            ],
        }

    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Route escalation to appropriate human agent
        LangSmith tracks routing decisions and timing
        """

        # Determine required expertise
        required_expertise = self._identify_required_expertise(state)

        # Calculate priority
        priority = self._calculate_priority(state)

        # Find best available human
        assigned_human = self._assign_human_agent(required_expertise, priority)

        # Create escalation data
        escalation_data = EscalationData(
            priority=priority,
            required_expertise=required_expertise,
            estimated_resolution_time=self._estimate_resolution_time(
                priority, required_expertise
            ),
            suggested_human_id=assigned_human["id"] if assigned_human else None,
            context_summary=self._create_context_summary(state),
            escalation_reason=state.get("escalation_reason", "Unknown"),
        )

        # Log escalation for context
        self._log_escalation_context(state, escalation_data)

        return {
            **state,
            "escalation_data": escalation_data,
            "human_assignment": assigned_human,
            "next_action": "await_human" if assigned_human else "queue_escalation",
        }

    def _identify_required_expertise(self, state: HybridSystemState) -> str:
        """Identify what type of expertise is needed"""
        query = state["query"].lower()

        # Use agent-specific keyword mapping
        expertise_mapping = self.agent_config.settings.get("routing", {}).get("expertise_domains", {})
        
        for domain, keywords in expertise_mapping.items():
            if any(keyword in query for keyword in keywords.get("keywords", [])):
                return domain
        
        return "general"

    def _calculate_priority(self, state: HybridSystemState) -> str:
        """Calculate escalation priority"""
        evaluation = state.get("evaluation_result")
        if not evaluation:
            return "medium"

        score = evaluation.overall_score
        escalation_history = evaluation.context_factors.get("escalation_history", 0)

        if score < 4.0 or escalation_history >= 2:
            return "high"
        elif score < 6.0:
            return "medium"
        else:
            return "low"

    def _assign_human_agent(
        self, expertise: str, priority: str
    ) -> dict[str, Any] | None:
        """Assign the best available human agent"""

        # Get agents for the required expertise
        if expertise == "technical":
            available_agents = [
                agent
                for agent in self.human_availability["technical_agents"]
                if agent["available"]
            ]
        else:
            available_agents = [
                agent
                for agent in self.human_availability["general_agents"]
                if agent["available"]
            ]

        if not available_agents:
            return None  # No agents available

        # Prioritize senior agents for high priority issues
        if priority == "high":
            senior_agents = [
                agent for agent in available_agents if agent["skill_level"] == "senior"
            ]
            if senior_agents:
                return senior_agents[0]

        # Return first available agent
        return available_agents[0]

    def _estimate_resolution_time(self, priority: str, expertise: str) -> int:
        """Estimate resolution time in minutes"""
        base_times = {
            ("high", "technical"): 15,
            ("medium", "technical"): 30,
            ("low", "technical"): 45,
            ("high", "general"): 10,
            ("medium", "general"): 20,
            ("low", "general"): 30,
        }

        return base_times.get((priority, expertise), 30)

    def _create_context_summary(self, state: HybridSystemState) -> str:
        """Create context summary for human agent"""
        evaluation = state.get("evaluation_result")

        summary = f"""
ESCALATION CONTEXT:
Query: {state["query"]}
AI Response: {state.get("ai_response", "N/A")}
Evaluation Score: {evaluation.overall_score:.1f}/10 if evaluation else 'N/A'
User: {state["user_id"]} | Session: {state["session_id"]}
Escalation Reason: {state.get("escalation_reason", "Unknown")}
        """.strip()

        return summary

    def _log_escalation_context(
        self, state: HybridSystemState, escalation_data: EscalationData
    ):
        """Log escalation for context tracking"""
        self.logger.escalation(
            user_id=state["user_id"],
            reason=escalation_data.escalation_reason,
            priority=escalation_data.priority,
            extra={
                "query_id": state["query_id"],
                "session_id": state["session_id"],
                "suggested_human_id": escalation_data.suggested_human_id,
                "required_expertise": escalation_data.required_expertise,
                "operation": "escalation_logged",
            },
        )
