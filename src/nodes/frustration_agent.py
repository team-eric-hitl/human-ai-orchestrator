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

        # Load frustration indicators from config
        self.frustration_indicators = self._load_frustration_indicators()

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

    def _load_frustration_indicators(self) -> dict[str, list[str]]:
        """Load frustration indicators from config"""

        default_indicators = {
            "high_frustration": [
                "angry", "furious", "outraged", "livid", "pissed", "mad",
                "ridiculous", "unacceptable", "disgusting", "horrible",
                "worst", "terrible", "awful", "useless", "garbage",
                "stupid", "idiotic", "moronic", "pathetic", "joke"
            ],
            "moderate_frustration": [
                "frustrated", "annoyed", "irritated", "upset", "disappointed",
                "unhappy", "dissatisfied", "confused", "lost", "stuck",
                "tired", "fed up", "sick", "bothered", "troubled"
            ],
            "escalation_phrases": [
                "speak to manager", "supervisor", "escalate", "complaint",
                "lawsuit", "lawyer", "attorney", "sue", "legal action",
                "corporate", "headquarters", "cancel", "refund"
            ],
            "urgency_indicators": [
                "urgent", "emergency", "asap", "immediately", "right now",
                "critical", "important", "deadline", "time sensitive"
            ],
            "repeat_indicators": [
                "again", "still", "keep", "multiple times", "several times",
                "how many times", "over and over", "repeatedly"
            ]
        }

        # Get from config or use defaults
        return self.agent_config.settings.get("frustration_indicators", default_indicators)

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
        history_analysis = self._analyze_interaction_history(state)

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

        # Rule-based analysis
        rule_based_score = self._rule_based_frustration_score(query_lower)

        # LLM-based analysis if available
        llm_analysis = None
        if self.llm_provider:
            try:
                llm_analysis = self._llm_frustration_analysis(query)
            except Exception as e:
                self.logger.error(
                    "LLM frustration analysis failed",
                    extra={
                        "error": str(e),
                        "query_length": len(query),
                        "operation": "llm_frustration_analysis",
                    },
                )

        # Combine scores
        if llm_analysis:
            combined_score = (rule_based_score["score"] + llm_analysis["score"]) / 2
            confidence = min(rule_based_score["confidence"], llm_analysis["confidence"])
        else:
            combined_score = rule_based_score["score"]
            confidence = rule_based_score["confidence"] * 0.8  # Lower confidence without LLM

        # Determine frustration level
        frustration_level = self._score_to_frustration_level(combined_score)

        return {
            "current_query_score": combined_score,
            "frustration_level": frustration_level.value,
            "confidence": confidence,
            "rule_based_indicators": rule_based_score["indicators"],
            "llm_analysis": llm_analysis["reasoning"] if llm_analysis else None,
            "raw_scores": {
                "rule_based": rule_based_score["score"],
                "llm_based": llm_analysis["score"] if llm_analysis else None,
            }
        }

    def _rule_based_frustration_score(self, query: str) -> dict[str, Any]:
        """Calculate frustration score using rule-based approach"""

        score = 0.0
        indicators_found = []

        # Check for different types of frustration indicators
        for category, keywords in self.frustration_indicators.items():
            category_matches = []
            for keyword in keywords:
                if keyword in query:
                    category_matches.append(keyword)

            if category_matches:
                indicators_found.extend([(category, match) for match in category_matches])

                # Weight different categories
                if category == "high_frustration":
                    score += len(category_matches) * 3.0
                elif category == "moderate_frustration":
                    score += len(category_matches) * 2.0
                elif category == "escalation_phrases":
                    score += len(category_matches) * 4.0
                elif category == "urgency_indicators":
                    score += len(category_matches) * 1.5
                elif category == "repeat_indicators":
                    score += len(category_matches) * 2.5

        # Check for caps lock (shouting)
        caps_ratio = sum(1 for c in query if c.isupper()) / max(len(query), 1)
        if caps_ratio > 0.7 and len(query) > 10:
            score += 2.0
            indicators_found.append(("shouting", "excessive_caps"))

        # Check for excessive punctuation
        exclamation_count = query.count('!')
        question_count = query.count('?')
        if exclamation_count > 2:
            score += min(exclamation_count * 0.5, 2.0)
            indicators_found.append(("emphasis", f"{exclamation_count}_exclamations"))

        # Normalize score to 0-10 scale
        normalized_score = min(10.0, score)

        # Calculate confidence based on number of indicators
        confidence = min(0.95, 0.5 + (len(indicators_found) * 0.1))

        return {
            "score": normalized_score,
            "confidence": confidence,
            "indicators": indicators_found,
        }

    def _llm_frustration_analysis(self, query: str) -> dict[str, Any]:
        """Use LLM to analyze frustration in the query"""

        analysis_prompt = self.agent_config.get_prompt("frustration_analysis")
        system_prompt = self.agent_config.get_prompt("system")

        analysis_query = analysis_prompt.format(customer_query=query)

        llm_response = self.llm_provider.generate_response(
            prompt=analysis_query,
            system_prompt=system_prompt
        )

        # Parse LLM response (simplified - would use structured output in production)
        try:
            lines = llm_response.strip().split('\n')
            score_line = next((line for line in lines if 'score:' in line.lower()), "score: 5.0")
            score = float(score_line.split(':')[1].strip())

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

    def _analyze_interaction_history(self, state: HybridSystemState) -> dict[str, Any]:
        """Analyze interaction history for escalating frustration patterns"""

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
            return {
                "pattern_score": 0.0,
                "escalation_trend": "none",
                "interaction_count": len(recent_queries),
                "time_pattern": "normal",
            }

        # Analyze frustration progression
        frustration_scores = []
        for query in recent_queries[-5:]:  # Last 5 queries
            query_analysis = self._rule_based_frustration_score(query.lower())
            frustration_scores.append(query_analysis["score"])

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

        if current["rule_based_indicators"]:
            factor_types = set([indicator[0] for indicator in current["rule_based_indicators"]])
            if "escalation_phrases" in factor_types:
                factors.append("escalation_language")
            if "high_frustration" in factor_types:
                factors.append("strong_negative_sentiment")

        # Historical factors
        if history["escalation_trend"] == "escalating":
            factors.append("escalating_frustration_pattern")

        if history["interaction_count"] > 5:
            factors.append("frequent_interactions")

        if history["time_pattern"] == "rapid_fire":
            factors.append("rapid_successive_queries")

        return factors

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
