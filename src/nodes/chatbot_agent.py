"""
Chatbot Agent Node (Answer Agent)
Responsibility: Generate customer-focused AI responses with enhanced service orientation
Designed to work as the primary chatbot in the human-in-the-loop system
"""

import time

from langchain_core.messages import AIMessage, HumanMessage
from langsmith import traceable

from ..core.config import ConfigManager
from ..core.logging import get_logger
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import HybridSystemState


class ChatbotAgentNode:
    """LangGraph node for generating customer service-focused chatbot responses"""

    def __init__(
        self, config_manager: ConfigManager, context_provider: ContextProvider
    ):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("chatbot_agent")
        self.context_provider = context_provider
        self.logger = get_logger(__name__)
        self.llm_provider = self._initialize_llm_provider()

    def _initialize_llm_provider(self):
        """Initialize the LLM provider with fallback strategy"""
        try:
            factory = LLMProviderFactory(str(self.config_manager.config_dir))

            # Use agent-specific model configuration
            preferred_model = (
                self.agent_config.get_preferred_model() if self.agent_config else None
            )
            fallback_models = (
                self.agent_config.get_fallback_models() if self.agent_config else []
            )
            provider = factory.create_provider_with_fallback(
                preferred_model=preferred_model
            )

            self.logger.info(
                "Chatbot Agent LLM provider initialized",
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

    @traceable(run_type="llm", name="Chatbot Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main chatbot function - generate customer service response
        Enhanced for the human-in-the-loop system with customer service focus
        """
        start_time = time.time()

        # Get configuration from agent config
        system_prompt = (
            self.agent_config.get_prompt("system")
            if self.agent_config
            else "You are a helpful customer service assistant."
        )

        # Build comprehensive context for customer service
        context_prompt = self._build_customer_service_context(state)

        # Detect customer urgency and tone
        customer_analysis = self._analyze_customer_state(state)

        # Generate customer service response
        ai_response = self._generate_customer_service_response(
            state["query"], context_prompt, system_prompt, customer_analysis
        )

        # Calculate actual response time
        response_time = time.time() - start_time

        # Add customer service metadata
        response_metadata = self._create_response_metadata(
            ai_response, customer_analysis, response_time
        )

        # Save interaction to context
        self._save_interaction_context(state, ai_response, response_metadata)

        # Update state with customer service enhancements
        return {
            **state,
            "ai_response": ai_response,
            "response_metadata": response_metadata,
            "customer_analysis": customer_analysis,
            "initial_assessment": {
                "context_used": len(context_prompt) > 0,
                "confidence": response_metadata.get("confidence", 0.85),
                "response_time": response_time,
                "customer_service_score": response_metadata.get("service_score", 8.0),
            },
            "messages": state.get("messages", [])
            + [HumanMessage(content=state["query"]), AIMessage(content=ai_response)],
            "next_action": "quality_check",
        }

    def _build_context_prompt(self, state: HybridSystemState) -> str:
        """Build context-aware prompt from conversation history (legacy method)"""
        return self._build_customer_service_context(state)

    def _build_customer_service_context(self, state: HybridSystemState) -> str:
        """Build comprehensive customer service context"""

        # Handle case when context provider is disabled
        if self.context_provider is None:
            return self._get_context_template("new_customer_note")

        context_summary = self.context_provider.get_context_summary(
            state["user_id"], state["session_id"]
        )

        if context_summary["entries_count"] == 0:
            return self._get_context_template("new_customer_note")

        # Build customer service focused context
        context_prompt = self._get_context_template("customer_context_header") + "\n"

        # Customer interaction history
        context_prompt += self._get_context_template("interaction_history").format(
            count=context_summary['entries_count']
        ) + "\n"

        # Customer satisfaction indicators
        if context_summary["escalation_count"] > 0:
            context_prompt += self._get_context_template("escalation_warning").format(
                count=context_summary['escalation_count']
            ) + "\n"

        # Recent interaction topics
        if context_summary["recent_queries"]:
            topics = ', '.join(context_summary['recent_queries'][:3])
            context_prompt += self._get_context_template("recent_topics").format(
                topics=topics
            ) + "\n"

        # Customer experience indicators
        if context_summary["entries_count"] > 5:
            context_prompt += self._get_context_template("frequent_customer") + "\n"
        elif context_summary["entries_count"] == 1:
            context_prompt += self._get_context_template("new_customer_guidance") + "\n"

        # Add customer service guidance
        context_prompt += "\n" + self._get_context_template("service_guidance_header") + "\n"
        service_guidelines = self._get_context_template("service_guidelines")
        for guideline in service_guidelines[:3]:  # First 3 guidelines
            context_prompt += guideline + "\n"

        if context_summary["escalation_count"] > 0:
            context_prompt += service_guidelines[3] + "\n"  # Escalation guideline

        return context_prompt

    def _generate_response(
        self, query: str, context_prompt: str, system_prompt: str
    ) -> str:
        """Generate AI response using LLM (legacy method)"""
        return self._generate_customer_service_response(
            query, context_prompt, system_prompt, {}
        )

    def _generate_customer_service_response(
        self,
        query: str,
        context_prompt: str,
        system_prompt: str,
        customer_analysis: dict,
    ) -> str:
        """Generate customer service focused response using LLM"""
        if not self.llm_provider:
            return self._get_error_template("technical_difficulties")

        try:
            # Build customer service focused prompt
            full_prompt = self._build_customer_service_prompt(
                query, context_prompt, customer_analysis
            )

            # Generate response using LLM with customer service system prompt
            response = self.llm_provider.generate_response(
                prompt=full_prompt, system_prompt=system_prompt
            )

            # Post-process response for customer service standards
            response = self._enhance_customer_service_response(
                response, customer_analysis
            )

            return response

        except Exception as e:
            self.logger.error(
                "Error generating customer service response",
                extra={
                    "error": str(e),
                    "query_length": len(query),
                    "has_context": bool(context_prompt),
                    "customer_analysis": customer_analysis,
                    "operation": "generate_customer_service_response",
                },
            )
            return self._get_error_template("service_failure")

    def _save_interaction_context(
        self, state: HybridSystemState, response: str, metadata: dict | None = None
    ):
        """Save interaction to context store with enhanced metadata"""
        # Skip if context provider is disabled
        if self.context_provider is None:
            return

        from datetime import datetime

        from ..interfaces.core.context import ContextEntry

        # Save query
        timestamp = (
            datetime.fromisoformat(state["timestamp"])
            if isinstance(state["timestamp"], str)
            else state["timestamp"]
        )
        query_metadata = {"query_id": state["query_id"]}
        if metadata and "customer_analysis" in metadata:
            query_metadata["customer_analysis"] = metadata["customer_analysis"]

        query_context = ContextEntry(
            entry_id=f"{state['query_id']}_query",
            user_id=state["user_id"],
            session_id=state["session_id"],
            timestamp=timestamp,
            entry_type="query",
            content=state["query"],
            metadata=query_metadata,
        )
        self.context_provider.save_context_entry(query_context)

        # Save response with enhanced metadata
        response_metadata = {
            "query_id": state["query_id"],
            "model_confidence": metadata.get("confidence", 0.85) if metadata else 0.85,
            "service_score": metadata.get("service_score", 8.0) if metadata else 8.0,
            "response_type": "chatbot_response",
        }
        if metadata:
            response_metadata.update(metadata)

        response_context = ContextEntry(
            entry_id=f"{state['query_id']}_response",
            user_id=state["user_id"],
            session_id=state["session_id"],
            timestamp=timestamp,
            entry_type="response",
            content=response,
            metadata=response_metadata,
        )
        self.context_provider.save_context_entry(response_context)

    def _analyze_customer_state(self, state: HybridSystemState) -> dict:
        """Analyze customer state for service customization"""
        query = state.get("query", "").lower()

        # Get sentiment analysis configuration
        sentiment_config = self._get_sentiment_config()
        urgency_keywords = sentiment_config.get("urgency_keywords", [])
        frustration_keywords = sentiment_config.get("frustration_keywords", [])
        politeness_keywords = sentiment_config.get("politeness_keywords", [])

        analysis = {
            "urgency_detected": any(keyword in query for keyword in urgency_keywords),
            "frustration_detected": any(
                keyword in query for keyword in frustration_keywords
            ),
            "politeness_detected": any(
                keyword in query for keyword in politeness_keywords
            ),
            "query_length": len(query),
            "question_marks": query.count("?"),
            "exclamation_marks": query.count("!"),
            "caps_ratio": sum(1 for c in query if c.isupper()) / max(len(query), 1),
        }

        # Get tone thresholds from configuration
        tone_thresholds = self._get_quality_config().get("tone_thresholds", {})
        caps_threshold = tone_thresholds.get("caps_ratio_emphatic", 0.3)
        exclamation_threshold = tone_thresholds.get("exclamation_emphatic", 2)

        # Determine customer tone
        if analysis["caps_ratio"] > caps_threshold or analysis["exclamation_marks"] > exclamation_threshold:
            analysis["tone"] = "emphatic"
        elif analysis["frustration_detected"]:
            analysis["tone"] = "frustrated"
        elif analysis["urgency_detected"]:
            analysis["tone"] = "urgent"
        elif analysis["politeness_detected"]:
            analysis["tone"] = "polite"
        else:
            analysis["tone"] = "neutral"

        return analysis

    def _build_customer_service_prompt(
        self, query: str, context_prompt: str, customer_analysis: dict
    ) -> str:
        """Build comprehensive customer service prompt"""
        prompt_parts = []

        # Add context if available
        if context_prompt:
            prompt_parts.append(context_prompt)

        # Add customer analysis
        if customer_analysis:
            prompt_parts.append("\n" + self._get_response_template("tone_analysis_header"))
            prompt_parts.append(
                self._get_response_template("tone_detected").format(
                    tone=customer_analysis.get('tone', 'neutral')
                )
            )

            if customer_analysis.get("urgency_detected"):
                prompt_parts.append(self._get_response_template("urgency_guidance"))
            if customer_analysis.get("frustration_detected"):
                prompt_parts.append(self._get_response_template("frustration_guidance"))
            if customer_analysis.get("politeness_detected"):
                prompt_parts.append(self._get_response_template("politeness_guidance"))

        # Add the actual customer query
        prompt_parts.append(
            "\n" + self._get_response_template("query_header").format(query=query)
        )

        # Add response guidance
        prompt_parts.append("\n" + self._get_response_template("response_requirements_header"))
        response_guidelines = self._get_response_template("response_guidelines")
        for guideline in response_guidelines:
            prompt_parts.append(guideline)

        return "\n".join(prompt_parts)

    def _enhance_customer_service_response(
        self, response: str, customer_analysis: dict
    ) -> str:
        """Post-process response to enhance customer service quality"""
        # Get empathy phrases from configuration
        sentiment_config = self._get_sentiment_config()
        empathy_phrases = sentiment_config.get("empathy_phrases", ["sorry", "apologize", "understand"])

        # Add empathy for frustrated customers
        if customer_analysis.get("frustration_detected") and not any(
            phrase in response.lower() for phrase in empathy_phrases
        ):
            response = "I understand this can be frustrating. " + response

        # Add urgency acknowledgment
        if (
            customer_analysis.get("urgency_detected")
            and "urgent" not in response.lower()
        ):
            response = (
                response
                + " I've prioritized your request to help resolve this quickly."
            )

        # Ensure polite tone is maintained
        if not response.endswith((".", "!", "?")):
            response += "."

        return response

    def _create_response_metadata(self, response: str, customer_analysis: dict, response_time: float) -> dict:
        """Create metadata for the response"""
        # Get quality scoring configuration
        quality_config = self._get_quality_config()

        # Calculate basic service score
        service_score = quality_config.get("base_service_score", 8.0)

        # Get service score adjustments
        score_adjustments = quality_config.get("service_score_adjustments", {})
        substantial_threshold = score_adjustments.get("substantial_response_threshold", 50)
        substantial_bonus = score_adjustments.get("substantial_response_bonus", 0.5)
        empathy_bonus = score_adjustments.get("frustrated_empathy_bonus", 1.0)

        # Adjust based on response characteristics
        if len(response) > substantial_threshold:  # Substantial response
            service_score += substantial_bonus

        # Get empathy phrases from sentiment config
        sentiment_config = self._get_sentiment_config()
        empathy_phrases = sentiment_config.get("empathy_phrases", ["sorry", "apologize", "understand"])

        if customer_analysis.get("tone") == "frustrated" and any(
            phrase in response.lower() for phrase in empathy_phrases
        ):
            service_score += empathy_bonus  # Bonus for empathy with frustrated customers

        # Calculate confidence based on response quality indicators
        confidence = quality_config.get("base_confidence", 0.85)

        # Get confidence adjustments
        conf_adjustments = quality_config.get("confidence_adjustments", {})
        short_threshold = conf_adjustments.get("short_response_threshold", 20)
        short_penalty = conf_adjustments.get("short_response_penalty", -0.1)
        question_bonus = conf_adjustments.get("question_bonus", 0.05)

        if len(response) < short_threshold:  # Very short responses might be lower quality
            confidence += short_penalty
        if "?" in response:  # Asking questions is good for clarification
            confidence += question_bonus

        return {
            "confidence": min(1.0, confidence),
            "service_score": min(10.0, service_score),
            "response_length": len(response),
            "customer_analysis": customer_analysis,
            "response_time": response_time,
        }

    def _get_context_template(self, template_key: str) -> str:
        """Get context template from configuration"""
        if not self.agent_config:
            return ""

        context_templates = self.agent_config.prompts.get("context_templates", {})
        return context_templates.get(template_key, "")

    def _get_response_template(self, template_key: str) -> str:
        """Get response template from configuration"""
        if not self.agent_config:
            return ""

        response_templates = self.agent_config.prompts.get("response_templates", {})
        return response_templates.get(template_key, "")

    def _get_error_template(self, template_key: str) -> str:
        """Get error template from configuration"""
        if not self.agent_config:
            return "I apologize, but I'm experiencing technical difficulties."

        error_templates = self.agent_config.prompts.get("error_templates", {})
        return error_templates.get(template_key, "I apologize, but I'm experiencing technical difficulties.")

    def _get_sentiment_config(self) -> dict:
        """Get sentiment analysis configuration"""
        if not self.agent_config:
            return {}

        return self.agent_config.prompts.get("sentiment_analysis", {})

    def _get_quality_config(self) -> dict:
        """Get quality scoring configuration"""
        if not self.agent_config:
            return {}

        return self.agent_config.prompts.get("quality_scoring", {})
