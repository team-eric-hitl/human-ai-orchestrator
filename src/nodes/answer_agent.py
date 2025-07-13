"""
Chatbot Agent Node (Answer Agent)
Responsibility: Generate customer-focused AI responses with enhanced service orientation
Designed to work as the primary chatbot in the human-in-the-loop system
"""

from langchain_core.messages import AIMessage, HumanMessage
from langsmith import traceable

from ..core.logging import get_logger
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import HybridSystemState
from ..core.config import ConfigManager


class AnswerAgentNode:
    """LangGraph node for generating customer service-focused chatbot responses"""

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

    @traceable(run_type="llm", name="Chatbot Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main chatbot function - generate customer service response
        Enhanced for the human-in-the-loop system with customer service focus
        """

        # Get configuration from agent config
        system_prompt = self.agent_config.get_prompt("system")
        customer_service_prompt = self.agent_config.get_prompt("customer_service", "")

        # Build comprehensive context for customer service
        context_prompt = self._build_customer_service_context(state)

        # Detect customer urgency and tone
        customer_analysis = self._analyze_customer_state(state)

        # Generate customer service response
        ai_response = self._generate_customer_service_response(
            state["query"], context_prompt, system_prompt, customer_analysis
        )

        # Add customer service metadata
        response_metadata = self._create_response_metadata(ai_response, customer_analysis)

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
                "response_time": response_metadata.get("response_time", 2.3),
                "customer_service_score": response_metadata.get("service_score", 8.0),
            },
            "messages": state.get("messages", [])
            + [HumanMessage(content=state["query"]), AIMessage(content=ai_response)],
            "next_action": "quality_check",  # Go to quality agent instead of evaluator
        }

    def _build_context_prompt(self, state: HybridSystemState) -> str:
        """Build context-aware prompt from conversation history (legacy method)"""
        return self._build_customer_service_context(state)

    def _build_customer_service_context(self, state: HybridSystemState) -> str:
        """Build comprehensive customer service context"""

        context_summary = self.context_provider.get_context_summary(
            state["user_id"], state["session_id"]
        )

        if context_summary["entries_count"] == 0:
            return "New customer - no previous interaction history."

        # Build customer service focused context
        context_prompt = "CUSTOMER CONTEXT:\n"
        
        # Customer interaction history
        context_prompt += f"- Customer has had {context_summary['entries_count']} previous interactions\n"
        
        # Customer satisfaction indicators
        if context_summary["escalation_count"] > 0:
            context_prompt += f"- Previous escalations: {context_summary['escalation_count']} (handle with extra care)\n"
        
        # Recent interaction topics
        if context_summary["recent_queries"]:
            context_prompt += f"- Recent topics: {', '.join(context_summary['recent_queries'][:3])}\n"
        
        # Customer experience indicators
        if context_summary["entries_count"] > 5:
            context_prompt += "- Frequent customer - provide detailed, comprehensive assistance\n"
        elif context_summary["entries_count"] == 1:
            context_prompt += "- New customer - be welcoming and thorough in explanations\n"

        # Add customer service guidance
        context_prompt += "\nCUSTOMER SERVICE GUIDANCE:\n"
        context_prompt += "- Prioritize customer satisfaction and helpfulness\n"
        context_prompt += "- Be empathetic and understanding\n"
        context_prompt += "- Provide clear, actionable solutions\n"
        
        if context_summary["escalation_count"] > 0:
            context_prompt += "- Extra attention needed due to previous escalations\n"

        return context_prompt

    def _generate_response(
        self, query: str, context_prompt: str, system_prompt: str
    ) -> str:
        """Generate AI response using LLM (legacy method)"""
        return self._generate_customer_service_response(query, context_prompt, system_prompt, {})

    def _generate_customer_service_response(
        self, query: str, context_prompt: str, system_prompt: str, customer_analysis: dict
    ) -> str:
        """Generate customer service focused response using LLM"""
        if not self.llm_provider:
            return "I apologize, but I'm currently experiencing technical difficulties. Please try again in a moment, or if this issue persists, I'll connect you with one of our human agents who can assist you immediately."

        try:
            # Build customer service focused prompt
            full_prompt = self._build_customer_service_prompt(query, context_prompt, customer_analysis)

            # Generate response using LLM with customer service system prompt
            response = self.llm_provider.generate_response(
                prompt=full_prompt, system_prompt=system_prompt
            )

            # Post-process response for customer service standards
            response = self._enhance_customer_service_response(response, customer_analysis)

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
            return "I sincerely apologize, but I'm experiencing technical difficulties at the moment. To ensure you receive the best possible assistance, I'm going to connect you with one of our human agents who can help resolve your question immediately."

    def _save_interaction_context(self, state: HybridSystemState, response: str, metadata: dict = None):
        """Save interaction to context store with enhanced metadata"""
        from ..interfaces.core.context import ContextEntry
        from datetime import datetime

        # Save query
        timestamp = datetime.fromisoformat(state["timestamp"]) if isinstance(state["timestamp"], str) else state["timestamp"]
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
        
        # Basic sentiment analysis
        urgency_keywords = ["urgent", "asap", "immediately", "emergency", "critical", "help"]
        frustration_keywords = ["frustrated", "angry", "upset", "disappointed", "problem"]
        politeness_keywords = ["please", "thank you", "thanks", "appreciate"]
        
        analysis = {
            "urgency_detected": any(keyword in query for keyword in urgency_keywords),
            "frustration_detected": any(keyword in query for keyword in frustration_keywords),
            "politeness_detected": any(keyword in query for keyword in politeness_keywords),
            "query_length": len(query),
            "question_marks": query.count("?"),
            "exclamation_marks": query.count("!"),
            "caps_ratio": sum(1 for c in query if c.isupper()) / max(len(query), 1),
        }
        
        # Determine customer tone
        if analysis["caps_ratio"] > 0.3 or analysis["exclamation_marks"] > 2:
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

    def _build_customer_service_prompt(self, query: str, context_prompt: str, customer_analysis: dict) -> str:
        """Build comprehensive customer service prompt"""
        prompt_parts = []
        
        # Add context if available
        if context_prompt:
            prompt_parts.append(context_prompt)
        
        # Add customer analysis
        if customer_analysis:
            prompt_parts.append(f"\nCUSTOMER TONE ANALYSIS:")
            prompt_parts.append(f"- Detected tone: {customer_analysis.get('tone', 'neutral')}")
            
            if customer_analysis.get("urgency_detected"):
                prompt_parts.append("- URGENT request detected - prioritize quick, direct response")
            if customer_analysis.get("frustration_detected"):
                prompt_parts.append("- Customer frustration detected - be extra empathetic and helpful")
            if customer_analysis.get("politeness_detected"):
                prompt_parts.append("- Polite customer - match their courteous tone")
        
        # Add the actual customer query
        prompt_parts.append(f"\nCUSTOMER QUERY: {query}")
        
        # Add response guidance
        prompt_parts.append("\nRESPONSE REQUIREMENTS:")
        prompt_parts.append("- Be helpful, professional, and customer-focused")
        prompt_parts.append("- Provide clear, actionable solutions when possible")
        prompt_parts.append("- Show empathy and understanding")
        prompt_parts.append("- Be concise but thorough")
        
        return "\n".join(prompt_parts)

    def _enhance_customer_service_response(self, response: str, customer_analysis: dict) -> str:
        """Post-process response to enhance customer service quality"""
        # Basic enhancement - could be expanded with more sophisticated processing
        
        # Add empathy for frustrated customers
        if customer_analysis.get("frustration_detected") and not any(
            phrase in response.lower() for phrase in ["sorry", "apologize", "understand"]
        ):
            response = "I understand this can be frustrating. " + response
        
        # Add urgency acknowledgment
        if customer_analysis.get("urgency_detected") and "urgent" not in response.lower():
            response = response + " I've prioritized your request to help resolve this quickly."
        
        # Ensure polite tone is maintained
        if not response.endswith((".", "!", "?")):
            response += "."
        
        return response

    def _create_response_metadata(self, response: str, customer_analysis: dict) -> dict:
        """Create metadata for the response"""
        
        # Calculate basic service score
        service_score = 8.0  # Base score
        
        # Adjust based on response characteristics
        if len(response) > 50:  # Substantial response
            service_score += 0.5
        if customer_analysis.get("tone") == "frustrated" and any(
            phrase in response.lower() for phrase in ["sorry", "apologize", "understand"]
        ):
            service_score += 1.0  # Bonus for empathy with frustrated customers
        
        # Calculate confidence based on response quality indicators
        confidence = 0.85  # Base confidence
        if len(response) < 20:  # Very short responses might be lower quality
            confidence -= 0.1
        if "?" in response:  # Asking questions is good for clarification
            confidence += 0.05
        
        return {
            "confidence": min(1.0, confidence),
            "service_score": min(10.0, service_score),
            "response_length": len(response),
            "customer_analysis": customer_analysis,
            "response_time": 2.3,  # Would be actual timing in production
        }
