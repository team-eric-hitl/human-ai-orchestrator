"""
Module 2: Evaluator Agent Node
Responsibility: Evaluate AI responses and decide on escalation
"""

from typing import Any

from langsmith import traceable

from ..core.logging import get_logger
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.config import ConfigProvider
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import EvaluationResult, HybridSystemState


class EvaluatorAgentNode:
    """LangGraph node for evaluating responses and escalation decisions"""

    def __init__(
        self, config_provider: ConfigProvider, context_provider: ContextProvider
    ):
        self.config_provider = config_provider
        self.context_provider = context_provider
        self.logger = get_logger(__name__)
        self.llm_provider = self._initialize_llm_provider()

    def _initialize_llm_provider(self):
        """Initialize LLM provider for evaluation with fallback strategy"""
        try:
            factory = LLMProviderFactory()
            provider = factory.create_provider_with_fallback()
            self.logger.info(
                "Evaluator Agent LLM provider initialized",
                extra={
                    "operation": "initialize_llm_provider",
                    "model_name": provider.model_config.name,
                    "model_type": provider.model_config.type,
                },
            )
            return provider
        except Exception as e:
            self.logger.error(
                "Failed to initialize Evaluator LLM provider",
                extra={"error": str(e), "operation": "initialize_llm_provider"},
            )
            return None

    @traceable(name="Response Evaluator")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Evaluate AI response and decide on escalation
        LangSmith automatically tracks evaluation metrics
        """

        # Analyze context factors
        context_factors = self._analyze_context_factors(state)

        # Evaluate response quality using LLM
        evaluation = self._evaluate_response(state, context_factors)

        # Make escalation decision
        should_escalate, escalation_reason = self._decide_escalation(evaluation)

        # Determine next action
        next_action = "escalate" if should_escalate else "respond"

        return {
            **state,
            "evaluation_result": evaluation,
            "escalation_decision": should_escalate,
            "escalation_reason": escalation_reason,
            "next_action": next_action,
        }

    def _analyze_context_factors(self, state: HybridSystemState) -> dict[str, Any]:
        """Analyze user context for evaluation"""

        context_summary = self.context_provider.get_context_summary(
            state["user_id"], state["session_id"]
        )

        return {
            "escalation_history": context_summary.get("escalation_count", 0),
            "interaction_frequency": context_summary.get("entries_count", 0),
            "repeat_query_detected": self._detect_repeat_query(state),
            "user_patience_indicators": self._get_patience_indicators(context_summary),
        }

    def _evaluate_response(
        self, state: HybridSystemState, context_factors: dict[str, Any]
    ) -> EvaluationResult:
        """Evaluate response quality with LLM"""

        # Use LLM to evaluate the response if available
        if self.llm_provider:
            try:
                llm_evaluation = self.llm_provider.evaluate_response(
                    query=state["query"], response=state.get("ai_response", "")
                )

                # Apply context adjustments
                adjustment = self._calculate_context_adjustment(context_factors)

                return EvaluationResult(
                    overall_score=max(
                        1.0, llm_evaluation["overall_score"] + adjustment
                    ),
                    accuracy=max(1.0, llm_evaluation["accuracy"] + adjustment),
                    completeness=max(1.0, llm_evaluation["completeness"] + adjustment),
                    clarity=max(1.0, llm_evaluation["clarity"] + adjustment),
                    user_satisfaction=max(
                        1.0, llm_evaluation["user_satisfaction"] + adjustment
                    ),
                    confidence=max(0.1, 0.85 + (adjustment * 0.1)),
                    reasoning=f"LLM evaluation: {llm_evaluation['reasoning']}. Context adjustment: {adjustment}",
                    context_factors=context_factors,
                )
            except Exception as e:
                self.logger.error(
                    "LLM evaluation failed",
                    extra={
                        "error": str(e),
                        "query_length": len(state.get("query", "")),
                        "response_length": len(state.get("ai_response", "")),
                        "operation": "llm_evaluation",
                    },
                )

        # Fallback to simple evaluation
        base_scores = {
            "accuracy": 8.5,
            "completeness": 7.8,
            "clarity": 9.0,
            "user_satisfaction": 8.2,
        }

        adjustment = self._calculate_context_adjustment(context_factors)

        return EvaluationResult(
            overall_score=max(
                1.0, (sum(base_scores.values()) / len(base_scores)) + adjustment
            ),
            accuracy=max(1.0, base_scores["accuracy"] + adjustment),
            completeness=max(1.0, base_scores["completeness"] + adjustment),
            clarity=max(1.0, base_scores["clarity"] + adjustment),
            user_satisfaction=max(1.0, base_scores["user_satisfaction"] + adjustment),
            confidence=max(0.1, 0.85 + (adjustment * 0.1)),
            reasoning=f"Fallback evaluation with context adjustment: {adjustment}",
            context_factors=context_factors,
        )

    def _decide_escalation(self, evaluation: EvaluationResult) -> tuple[bool, str]:
        """Decide if escalation is needed"""

        threshold = self.config_provider.thresholds.escalation_score
        reasons = []

        if evaluation.overall_score < threshold:
            reasons.append(
                f"Score {evaluation.overall_score:.1f} below threshold {threshold}"
            )

        if evaluation.context_factors["repeat_query_detected"]:
            reasons.append("User repeating similar query")

        if evaluation.context_factors["escalation_history"] >= 2:
            reasons.append("Multiple previous escalations")

        should_escalate = len(reasons) > 0
        escalation_reason = "; ".join(reasons) if reasons else "No escalation needed"

        return should_escalate, escalation_reason

    def _detect_repeat_query(self, state: HybridSystemState) -> bool:
        """Detect if user is repeating similar queries"""
        recent_context = self.context_provider.get_recent_context(
            state["user_id"], state["session_id"], limit=5
        )

        queries = [
            entry.content for entry in recent_context if entry.entry_type == "query"
        ]
        current_query = state["query"].lower()

        for prev_query in queries[:2]:  # Check last 2 queries
            similarity = len(
                set(current_query.split()) & set(prev_query.lower().split())
            )
            if similarity >= 3:  # 3+ common words
                return True

        return False

    def _get_patience_indicators(self, context_summary: dict[str, Any]) -> list:
        """Get indicators of user patience/frustration"""
        indicators = []

        if context_summary.get("escalation_count", 0) > 0:
            indicators.append("previous_escalations")

        if context_summary.get("entries_count", 0) > 5:
            indicators.append("high_frequency_user")

        return indicators

    def _calculate_context_adjustment(self, context_factors: dict[str, Any]) -> float:
        """Calculate score adjustment based on context"""
        adjustment = 0.0

        if context_factors["repeat_query_detected"]:
            adjustment -= 1.5

        if context_factors["escalation_history"] > 1:
            adjustment -= 0.5

        if len(context_factors["user_patience_indicators"]) > 1:
            adjustment -= 0.8

        return adjustment
