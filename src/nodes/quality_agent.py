"""
Quality Agent Node
Responsibility: Review chatbot answers and decide if adequate, needs adjustment, or requires human intervention
"""

from enum import Enum
from typing import Any

from langsmith import traceable

from ..core.config import ConfigManager
from ..core.logging import get_logger
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import HybridSystemState


class QualityDecision(Enum):
    ADEQUATE = "adequate"
    NEEDS_ADJUSTMENT = "needs_adjustment"
    HUMAN_INTERVENTION = "human_intervention"


class QualityAgentNode:
    """LangGraph node for quality assessment of chatbot responses"""

    def __init__(self, config_manager: ConfigManager, context_provider: ContextProvider):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("quality_agent")
        self.context_provider = context_provider
        self.logger = get_logger(__name__)
        self.llm_provider = self._initialize_llm_provider()

    def _initialize_llm_provider(self):
        """Initialize the LLM provider for quality assessment"""
        try:
            factory = LLMProviderFactory(self.config_manager.config_dir)

            preferred_model = self.agent_config.get_preferred_model()
            provider = factory.create_provider_with_fallback(
                preferred_model=preferred_model
            )

            self.logger.info(
                "Quality Agent LLM provider initialized",
                extra={
                    "operation": "initialize_llm_provider",
                    "model_name": provider.model_name,
                    "model_type": provider.provider_type,
                    "preferred_model": preferred_model,
                },
            )
            return provider
        except Exception as e:
            self.logger.error(
                "Failed to initialize Quality Agent LLM provider",
                extra={"error": str(e), "operation": "initialize_llm_provider"},
            )
            return None

    @traceable(name="Quality Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main quality assessment function
        Reviews chatbot response and determines quality level
        """

        # Get the chatbot response to assess
        chatbot_response = state.get("ai_response", "")
        customer_query = state.get("query", "")

        if not chatbot_response:
            return {
                **state,
                "quality_assessment": {
                    "decision": QualityDecision.HUMAN_INTERVENTION.value,
                    "confidence": 0.0,
                    "reasoning": "No chatbot response to assess",
                    "adjustment_needed": False,
                },
                "next_action": "human_intervention",
            }

        # Perform quality assessment
        quality_assessment = self._assess_response_quality(
            customer_query, chatbot_response, state
        )

        # Flag if adjustment is needed (but don't actually adjust)
        if quality_assessment["decision"] == QualityDecision.NEEDS_ADJUSTMENT.value:
            quality_assessment["flag_reason"] = quality_assessment["reasoning"]
            quality_assessment["adjustment_suggested"] = True
        else:
            quality_assessment["adjustment_suggested"] = False

        # Determine next action
        next_action = self._determine_next_action(quality_assessment["decision"])

        # Log quality assessment
        self._log_quality_assessment(state, quality_assessment)

        return {
            **state,
            "quality_assessment": quality_assessment,
            "next_action": next_action,
        }

    def _assess_response_quality(
        self, query: str, response: str, state: HybridSystemState
    ) -> dict[str, Any]:
        """Assess the quality of the chatbot response"""

        # Get quality thresholds from config
        thresholds = self.agent_config.settings.get("quality_thresholds", {
            "adequate_score": 7.0,
            "adjustment_score": 5.0,
        })

        # Check if running in compact mode (for Streamlit performance optimization)
        compact_mode = self._should_use_compact_mode()

        # Use LLM for quality assessment if available
        if self.llm_provider:
            try:
                llm_assessment = self._llm_quality_assessment(query, response, compact=compact_mode)
                overall_score = llm_assessment["overall_score"]
                reasoning = llm_assessment["reasoning"]

                # Apply context-based adjustments
                context_adjustment = self._calculate_context_adjustment(state)
                final_score = max(1.0, overall_score + context_adjustment)

            except Exception as e:
                self.logger.error(
                    "LLM quality assessment failed",
                    extra={
                        "error": str(e),
                        "query_length": len(query),
                        "response_length": len(response),
                        "operation": "llm_quality_assessment",
                    },
                )
                # Fallback to rule-based assessment
                final_score, reasoning = self._rule_based_assessment(query, response)
        else:
            final_score, reasoning = self._rule_based_assessment(query, response)

        # Make decision based on score
        decision = self._make_quality_decision(final_score, thresholds)

        return {
            "decision": decision.value,
            "overall_score": final_score,
            "confidence": min(0.95, max(0.5, final_score / 10.0)),
            "reasoning": reasoning,
            "adjustment_needed": decision == QualityDecision.NEEDS_ADJUSTMENT,
            "thresholds_used": thresholds,
        }

    def _llm_quality_assessment(self, query: str, response: str, compact: bool = True) -> dict[str, Any]:
        """Use LLM to assess response quality"""

        # Use compact prompt for faster responses
        prompt_key = "quality_assessment_compact" if compact else "quality_assessment"
        assessment_prompt = self.agent_config.get_prompt(prompt_key)
        system_prompt = self.agent_config.get_prompt("system")

        evaluation_query = assessment_prompt.format(
            customer_query=query,
            chatbot_response=response
        )

        # Log the LLM call at agent level
        self.logger.info(
            "Quality Agent calling LLM",
            extra={
                "agent": "quality_agent",
                "model_name": self.llm_provider.model_name,
                "provider_type": self.llm_provider.provider_type,
                "prompt_length": len(evaluation_query),
                "system_prompt_length": len(system_prompt),
                "compact_mode": compact,
                "operation": "agent_llm_call"
            }
        )

        llm_response = self.llm_provider.generate_response(
            prompt=evaluation_query,
            system_prompt=system_prompt
        )

        # Parse compact format: [score]|[confidence]|[brief assessment]
        if compact:
            try:
                response_text = llm_response.strip()

                # Handle multi-line responses by taking the first line that matches format
                lines = response_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Try pipe-separated format
                    if '|' in line and len(line.split('|')) >= 3:
                        parts = line.split('|')
                        try:
                            score = float(parts[0].strip())
                            confidence = float(parts[1].strip())
                            reasoning = parts[2].strip()

                            # Validate score and confidence ranges
                            if 1.0 <= score <= 10.0 and 0.0 <= confidence <= 1.0:
                                return {
                                    "overall_score": score,
                                    "reasoning": f"LLM assessment: {reasoning}",
                                }
                        except (ValueError, IndexError):
                            continue

                # Fallback: try to extract score from any line
                import re
                for line in lines:
                    score_match = re.search(r'(\d+(?:\.\d+)?)', line.strip())
                    if score_match:
                        score = float(score_match.group(1))
                        if 1.0 <= score <= 10.0:
                            return {
                                "overall_score": score,
                                "reasoning": f"LLM assessment: {response_text}",
                            }

            except Exception as e:
                self.logger.warning(
                    "Compact format parsing failed",
                    extra={
                        "error": str(e),
                        "response_preview": llm_response[:100],
                        "operation": "compact_parsing",
                    }
                )

            # Use rule-based fallback when compact parsing completely fails
            fallback_score, fallback_reasoning = self._rule_based_assessment(query, response)
            return {
                "overall_score": fallback_score,
                "reasoning": f"Compact parsing failed, used rule-based assessment: {fallback_reasoning}",
            }

        # Parse verbose format (original logic)
        try:
            import re

            # Try multiple score extraction patterns
            score_patterns = [
                r'score[:\s]*(\d+(?:\.\d+)?)/10',           # "Score: 7/10" or "Score 7/10"
                r'score[:\s]*(\d+(?:\.\d+)?)\s*out\s*of\s*10',  # "Score: 7 out of 10"
                r'score[:\s]*(\d+(?:\.\d+)?)',              # "Score: 7.5"
                r'(\d+(?:\.\d+)?)/10',                      # Just "7/10" anywhere
                r'overall[:\s]*(\d+(?:\.\d+)?)/10',         # "Overall: 7/10"
                r'rating[:\s]*(\d+(?:\.\d+)?)/10',          # "Rating: 7/10"
            ]

            extracted_score = None
            score_match_text = ""

            # Try each pattern to extract score
            for pattern in score_patterns:
                match = re.search(pattern, llm_response, re.IGNORECASE)
                if match:
                    extracted_score = float(match.group(1))
                    score_match_text = match.group(0)
                    break

            # If no score pattern found, try line-by-line search for score keyword
            if extracted_score is None:
                lines = llm_response.strip().split('\n')
                for line in lines:
                    if 'score' in line.lower():
                        # Try to extract any number from the line
                        numbers = re.findall(r'(\d+(?:\.\d+)?)', line)
                        if numbers:
                            # Take the first reasonable score (1-10 range)
                            for num_str in numbers:
                                num = float(num_str)
                                if 1.0 <= num <= 10.0:
                                    extracted_score = num
                                    score_match_text = line.strip()
                                    break
                        if extracted_score is not None:
                            break

            # Ensure score is within valid range
            if extracted_score is not None:
                extracted_score = max(1.0, min(10.0, extracted_score))

                # Remove the score line from reasoning to avoid duplication
                reasoning = llm_response
                if score_match_text:
                    reasoning = reasoning.replace(score_match_text, "").strip()

                return {
                    "overall_score": extracted_score,
                    "reasoning": f"LLM assessment: {reasoning}",
                }
            else:
                # No score found - this indicates a parsing issue
                self.logger.warning(
                    "No score found in LLM response, using fallback",
                    extra={
                        "operation": "llm_quality_assessment_parsing",
                        "response_preview": llm_response[:100],
                    }
                )
                raise ValueError("No score pattern matched")

        except Exception as e:
            # Fallback parsing - use rule-based assessment instead of hardcoded 7.0
            self.logger.error(
                "LLM score parsing failed, using rule-based fallback",
                extra={
                    "error": str(e),
                    "operation": "llm_quality_assessment_parsing",
                    "response_preview": llm_response[:100],
                }
            )
            return {
                "overall_score": 5.0,  # Conservative fallback score
                "reasoning": f"LLM assessment parsing failed: {llm_response[:200]}...",
            }

    def _rule_based_assessment(self, query: str, response: str) -> tuple[float, str]:
        """Fallback rule-based quality assessment"""

        score = 7.0  # Base score
        reasons = []

        # Length checks
        if len(response) < 20:
            score -= 2.0
            reasons.append("Response too short")
        elif len(response) > 1000:
            score -= 1.0
            reasons.append("Response too verbose")

        # Relevance check (simple keyword matching)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words & response_words)

        if overlap < 2:
            score -= 1.5
            reasons.append("Low relevance to query")
        elif overlap > len(query_words) * 0.7:
            score += 0.5
            reasons.append("High relevance to query")

        # Check for common problematic phrases
        problematic_phrases = [
            "i don't know", "i can't help", "contact support",
            "error", "unable to", "not available"
        ]

        for phrase in problematic_phrases:
            if phrase in response.lower():
                score -= 1.0
                reasons.append(f"Contains problematic phrase: {phrase}")
                break

        # Ensure score is within bounds
        score = max(1.0, min(10.0, score))

        reasoning = f"Rule-based assessment: {'; '.join(reasons) if reasons else 'Standard response quality'}"

        return score, reasoning

    def _calculate_context_adjustment(self, state: HybridSystemState) -> float:
        """Calculate quality score adjustment based on context"""

        adjustment = 0.0

        # Skip context adjustment if context provider is disabled
        if self.context_provider is None:
            return adjustment

        # Get user context
        context_summary = self.context_provider.get_context_summary(
            state["user_id"], state["session_id"]
        )

        # Adjust for repeat queries (user might be frustrated)
        if context_summary.get("entries_count", 0) > 3:
            adjustment -= 0.5

        # Adjust for previous escalations
        escalation_count = context_summary.get("escalation_count", 0)
        if escalation_count > 0:
            adjustment -= (escalation_count * 0.3)

        return adjustment

    def _make_quality_decision(
        self, score: float, thresholds: dict[str, float]
    ) -> QualityDecision:
        """Make quality decision based on score and thresholds"""

        adequate_threshold = thresholds.get("adequate_score", 7.0)
        adjustment_threshold = thresholds.get("adjustment_score", 5.0)

        if score >= adequate_threshold:
            return QualityDecision.ADEQUATE
        elif score >= adjustment_threshold:
            return QualityDecision.NEEDS_ADJUSTMENT
        else:
            return QualityDecision.HUMAN_INTERVENTION

    # Note: Response adjustment functionality has been removed.
    # The quality agent now only flags responses that need improvement
    # rather than automatically adjusting them.

    def _determine_next_action(self, decision: str) -> str:
        """Determine the next action based on quality decision"""

        action_mapping = {
            QualityDecision.ADEQUATE.value: "respond_to_customer",
            QualityDecision.NEEDS_ADJUSTMENT.value: "flag_for_review",  # Changed from adjustment to flagging
            QualityDecision.HUMAN_INTERVENTION.value: "escalate_to_human",
        }

        return action_mapping.get(decision, "escalate_to_human")

    def _should_use_compact_mode(self) -> bool:
        """Check if compact mode should be used based on Streamlit session state"""
        try:
            import streamlit as st
            # Check if we're in a Streamlit context and performance mode is set
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'performance_mode'):
                performance_mode = st.session_state.performance_mode
                return performance_mode in ["Fast (Compact)", "Fastest (Parallel)"]
        except Exception:
            pass  # Not in Streamlit context or no session state
        return False  # Default to verbose mode

    def _log_quality_assessment(
        self, state: HybridSystemState, assessment: dict[str, Any]
    ):
        """Log quality assessment for monitoring"""

        self.logger.info(
            "Quality assessment completed",
            extra={
                "operation": "quality_assessment",
                "query_id": state["query_id"],
                "user_id": state["user_id"],
                "session_id": state["session_id"],
                "quality_decision": assessment["decision"],
                "quality_score": assessment["overall_score"],
                "confidence": assessment["confidence"],
                "adjustment_needed": assessment["adjustment_needed"],
            },
        )
