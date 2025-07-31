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
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.state_schema import HybridSystemState
from ..nodes.sync_llm_routing import SyncLLMRoutingAgent
from ..interfaces.human_agents import Specialization


class RoutingStrategy(Enum):
    SKILL_BASED = "skill_based"
    WORKLOAD_BALANCED = "workload_balanced"
    ROUND_ROBIN = "round_robin"
    PRIORITY_BASED = "priority_based"
    EMPLOYEE_WELLBEING = "employee_wellbeing"


class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    BREAK = "break"
    OFFLINE = "offline"


class RoutingAgentNode:
    """LangGraph node for intelligent routing of escalations to human agents"""

    def __init__(self, config_manager: ConfigManager, context_provider: ContextProvider):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("routing_agent")
        self.context_provider = context_provider
        self.logger = get_logger(__name__)
        self.llm_provider = self._initialize_llm_provider()

        # Initialize synchronous LLM routing agent with database integration
        self.sync_llm_routing_agent = SyncLLMRoutingAgent()
        
        # Load human agent data (legacy support)
        self.human_agents = self._load_human_agents()
        self.routing_history = []  # Track routing decisions
        
        # Flag to use new LLM routing system
        self.use_llm_routing = self.agent_config.settings.get("use_llm_routing", True)

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

    def _load_human_agents(self) -> list[dict[str, Any]]:
        """Load human agent data from configuration"""

        # This would typically come from a database or HR system
        default_agents = [
            {
                "id": "agent_001",
                "name": "Sarah Johnson",
                "email": "sarah.johnson@company.com",
                "status": AgentStatus.AVAILABLE.value,
                "skills": ["technical", "billing", "account_management"],
                "skill_level": "senior",
                "languages": ["english", "spanish"],
                "current_workload": 2,
                "max_concurrent": 5,
                "frustration_tolerance": "high",
                "specializations": ["complex_technical_issues", "enterprise_accounts"],
                "performance_metrics": {
                    "avg_resolution_time": 18,  # minutes
                    "customer_satisfaction": 4.7,  # out of 5
                    "escalation_rate": 0.12,  # percentage
                },
                "schedule": {
                    "timezone": "PST",
                    "working_hours": {"start": "09:00", "end": "17:00"},
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                },
                "last_frustration_assignment": None,
                "consecutive_difficult_cases": 0,
            },
            {
                "id": "agent_002",
                "name": "Mike Chen",
                "email": "mike.chen@company.com",
                "status": AgentStatus.AVAILABLE.value,
                "skills": ["general", "billing", "refunds"],
                "skill_level": "junior",
                "languages": ["english", "mandarin"],
                "current_workload": 1,
                "max_concurrent": 3,
                "frustration_tolerance": "medium",
                "specializations": ["billing_issues", "refund_processing"],
                "performance_metrics": {
                    "avg_resolution_time": 25,
                    "customer_satisfaction": 4.4,
                    "escalation_rate": 0.18,
                },
                "schedule": {
                    "timezone": "PST",
                    "working_hours": {"start": "10:00", "end": "18:00"},
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                },
                "last_frustration_assignment": datetime.now() - timedelta(hours=2),
                "consecutive_difficult_cases": 1,
            },
            {
                "id": "agent_003",
                "name": "Emily Rodriguez",
                "email": "emily.rodriguez@company.com",
                "status": AgentStatus.BUSY.value,
                "skills": ["technical", "product_support", "integrations"],
                "skill_level": "senior",
                "languages": ["english", "spanish", "portuguese"],
                "current_workload": 4,
                "max_concurrent": 4,
                "frustration_tolerance": "high",
                "specializations": ["api_integrations", "enterprise_support"],
                "performance_metrics": {
                    "avg_resolution_time": 22,
                    "customer_satisfaction": 4.8,
                    "escalation_rate": 0.08,
                },
                "schedule": {
                    "timezone": "EST",
                    "working_hours": {"start": "08:00", "end": "16:00"},
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                },
                "last_frustration_assignment": datetime.now() - timedelta(days=1),
                "consecutive_difficult_cases": 0,
            },
        ]

        # Load from config or use defaults
        agents = self.agent_config.settings.get("human_agents", default_agents)

        # Ensure datetime objects for date fields
        for agent in agents:
            if agent.get("last_frustration_assignment") and isinstance(agent["last_frustration_assignment"], str):
                agent["last_frustration_assignment"] = datetime.fromisoformat(agent["last_frustration_assignment"])

        return agents

    @traceable(name="Routing Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main routing function - select best human agent for escalation
        """

        if self.use_llm_routing:
            return self._sync_llm_based_routing(state)
        else:
            return self._legacy_routing(state)

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
            self.logger.error(f"Sync LLM routing failed: {e}, falling back to legacy routing")
            return self._legacy_routing(state)

    def _legacy_routing(self, state: HybridSystemState) -> HybridSystemState:
        """Legacy routing function - select best human agent for escalation"""

        # Determine routing requirements
        routing_requirements = self._analyze_routing_requirements(state)

        # Get available agents
        available_agents = self._get_available_agents()

        if not available_agents:
            return self._handle_no_agents_available(state, routing_requirements)

        # Apply routing strategy
        routing_strategy = self._determine_routing_strategy(routing_requirements)
        selected_agent = self._select_agent(
            available_agents, routing_requirements, routing_strategy
        )

        # Consider employee wellbeing factors
        final_agent = self._apply_wellbeing_considerations(
            selected_agent, available_agents, routing_requirements
        )

        # Update agent workload and routing history
        self._update_agent_assignment(final_agent, routing_requirements)

        # Create routing decision record
        routing_decision = self._create_routing_decision(
            state, final_agent, routing_requirements, routing_strategy
        )

        # Log routing decision
        self._log_routing_decision(state, routing_decision)

        return {
            **state,
            "routing_decision": routing_decision,
            "assigned_human_agent": final_agent,
            "routing_requirements": routing_requirements,
            "next_action": "transfer_to_human",
        }

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

    def _get_available_agents(self) -> list[dict[str, Any]]:
        """Get list of available human agents"""

        available = []
        current_time = datetime.now()

        for agent in self.human_agents:
            # Check basic availability
            if agent["status"] != AgentStatus.AVAILABLE.value:
                continue

            # Check workload capacity
            if agent["current_workload"] >= agent["max_concurrent"]:
                continue

            # Check working hours (simplified)
            # In production, this would be more sophisticated
            available.append(agent)

        return available

    def _determine_routing_strategy(self, requirements: dict[str, Any]) -> RoutingStrategy:
        """Determine which routing strategy to use"""

        priority = requirements["priority"]
        complexity = requirements["complexity"]
        frustration_level = requirements["customer_frustration_level"]

        # High priority or critical frustration -> skill-based routing
        if priority in ["critical", "high"] or frustration_level in ["critical", "high"]:
            return RoutingStrategy.SKILL_BASED

        # High complexity -> skill-based routing
        if complexity == "high":
            return RoutingStrategy.SKILL_BASED

        # Otherwise, balance workload and employee wellbeing
        return RoutingStrategy.EMPLOYEE_WELLBEING

    def _select_agent(
        self,
        available_agents: list[dict[str, Any]],
        requirements: dict[str, Any],
        strategy: RoutingStrategy
    ) -> dict[str, Any]:
        """Select best agent based on strategy"""

        if strategy == RoutingStrategy.SKILL_BASED:
            return self._skill_based_selection(available_agents, requirements)
        elif strategy == RoutingStrategy.WORKLOAD_BALANCED:
            return self._workload_balanced_selection(available_agents)
        elif strategy == RoutingStrategy.EMPLOYEE_WELLBEING:
            return self._wellbeing_based_selection(available_agents, requirements)
        else:
            # Default to skill-based
            return self._skill_based_selection(available_agents, requirements)

    def _skill_based_selection(
        self, agents: list[dict[str, Any]], requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Select agent based on skill matching"""

        required_skills = requirements["required_skills"]
        complexity = requirements["complexity"]

        # Score agents based on skill match
        scored_agents = []
        for agent in agents:
            score = 0

            # Skill matching
            agent_skills = agent["skills"]
            skill_matches = len(set(required_skills) & set(agent_skills))
            score += skill_matches * 10

            # Skill level bonus for complex cases
            if complexity in ["medium", "high"] and agent["skill_level"] == "senior":
                score += 5

            # Performance metrics
            score += agent["performance_metrics"]["customer_satisfaction"] * 2
            score -= agent["performance_metrics"]["escalation_rate"] * 10

            # Availability (lower workload is better)
            workload_ratio = agent["current_workload"] / agent["max_concurrent"]
            score += (1 - workload_ratio) * 5

            scored_agents.append((agent, score))

        # Return highest scoring agent
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return scored_agents[0][0] if scored_agents else agents[0]

    def _workload_balanced_selection(self, agents: list[dict[str, Any]]) -> dict[str, Any]:
        """Select agent with lowest current workload"""

        return min(agents, key=lambda x: x["current_workload"])

    def _wellbeing_based_selection(
        self, agents: list[dict[str, Any]], requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Select agent considering employee wellbeing factors"""

        frustration_level = requirements["customer_frustration_level"]

        # Score agents considering wellbeing
        scored_agents = []
        for agent in agents:
            score = 0

            # Basic skill matching
            required_skills = requirements["required_skills"]
            agent_skills = agent["skills"]
            skill_matches = len(set(required_skills) & set(agent_skills))
            score += skill_matches * 5

            # Workload consideration
            workload_ratio = agent["current_workload"] / agent["max_concurrent"]
            score += (1 - workload_ratio) * 10

            # Frustration tolerance for frustrated customers
            if frustration_level in ["high", "critical"]:
                if agent["frustration_tolerance"] == "high":
                    score += 8
                elif agent["frustration_tolerance"] == "medium":
                    score += 3
                # Low tolerance gets no bonus

            # Avoid overloading with difficult cases
            consecutive_difficult = agent.get("consecutive_difficult_cases", 0)
            if consecutive_difficult >= 2:
                score -= 5

            # Time since last frustration case
            last_frustration = agent.get("last_frustration_assignment")
            if last_frustration and frustration_level in ["high", "critical"]:
                hours_since = (datetime.now() - last_frustration).total_seconds() / 3600
                if hours_since < 2:  # Less than 2 hours ago
                    score -= 3
                elif hours_since > 4:  # More than 4 hours ago
                    score += 2

            scored_agents.append((agent, score))

        # Return highest scoring agent
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        return scored_agents[0][0] if scored_agents else agents[0]

    def _apply_wellbeing_considerations(
        self,
        selected_agent: dict[str, Any],
        available_agents: list[dict[str, Any]],
        requirements: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply final wellbeing checks and potentially re-route"""

        frustration_level = requirements["customer_frustration_level"]

        # Check if selected agent has too many consecutive difficult cases
        consecutive_difficult = selected_agent.get("consecutive_difficult_cases", 0)

        if frustration_level in ["high", "critical"] and consecutive_difficult >= 3:
            # Try to find an alternative agent
            alternatives = [
                agent for agent in available_agents
                if agent["id"] != selected_agent["id"]
                and agent.get("consecutive_difficult_cases", 0) < 2
                and agent["frustration_tolerance"] in ["medium", "high"]
            ]

            if alternatives:
                # Select best alternative
                return self._skill_based_selection(alternatives, requirements)

        return selected_agent

    def _update_agent_assignment(
        self, agent: dict[str, Any], requirements: dict[str, Any]
    ):
        """Update agent workload and tracking data"""

        # Update workload
        for stored_agent in self.human_agents:
            if stored_agent["id"] == agent["id"]:
                stored_agent["current_workload"] += 1

                # Update frustration tracking if this is a frustrated customer
                frustration_level = requirements["customer_frustration_level"]
                if frustration_level in ["high", "critical"]:
                    stored_agent["last_frustration_assignment"] = datetime.now()
                    stored_agent["consecutive_difficult_cases"] = stored_agent.get("consecutive_difficult_cases", 0) + 1
                else:
                    # Reset consecutive difficult cases for easy case
                    stored_agent["consecutive_difficult_cases"] = 0

                break

    def _create_routing_decision(
        self,
        state: HybridSystemState,
        agent: dict[str, Any],
        requirements: dict[str, Any],
        strategy: RoutingStrategy
    ) -> dict[str, Any]:
        """Create routing decision record"""

        return {
            "assigned_agent_id": agent["id"],
            "assigned_agent_name": agent["name"],
            "assigned_agent_email": agent["email"],
            "routing_strategy": strategy.value,
            "routing_requirements": requirements,
            "agent_match_score": self._calculate_match_score(agent, requirements),
            "estimated_resolution_time": requirements["estimated_resolution_time"],
            "routing_timestamp": datetime.now().isoformat(),
            "routing_confidence": self._calculate_routing_confidence(agent, requirements),
            "alternative_agents": [
                {"id": a["id"], "name": a["name"]}
                for a in self._get_available_agents()[:3]
                if a["id"] != agent["id"]
            ],
        }

    def _calculate_match_score(self, agent: dict[str, Any], requirements: dict[str, Any]) -> float:
        """Calculate how well the agent matches the requirements"""

        score = 0.0
        max_score = 0.0

        # Skill matching
        required_skills = requirements["required_skills"]
        agent_skills = agent["skills"]
        skill_matches = len(set(required_skills) & set(agent_skills))
        skill_total = len(required_skills)

        if skill_total > 0:
            score += (skill_matches / skill_total) * 40
        max_score += 40

        # Experience level matching
        complexity = requirements["complexity"]
        if complexity == "high" and agent["skill_level"] == "senior":
            score += 20
        elif complexity == "medium" and agent["skill_level"] in ["senior", "intermediate"]:
            score += 15
        elif complexity == "low":
            score += 10
        max_score += 20

        # Workload appropriateness
        workload_ratio = agent["current_workload"] / agent["max_concurrent"]
        score += (1 - workload_ratio) * 20
        max_score += 20

        # Performance metrics
        score += agent["performance_metrics"]["customer_satisfaction"] * 4
        max_score += 20

        return (score / max_score) * 100 if max_score > 0 else 0

    def _calculate_routing_confidence(self, agent: dict[str, Any], requirements: dict[str, Any]) -> float:
        """Calculate confidence in the routing decision"""

        match_score = self._calculate_match_score(agent, requirements)

        # High match score = high confidence
        base_confidence = match_score / 100

        # Adjust for availability
        workload_ratio = agent["current_workload"] / agent["max_concurrent"]
        if workload_ratio < 0.5:
            base_confidence += 0.1
        elif workload_ratio > 0.8:
            base_confidence -= 0.1

        # Adjust for agent performance
        if agent["performance_metrics"]["customer_satisfaction"] > 4.5:
            base_confidence += 0.05

        return min(1.0, max(0.0, base_confidence))

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
        """Convert new agent format to legacy format for compatibility"""
        
        # Map specializations back to skills
        specialization_to_skills = {
            "claims": ["technical", "billing"],
            "billing": ["billing", "account_management"],
            "policy": ["account_management", "general"],
            "technical": ["technical", "product_support"],
            "escalation": ["technical", "compliance"],
            "general": ["general", "product_support"]
        }
        
        specializations = agent_info.get("specializations", [])
        skills = []
        for spec in specializations:
            skills.extend(specialization_to_skills.get(spec, ["general"]))
        
        # Remove duplicates
        skills = list(set(skills))
        
        # Map experience level to skill level
        experience_to_skill_level = {
            1: "junior",
            2: "junior", 
            3: "intermediate",
            4: "senior",
            5: "senior"
        }
        
        skill_level = experience_to_skill_level.get(agent_info.get("experience_level", 1), "junior")
        
        return {
            "id": agent_info["id"],
            "name": agent_info["name"],
            "email": agent_info["email"],
            "status": "available",  # Simplified for now
            "skills": skills,
            "skill_level": skill_level,
            "languages": agent_info.get("languages", ["english"]),
            "current_workload": int(agent_info.get("current_workload", "0/5").split("/")[0]),
            "max_concurrent": int(agent_info.get("current_workload", "0/5").split("/")[1]),
            "frustration_tolerance": "high" if agent_info.get("experience_level", 1) >= 4 else "medium",
            "specializations": specializations,
            "performance_metrics": {
                "avg_resolution_time": 20,  # Default values
                "customer_satisfaction": 4.5,
                "escalation_rate": 0.15,
            }
        }
