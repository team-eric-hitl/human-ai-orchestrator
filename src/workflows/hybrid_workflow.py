"""
Main workflow orchestration combining all nodes
"""

import uuid
from datetime import datetime
from typing import Any

from ..core.config import ConfigManager
from ..core.context_manager import SQLiteContextProvider
from ..interfaces.core.state_schema import HybridSystemState
from ..nodes.chatbot_agent import ChatbotAgentNode
from ..nodes.escalation_router import EscalationRouterNode
from ..nodes.evaluator_agent import EvaluatorAgentNode
from ..nodes.mock_automation_agent import MockAutomationAgent


class HybridSystemWorkflow:
    """Complete hybrid AI system workflow using LangGraph"""

    def __init__(
        self, config_dir: str = "config", context_db: str = "hybrid_system.db"
    ):
        # Initialize providers
        self.config_provider = ConfigManager(config_dir)
        self.context_provider = SQLiteContextProvider(context_db)

        # Initialize nodes
        self.automation_agent = MockAutomationAgent(self.config_provider, self.context_provider)
        self.answer_agent = ChatbotAgentNode(self.config_provider, self.context_provider)
        self.evaluator_agent = EvaluatorAgentNode(
            self.config_provider, self.context_provider
        )
        self.escalation_router = EscalationRouterNode(self.config_provider)

        # Build workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        """Build the complete workflow (simplified for now)"""
        # This would use LangGraph StateGraph in a real implementation
        # For now, we'll use a simple sequential workflow
        return self._sequential_workflow

    def _sequential_workflow(self, state: HybridSystemState) -> HybridSystemState:
        """Sequential workflow implementation with automation-first approach"""

        # Step 1: Try automation first
        state = self.automation_agent(state)

        # Step 2: Check if automation handled the request
        if state.get("automation_response") and not state.get("requires_escalation", False):
            # Automation succeeded - use automated response
            state = self._automation_response_handler(state)
        else:
            # Step 3: Fall back to AI chatbot for complex queries
            state = self.answer_agent(state)

            # Step 4: Evaluate response
            state = self.evaluator_agent(state)

            # Step 5: Route escalation if needed
            if state.get("escalation_decision", False) or state.get("requires_escalation", False):
                state = self.escalation_router(state)
            else:
                # Step 6: Handle final AI response
                state = self._ai_response_handler(state)

        return state

    def _automation_response_handler(self, state: HybridSystemState) -> HybridSystemState:
        """Handle successful automation response delivery"""
        automation_response = state.get("automation_response", "")
        automation_metadata = state.get("automation_metadata", {})

        return {
            **state,
            "final_response": automation_response,
            "response_source": "automation",
            "automation_metadata": automation_metadata,
            "workflow_complete": True,
        }

    def _ai_response_handler(self, state: HybridSystemState) -> HybridSystemState:
        """Handle final AI response delivery"""

        return {
            **state,
            "final_response": state.get("ai_response", "No response generated"),
            "response_source": "ai_chatbot",
            "workflow_complete": True,
        }

    def process_query(
        self, query: str, user_id: str, session_id: str | None = None
    ) -> dict[str, Any]:
        """Process a complete query through the hybrid system"""

        if session_id is None:
            session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create initial state
        initial_state = HybridSystemState(
            query_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            query=query,
            timestamp=datetime.now(),
            messages=[],
        )

        # Execute workflow
        result = self.workflow(initial_state)

        return {
            "query_id": result["query_id"],
            "escalated": result.get("escalation_decision", False) or result.get("requires_escalation", False),
            "final_response": result.get("final_response"),
            "response_source": result.get("response_source", "unknown"),
            "automation_metadata": result.get("automation_metadata"),
            "evaluation": result.get("evaluation_result"),
            "escalation_data": result.get("escalation_data"),
            "workflow_complete": result.get("workflow_complete", False),
        }
