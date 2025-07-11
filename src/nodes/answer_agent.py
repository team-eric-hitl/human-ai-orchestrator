"""
Module 1: Answer Agent Node
Responsibility: Generate initial AI responses to user queries
"""

from langchain_core.messages import AIMessage, HumanMessage
from langsmith import traceable

from ..core.logging import get_logger
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import HybridSystemState
from ..core.config import ConfigManager


class AnswerAgentNode:
    """LangGraph node for generating initial AI responses"""

    def __init__(self, config_manager: ConfigManager, context_provider: ContextProvider):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("answer_agent")
        self.context_provider = context_provider
        self.logger = get_logger(__name__)
        self.llm_provider = self._initialize_llm_provider()

    def _initialize_llm_provider(self):
        """Initialize the LLM provider with fallback strategy"""
        try:
            factory = LLMProviderFactory(self.config_manager.config_dir)
            
            # Use agent-specific model configuration
            preferred_model = self.agent_config.get_preferred_model()
            fallback_models = self.agent_config.get_fallback_models()
            provider = factory.create_provider_with_fallback(
                preferred_model=preferred_model
            )
            
            self.logger.info(
                "Answer Agent LLM provider initialized",
                extra={
                    "operation": "initialize_llm_provider",
                    "model_name": provider.model_name,
                    "model_type": provider.provider_type,
                    "preferred_model": preferred_model,
                    "fallback_models": fallback_models,
                },
            )
            return provider
        except Exception as e:
            self.logger.error(
                "Failed to initialize LLM provider",
                extra={"error": str(e), "operation": "initialize_llm_provider"},
            )
            return None

    @traceable(run_type="llm", name="Answer Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main node function - generate AI response
        LangSmith automatically tracks: tokens, latency, costs, errors
        """

        # Get configuration from agent config
        system_prompt = self.agent_config.get_prompt("system")
        context_integration = self.agent_config.prompts.get("context_integration_prompt", "")

        # Build context-aware prompt
        context_prompt = self._build_context_prompt(state)

        # Generate response using real LLM
        ai_response = self._generate_response(
            state["query"], context_prompt, system_prompt
        )

        # Save interaction to context
        self._save_interaction_context(state, ai_response)

        # Update state
        return {
            **state,
            "ai_response": ai_response,
            "initial_assessment": {
                "context_used": len(context_prompt) > 0,
                "confidence": 0.85,  # Would come from actual model
                "response_time": 2.3,  # Tracked automatically by LangSmith
            },
            "messages": state.get("messages", [])
            + [HumanMessage(content=state["query"]), AIMessage(content=ai_response)],
            "next_action": "evaluate",
        }

    def _build_context_prompt(self, state: HybridSystemState) -> str:
        """Build context-aware prompt from conversation history"""

        context_summary = self.context_provider.get_context_summary(
            state["user_id"], state["session_id"]
        )

        if context_summary["entries_count"] == 0:
            return ""

        context_prompt = "CONVERSATION CONTEXT:\n"
        context_prompt += (
            f"- User has had {context_summary['entries_count']} recent interactions\n"
        )

        if context_summary["recent_queries"]:
            context_prompt += (
                f"- Recent topics: {', '.join(context_summary['recent_queries'][:2])}\n"
            )

        if context_summary["escalation_count"] > 0:
            context_prompt += (
                f"- Previous escalations: {context_summary['escalation_count']}\n"
            )

        return context_prompt

    def _generate_response(
        self, query: str, context_prompt: str, system_prompt: str
    ) -> str:
        """Generate AI response using LLM"""
        if not self.llm_provider:
            return "Sorry, I'm having trouble connecting to the AI service. Please try again later."

        try:
            # Build full prompt with context
            full_prompt = query
            if context_prompt:
                full_prompt = f"{context_prompt}\n\nUser: {query}"

            # Generate response using local LLM
            response = self.llm_provider.generate_response(
                prompt=full_prompt, system_prompt=system_prompt
            )

            return response

        except Exception as e:
            self.logger.error(
                "Error generating AI response",
                extra={
                    "error": str(e),
                    "query_length": len(query),
                    "has_context": bool(context_prompt),
                    "operation": "generate_response",
                },
            )
            return "I apologize, but I encountered an error while processing your request. Please try again."

    def _save_interaction_context(self, state: HybridSystemState, response: str):
        """Save interaction to context store"""
        from ..interfaces.core.context import ContextEntry
        from datetime import datetime

        # Save query
        timestamp = datetime.fromisoformat(state["timestamp"]) if isinstance(state["timestamp"], str) else state["timestamp"]
        query_context = ContextEntry(
            entry_id=f"{state['query_id']}_query",
            user_id=state["user_id"],
            session_id=state["session_id"],
            timestamp=timestamp,
            entry_type="query",
            content=state["query"],
            metadata={"query_id": state["query_id"]},
        )
        self.context_provider.save_context_entry(query_context)

        # Save response
        response_context = ContextEntry(
            entry_id=f"{state['query_id']}_response",
            user_id=state["user_id"],
            session_id=state["session_id"],
            timestamp=timestamp,
            entry_type="response",
            content=response,
            metadata={"query_id": state["query_id"], "model_confidence": 0.85},
        )
        self.context_provider.save_context_entry(response_context)
