"""LLM-powered routing agent that uses simplified scoring for intelligent decisions."""

from typing import Dict, List, Optional, Any
from datetime import datetime

from ..core.logging import get_logger
from ..services.simple_scoring_engine import SimplifiedScoringEngine
from ..data.human_agents_repository import SQLiteHumanAgentRepository
from ..interfaces.human_agents import HumanAgent, Specialization


class LLMRoutingAgent:
    """
    LLM-powered routing agent that combines simplified scoring with context-aware decisions.
    
    This agent uses a simplified scoring engine to provide clean metrics to an LLM,
    which then makes nuanced routing decisions based on multiple factors.
    """

    def __init__(
        self,
        human_agent_repository: Optional[SQLiteHumanAgentRepository] = None,
        scoring_engine: Optional[SimplifiedScoringEngine] = None
    ):
        """Initialize LLM routing agent."""
        self.repository = human_agent_repository or SQLiteHumanAgentRepository()
        self.scoring_engine = scoring_engine or SimplifiedScoringEngine()
        self.logger = get_logger(__name__)

    async def route_to_human(
        self,
        conversation_context: Dict[str, Any],
        customer_context: Dict[str, Any] = None,
        urgency_level: int = 1
    ) -> Dict[str, Any]:
        """
        Route a conversation to the best human agent using LLM decision-making.
        
        Args:
            conversation_context: Context about the conversation and request
            customer_context: Information about the customer
            urgency_level: Urgency level (1-5)
            
        Returns:
            Routing decision with selected agent and reasoning
        """
        try:
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
            
            # Get simplified metrics for LLM
            routing_summary = await self.scoring_engine.get_routing_summary(
                candidate_agents, routing_context
            )
            
            # Prepare LLM prompt with structured data
            llm_decision = await self._make_llm_routing_decision(
                routing_summary, conversation_context
            )
            
            # Validate and finalize decision
            final_decision = await self._finalize_routing_decision(
                llm_decision, candidate_agents
            )
            
            return final_decision
            
        except Exception as e:
            self.logger.error(f"Failed to route conversation: {e}")
            return {
                "success": False,
                "reason": f"Routing error: {str(e)}",
                "fallback_action": "queue_for_callback"
            }

    def _extract_routing_context(
        self,
        conversation_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        urgency_level: int
    ) -> Dict[str, Any]:
        """Extract and normalize routing context."""
        # Default context
        routing_context = {
            "urgency_level": urgency_level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Extract from conversation context
        if conversation_context:
            routing_context.update({
                "specialization_required": conversation_context.get("required_specialization"),
                "issue_type": conversation_context.get("issue_type"),
                "issue_description": conversation_context.get("issue_description"),
                "complexity_level": conversation_context.get("complexity_level", 1),
                "estimated_duration": conversation_context.get("estimated_duration_minutes")
            })
        
        # Extract from customer context  
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
        # Start with all agents for high urgency, otherwise filter by availability
        if routing_context.get("urgency_level", 1) >= 4:
            candidate_agents = await self.repository.get_all()
            # Filter to only those who can take more conversations
            candidate_agents = [
                agent for agent in candidate_agents
                if agent.workload.active_conversations < agent.max_concurrent_conversations
            ]
        else:
            # Normal priority - get available agents
            if routing_context.get("specialization_required"):
                try:
                    specialization = Specialization(routing_context["specialization_required"])
                    candidate_agents = await self.repository.get_by_specialization(specialization)
                except ValueError:
                    # If specialization not recognized, get all available
                    candidate_agents = await self.repository.get_available_agents()
            else:
                candidate_agents = await self.repository.get_available_agents()
        
        return candidate_agents

    async def _make_llm_routing_decision(
        self,
        routing_summary: Dict[str, Any],
        conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make routing decision using LLM.
        
        In a real implementation, this would call an actual LLM API.
        For the prototype, we'll simulate intelligent decision-making logic.
        """
        # Simulate LLM decision-making with rule-based logic
        # In production, replace this with actual LLM API call
        
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
        
        # Score agents based on multiple factors (simulating LLM reasoning)
        scored_agents = []
        
        for agent in available_agents:
            score = 0.0
            reasoning_factors = []
            
            # Specialization match (high weight)
            if agent["specialization_match"]:
                score += 0.4
                reasoning_factors.append("Has required specialization")
            elif "general" in agent["specializations"]:
                score += 0.2
                reasoning_factors.append("General capability")
            
            # Experience level
            exp_score = agent["experience_level"] / 5.0 * 0.2
            score += exp_score
            if agent["experience_level"] >= 4:
                reasoning_factors.append("Senior experience")
            
            # Performance factors
            if agent["satisfaction_score"] >= 8.5:
                score += 0.15
                reasoning_factors.append("High customer satisfaction")
            
            if agent["stress_level"] <= 3.0:
                score += 0.1
                reasoning_factors.append("Low stress level")
            
            # Workload consideration
            if agent["utilization_percentage"] < 50:
                score += 0.1
                reasoning_factors.append("Light workload")
            elif agent["utilization_percentage"] >= 80:
                score -= 0.1
                reasoning_factors.append("Heavy workload")
            
            # Language match
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
        
        # Calculate confidence based on score gap
        if len(scored_agents) > 1:
            score_gap = best_agent["score"] - scored_agents[1]["score"]
            confidence = min(1.0, 0.5 + score_gap)  # Base 50% + gap bonus
        else:
            confidence = 0.8  # Only one option
        
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
                    "reasoning": agent["reasoning"][:2]  # Top 2 reasons
                }
                for agent in scored_agents[1:3]  # Next 2 best options
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
        
        # Return complete decision
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

    async def explain_routing_decision(
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

    # Method to simulate LLM prompt (for demonstration)
    def _generate_llm_prompt(self, routing_summary: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate the actual prompt that would be sent to an LLM."""
        agent_details = routing_summary["agent_details"]
        available_agents = [a for a in agent_details if a["is_available"]]
        
        prompt = f"""You are an intelligent customer service routing system. Analyze the following data and select the best agent for this customer request.

REQUEST CONTEXT:
- Issue Type: {context.get('issue_type', 'General inquiry')}  
- Specialization Needed: {routing_summary['context'].get('specialization_required', 'Any')}
- Customer Language: {routing_summary['context'].get('customer_language', 'English')}
- Urgency Level: {routing_summary['context'].get('urgency_level', 1)}/5
- Customer Tier: {routing_summary['context'].get('customer_tier', 'Standard')}

TEAM STATUS:
- Total Available Agents: {routing_summary['available_agents']}/{routing_summary['total_agents']}
- Specialization Matches: {routing_summary['specialization_matches']}
- Average Team Utilization: {routing_summary['average_utilization']}%

AVAILABLE AGENTS:
"""
        
        for i, agent in enumerate(available_agents[:5], 1):  # Top 5 agents
            prompt += f"""
{i}. {agent['agent_name']} ({agent['agent_id']})
   - Experience: {agent['experience_description']} (Level {agent['experience_level']})
   - Specializations: {', '.join(agent['specializations'])}
   - Current Status: {agent['availability_reason']}
   - Workload: {agent['active_conversations']}/{agent['max_conversations']} conversations ({agent['utilization_percentage']}%)
   - Performance: {agent['satisfaction_score']}/10 satisfaction, {agent['stress_level']}/10 stress
   - Languages: {', '.join(agent['languages'])}
   - Summary: {agent['summary']}
   - Strengths: {', '.join(agent['recommendation_factors']) if agent['recommendation_factors'] else 'None noted'}
   - Concerns: {', '.join(agent['concerns']) if agent['concerns'] else 'None'}
"""
        
        prompt += """
INSTRUCTIONS:
1. Select the best agent considering all factors
2. Provide your confidence level (1-10)
3. List your top 3 reasons for the selection
4. Mention any concerns or alternative suggestions
5. Consider specialization match, workload balance, performance, and employee wellbeing

RESPONSE FORMAT:
Selected Agent: [Agent Name]
Confidence: [1-10]
Reasoning: [Bullet points]
Concerns: [Any concerns]
Alternatives: [If applicable]
"""
        
        return prompt