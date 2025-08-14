"""
Routing Agent Node
Responsibility: Select the best human agent for escalations, balancing workload and employee experience
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from langsmith import traceable

from ..core.config import ConfigManager
from ..core.logging import get_logger
from ..core.agent_field_mapper import AgentFieldMapper
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import HybridSystemState
from ..nodes.sync_llm_routing import SyncLLMRoutingAgent
from ..interfaces.human_agents import Specialization


class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    BREAK = "break"
    OFFLINE = "offline"


class HumanRoutingAgentNode:
    """LangGraph node for intelligent routing of escalations to human agents"""

    def __init__(self, config_manager: ConfigManager, context_provider: ContextProvider):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("human_routing_agent")
        self.context_provider = context_provider
        self.logger = get_logger(__name__)
        self.llm_provider = self._initialize_llm_provider()

        # Initialize field mapper for database to agent format conversion
        self.field_mapper = AgentFieldMapper()

        # Initialize synchronous LLM routing agent with database integration
        self.sync_llm_routing_agent = SyncLLMRoutingAgent()
        
        self.routing_history = []  # Track routing decisions
        

    def _initialize_llm_provider(self):
        """Initialize LLM provider for intelligent routing decisions"""
        try:
            factory = LLMProviderFactory(self.config_manager.config_dir)

            preferred_model = self.agent_config.get_preferred_model()
            provider = factory.create_provider_with_fallback(
                preferred_model=preferred_model
            )

            self.logger.info(
                "Routing Agent LLM provider initialized",
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
                "Failed to initialize Routing Agent LLM provider",
                extra={"error": str(e), "operation": "initialize_llm_provider"},
            )
            return None


    @traceable(name="Routing Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main routing function - select best human agent for escalation
        """

        return self._sync_llm_based_routing(state)

    def _sync_llm_based_routing(self, state: HybridSystemState) -> HybridSystemState:
        """Use synchronous LLM-powered routing with database integration"""
        try:
            # Analyze routing requirements (enhanced with context if available)
            routing_requirements = self._analyze_routing_requirements(state)
            
            # Enhance routing requirements with Context Manager data if available
            if state.get("enriched_context"):
                routing_requirements = self._enhance_routing_with_context(routing_requirements, state)
            
            # Convert to conversation and customer context for LLM router
            conversation_context = self._create_conversation_context(state, routing_requirements)
            customer_context = self._create_customer_context(state)
            urgency_level = self._map_priority_to_urgency(routing_requirements["priority"])
            
            # Use synchronous LLM routing agent
            routing_result = self.sync_llm_routing_agent.route_to_human(
                conversation_context=conversation_context,
                customer_context=customer_context,
                urgency_level=urgency_level
            )
            
            if routing_result["success"]:
                # Extract selected agent info
                selected_agent = routing_result["selected_agent"]
                decision_details = routing_result["decision_details"]
                
                # Create routing decision in expected format
                routing_decision = {
                    "assigned_agent_id": selected_agent["id"],
                    "assigned_agent_name": selected_agent["name"],
                    "assigned_agent_email": selected_agent["email"],
                    "routing_strategy": "llm_powered",
                    "routing_requirements": routing_requirements,
                    "agent_match_score": decision_details["score"] * 100,  # Convert to 0-100 scale
                    "estimated_resolution_time": routing_requirements["estimated_resolution_time"],
                    "routing_timestamp": routing_result["routing_timestamp"],
                    "routing_confidence": decision_details["confidence"],
                    "alternative_agents": [
                        {"id": alt["agent_id"], "name": alt["agent_name"]}
                        for alt in decision_details.get("alternatives", [])[:3]
                    ],
                    "llm_reasoning": decision_details.get("reasoning", []),
                    "llm_explanation": self.sync_llm_routing_agent.explain_routing_decision(routing_result, conversation_context)
                }
                
                # Convert to legacy agent format for compatibility
                final_agent = self._convert_to_legacy_format(selected_agent)
                
                # Log routing decision
                self._log_routing_decision(state, routing_decision)
                
                return {
                    **state,
                    "routing_decision": routing_decision,
                    "assigned_human_agent": final_agent,
                    "routing_requirements": routing_requirements,
                    "next_action": "transfer_to_human",
                }
            else:
                # Handle routing failure
                return self._handle_no_agents_available(state, routing_requirements)
                
        except Exception as e:
            self.logger.error(f"Sync LLM routing failed: {e}")
            return self._handle_no_agents_available(state, self._analyze_routing_requirements(state))


    def _analyze_routing_requirements(self, state: HybridSystemState) -> dict[str, Any]:
        """Analyze the escalation to determine routing requirements"""

        query = state.get("query", "")
        escalation_reason = state.get("escalation_reason", "")
        frustration_analysis = state.get("frustration_analysis", {})
        quality_assessment = state.get("quality_assessment", {})

        # Determine required skills
        required_skills = self._identify_required_skills(query, escalation_reason)

        # Determine priority level
        priority = self._calculate_escalation_priority(
            frustration_analysis, quality_assessment, state
        )

        # Determine complexity level
        complexity = self._assess_case_complexity(query, state)

        # Check for special requirements
        special_requirements = self._identify_special_requirements(query, state)

        return {
            "required_skills": required_skills,
            "priority": priority,
            "complexity": complexity,
            "special_requirements": special_requirements,
            "customer_frustration_level": frustration_analysis.get("overall_level", "low"),
            "estimated_resolution_time": self._estimate_resolution_time(complexity, required_skills),
            "escalation_type": self._classify_escalation_type(escalation_reason),
        }

    def _identify_required_skills(self, query: str, escalation_reason: str) -> list[str]:
        """Identify what skills are needed for this escalation"""

        combined_text = f"{query} {escalation_reason}".lower()

        # Skill keyword mapping
        skill_keywords = self.agent_config.settings.get("skill_keywords", {
            "technical": [
                "api", "integration", "code", "bug", "error", "technical",
                "system", "database", "server", "authentication", "ssl"
            ],
            "billing": [
                "billing", "invoice", "payment", "charge", "refund", "price",
                "subscription", "plan", "cost", "fee"
            ],
            "account_management": [
                "account", "profile", "settings", "permissions", "access",
                "user", "admin", "organization", "team"
            ],
            "product_support": [
                "feature", "functionality", "how to", "tutorial", "guide",
                "documentation", "product", "usage"
            ],
            "compliance": [
                "privacy", "gdpr", "security", "compliance", "audit",
                "regulation", "legal", "policy"
            ],
        })

        required_skills = []
        for skill, keywords in skill_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                required_skills.append(skill)

        # Default to general if no specific skills identified
        if not required_skills:
            required_skills = ["general"]

        return required_skills

    def _calculate_escalation_priority(
        self, frustration_analysis: dict[str, Any],
        quality_assessment: dict[str, Any],
        state: HybridSystemState
    ) -> str:
        """Calculate priority level for the escalation"""

        priority_score = 0

        # Frustration level contribution
        frustration_level = frustration_analysis.get("overall_level", "low")
        frustration_scores = {
            "critical": 4,
            "high": 3,
            "moderate": 2,
            "low": 1,
        }
        priority_score += frustration_scores.get(frustration_level, 1)

        # Quality assessment contribution
        quality_score = quality_assessment.get("overall_score", 7.0)
        if quality_score < 4.0:
            priority_score += 2
        elif quality_score < 6.0:
            priority_score += 1

        # Context-based factors
        context_summary = self.context_provider.get_context_summary(
            state["user_id"], state["session_id"]
        )

        # Previous escalations increase priority
        escalation_count = context_summary.get("escalation_count", 0)
        if escalation_count > 1:
            priority_score += min(escalation_count, 3)

        # Frequent interactions might indicate urgency
        interaction_count = context_summary.get("entries_count", 0)
        if interaction_count > 5:
            priority_score += 1

        # Convert score to priority level
        if priority_score >= 7:
            return "critical"
        elif priority_score >= 5:
            return "high"
        elif priority_score >= 3:
            return "medium"
        else:
            return "low"

    def _assess_case_complexity(self, query: str, state: HybridSystemState) -> str:
        """Assess the complexity of the case"""

        complexity_indicators = {
            "high": [
                "integration", "api", "enterprise", "custom", "multiple",
                "complex", "advanced", "migration", "database", "server"
            ],
            "medium": [
                "configuration", "setup", "billing", "account", "permissions",
                "features", "workflow", "reporting"
            ],
        }

        query_lower = query.lower()

        for level, indicators in complexity_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                return level

        # Check query length as complexity indicator
        if len(query) > 500:
            return "medium"

        return "low"

    def _identify_special_requirements(self, query: str, state: HybridSystemState) -> list[str]:
        """Identify any special requirements for routing"""

        requirements = []
        query_lower = query.lower()

        # Language requirements
        language_indicators = {
            "spanish": ["en español", "habla español", "spanish"],
            "french": ["en français", "french", "français"],
            "german": ["auf deutsch", "german", "deutsch"],
        }

        for language, indicators in language_indicators.items():
            if any(indicator in query_lower for indicator in indicators):
                requirements.append(f"language_{language}")

        # Time sensitivity
        urgency_indicators = [
            "urgent", "asap", "immediately", "emergency", "critical",
            "deadline", "time sensitive", "right now"
        ]

        if any(indicator in query_lower for indicator in urgency_indicators):
            requirements.append("time_sensitive")

        # VIP customer (would come from customer data)
        # This is a placeholder - in reality, you'd check customer tier/status
        requirements.append("standard_customer")  # or "vip_customer"

        return requirements

    def _estimate_resolution_time(self, complexity: str, skills: list[str]) -> int:
        """Estimate resolution time in minutes"""

        base_times = {
            "low": 15,
            "medium": 30,
            "high": 60,
        }

        base_time = base_times.get(complexity, 30)

        # Adjust for skill complexity
        skill_multipliers = {
            "technical": 1.5,
            "compliance": 2.0,
            "billing": 1.2,
            "general": 1.0,
        }

        max_multiplier = max(skill_multipliers.get(skill, 1.0) for skill in skills)

        return int(base_time * max_multiplier)

    def _classify_escalation_type(self, escalation_reason: str) -> str:
        """Classify the type of escalation"""

        reason_lower = escalation_reason.lower()

        if "frustration" in reason_lower:
            return "frustration_based"
        elif "quality" in reason_lower or "inadequate" in reason_lower:
            return "quality_based"
        elif "technical" in reason_lower:
            return "technical_complexity"
        elif "repeat" in reason_lower:
            return "repeat_issue"
        else:
            return "general_escalation"





    def _handle_no_agents_available(
        self, state: HybridSystemState, requirements: dict[str, Any]
    ) -> HybridSystemState:
        """Handle case when no agents are available"""

        self.logger.warning(
            "No human agents available for escalation",
            extra={
                "operation": "routing_no_agents",
                "query_id": state["query_id"],
                "priority": requirements["priority"],
                "required_skills": requirements["required_skills"],
            },
        )

        # Create queue entry
        queue_entry = {
            "queue_position": self._get_queue_position(),
            "estimated_wait_time": self._estimate_queue_wait_time(),
            "priority": requirements["priority"],
            "requirements": requirements,
            "queued_timestamp": datetime.now().isoformat(),
        }

        return {
            **state,
            "routing_decision": {
                "status": "queued",
                "queue_entry": queue_entry,
                "routing_requirements": requirements,
            },
            "assigned_human_agent": None,
            "next_action": "queue_for_human",
        }

    def _get_queue_position(self) -> int:
        """Get position in queue (simplified implementation)"""
        # In production, this would query the actual queue system
        return len(self.routing_history) + 1

    def _estimate_queue_wait_time(self) -> int:
        """Estimate wait time in minutes (simplified implementation)"""
        # In production, this would consider actual queue length and agent availability
        return 15

    def _log_routing_decision(self, state: HybridSystemState, decision: dict[str, Any]):
        """Log routing decision for monitoring and analytics"""

        self.logger.info(
            "Routing decision completed",
            extra={
                "operation": "routing_decision",
                "query_id": state["query_id"],
                "user_id": state["user_id"],
                "session_id": state["session_id"],
                "assigned_agent_id": decision.get("assigned_agent_id"),
                "routing_strategy": decision.get("routing_strategy"),
                "match_score": decision.get("agent_match_score"),
                "routing_confidence": decision.get("routing_confidence"),
                "estimated_resolution_time": decision.get("estimated_resolution_time"),
            },
        )

        # Add to routing history for queue management
        self.routing_history.append({
            "timestamp": datetime.now(),
            "decision": decision,
            "state": state,
        })

    def _create_conversation_context(self, state: HybridSystemState, requirements: dict[str, Any]) -> dict[str, Any]:
        """Create conversation context for LLM routing agent"""
        
        # Map skills to specializations
        skill_to_specialization = {
            "technical": "technical",
            "billing": "billing", 
            "account_management": "policy",
            "product_support": "general",
            "compliance": "escalation"
        }
        
        required_skills = requirements.get("required_skills", [])
        required_specialization = None
        
        if required_skills:
            # Use first matching specialization
            for skill in required_skills:
                if skill in skill_to_specialization:
                    required_specialization = skill_to_specialization[skill]
                    break
        
        return {
            "issue_type": requirements.get("escalation_type", "general_inquiry"),
            "required_specialization": required_specialization,
            "issue_description": state.get("query", "Customer escalation request"),
            "complexity_level": self._map_complexity_to_level(requirements.get("complexity", "low")),
            "estimated_duration_minutes": requirements.get("estimated_resolution_time", 30)
        }

    def _create_customer_context(self, state: HybridSystemState) -> dict[str, Any]:
        """Create customer context for LLM routing agent"""
        
        # Extract language preference from special requirements
        special_requirements = state.get("routing_requirements", {}).get("special_requirements", [])
        language_preference = None
        
        for req in special_requirements:
            if req.startswith("language_"):
                language_preference = req.replace("language_", "")
                break
        
        # Determine customer tier from requirements
        tier = "standard"
        if "vip_customer" in special_requirements:
            tier = "vip"
        
        return {
            "preferred_language": language_preference,
            "tier": tier,
            "customer_id": state.get("user_id"),
            "last_agent_id": None  # Could be enhanced with session history
        }

    def _map_priority_to_urgency(self, priority: str) -> int:
        """Map priority level to urgency scale (1-5)"""
        priority_mapping = {
            "low": 1,
            "medium": 2, 
            "high": 4,
            "critical": 5
        }
        return priority_mapping.get(priority, 1)

    def _map_complexity_to_level(self, complexity: str) -> int:
        """Map complexity to numeric level (1-5)"""
        complexity_mapping = {
            "low": 1,
            "medium": 3,
            "high": 5
        }
        return complexity_mapping.get(complexity, 1)

    def _enhance_routing_with_context(self, routing_requirements: dict[str, Any], state: HybridSystemState) -> dict[str, Any]:
        """Enhance routing requirements with Context Manager analysis"""
        context_analysis = state.get("context_analysis", {})
        context_summaries = state.get("context_summaries", {})
        
        # Create enhanced copy of routing requirements
        enhanced_requirements = routing_requirements.copy()
        
        # Extract routing-specific insights from context
        routing_summary = context_summaries.get("for_routing_decision", "")
        
        # Parse routing considerations
        if "high_escalation_user" in routing_summary:
            enhanced_requirements["user_escalation_history"] = "high_risk"
            enhanced_requirements["priority"] = self._escalate_priority(enhanced_requirements["priority"])
        
        if "technical_complexity" in routing_summary:
            enhanced_requirements["requires_technical_specialist"] = True
            enhanced_requirements["complexity"] = "high"
            
        if "billing_issue" in routing_summary:
            enhanced_requirements["requires_billing_specialist"] = True
        
        # Use context recommendations
        context_recommendations = context_analysis.get("recommendations", [])
        enhanced_requirements["context_recommendations"] = context_recommendations
        
        # Extract user behavior patterns
        priority_context = context_analysis.get("priority_context", {})
        if "user_profile" in priority_context:
            user_profile = priority_context["user_profile"]["data"]
            enhanced_requirements["user_behavior_pattern"] = user_profile.get("user_behavior_pattern")
            enhanced_requirements["user_escalation_rate"] = user_profile.get("escalation_rate", 0)
            enhanced_requirements["user_interaction_frequency"] = user_profile.get("interaction_frequency")
        
        # Extract similar cases insights
        if "similar_cases" in priority_context:
            similar_cases = priority_context["similar_cases"]["data"]
            if similar_cases:
                enhanced_requirements["similar_cases_found"] = len(similar_cases)
                enhanced_requirements["top_similarity_score"] = similar_cases[0]["similarity_score"]
        
        # Adjust routing strategy based on context
        if any("immediate human escalation" in rec for rec in context_recommendations):
            enhanced_requirements["force_senior_agent"] = True
            enhanced_requirements["priority"] = "critical"
        
        if any("technical specialist" in rec for rec in context_recommendations):
            enhanced_requirements["required_skills"] = enhanced_requirements.get("required_skills", []) + ["technical"]
        
        # Log context enhancement
        self.logger.info(
            "Routing enhanced with context manager data",
            extra={
                "operation": "context_enhancement",
                "query_id": state.get("query_id"),
                "context_recommendations": len(context_recommendations),
                "priority_sources": list(priority_context.keys()),
                "original_priority": routing_requirements["priority"],
                "enhanced_priority": enhanced_requirements["priority"]
            }
        )
        
        return enhanced_requirements
    
    def _escalate_priority(self, current_priority: str) -> str:
        """Escalate priority level based on context insights"""
        priority_escalation = {
            "low": "medium",
            "medium": "high", 
            "high": "critical",
            "critical": "critical"  # Already at max
        }
        return priority_escalation.get(current_priority, current_priority)

    def _convert_to_legacy_format(self, agent_info: dict[str, Any]) -> dict[str, Any]:
        """Convert new agent format to legacy format for compatibility using field mapper"""
        try:
            # Use field mapper to convert database format to agent format
            # This handles all the complex field mappings and transformations
            legacy_format = self.field_mapper.map_database_to_agent(agent_info, include_computed=True)
            
            # Ensure required fields are present with safe defaults
            required_defaults = {
                "id": agent_info.get("id", "unknown"),
                "name": agent_info.get("name", "Unknown Agent"),
                "email": agent_info.get("email", "unknown@company.com"),
                "status": "available",
                "skills": ["general"],
                "skill_level": "junior",
                "languages": ["english"],
                "current_workload": 0,
                "max_concurrent": 3,
                "frustration_tolerance": "medium",
                "specializations": [],
                "shift_start": "09:00",
                "shift_end": "17:00"
            }
            
            # Fill in any missing required fields with defaults
            for field, default_value in required_defaults.items():
                if field not in legacy_format or legacy_format[field] is None:
                    legacy_format[field] = default_value
            
            # Handle current_workload parsing if it's in "X/Y" format
            current_workload = legacy_format.get("current_workload", 0)
            if isinstance(current_workload, str) and "/" in current_workload:
                try:
                    parts = current_workload.split("/")
                    legacy_format["current_workload"] = int(parts[0])
                    legacy_format["max_concurrent"] = int(parts[1])
                except (ValueError, IndexError):
                    legacy_format["current_workload"] = 0
                    legacy_format["max_concurrent"] = 3
            
            self.logger.debug(
                "Successfully converted agent to legacy format",
                extra={
                    "agent_id": legacy_format.get("id"),
                    "mapped_fields": list(legacy_format.keys())
                }
            )
            
            return legacy_format
            
        except Exception as e:
            self.logger.error(
                f"Failed to convert agent to legacy format: {e}",
                extra={"agent_id": agent_info.get("id", "unknown")}
            )
            # Return fallback format from field mapper
            return self.field_mapper._get_fallback_agent_record(agent_info)
