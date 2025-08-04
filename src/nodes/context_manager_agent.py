"""
Context Manager Agent Node
Responsibility: Retrieve and manage context from SQL database, web search, and other sources
"""

import json
from datetime import datetime
from typing import Any

from langsmith import traceable

from ..core.config import ConfigManager
from ..core.logging import get_logger
from ..integrations.llm_providers import LLMProviderFactory
from ..interfaces.core.context import ContextEntry, ContextProvider
from ..interfaces.core.state_schema import HybridSystemState


class ContextManagerAgentNode:
    """LangGraph node for intelligent context retrieval and management"""

    def __init__(self, config_manager: ConfigManager, context_provider: ContextProvider):
        self.config_manager = config_manager
        self.agent_config = config_manager.get_agent_config("context_manager_agent")
        self.context_provider = context_provider
        self.logger = get_logger(__name__)
        self.llm_provider = self._initialize_llm_provider()

    def _initialize_llm_provider(self):
        """Initialize LLM provider for context analysis and summarization"""
        try:
            factory = LLMProviderFactory(self.config_manager.config_dir)

            preferred_model = self.agent_config.get_preferred_model()
            provider = factory.create_provider_with_fallback(
                preferred_model=preferred_model
            )

            self.logger.info(
                "Context Manager Agent LLM provider initialized",
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
                "Failed to initialize Context Manager Agent LLM provider",
                extra={"error": str(e), "operation": "initialize_llm_provider"},
            )
            return None

    @traceable(name="Context Manager Agent")
    def __call__(self, state: HybridSystemState) -> HybridSystemState:
        """
        Main context management function
        Retrieves and enriches context for other agents and humans
        """

        query = state.get("query", "")
        user_id = state["user_id"]
        session_id = state["session_id"]

        # Gather context from multiple sources
        context_data = self._gather_comprehensive_context(
            query, user_id, session_id, state
        )

        # Analyze and prioritize context
        context_analysis = self._analyze_context_relevance(query, context_data)

        # Create context summary for different audiences
        context_summaries = self._create_context_summaries(
            context_analysis, state
        )

        # Store enhanced context
        self._store_enhanced_context(state, context_analysis)

        # Log context gathering
        self._log_context_gathering(state, context_analysis)

        return {
            **state,
            "context_data": context_data,
            "context_analysis": context_analysis,
            "context_summaries": context_summaries,
            "enriched_context": True,
        }

    def _gather_comprehensive_context(
        self, query: str, user_id: str, session_id: str, state: HybridSystemState
    ) -> dict[str, Any]:
        """Gather context from all available sources"""

        context_data = {
            "interaction_history": self._get_interaction_history(user_id, session_id),
            "user_profile": self._get_user_profile(user_id),
            "similar_cases": self._find_similar_cases(query, user_id),
            "escalation_history": self._get_escalation_history(user_id),
            "product_context": self._get_product_context(query),
            "web_search_results": self._perform_web_search(query),
            "knowledge_base": self._search_knowledge_base(query),
            "system_status": self._check_system_status(),
        }

        return context_data

    def _get_interaction_history(self, user_id: str, session_id: str) -> dict[str, Any]:
        """Get detailed interaction history"""

        # Get recent interactions
        recent_context = self.context_provider.get_recent_context(
            user_id, session_id, limit=20
        )

        # Get session-specific context
        session_context = self.context_provider.get_context_summary(
            user_id, session_id
        )

        # Get broader user history (across sessions)
        broader_history = self._get_user_interaction_history(user_id, days=30)

        return {
            "recent_interactions": [
                {
                    "entry_id": entry.entry_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "type": entry.entry_type,
                    "content": entry.content[:200],  # Truncate for summary
                    "metadata": entry.metadata,
                }
                for entry in recent_context
            ],
            "session_summary": session_context,
            "user_history_summary": broader_history,
            "total_interactions": len(recent_context),
        }

    def _get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Get user profile information"""

        # This would typically query a user database
        # For now, we'll create a basic profile from interaction patterns

        user_context = self.context_provider.get_recent_context(
            user_id, None, limit=100  # Get recent interactions across all sessions
        )

        # Analyze interaction patterns
        query_types = []
        interaction_times = []
        escalation_count = 0

        for entry in user_context:
            if entry.entry_type == "query":
                query_types.append(self._classify_query_type(entry.content))
                interaction_times.append(entry.timestamp)
            elif entry.entry_type == "escalation":
                escalation_count += 1

        # Calculate user behavior patterns
        profile = {
            "user_id": user_id,
            "total_interactions": len(user_context),
            "interaction_frequency": self._calculate_interaction_frequency(interaction_times),
            "common_query_types": self._get_common_query_types(query_types),
            "escalation_rate": escalation_count / max(len(query_types), 1),
            "preferred_interaction_times": self._analyze_interaction_times(interaction_times),
            "user_behavior_pattern": self._classify_user_behavior(
                len(user_context), escalation_count, query_types
            ),
        }

        return profile

    def _find_similar_cases(self, query: str, user_id: str) -> list[dict[str, Any]]:
        """Find similar cases from the database"""

        # Get recent queries from all users (anonymized)
        all_recent_context = self._get_system_wide_context(limit=1000)

        similar_cases = []
        query_words = set(query.lower().split())

        for entry in all_recent_context:
            if entry.entry_type == "query" and entry.user_id != user_id:
                entry_words = set(entry.content.lower().split())
                similarity = len(query_words & entry_words) / len(query_words | entry_words)

                if similarity > 0.3:  # 30% similarity threshold
                    similar_cases.append({
                        "similarity_score": similarity,
                        "query": entry.content[:150],  # Truncated for privacy
                        "timestamp": entry.timestamp.isoformat(),
                        "resolution_info": self._get_case_resolution_info(entry.entry_id),
                    })

        # Sort by similarity and return top 5
        similar_cases.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_cases[:5]

    def _get_escalation_history(self, user_id: str) -> dict[str, Any]:
        """Get user's escalation history"""

        escalation_entries = self.context_provider.get_recent_context(
            user_id, None, limit=50
        )

        escalations = [
            entry for entry in escalation_entries
            if entry.entry_type in ["escalation", "escalation_decision"]
        ]

        if not escalations:
            return {
                "total_escalations": 0,
                "recent_escalations": [],
                "escalation_reasons": [],
                "resolution_times": [],
            }

        # Analyze escalation patterns
        escalation_reasons = []
        resolution_times = []

        for escalation in escalations:
            if escalation.metadata:
                reason = escalation.metadata.get("escalation_reason", "unknown")
                escalation_reasons.append(reason)

                # Try to find resolution time (simplified)
                resolution_time = escalation.metadata.get("resolution_time_minutes")
                if resolution_time:
                    resolution_times.append(resolution_time)

        return {
            "total_escalations": len(escalations),
            "recent_escalations": [
                {
                    "timestamp": esc.timestamp.isoformat(),
                    "reason": esc.metadata.get("escalation_reason", "unknown") if esc.metadata else "unknown",
                    "content": esc.content[:100],
                }
                for esc in escalations[:5]
            ],
            "escalation_reasons": escalation_reasons,
            "avg_resolution_time": sum(resolution_times) / len(resolution_times) if resolution_times else None,
        }

    def _get_product_context(self, query: str) -> dict[str, Any]:
        """Get product-related context based on query"""

        # Product keyword mapping
        product_keywords = self.agent_config.settings.get("product_keywords", {
            "billing": ["billing", "invoice", "payment", "subscription", "charge"],
            "api": ["api", "integration", "webhook", "endpoint", "authentication"],
            "dashboard": ["dashboard", "analytics", "reporting", "charts", "metrics"],
            "account": ["account", "profile", "settings", "permissions", "users"],
            "mobile": ["mobile", "app", "ios", "android", "phone"],
        })

        query_lower = query.lower()
        related_products = []

        for product, keywords in product_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                related_products.append(product)

        # Get product-specific information
        product_info = {}
        for product in related_products:
            product_info[product] = self._get_specific_product_info(product)

        return {
            "related_products": related_products,
            "product_info": product_info,
            "query_classification": self._classify_query_type(query),
        }

    def _perform_web_search(self, query: str) -> dict[str, Any]:
        """Perform web search for additional context (simulated)"""

        # In production, this would use a real web search API
        # For now, we'll simulate based on query patterns

        search_enabled = self.agent_config.settings.get("web_search_enabled", False)

        if not search_enabled:
            return {
                "enabled": False,
                "results": [],
                "search_performed": False,
            }

        # Simulate search results based on query type
        query_type = self._classify_query_type(query)
        simulated_results = self._generate_simulated_search_results(query, query_type)

        return {
            "enabled": True,
            "search_performed": True,
            "query_type": query_type,
            "results": simulated_results,
            "search_timestamp": datetime.now().isoformat(),
        }

    def _search_knowledge_base(self, query: str) -> dict[str, Any]:
        """Search internal knowledge base"""

        # In production, this would query a knowledge base system
        # For now, we'll use stored context as a proxy knowledge base

        knowledge_entries = self._get_system_wide_context(limit=500)

        # Find relevant knowledge base entries
        query_words = set(query.lower().split())
        relevant_entries = []

        for entry in knowledge_entries:
            if entry.entry_type in ["response", "resolution"]:
                entry_words = set(entry.content.lower().split())
                relevance = len(query_words & entry_words) / len(query_words)

                if relevance > 0.2:  # 20% relevance threshold
                    relevant_entries.append({
                        "relevance_score": relevance,
                        "content": entry.content[:200],
                        "timestamp": entry.timestamp.isoformat(),
                        "entry_type": entry.entry_type,
                    })

        # Sort by relevance
        relevant_entries.sort(key=lambda x: x["relevance_score"], reverse=True)

        return {
            "search_performed": True,
            "total_entries_searched": len(knowledge_entries),
            "relevant_entries": relevant_entries[:10],
            "search_timestamp": datetime.now().isoformat(),
        }

    def _check_system_status(self) -> dict[str, Any]:
        """Check current system status and any known issues"""

        # In production, this would check actual system monitoring
        # For now, we'll simulate system status

        return {
            "overall_status": "operational",
            "api_status": "operational",
            "database_status": "operational",
            "known_issues": [],
            "maintenance_scheduled": False,
            "last_updated": datetime.now().isoformat(),
        }

    def _analyze_context_relevance(
        self, query: str, context_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze and prioritize context based on relevance to current query"""

        analysis = {
            "query": query,
            "relevance_scores": {},
            "priority_context": {},
            "context_summary": "",
            "recommendations": [],
        }

        # Score each context source
        analysis["relevance_scores"] = {
            "interaction_history": self._score_interaction_relevance(query, context_data["interaction_history"]),
            "user_profile": self._score_profile_relevance(query, context_data["user_profile"]),
            "similar_cases": self._score_similar_cases_relevance(context_data["similar_cases"]),
            "escalation_history": self._score_escalation_relevance(context_data["escalation_history"]),
            "product_context": self._score_product_relevance(query, context_data["product_context"]),
            "knowledge_base": self._score_knowledge_relevance(context_data["knowledge_base"]),
        }

        # Identify priority context (highest scoring)
        priority_threshold = 0.6
        for source, score in analysis["relevance_scores"].items():
            if score > priority_threshold:
                analysis["priority_context"][source] = {
                    "score": score,
                    "data": context_data[source],
                }

        # Generate context summary using LLM if available
        if self.llm_provider:
            analysis["context_summary"] = self._generate_context_summary(
                query, analysis["priority_context"]
            )
        else:
            analysis["context_summary"] = self._generate_simple_context_summary(
                analysis["priority_context"]
            )

        # Generate recommendations
        analysis["recommendations"] = self._generate_context_recommendations(
            analysis["relevance_scores"], context_data
        )

        return analysis

    def _create_context_summaries(
        self, context_analysis: dict[str, Any], state: HybridSystemState
    ) -> dict[str, str]:
        """Create different context summaries for different audiences"""

        summaries = {
            "for_ai_agents": self._create_ai_agent_summary(context_analysis),
            "for_human_agents": self._create_human_agent_summary(context_analysis, state),
            "for_quality_assessment": self._create_quality_summary(context_analysis),
            "for_routing_decision": self._create_routing_summary(context_analysis),
        }

        return summaries

    def _create_ai_agent_summary(self, analysis: dict[str, Any]) -> str:
        """Create context summary optimized for AI agents"""

        summary_parts = []

        # Add high-priority context
        for source, data in analysis["priority_context"].items():
            if source == "interaction_history":
                recent_count = data["data"]["total_interactions"]
                summary_parts.append(f"User has {recent_count} recent interactions")

            elif source == "escalation_history":
                escalation_count = data["data"]["total_escalations"]
                if escalation_count > 0:
                    summary_parts.append(f"User has {escalation_count} previous escalations")

            elif source == "similar_cases":
                case_count = len(data["data"])
                if case_count > 0:
                    summary_parts.append(f"Found {case_count} similar cases")

        # Add recommendations
        if analysis["recommendations"]:
            summary_parts.append(f"Recommendations: {'; '.join(analysis['recommendations'][:2])}")

        return " | ".join(summary_parts) if summary_parts else "No significant context available"

    def _create_human_agent_summary(
        self, analysis: dict[str, Any], state: HybridSystemState
    ) -> str:
        """Create detailed context summary for human agents"""

        summary = f"CONTEXT FOR: {state['user_id']}\n"
        summary += f"Query: {state['query']}\n\n"

        # User background
        if "user_profile" in analysis["priority_context"]:
            profile = analysis["priority_context"]["user_profile"]["data"]
            summary += "User Profile:\n"
            summary += f"- Total interactions: {profile['total_interactions']}\n"
            summary += f"- Escalation rate: {profile['escalation_rate']:.1%}\n"
            summary += f"- Behavior pattern: {profile['user_behavior_pattern']}\n\n"

        # Recent history
        if "interaction_history" in analysis["priority_context"]:
            history = analysis["priority_context"]["interaction_history"]["data"]
            summary += "Recent History:\n"
            for interaction in history["recent_interactions"][:3]:
                summary += f"- {interaction['timestamp']}: {interaction['content']}\n"
            summary += "\n"

        # Similar cases
        if "similar_cases" in analysis["priority_context"]:
            cases = analysis["priority_context"]["similar_cases"]["data"]
            if cases:
                summary += "Similar Cases Found:\n"
                for case in cases[:2]:
                    summary += f"- {case['similarity_score']:.0%} similar: {case['query']}\n"
                summary += "\n"

        # Recommendations
        if analysis["recommendations"]:
            summary += "Recommendations:\n"
            for rec in analysis["recommendations"]:
                summary += f"- {rec}\n"

        return summary

    def _create_quality_summary(self, analysis: dict[str, Any]) -> str:
        """Create context summary for quality assessment"""

        factors = []

        # Check for repeat issues
        if "interaction_history" in analysis["priority_context"]:
            history = analysis["priority_context"]["interaction_history"]["data"]
            if history["total_interactions"] > 3:
                factors.append("frequent_user")

        # Check escalation history
        if "escalation_history" in analysis["priority_context"]:
            escalations = analysis["priority_context"]["escalation_history"]["data"]
            if escalations["total_escalations"] > 0:
                factors.append("previous_escalations")

        # Check for similar unresolved cases
        if "similar_cases" in analysis["priority_context"]:
            cases = analysis["priority_context"]["similar_cases"]["data"]
            unresolved = [case for case in cases if not case.get("resolution_info")]
            if unresolved:
                factors.append("similar_unresolved_cases")

        return "Quality factors: " + ", ".join(factors) if factors else "No quality risk factors identified"

    def _create_routing_summary(self, analysis: dict[str, Any]) -> str:
        """Create context summary for routing decisions"""

        routing_factors = []

        # User behavior pattern
        if "user_profile" in analysis["priority_context"]:
            profile = analysis["priority_context"]["user_profile"]["data"]
            behavior = profile["user_behavior_pattern"]
            routing_factors.append(f"user_pattern:{behavior}")

            if profile["escalation_rate"] > 0.3:
                routing_factors.append("high_escalation_user")

        # Product complexity
        if "product_context" in analysis["priority_context"]:
            products = analysis["priority_context"]["product_context"]["data"]["related_products"]
            if "api" in products:
                routing_factors.append("technical_complexity")
            if "billing" in products:
                routing_factors.append("billing_issue")

        return "Routing considerations: " + ", ".join(routing_factors)

    # Helper methods for scoring context relevance

    def _score_interaction_relevance(self, query: str, history: dict[str, Any]) -> float:
        """Score relevance of interaction history"""
        score = 0.0

        # Recent interactions are always somewhat relevant
        if history["total_interactions"] > 0:
            score += 0.3

        # Frequent recent interactions suggest ongoing issue
        if history["total_interactions"] > 3:
            score += 0.2

        # Check if recent interactions are related to current query
        query_words = set(query.lower().split())
        for interaction in history["recent_interactions"][:5]:
            content_words = set(interaction["content"].lower().split())
            if len(query_words & content_words) > 2:
                score += 0.1

        return min(1.0, score)

    def _score_profile_relevance(self, query: str, profile: dict[str, Any]) -> float:
        """Score relevance of user profile"""
        score = 0.3  # Base relevance

        # High escalation rate users need careful handling
        if profile["escalation_rate"] > 0.2:
            score += 0.3

        # Frequent users have more context value
        if profile["total_interactions"] > 10:
            score += 0.2

        return min(1.0, score)

    def _score_similar_cases_relevance(self, similar_cases: list[dict[str, Any]]) -> float:
        """Score relevance of similar cases"""
        if not similar_cases:
            return 0.0

        # Score based on similarity of top case
        top_similarity = similar_cases[0]["similarity_score"]
        return min(1.0, top_similarity * 1.5)  # Boost similarity score

    def _score_escalation_relevance(self, escalation_history: dict[str, Any]) -> float:
        """Score relevance of escalation history"""
        if escalation_history["total_escalations"] == 0:
            return 0.0

        # Recent escalations are highly relevant
        return min(1.0, 0.5 + escalation_history["total_escalations"] * 0.2)

    def _score_product_relevance(self, query: str, product_context: dict[str, Any]) -> float:
        """Score relevance of product context"""
        related_products = product_context["related_products"]

        if not related_products:
            return 0.1  # Low base relevance

        # More related products = higher relevance
        return min(1.0, 0.4 + len(related_products) * 0.2)

    def _score_knowledge_relevance(self, knowledge_base: dict[str, Any]) -> float:
        """Score relevance of knowledge base results"""
        relevant_entries = knowledge_base["relevant_entries"]

        if not relevant_entries:
            return 0.0

        # Score based on top relevance score
        top_relevance = relevant_entries[0]["relevance_score"]
        return min(1.0, top_relevance * 2.0)  # Boost relevance score

    # Additional helper methods

    def _get_user_interaction_history(self, user_id: str, days: int = 30) -> dict[str, Any]:
        """Get broader user interaction history"""
        # This would query the database for historical data
        # Simplified implementation
        return {
            "total_sessions": 5,
            "avg_session_length": 15,  # minutes
            "common_issues": ["billing", "technical"],
            "resolution_rate": 0.85,
        }

    def _get_system_wide_context(self, limit: int = 1000) -> list[ContextEntry]:
        """Get system-wide context entries (anonymized)"""
        # This would query across all users with privacy protection
        # Simplified implementation returns empty list
        return []

    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()

        if any(word in query_lower for word in ["billing", "payment", "invoice", "charge"]):
            return "billing"
        elif any(word in query_lower for word in ["api", "integration", "technical", "code"]):
            return "technical"
        elif any(word in query_lower for word in ["account", "profile", "settings", "password"]):
            return "account"
        elif any(word in query_lower for word in ["how to", "tutorial", "guide", "help"]):
            return "support"
        else:
            return "general"

    def _calculate_interaction_frequency(self, timestamps: list[datetime]) -> str:
        """Calculate user interaction frequency pattern"""
        if len(timestamps) < 2:
            return "insufficient_data"

        # Calculate average time between interactions
        time_diffs = [
            (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # hours
            for i in range(1, len(timestamps))
        ]

        avg_hours = sum(time_diffs) / len(time_diffs)

        if avg_hours < 1:
            return "very_frequent"
        elif avg_hours < 24:
            return "daily"
        elif avg_hours < 168:  # 7 days
            return "weekly"
        else:
            return "occasional"

    def _get_common_query_types(self, query_types: list[str]) -> list[str]:
        """Get most common query types for user"""
        if not query_types:
            return []

        # Count occurrences
        type_counts = {}
        for qtype in query_types:
            type_counts[qtype] = type_counts.get(qtype, 0) + 1

        # Sort by frequency
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        return [qtype for qtype, count in sorted_types[:3]]

    def _analyze_interaction_times(self, timestamps: list[datetime]) -> list[str]:
        """Analyze preferred interaction times"""
        if not timestamps:
            return []

        # Group by hour of day
        hour_counts = {}
        for ts in timestamps:
            hour = ts.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        # Find peak hours
        if not hour_counts:
            return []

        max_count = max(hour_counts.values())
        peak_hours = [hour for hour, count in hour_counts.items() if count == max_count]

        # Convert to time ranges
        time_ranges = []
        for hour in peak_hours[:2]:  # Top 2 peak hours
            if 9 <= hour <= 17:
                time_ranges.append("business_hours")
            elif 18 <= hour <= 22:
                time_ranges.append("evening")
            else:
                time_ranges.append("off_hours")

        return list(set(time_ranges))

    def _classify_user_behavior(
        self, total_interactions: int, escalation_count: int, query_types: list[str]
    ) -> str:
        """Classify user behavior pattern"""

        escalation_rate = escalation_count / max(total_interactions, 1)

        if escalation_rate > 0.3:
            return "escalation_prone"
        elif total_interactions > 20:
            return "power_user"
        elif len(set(query_types)) == 1:
            return "focused_user"
        elif total_interactions < 3:
            return "new_user"
        else:
            return "regular_user"

    def _get_case_resolution_info(self, entry_id: str) -> dict[str, Any] | None:
        """Get resolution information for a case"""
        # This would query resolution data
        # Simplified implementation
        return None

    def _get_specific_product_info(self, product: str) -> dict[str, Any]:
        """Get specific information about a product"""
        # This would query product databases
        # Simplified implementation
        return {
            "status": "operational",
            "recent_issues": [],
            "documentation_links": [],
        }

    def _generate_simulated_search_results(self, query: str, query_type: str) -> list[dict[str, Any]]:
        """Generate simulated web search results"""
        # This would use a real search API in production
        return [
            {
                "title": f"How to resolve {query_type} issues",
                "url": f"https://docs.example.com/{query_type}",
                "snippet": f"Common solutions for {query_type} related problems...",
                "relevance": 0.8,
            }
        ]

    def _generate_context_summary(self, query: str, priority_context: dict[str, Any]) -> str:
        """Generate context summary using LLM"""
        if not self.llm_provider:
            return self._generate_simple_context_summary(priority_context)

        try:
            summary_prompt = self.agent_config.get_prompt("context_summary")
            system_prompt = self.agent_config.get_prompt("system")

            context_text = json.dumps(priority_context, indent=2, default=str)

            prompt = summary_prompt.format(
                query=query,
                context_data=context_text
            )

            # Log the LLM call at agent level
            self.logger.info(
                "Context Manager Agent calling LLM",
                extra={
                    "agent": "context_manager_agent",
                    "model_name": self.llm_provider.model_name,
                    "provider_type": self.llm_provider.provider_type,
                    "prompt_length": len(prompt),
                    "system_prompt_length": len(system_prompt),
                    "context_entries": len(priority_context),
                    "operation": "agent_llm_call"
                }
            )

            summary = self.llm_provider.generate_response(
                prompt=prompt,
                system_prompt=system_prompt
            )

            return summary

        except Exception as e:
            self.logger.error(
                "Failed to generate LLM context summary",
                extra={"error": str(e), "operation": "generate_context_summary"},
            )
            return self._generate_simple_context_summary(priority_context)

    def _generate_simple_context_summary(self, priority_context: dict[str, Any]) -> str:
        """Generate simple context summary without LLM"""
        summary_parts = []

        for source, data in priority_context.items():
            summary_parts.append(f"{source}: score {data['score']:.1f}")

        return "; ".join(summary_parts) if summary_parts else "No priority context"

    def _generate_context_recommendations(
        self, relevance_scores: dict[str, float], context_data: dict[str, Any]
    ) -> list[str]:
        """Generate recommendations based on context analysis"""

        recommendations = []

        # High escalation history
        if (relevance_scores.get("escalation_history", 0) > 0.6 and
            context_data["escalation_history"]["total_escalations"] > 1):
            recommendations.append("Consider immediate human escalation due to escalation history")

        # Similar unresolved cases
        if relevance_scores.get("similar_cases", 0) > 0.7:
            unresolved_cases = [
                case for case in context_data["similar_cases"]
                if not case.get("resolution_info")
            ]
            if unresolved_cases:
                recommendations.append("Similar unresolved cases found - may require specialized handling")

        # Technical complexity
        if (relevance_scores.get("product_context", 0) > 0.6 and
            "api" in context_data["product_context"].get("related_products", [])):
            recommendations.append("Technical query detected - route to technical specialist")

        # Frequent user
        if (relevance_scores.get("user_profile", 0) > 0.7 and
            context_data["user_profile"]["total_interactions"] > 10):
            recommendations.append("Power user - provide detailed technical explanation")

        return recommendations

    def _store_enhanced_context(self, state: HybridSystemState, analysis: dict[str, Any]):
        """Store enhanced context analysis for future reference"""

        context_entry = ContextEntry(
            entry_id=f"{state['query_id']}_context_analysis",
            user_id=state["user_id"],
            session_id=state["session_id"],
            timestamp=datetime.fromisoformat(state["timestamp"]) if isinstance(state["timestamp"], str) else state["timestamp"],
            entry_type="context_analysis",
            content=analysis["context_summary"],
            metadata={
                "query_id": state["query_id"],
                "relevance_scores": analysis["relevance_scores"],
                "recommendations": analysis["recommendations"],
                "priority_sources": list(analysis["priority_context"].keys()),
            },
        )

        self.context_provider.save_context_entry(context_entry)

    def _log_context_gathering(self, state: HybridSystemState, analysis: dict[str, Any]):
        """Log context gathering for monitoring"""

        self.logger.info(
            "Context gathering completed",
            extra={
                "operation": "context_gathering",
                "query_id": state["query_id"],
                "user_id": state["user_id"],
                "session_id": state["session_id"],
                "relevance_scores": analysis["relevance_scores"],
                "priority_sources": list(analysis["priority_context"].keys()),
                "recommendations_count": len(analysis["recommendations"]),
            },
        )
