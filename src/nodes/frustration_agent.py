"""
Frustration Agent Node
Responsibility: Analyze customer comments to detect frustration levels and trigger human intervention
"""

from enum import Enum
from typing import Any

from langsmith import traceable

from ..core.config import ConfigManager
from ..core.logging import get_logger
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import HybridSystemState


class FrustrationLevel(Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class FrustrationAgentNode:
    """LangGraph node for detecting customer frustration levels"""

    def __init__(self, config_manager: ConfigManager, context_provider: ContextProvider):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("frustration_agent")
        self.context_provider = context_provider
        self.logger = get_logger(__name__)
        self.llm_provider = self._initialize_llm_provider()

        # No longer using rule-based indicators - using LLM-only approach

    def _initialize_llm_provider(self):
        """Initialize the LLM provider for frustration analysis"""
        try:
            factory = LLMProviderFactory(self.config_manager.config_dir)

            preferred_model = self.agent_config.get_preferred_model()
            provider = factory.create_provider_with_fallback(
                preferred_model=preferred_model
            )

            self.logger.info(
                "Frustration Agent LLM provider initialized",
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
                "Failed to initialize Frustration Agent LLM provider",
                extra={"error": str(e), "operation": "initialize_llm_provider"},
            )
            return None


    @traceable(name="Frustration Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main frustration detection function
        Analyzes customer query and interaction history for frustration indicators
        """

        customer_query = state.get("query", "")

        # Analyze current query for frustration
        current_analysis = self._analyze_query_frustration(customer_query)

        # Analyze interaction history for escalating frustration
        current_llm_score = current_analysis.get("current_query_score", 0.0)
        history_analysis = self._analyze_interaction_history(state, current_llm_score)

        # Combine analyses for overall frustration assessment
        overall_assessment = self._combine_frustration_analysis(
            current_analysis, history_analysis
        )

        # Determine if human intervention threshold is reached
        intervention_needed = self._check_intervention_threshold(overall_assessment)

        # Update frustration tracking in context
        self._update_frustration_context(state, overall_assessment)

        # Determine next action
        next_action = "escalate_for_frustration" if intervention_needed else state.get("next_action", "continue")

        # Log frustration analysis
        self._log_frustration_analysis(state, overall_assessment)

        return {
            **state,
            "frustration_analysis": overall_assessment,
            "frustration_intervention_needed": intervention_needed,
            "next_action": next_action,
        }

    def _analyze_query_frustration(self, query: str) -> dict[str, Any]:
        """Analyze the current query for frustration indicators"""

        query_lower = query.lower()

        # Check if running in compact mode (for Streamlit performance optimization)
        compact_mode = self._should_use_compact_mode()

        # LLM-based analysis only
        llm_analysis = None
        if self.llm_provider:
            try:
                llm_analysis = self._llm_frustration_analysis(query, compact=compact_mode)
            except Exception as e:
                self.logger.error(
                    "LLM frustration analysis failed",
                    extra={
                        "error": str(e),
                        "query_length": len(query),
                        "operation": "llm_frustration_analysis",
                        "compact_mode": compact_mode,
                    },
                )

        # Use LLM score or fallback
        if llm_analysis:
            combined_score = llm_analysis["score"]
            confidence = llm_analysis["confidence"]
        else:
            # Fallback when LLM fails
            combined_score = 2.0  # Conservative moderate score
            confidence = 0.3

        # Determine frustration level
        frustration_level = self._score_to_frustration_level(combined_score)

        return {
            "current_query_score": combined_score,
            "frustration_level": frustration_level.value,
            "confidence": confidence,
            "rule_based_indicators": [],  # No longer using rule-based
            "llm_analysis": llm_analysis["reasoning"] if llm_analysis else None,
            "raw_scores": {
                "rule_based": None,  # No longer using rule-based
                "llm_based": llm_analysis["score"] if llm_analysis else None,
            }
        }


    def _llm_frustration_analysis(self, query: str, compact: bool = True) -> dict[str, Any]:
        """Use LLM to analyze frustration in the query"""

        # Use compact prompt for faster responses
        prompt_key = "frustration_analysis_compact" if compact else "frustration_analysis"
        analysis_prompt = self.agent_config.get_prompt(prompt_key)
        system_prompt = self.agent_config.get_prompt("system")

        analysis_query = analysis_prompt.format(customer_query=query)

        # Log the LLM call at agent level
        self.logger.info(
            "Frustration Agent calling LLM",
            extra={
                "agent": "frustration_agent",
                "model_name": self.llm_provider.model_name,
                "provider_type": self.llm_provider.provider_type,
                "prompt_length": len(analysis_query),
                "system_prompt_length": len(system_prompt),
                "compact_mode": compact,
                "operation": "agent_llm_call"
            }
        )

        llm_response = self.llm_provider.generate_response(
            prompt=analysis_query,
            system_prompt=system_prompt
        )

        # Parse compact format: [score]|[confidence]|[brief reason]
        if compact:
            try:
                response = llm_response.strip()
                if '|' in response:
                    parts = response.split('|')
                    if len(parts) >= 3:
                        score = float(parts[0].strip())
                        confidence = float(parts[1].strip())
                        reasoning = parts[2].strip()

                        return {
                            "score": max(0.0, min(10.0, score)),
                            "confidence": max(0.1, min(1.0, confidence)),
                            "reasoning": reasoning,
                        }
            except Exception:
                pass

            # Fallback for compact format parsing failure
            return {
                "score": 5.0,
                "confidence": 0.6,
                "reasoning": f"Compact parsing failed: {llm_response[:50]}...",
            }

        # Parse verbose format (original logic)
        try:
            lines = llm_response.strip().split('\n')
            score_line = next((line for line in lines if 'score:' in line.lower()), "score: 5.0")

            # Extract score - handle both "5.0" and "9/10" formats
            score_text = score_line.split(':')[1].strip()
            if '/' in score_text:
                # Handle "9/10" format
                numerator, denominator = score_text.split('/')
                score = (float(numerator.strip()) / float(denominator.strip())) * 10.0
            else:
                # Handle "5.0" format
                score = float(score_text)

            confidence_line = next((line for line in lines if 'confidence:' in line.lower()), "confidence: 0.7")
            confidence = float(confidence_line.split(':')[1].strip())

            reasoning = llm_response.replace(score_line, "").replace(confidence_line, "").strip()

            return {
                "score": max(0.0, min(10.0, score)),
                "confidence": max(0.1, min(1.0, confidence)),
                "reasoning": reasoning,
            }
        except Exception:
            # Fallback parsing
            return {
                "score": 5.0,
                "confidence": 0.6,
                "reasoning": f"LLM analysis: {llm_response[:200]}...",
            }

    def _analyze_interaction_history(self, state: HybridSystemState, current_llm_score: float = None) -> dict[str, Any]:
        """Analyze interaction history for escalating frustration patterns"""

        # Skip history analysis if context provider is disabled
        if self.context_provider is None:
            return {
                "escalation_trend": "stable",
                "trend_confidence": 0.5,
                "history_context": "No historical context available",
                "query_repetition_score": 0.0,
                "pattern_score": 0.0,
                "interaction_count": 1,
                "time_pattern": "normal"
            }

        # Get recent context
        recent_context = self.context_provider.get_recent_context(
            state["user_id"], state["session_id"], limit=10
        )

        # Extract recent queries
        recent_queries = [
            entry.content for entry in recent_context
            if entry.entry_type == "query"
        ]

        if len(recent_queries) < 2:
            # For first turn, use current LLM score as pattern score
            pattern_score = current_llm_score if current_llm_score is not None else 0.0
            return {
                "pattern_score": pattern_score,
                "escalation_trend": "none",
                "interaction_count": len(recent_queries),
                "time_pattern": "normal",
            }

        # Analyze frustration progression using LLM
        frustration_scores = []
        for query in recent_queries[-5:]:  # Last 5 queries
            try:
                if self.llm_provider:
                    llm_analysis = self._llm_frustration_analysis(query)
                    frustration_scores.append(llm_analysis["score"])
                else:
                    # Fallback to moderate score when LLM unavailable
                    frustration_scores.append(2.0)
            except Exception:
                # Fallback on error
                frustration_scores.append(2.0)

        # Calculate trend
        if len(frustration_scores) >= 3:
            trend = self._calculate_frustration_trend(frustration_scores)
        else:
            trend = "insufficient_data"

        # Calculate pattern score based on trend and frequency
        pattern_score = self._calculate_pattern_score(frustration_scores, recent_context)

        return {
            "pattern_score": pattern_score,
            "escalation_trend": trend,
            "interaction_count": len(recent_queries),
            "frustration_scores": frustration_scores,
            "time_pattern": self._analyze_time_pattern(recent_context),
        }

    def _calculate_frustration_trend(self, scores: list[float]) -> str:
        """Calculate if frustration is escalating, stable, or decreasing"""

        if len(scores) < 3:
            return "insufficient_data"

        # Compare recent scores to earlier ones
        recent_avg = sum(scores[-2:]) / 2
        earlier_avg = sum(scores[:-2]) / len(scores[:-2])

        if recent_avg > earlier_avg + 1.0:
            return "escalating"
        elif recent_avg < earlier_avg - 1.0:
            return "decreasing"
        else:
            return "stable"

    def _calculate_pattern_score(self, frustration_scores: list[float], context: list) -> float:
        """Calculate overall pattern score based on frustration progression"""

        if not frustration_scores:
            return 0.0

        # Base score from average frustration
        avg_frustration = sum(frustration_scores) / len(frustration_scores)

        # Bonus for escalating pattern
        if len(frustration_scores) >= 3:
            trend = self._calculate_frustration_trend(frustration_scores)
            if trend == "escalating":
                avg_frustration += 2.0
            elif trend == "stable" and avg_frustration > 5.0:
                avg_frustration += 1.0

        # Bonus for rapid interactions (might indicate urgency/frustration)
        if len(context) > 5:
            avg_frustration += 1.0

        return min(10.0, avg_frustration)

    def _analyze_time_pattern(self, context: list) -> str:
        """Analyze timing patterns in interactions"""

        if len(context) < 3:
            return "normal"

        # Check if interactions are very frequent (potential frustration indicator)
        timestamps = [entry.timestamp for entry in context[-5:]]
        if len(timestamps) >= 3:
            # Calculate average time between interactions
            time_diffs = [
                (timestamps[i] - timestamps[i-1]).total_seconds() / 60
                for i in range(1, len(timestamps))
            ]
            avg_time_diff = sum(time_diffs) / len(time_diffs)

            if avg_time_diff < 2:  # Less than 2 minutes between interactions
                return "rapid_fire"
            elif avg_time_diff > 60:  # More than 1 hour
                return "spaced_out"

        return "normal"

    def _score_to_frustration_level(self, score: float) -> FrustrationLevel:
        """Convert numerical score to frustration level"""

        thresholds = self.agent_config.settings.get("frustration_thresholds", {
            "critical": 8.0,
            "high": 6.0,
            "moderate": 3.0,
        })

        if score >= thresholds["critical"]:
            return FrustrationLevel.CRITICAL
        elif score >= thresholds["high"]:
            return FrustrationLevel.HIGH
        elif score >= thresholds["moderate"]:
            return FrustrationLevel.MODERATE
        else:
            return FrustrationLevel.LOW

    def _combine_frustration_analysis(
        self, current_analysis: dict[str, Any], history_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """Combine current query and historical frustration analysis"""

        # Weight current query more heavily, but consider history
        current_weight = 0.7
        history_weight = 0.3

        combined_score = (
            current_analysis["current_query_score"] * current_weight +
            history_analysis["pattern_score"] * history_weight
        )

        # Determine overall frustration level
        overall_level = self._score_to_frustration_level(combined_score)

        return {
            "overall_score": combined_score,
            "overall_level": overall_level.value,
            "confidence": current_analysis["confidence"],
            "current_analysis": current_analysis,
            "history_analysis": history_analysis,
            "contributing_factors": self._identify_contributing_factors(
                current_analysis, history_analysis
            ),
        }

    def _identify_contributing_factors(
        self, current: dict[str, Any], history: dict[str, Any]
    ) -> list[str]:
        """Identify what factors are contributing to frustration"""

        factors = []

        # Current query factors
        if current["current_query_score"] > 6.0:
            factors.append("high_frustration_language")

        # Use LLM analysis for factor identification
        if current.get("llm_analysis"):
            # Extract key phrases from LLM reasoning to identify factors
            llm_reasoning = current["llm_analysis"].lower()
            if "escalat" in llm_reasoning or "urgent" in llm_reasoning:
                factors.append("escalation_language")
            if "frustrat" in llm_reasoning or "anger" in llm_reasoning:
                factors.append("strong_negative_sentiment")

        # Historical factors
        if history["escalation_trend"] == "escalating":
            factors.append("escalating_frustration_pattern")

        if history["interaction_count"] > 5:
            factors.append("frequent_interactions")

        if history["time_pattern"] == "rapid_fire":
            factors.append("rapid_successive_queries")

        return factors

    def _should_use_compact_mode(self) -> bool:
        """Check if compact mode should be used based on Streamlit session state"""
        try:
            import streamlit as st
            # Check if we're in a Streamlit context and performance mode is set
            if hasattr(st, 'session_state') and hasattr(st.session_state, 'performance_mode'):
                performance_mode = st.session_state.performance_mode
                return performance_mode in ["Fast (Compact)", "Fastest (Parallel)"]
        except:
            pass  # Not in Streamlit context or no session state
        return False  # Default to verbose mode

    def _check_intervention_threshold(self, assessment: dict[str, Any]) -> bool:
        """Check if frustration level warrants human intervention"""

        intervention_threshold = self.agent_config.settings.get(
            "intervention_threshold", "high"
        )

        current_level = assessment["overall_level"]

        # Map threshold to intervention decision
        threshold_map = {
            "critical": [FrustrationLevel.CRITICAL.value],
            "high": [FrustrationLevel.CRITICAL.value, FrustrationLevel.HIGH.value],
            "moderate": [
                FrustrationLevel.CRITICAL.value,
                FrustrationLevel.HIGH.value,
                FrustrationLevel.MODERATE.value,
            ],
        }

        return current_level in threshold_map.get(intervention_threshold, ["critical"])

    def _update_frustration_context(
        self, state: HybridSystemState, assessment: dict[str, Any]
    ):
        """Update context with frustration analysis"""

        # Skip context update if context provider is disabled
        if self.context_provider is None:
            return

        from datetime import datetime

        from ..interfaces.core.context import ContextEntry

        frustration_context = ContextEntry(
            entry_id=f"{state['query_id']}_frustration",
            user_id=state["user_id"],
            session_id=state["session_id"],
            timestamp=datetime.fromisoformat(state["timestamp"]) if isinstance(state["timestamp"], str) else state["timestamp"],
            entry_type="frustration_analysis",
            content=f"Frustration level: {assessment['overall_level']} (score: {assessment['overall_score']:.1f})",
            metadata={
                "query_id": state["query_id"],
                "frustration_score": assessment["overall_score"],
                "frustration_level": assessment["overall_level"],
                "contributing_factors": assessment["contributing_factors"],
                "intervention_needed": self._check_intervention_threshold(assessment),
            },
        )

        self.context_provider.save_context_entry(frustration_context)

    def _log_frustration_analysis(
        self, state: HybridSystemState, assessment: dict[str, Any]
    ):
        """Log frustration analysis for monitoring"""

        self.logger.info(
            "Frustration analysis completed",
            extra={
                "operation": "frustration_analysis",
                "query_id": state["query_id"],
                "user_id": state["user_id"],
                "session_id": state["session_id"],
                "frustration_level": assessment["overall_level"],
                "frustration_score": assessment["overall_score"],
                "confidence": assessment["confidence"],
                "contributing_factors": assessment["contributing_factors"],
                "intervention_needed": self._check_intervention_threshold(assessment),
            },
        )
