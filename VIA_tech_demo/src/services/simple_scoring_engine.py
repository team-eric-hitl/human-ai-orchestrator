"""Simplified scoring engine for LLM-powered routing decisions."""

from typing import List, Dict, Any
from datetime import datetime

from ..core.logging import get_logger
from ..interfaces.human_agents import HumanAgent, HumanAgentStatus, Specialization


class SimplifiedScoringEngine:
    """Simplified scoring engine that provides key metrics for LLM decision-making."""

    def __init__(self):
        """Initialize simplified scoring engine."""
        self.logger = get_logger(__name__)

    async def get_agent_metrics(
        self, 
        agents: List[HumanAgent],
        required_specialization: str = None,
        customer_language: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get simplified metrics for agents that an LLM can use for routing decisions.
        
        Args:
            agents: List of agents to evaluate
            required_specialization: Required specialization (optional)
            customer_language: Customer's preferred language (optional)
            
        Returns:
            List of agent metrics dictionaries
        """
        agent_metrics = []
        
        for agent in agents:
            # Basic availability check
            is_available = self._is_agent_available(agent)
            
            # Specialization match
            specialization_match = self._check_specialization_match(
                agent, required_specialization
            )
            
            # Language capability
            language_match = self._check_language_match(agent, customer_language)
            
            # Current workload assessment
            workload_info = self._assess_workload(agent)
            
            # Experience and performance summary
            performance_info = self._summarize_performance(agent)
            
            # Create simplified metrics
            metrics = {
                # Basic info
                "agent_id": agent.id,
                "agent_name": agent.name,
                "email": agent.email,
                
                # Availability
                "status": agent.status.value if hasattr(agent.status, 'value') else str(agent.status),
                "is_available": is_available,
                "availability_reason": self._get_availability_reason(agent),
                
                # Skills and experience
                "experience_level": agent.experience_level,
                "experience_description": self._describe_experience_level(agent.experience_level),
                "specializations": [
                    s.value if hasattr(s, 'value') else str(s) 
                    for s in agent.specializations
                ],
                "specialization_match": specialization_match,
                "languages": agent.languages,
                "language_match": language_match,
                
                # Current workload
                "active_conversations": agent.workload.active_conversations,
                "max_conversations": agent.max_concurrent_conversations,
                "utilization_percentage": workload_info["utilization_percentage"],
                "capacity_available": workload_info["capacity_available"],
                "workload_status": workload_info["status"],
                
                # Performance indicators
                "satisfaction_score": agent.workload.satisfaction_score,
                "satisfaction_level": self._categorize_satisfaction(agent.workload.satisfaction_score),
                "stress_level": agent.workload.stress_level,
                "stress_status": self._categorize_stress(agent.workload.stress_level),
                "avg_response_time": agent.workload.avg_response_time_minutes,
                "response_time_rating": self._rate_response_time(agent.workload.avg_response_time_minutes),
                
                # Schedule info (if available)
                "shift_start": agent.shift_start,
                "shift_end": agent.shift_end,
                "last_activity": agent.last_activity.isoformat() if agent.last_activity else None,
                
                # Summary for LLM
                "summary": self._create_agent_summary(agent, specialization_match, language_match),
                "recommendation_factors": self._get_recommendation_factors(
                    agent, specialization_match, language_match
                ),
                "concerns": self._get_potential_concerns(agent)
            }
            
            agent_metrics.append(metrics)
        
        # Sort by availability and basic suitability
        agent_metrics.sort(key=lambda x: (
            not x["is_available"],  # Available first
            not x["specialization_match"],  # Specialization match next
            x["utilization_percentage"],  # Lower utilization better
            x["stress_level"],  # Lower stress better
            -x["experience_level"]  # Higher experience better
        ))
        
        return agent_metrics

    def _is_agent_available(self, agent: HumanAgent) -> bool:
        """Check if agent is available for assignment."""
        if agent.status in [HumanAgentStatus.OFFLINE, HumanAgentStatus.BREAK]:
            return False
        if agent.workload.active_conversations >= agent.max_concurrent_conversations:
            return False
        return True

    def _get_availability_reason(self, agent: HumanAgent) -> str:
        """Get human-readable reason for availability status."""
        if agent.status == HumanAgentStatus.OFFLINE:
            return "Agent is offline"
        elif agent.status == HumanAgentStatus.BREAK:
            return "Agent is on break"
        elif agent.workload.active_conversations >= agent.max_concurrent_conversations:
            return f"At maximum capacity ({agent.workload.active_conversations}/{agent.max_concurrent_conversations})"
        elif agent.status == HumanAgentStatus.BUSY:
            return f"Busy but can take more conversations ({agent.workload.active_conversations}/{agent.max_concurrent_conversations})"
        else:
            return "Available"

    def _check_specialization_match(self, agent: HumanAgent, required_spec: str) -> bool:
        """Check if agent has required specialization."""
        if not required_spec:
            return True
        
        agent_specs = [
            s.value if hasattr(s, 'value') else str(s) 
            for s in agent.specializations
        ]
        
        # Exact match or general capability
        return required_spec in agent_specs or "general" in agent_specs

    def _check_language_match(self, agent: HumanAgent, customer_language: str) -> bool:
        """Check if agent can handle customer's language."""
        if not customer_language:
            return True
        return customer_language in agent.languages

    def _assess_workload(self, agent: HumanAgent) -> Dict[str, Any]:
        """Assess agent's current workload."""
        if agent.max_concurrent_conversations == 0:
            utilization = 0.0
        else:
            utilization = agent.workload.active_conversations / agent.max_concurrent_conversations
        
        capacity_available = agent.max_concurrent_conversations - agent.workload.active_conversations
        
        if utilization == 0:
            status = "No active conversations"
        elif utilization < 0.5:
            status = "Light workload"
        elif utilization < 0.8:
            status = "Moderate workload"
        elif utilization < 1.0:
            status = "Heavy workload"
        else:
            status = "At capacity"
        
        return {
            "utilization_percentage": round(utilization * 100, 1),
            "capacity_available": max(0, capacity_available),
            "status": status
        }

    def _summarize_performance(self, agent: HumanAgent) -> Dict[str, Any]:
        """Summarize agent's performance."""
        return {
            "satisfaction": agent.workload.satisfaction_score,
            "stress": agent.workload.stress_level,
            "response_time": agent.workload.avg_response_time_minutes
        }

    def _describe_experience_level(self, level: int) -> str:
        """Convert experience level to description."""
        descriptions = {
            1: "Entry level",
            2: "Junior", 
            3: "Mid-level",
            4: "Senior",
            5: "Expert"
        }
        return descriptions.get(level, f"Level {level}")

    def _categorize_satisfaction(self, score: float) -> str:
        """Categorize satisfaction score."""
        if score >= 9.0:
            return "Excellent"
        elif score >= 8.0:
            return "Very Good"
        elif score >= 7.0:
            return "Good"
        elif score >= 6.0:
            return "Fair"
        else:
            return "Needs Improvement"

    def _categorize_stress(self, level: float) -> str:
        """Categorize stress level."""
        if level <= 3.0:
            return "Low stress"
        elif level <= 5.0:
            return "Moderate stress"
        elif level <= 7.0:
            return "High stress"
        else:
            return "Very high stress"

    def _rate_response_time(self, minutes: float) -> str:
        """Rate response time performance."""
        if minutes == 0:
            return "No data"
        elif minutes <= 3.0:
            return "Excellent"
        elif minutes <= 5.0:
            return "Good"
        elif minutes <= 8.0:
            return "Fair"
        else:
            return "Slow"

    def _create_agent_summary(
        self, 
        agent: HumanAgent, 
        spec_match: bool, 
        lang_match: bool
    ) -> str:
        """Create a concise summary of agent suitability."""
        summary_parts = []
        
        # Experience and role
        exp_desc = self._describe_experience_level(agent.experience_level)
        summary_parts.append(f"{exp_desc} agent")
        
        # Specializations
        specs = [s.value if hasattr(s, 'value') else str(s) for s in agent.specializations]
        if specs:
            summary_parts.append(f"specializes in {', '.join(specs)}")
        
        # Current status
        if not self._is_agent_available(agent):
            summary_parts.append("currently unavailable")
        else:
            workload = self._assess_workload(agent)
            summary_parts.append(f"available with {workload['status'].lower()}")
        
        # Performance highlight
        if agent.workload.satisfaction_score >= 8.5:
            summary_parts.append("high customer satisfaction")
        elif agent.workload.stress_level >= 7.0:
            summary_parts.append("currently under stress")
        
        return ". ".join(summary_parts).capitalize() + "."

    def _get_recommendation_factors(
        self, 
        agent: HumanAgent, 
        spec_match: bool, 
        lang_match: bool
    ) -> List[str]:
        """Get factors that recommend this agent."""
        factors = []
        
        if spec_match and agent.specializations:
            factors.append("Has required specialization")
        
        if lang_match and len(agent.languages) > 1:
            factors.append("Multilingual capability")
        
        if agent.experience_level >= 4:
            factors.append("Senior experience level")
        
        if agent.workload.satisfaction_score >= 8.5:
            factors.append("High customer satisfaction rating")
        
        if self._is_agent_available(agent):
            workload = self._assess_workload(agent)
            if workload["utilization_percentage"] < 50:
                factors.append("Light current workload")
        
        if agent.workload.stress_level <= 3.0:
            factors.append("Low stress level")
        
        if agent.workload.avg_response_time_minutes > 0 and agent.workload.avg_response_time_minutes <= 5.0:
            factors.append("Fast response time")
        
        return factors

    def _get_potential_concerns(self, agent: HumanAgent) -> List[str]:
        """Get potential concerns about this agent."""
        concerns = []
        
        if not self._is_agent_available(agent):
            concerns.append(self._get_availability_reason(agent))
        
        if agent.workload.stress_level >= 7.0:
            concerns.append(f"High stress level ({agent.workload.stress_level}/10)")
        
        if agent.experience_level <= 2:
            concerns.append("Limited experience level")
        
        if agent.workload.satisfaction_score < 7.0:
            concerns.append(f"Below-average satisfaction score ({agent.workload.satisfaction_score}/10)")
        
        workload = self._assess_workload(agent)
        if workload["utilization_percentage"] >= 80:
            concerns.append("Heavy current workload")
        
        if agent.workload.avg_response_time_minutes > 8.0:
            concerns.append(f"Slow response time ({agent.workload.avg_response_time_minutes:.1f} min)")
        
        return concerns

    async def get_routing_summary(
        self, 
        agents: List[HumanAgent],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of routing options for LLM decision making.
        
        Args:
            agents: Available agents
            context: Additional context for routing
            
        Returns:
            Summary dictionary for LLM consumption
        """
        context = context or {}
        
        # Get agent metrics
        agent_metrics = await self.get_agent_metrics(
            agents,
            context.get("specialization_required"),
            context.get("customer_language")
        )
        
        # Create summary statistics
        total_agents = len(agents)
        available_agents = len([a for a in agent_metrics if a["is_available"]])
        specialization_matches = len([a for a in agent_metrics if a["specialization_match"]])
        
        # Experience distribution
        experience_dist = {}
        for agent in agent_metrics:
            exp_desc = agent["experience_description"]
            experience_dist[exp_desc] = experience_dist.get(exp_desc, 0) + 1
        
        # Workload summary
        avg_utilization = sum(a["utilization_percentage"] for a in agent_metrics) / len(agent_metrics) if agent_metrics else 0
        high_stress_count = len([a for a in agent_metrics if a["stress_level"] >= 7.0])
        
        return {
            "total_agents": total_agents,
            "available_agents": available_agents,
            "specialization_matches": specialization_matches,
            "experience_distribution": experience_dist,
            "average_utilization": round(avg_utilization, 1),
            "high_stress_agents": high_stress_count,
            "agent_details": agent_metrics,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }