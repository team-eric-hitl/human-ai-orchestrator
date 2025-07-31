"""Synchronous LLM routing agent compatible with LangGraph."""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..core.logging import get_logger
from ..services.simple_scoring_engine import SimplifiedScoringEngine
from ..data.human_agents_repository import SQLiteHumanAgentRepository
from ..interfaces.human_agents import HumanAgent, Specialization


class SyncLLMRoutingAgent:
    """
    Synchronous LLM-powered routing agent that works within LangGraph framework.
    
    This agent provides the same intelligent routing capabilities as the async version
    but works synchronously to integrate seamlessly with LangGraph nodes.
    """

    def __init__(
        self,
        human_agent_repository: Optional[SQLiteHumanAgentRepository] = None,
        scoring_engine: Optional[SimplifiedScoringEngine] = None
    ):
        """Initialize synchronous LLM routing agent."""
        self.repository = human_agent_repository or SQLiteHumanAgentRepository()
        self.scoring_engine = scoring_engine or SimplifiedScoringEngine()
        self.logger = get_logger(__name__)

    def route_to_human(
        self,
        conversation_context: Dict[str, Any],
        customer_context: Dict[str, Any] = None,
        urgency_level: int = 1
    ) -> Dict[str, Any]:
        """
        Route a conversation to the best human agent using LLM decision-making (synchronous).
        
        Args:
            conversation_context: Context about the conversation and request
            customer_context: Information about the customer
            urgency_level: Urgency level (1-5)
            
        Returns:
            Routing decision with selected agent and reasoning
        """
        try:
            # Use asyncio.run for database calls in a controlled way
            return self._run_async_routing(conversation_context, customer_context, urgency_level)
            
        except Exception as e:
            self.logger.error(f"Sync routing failed: {e}")
            return {
                "success": False,
                "reason": f"Routing error: {str(e)}",
                "fallback_action": "queue_for_callback"
            }

    def _run_async_routing(
        self,
        conversation_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        urgency_level: int
    ) -> Dict[str, Any]:
        """Run async routing operations safely using threading."""
        try:
            # Use ThreadPoolExecutor to run async operations in a separate thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self._run_async_in_thread,
                    conversation_context,
                    customer_context,
                    urgency_level
                )
                return future.result(timeout=30)  # 30 second timeout
                
        except Exception as e:
            self.logger.error(f"Async routing execution failed: {e}")
            return self._fallback_routing(conversation_context, customer_context, urgency_level)

    def _run_async_in_thread(
        self,
        conversation_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        urgency_level: int
    ) -> Dict[str, Any]:
        """Run async operations in a new thread with its own event loop."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(
                    self._async_route_to_human(conversation_context, customer_context, urgency_level)
                )
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Thread async routing failed: {e}")
            return self._fallback_routing(conversation_context, customer_context, urgency_level)

    async def _async_route_to_human(
        self,
        conversation_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        urgency_level: int
    ) -> Dict[str, Any]:
        """Async routing implementation."""
        # Extract routing requirements
        routing_context = self._extract_routing_context(
            conversation_context, customer_context, urgency_level
        )
        
        # Get candidate agents
        candidate_agents = await self._get_candidate_agents(routing_context)
        
        if not candidate_agents:
            return {
                "success": False,
                "reason": "No agents available",
                "fallback_action": "queue_for_callback"
            }
        
        # Get simplified metrics for decision making
        routing_summary = await self.scoring_engine.get_routing_summary(
            candidate_agents, routing_context
        )
        
        # Make routing decision (simplified LLM logic)
        decision = self._make_routing_decision(routing_summary, conversation_context)
        
        # Finalize decision
        final_decision = await self._finalize_routing_decision(decision, candidate_agents)
        
        return final_decision

    def _extract_routing_context(
        self,
        conversation_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        urgency_level: int
    ) -> Dict[str, Any]:
        """Extract and normalize routing context."""
        routing_context = {
            "urgency_level": urgency_level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if conversation_context:
            routing_context.update({
                "specialization_required": conversation_context.get("required_specialization"),
                "issue_type": conversation_context.get("issue_type"),
                "issue_description": conversation_context.get("issue_description"),
                "complexity_level": conversation_context.get("complexity_level", 1),
                "estimated_duration": conversation_context.get("estimated_duration_minutes")
            })
        
        if customer_context:
            routing_context.update({
                "customer_language": customer_context.get("preferred_language"),
                "customer_tier": customer_context.get("tier", "standard"),
                "previous_agent_id": customer_context.get("last_agent_id"),
                "customer_id": customer_context.get("customer_id"),
                "is_vip": customer_context.get("tier") == "vip"
            })
        
        return routing_context

    async def _get_candidate_agents(self, routing_context: Dict[str, Any]) -> List[HumanAgent]:
        """Get candidate agents based on routing context."""
        if routing_context.get("urgency_level", 1) >= 4:
            candidate_agents = await self.repository.get_all()
            candidate_agents = [
                agent for agent in candidate_agents
                if agent.workload.active_conversations < agent.max_concurrent_conversations
            ]
        else:
            if routing_context.get("specialization_required"):
                try:
                    specialization = Specialization(routing_context["specialization_required"])
                    candidate_agents = await self.repository.get_by_specialization(specialization)
                except ValueError:
                    candidate_agents = await self.repository.get_available_agents()
            else:
                candidate_agents = await self.repository.get_available_agents()
        
        return candidate_agents

    def _make_routing_decision(
        self,
        routing_summary: Dict[str, Any],
        conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make routing decision using simplified LLM-like logic."""
        available_agents = [
            agent for agent in routing_summary["agent_details"]
            if agent["is_available"]
        ]
        
        if not available_agents:
            return {
                "selected_agent_id": None,
                "confidence": 0.0,
                "reasoning": "No agents available",
                "alternative_agents": []
            }
        
        # Score agents based on multiple factors
        scored_agents = []
        
        for agent in available_agents:
            score = 0.0
            reasoning_factors = []
            
            # Specialization match (40% weight)
            if agent["specialization_match"]:
                score += 0.4
                reasoning_factors.append("Has required specialization")
            elif "general" in agent["specializations"]:
                score += 0.2
                reasoning_factors.append("General capability available")
            
            # Experience level (20% weight)
            exp_score = agent["experience_level"] / 5.0 * 0.2
            score += exp_score
            if agent["experience_level"] >= 4:
                reasoning_factors.append("Senior experience level")
            
            # Performance factors (20% weight)
            if agent["satisfaction_score"] >= 8.5:
                score += 0.15
                reasoning_factors.append("High customer satisfaction")
            
            if agent["stress_level"] <= 3.0:
                score += 0.05
                reasoning_factors.append("Low stress level")
            
            # Workload consideration (15% weight)
            if agent["utilization_percentage"] < 50:
                score += 0.15
                reasoning_factors.append("Light current workload")
            elif agent["utilization_percentage"] >= 80:
                score -= 0.05
            
            # Language match (5% weight)
            if agent["language_match"]:
                score += 0.05
                reasoning_factors.append("Language capability match")
            
            scored_agents.append({
                "agent": agent,
                "score": score,
                "reasoning": reasoning_factors
            })
        
        # Sort by score and select best
        scored_agents.sort(key=lambda x: x["score"], reverse=True)
        best_agent = scored_agents[0]
        
        # Calculate confidence
        if len(scored_agents) > 1:
            score_gap = best_agent["score"] - scored_agents[1]["score"]
            confidence = min(1.0, 0.6 + score_gap)
        else:
            confidence = 0.8
        
        return {
            "selected_agent_id": best_agent["agent"]["agent_id"],
            "selected_agent_name": best_agent["agent"]["agent_name"],
            "confidence": confidence,
            "score": best_agent["score"],
            "reasoning": best_agent["reasoning"],
            "alternative_agents": [
                {
                    "agent_id": agent["agent"]["agent_id"],
                    "agent_name": agent["agent"]["agent_name"],
                    "score": agent["score"],
                    "reasoning": agent["reasoning"][:2]
                }
                for agent in scored_agents[1:3]
            ]
        }

    async def _finalize_routing_decision(
        self,
        llm_decision: Dict[str, Any],
        candidate_agents: List[HumanAgent]
    ) -> Dict[str, Any]:
        """Finalize the routing decision with complete information."""
        if not llm_decision.get("selected_agent_id"):
            return {
                "success": False,
                "reason": "No suitable agent selected",
                "alternatives": [],
                "fallback_action": "queue_for_callback"
            }
        
        # Find the selected agent
        selected_agent = None
        for agent in candidate_agents:
            if agent.id == llm_decision["selected_agent_id"]:
                selected_agent = agent
                break
        
        if not selected_agent:
            return {
                "success": False,
                "reason": "Selected agent not found",
                "fallback_action": "retry_routing"
            }
        
        return {
            "success": True,
            "selected_agent": {
                "id": selected_agent.id,
                "name": selected_agent.name,
                "email": selected_agent.email,
                "experience_level": selected_agent.experience_level,
                "specializations": [
                    s.value if hasattr(s, 'value') else str(s) 
                    for s in selected_agent.specializations
                ],
                "current_workload": f"{selected_agent.workload.active_conversations}/{selected_agent.max_concurrent_conversations}"
            },
            "decision_details": {
                "confidence": llm_decision.get("confidence", 0.0),
                "score": llm_decision.get("score", 0.0),
                "reasoning": llm_decision.get("reasoning", []),
                "alternatives": llm_decision.get("alternative_agents", [])
            },
            "routing_timestamp": datetime.utcnow().isoformat(),
            "next_action": "assign_conversation"
        }

    def _fallback_routing(
        self,
        conversation_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        urgency_level: int
    ) -> Dict[str, Any]:
        """Fallback routing when async operations fail."""
        self.logger.warning("Using fallback routing due to async failure")
        
        # Simple fallback: return a generic response
        return {
            "success": False,
            "reason": "Routing system temporarily unavailable",
            "fallback_action": "queue_for_callback",
            "estimated_wait_time": 15
        }

    def explain_routing_decision(
        self,
        decision: Dict[str, Any],
        conversation_context: Dict[str, Any] = None
    ) -> str:
        """Generate human-readable explanation of routing decision."""
        if not decision.get("success"):
            return f"❌ Routing failed: {decision.get('reason', 'Unknown error')}"
        
        agent = decision["selected_agent"]
        details = decision["decision_details"]
        
        explanation_parts = [
            f"✅ Selected: {agent['name']} ({agent['experience_level']} experience)",
            f"🎯 Confidence: {details['confidence']:.0%}",
            f"📊 Score: {details['score']:.2f}/1.0"
        ]
        
        if details.get("reasoning"):
            explanation_parts.append(f"💡 Key factors: {', '.join(details['reasoning'][:3])}")
        
        if details.get("alternatives"):
            alt_names = [alt["agent_name"] for alt in details["alternatives"][:2]]
            explanation_parts.append(f"🔄 Alternatives: {', '.join(alt_names)}")
        
        return "\n".join(explanation_parts)