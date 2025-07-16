"""
Demo Orchestrator
Coordinates simulation of customer/chatbot/employee interactions for demonstration purposes
"""

import asyncio
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from .human_customer_simulator import HumanCustomerSimulator, CustomerPersonality, CustomerScenario
from .employee_simulator import EmployeeSimulator
from ..core.logging import get_logger


class DemoOrchestrator:
    """Orchestrates demonstration scenarios of the human-in-the-loop system"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.customer_simulator = HumanCustomerSimulator()
        self.employee_simulator = EmployeeSimulator()
        self.active_demonstrations = {}
        self.demo_scenarios = self._create_demo_scenarios()

    def _create_demo_scenarios(self) -> List[Dict[str, Any]]:
        """Create predefined demonstration scenarios"""
        
        scenarios = [
            {
                "name": "Happy Path - Simple Question",
                "description": "Polite customer with simple question, resolved by chatbot",
                "customer_personality": CustomerPersonality.POLITE,
                "customer_scenario": CustomerScenario.SIMPLE_QUESTION,
                "initial_frustration": 0,
                "expected_outcome": "resolved_by_chatbot",
                "chatbot_quality": "high",
            },
            {
                "name": "Escalation - Technical Issue",
                "description": "Technical user with complex API integration question",
                "customer_personality": CustomerPersonality.TECHNICAL,
                "customer_scenario": CustomerScenario.COMPLEX_INTEGRATION,
                "initial_frustration": 2,
                "expected_outcome": "escalated_to_technical_specialist",
                "chatbot_quality": "medium",
            },
            {
                "name": "Frustrated Customer",
                "description": "Frustrated customer with repeat issue, needs human intervention",
                "customer_personality": CustomerPersonality.FRUSTRATED,
                "customer_scenario": CustomerScenario.REPEAT_ISSUE,
                "initial_frustration": 6,
                "expected_outcome": "escalated_for_frustration",
                "chatbot_quality": "low",
            },
            {
                "name": "Impatient Business Customer",
                "description": "Business customer with urgent billing issue",
                "customer_personality": CustomerPersonality.IMPATIENT,
                "customer_scenario": CustomerScenario.BILLING_PROBLEM,
                "initial_frustration": 4,
                "expected_outcome": "escalated_to_billing_specialist",
                "chatbot_quality": "medium",
            },
            {
                "name": "Quality Issue - Poor Response",
                "description": "Customer receives inadequate chatbot response, needs adjustment",
                "customer_personality": CustomerPersonality.CONFUSED,
                "customer_scenario": CustomerScenario.SIMPLE_QUESTION,
                "initial_frustration": 1,
                "expected_outcome": "quality_adjustment_then_resolution",
                "chatbot_quality": "poor",
            },
            {
                "name": "Manager Escalation",
                "description": "Customer explicitly requests manager for complaint",
                "customer_personality": CustomerPersonality.BUSINESS,
                "customer_scenario": CustomerScenario.ESCALATION_REQUEST,
                "initial_frustration": 5,
                "expected_outcome": "escalated_to_manager",
                "chatbot_quality": "medium",
            },
        ]
        
        return scenarios

    def start_demo_scenario(self, scenario_name: str = None) -> Dict[str, Any]:
        """Start a demonstration scenario"""
        
        if scenario_name:
            scenario = next((s for s in self.demo_scenarios if s["name"] == scenario_name), None)
            if not scenario:
                raise ValueError(f"Scenario '{scenario_name}' not found")
        else:
            scenario = random.choice(self.demo_scenarios)
        
        # Create customer interaction
        customer_interaction = self.customer_simulator.create_customer_interaction(
            personality=scenario["customer_personality"],
            scenario=scenario["customer_scenario"],
            frustration_level=scenario["initial_frustration"]
        )
        
        demo_id = f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}"
        
        demo_session = {
            "demo_id": demo_id,
            "scenario": scenario,
            "customer_interaction": customer_interaction,
            "conversation_log": [],
            "system_decisions": [],
            "current_stage": "initial_query",
            "start_time": datetime.now(),
            "chatbot_responses": [],
            "escalation_data": None,
            "employee_interaction": None,
            "final_outcome": None,
        }
        
        self.active_demonstrations[demo_id] = demo_session
        
        # Log initial customer query
        self._log_demo_event(demo_id, "customer_query", {
            "query": customer_interaction["initial_query"],
            "customer_state": {
                "personality": customer_interaction["personality"],
                "frustration_level": customer_interaction["initial_frustration_level"],
                "scenario": customer_interaction["scenario"],
            }
        })
        
        return {
            "demo_id": demo_id,
            "scenario": scenario,
            "customer_query": customer_interaction["initial_query"],
            "customer_context": customer_interaction,
            "next_step": "chatbot_response",
        }

    def simulate_chatbot_response(self, demo_id: str) -> Dict[str, Any]:
        """Simulate chatbot response based on scenario quality settings"""
        
        if demo_id not in self.active_demonstrations:
            raise ValueError(f"Demo {demo_id} not found")
        
        demo = self.active_demonstrations[demo_id]
        scenario = demo["scenario"]
        customer_interaction = demo["customer_interaction"]
        
        # Generate chatbot response based on quality setting
        chatbot_response = self._generate_simulated_chatbot_response(
            customer_interaction["initial_query"],
            scenario["chatbot_quality"],
            customer_interaction["personality"]
        )
        
        demo["chatbot_responses"].append(chatbot_response)
        demo["current_stage"] = "chatbot_responded"
        
        self._log_demo_event(demo_id, "chatbot_response", {
            "response": chatbot_response["response"],
            "quality_level": scenario["chatbot_quality"],
            "confidence": chatbot_response["confidence"],
        })
        
        return {
            "demo_id": demo_id,
            "chatbot_response": chatbot_response["response"],
            "response_metadata": chatbot_response,
            "next_step": "quality_assessment",
        }

    def simulate_quality_assessment(self, demo_id: str) -> Dict[str, Any]:
        """Simulate quality agent assessment"""
        
        demo = self.active_demonstrations[demo_id]
        scenario = demo["scenario"]
        chatbot_response = demo["chatbot_responses"][-1]
        customer_interaction = demo["customer_interaction"]
        
        # Simulate quality assessment
        quality_assessment = self._simulate_quality_agent_decision(
            customer_interaction["initial_query"],
            chatbot_response["response"],
            scenario["chatbot_quality"]
        )
        
        demo["current_stage"] = "quality_assessed"
        
        self._log_demo_event(demo_id, "quality_assessment", quality_assessment)
        
        return {
            "demo_id": demo_id,
            "quality_assessment": quality_assessment,
            "next_step": quality_assessment["next_action"],
        }

    def simulate_frustration_analysis(self, demo_id: str) -> Dict[str, Any]:
        """Simulate frustration agent analysis"""
        
        demo = self.active_demonstrations[demo_id]
        scenario = demo["scenario"]
        customer_interaction = demo["customer_interaction"]
        
        # Simulate frustration analysis
        frustration_analysis = self._simulate_frustration_agent_analysis(
            customer_interaction["initial_query"],
            customer_interaction["initial_frustration_level"],
            customer_interaction["personality"]
        )
        
        self._log_demo_event(demo_id, "frustration_analysis", frustration_analysis)
        
        return {
            "demo_id": demo_id,
            "frustration_analysis": frustration_analysis,
            "intervention_needed": frustration_analysis["intervention_needed"],
            "next_step": "routing_decision" if frustration_analysis["intervention_needed"] else "respond_to_customer",
        }

    def simulate_routing_decision(self, demo_id: str) -> Dict[str, Any]:
        """Simulate routing agent decision"""
        
        demo = self.active_demonstrations[demo_id]
        scenario = demo["scenario"]
        customer_interaction = demo["customer_interaction"]
        
        # Simulate routing decision
        routing_decision = self._simulate_routing_agent_decision(
            customer_interaction,
            scenario["expected_outcome"]
        )
        
        demo["escalation_data"] = routing_decision
        demo["current_stage"] = "routed_to_human"
        
        self._log_demo_event(demo_id, "routing_decision", routing_decision)
        
        return {
            "demo_id": demo_id,
            "routing_decision": routing_decision,
            "assigned_employee": routing_decision["assigned_employee"],
            "next_step": "human_agent_response",
        }

    def simulate_human_agent_response(self, demo_id: str) -> Dict[str, Any]:
        """Simulate human agent handling the escalation"""
        
        demo = self.active_demonstrations[demo_id]
        customer_interaction = demo["customer_interaction"]
        routing_decision = demo["escalation_data"]
        
        if not routing_decision:
            raise ValueError("No routing decision found")
        
        # Use employee simulator to handle the case
        employee_response = self.employee_simulator.handle_escalated_case(
            assigned_employee_id=routing_decision["assigned_employee"]["id"],
            customer_context=customer_interaction,
            escalation_reason=routing_decision.get("escalation_reason", "Quality/Frustration escalation"),
            customer_query=customer_interaction["initial_query"],
            chatbot_response=demo["chatbot_responses"][-1]["response"] if demo["chatbot_responses"] else None
        )
        
        demo["employee_interaction"] = employee_response
        demo["current_stage"] = "human_agent_handling"
        
        self._log_demo_event(demo_id, "human_agent_response", employee_response)
        
        return {
            "demo_id": demo_id,
            "employee_response": employee_response,
            "next_step": "customer_response_to_human",
        }

    def simulate_customer_response_to_human(self, demo_id: str) -> Dict[str, Any]:
        """Simulate customer response to human agent"""
        
        demo = self.active_demonstrations[demo_id]
        employee_response = demo["employee_interaction"]
        
        # Customer simulator evaluates human agent response
        customer_response = self.customer_simulator.respond_to_chatbot(
            employee_response["employee_response"],
            demo["customer_interaction"]
        )
        
        # Most customers are satisfied with human agents
        customer_response["satisfaction_with_response"] = min(10, customer_response["satisfaction_with_response"] + 2)
        customer_response["wants_escalation"] = False  # Assume human agents resolve issues
        
        demo["current_stage"] = "customer_responded_to_human"
        
        self._log_demo_event(demo_id, "customer_response_to_human", customer_response)
        
        return {
            "demo_id": demo_id,
            "customer_response": customer_response,
            "next_step": "resolution",
        }

    def simulate_resolution(self, demo_id: str) -> Dict[str, Any]:
        """Simulate case resolution"""
        
        demo = self.active_demonstrations[demo_id]
        employee_interaction = demo.get("employee_interaction")
        
        if employee_interaction:
            # Resolve through employee simulator
            resolution_result = self.employee_simulator.continue_conversation(
                employee_interaction["case_id"],
                "Thank you, that resolved my issue!",
                customer_frustration=2  # Low frustration after resolution
            )
        else:
            # Direct chatbot resolution
            resolution_result = {
                "case_resolved": True,
                "resolution_result": {
                    "resolution_time_minutes": 3,
                    "customer_satisfaction": 8.5,
                    "resolution_method": "chatbot_direct",
                },
            }
        
        demo["final_outcome"] = resolution_result
        demo["current_stage"] = "resolved"
        demo["end_time"] = datetime.now()
        
        self._log_demo_event(demo_id, "resolution", resolution_result)
        
        return {
            "demo_id": demo_id,
            "resolution_result": resolution_result,
            "demo_completed": True,
            "summary": self._generate_demo_summary(demo_id),
        }

    def get_demo_log(self, demo_id: str) -> Dict[str, Any]:
        """Get complete demonstration log"""
        
        if demo_id not in self.active_demonstrations:
            raise ValueError(f"Demo {demo_id} not found")
        
        demo = self.active_demonstrations[demo_id]
        
        return {
            "demo_id": demo_id,
            "scenario": demo["scenario"],
            "conversation_log": demo["conversation_log"],
            "system_decisions": demo["system_decisions"],
            "current_stage": demo["current_stage"],
            "duration_seconds": (
                (demo.get("end_time", datetime.now()) - demo["start_time"]).total_seconds()
            ),
            "final_outcome": demo.get("final_outcome"),
        }

    def list_available_scenarios(self) -> List[Dict[str, Any]]:
        """List all available demonstration scenarios"""
        return [
            {
                "name": scenario["name"],
                "description": scenario["description"],
                "expected_outcome": scenario["expected_outcome"],
            }
            for scenario in self.demo_scenarios
        ]

    def get_active_demos(self) -> List[str]:
        """Get list of active demonstration IDs"""
        return list(self.active_demonstrations.keys())

    def _generate_simulated_chatbot_response(
        self, query: str, quality_level: str, personality: str
    ) -> Dict[str, Any]:
        """Generate simulated chatbot response with specified quality"""
        
        # Response templates by quality level
        if quality_level == "high":
            responses = [
                "I'd be happy to help you with that! Here's a step-by-step solution: [detailed helpful response with clear steps]",
                "Great question! Let me provide you with comprehensive information to resolve this: [thorough, accurate response]",
                "I understand exactly what you need. Here's how to solve this: [precise, helpful solution]",
            ]
            confidence = random.uniform(0.85, 0.95)
            
        elif quality_level == "medium":
            responses = [
                "I can help you with that. Here's what you can try: [partially helpful response, may need clarification]",
                "Let me provide some information about this: [adequate response but could be more detailed]", 
                "Here are some steps that should help: [reasonable response but not comprehensive]",
            ]
            confidence = random.uniform(0.65, 0.80)
            
        elif quality_level == "poor":
            responses = [
                "I'm not sure I understand your question completely. Could you clarify?",
                "Here's some general information that might help: [vague, not specific to the question]",
                "You might want to check our documentation for more details.",
            ]
            confidence = random.uniform(0.30, 0.55)
            
        else:  # low quality
            responses = [
                "I don't know how to help with that specific issue.",
                "This seems like a complex problem. You might need to contact support.",
                "I'm having trouble understanding your request.",
            ]
            confidence = random.uniform(0.20, 0.40)
        
        response = random.choice(responses)
        
        # Adjust response for personality
        if personality == CustomerPersonality.TECHNICAL.value and quality_level in ["high", "medium"]:
            response = response.replace("[", "First, check your API configuration. Then, [")
        elif personality == CustomerPersonality.FRUSTRATED.value and quality_level == "high":
            response = "I understand this can be frustrating. " + response
        
        return {
            "response": response,
            "confidence": confidence,
            "quality_level": quality_level,
            "response_time": random.uniform(1.5, 3.5),
        }

    def _simulate_quality_agent_decision(
        self, query: str, response: str, expected_quality: str
    ) -> Dict[str, Any]:
        """Simulate quality agent assessment"""
        
        # Map quality levels to scores
        quality_scores = {
            "high": random.uniform(8.0, 9.5),
            "medium": random.uniform(6.0, 7.5),
            "poor": random.uniform(4.0, 5.5),
            "low": random.uniform(2.0, 4.0),
        }
        
        score = quality_scores.get(expected_quality, 7.0)
        
        if score >= 7.0:
            decision = "adequate"
            next_action = "respond_to_customer"
        elif score >= 5.0:
            decision = "needs_adjustment"
            next_action = "adjust_response"
        else:
            decision = "human_intervention"
            next_action = "escalate_to_human"
        
        return {
            "decision": decision,
            "overall_score": score,
            "confidence": random.uniform(0.7, 0.9),
            "reasoning": f"Response quality assessment: {decision}",
            "next_action": next_action,
        }

    def _simulate_frustration_agent_analysis(
        self, query: str, initial_frustration: int, personality: str
    ) -> Dict[str, Any]:
        """Simulate frustration agent analysis"""
        
        # Adjust frustration based on personality
        if personality == CustomerPersonality.FRUSTRATED.value:
            frustration_score = initial_frustration + random.uniform(1.0, 2.0)
        elif personality == CustomerPersonality.IMPATIENT.value:
            frustration_score = initial_frustration + random.uniform(0.5, 1.5)
        else:
            frustration_score = initial_frustration + random.uniform(-0.5, 0.5)
        
        frustration_score = max(0, min(10, frustration_score))
        
        # Determine intervention need
        intervention_needed = frustration_score > 6.0
        
        if frustration_score >= 8.0:
            level = "critical"
        elif frustration_score >= 6.0:
            level = "high"
        elif frustration_score >= 3.0:
            level = "moderate"
        else:
            level = "low"
        
        return {
            "overall_score": frustration_score,
            "overall_level": level,
            "confidence": random.uniform(0.7, 0.9),
            "intervention_needed": intervention_needed,
            "contributing_factors": [f"{personality}_personality", "initial_query_tone"],
        }

    def _simulate_routing_agent_decision(
        self, customer_interaction: Dict[str, Any], expected_outcome: str
    ) -> Dict[str, Any]:
        """Simulate routing agent decision"""
        
        # Get available employees
        employees = self.employee_simulator.get_employee_status()
        available_employees = [emp for emp in employees if emp["availability"] == "available"]
        
        if not available_employees:
            return {
                "status": "queued",
                "estimated_wait_time": 15,
                "queue_position": 3,
            }
        
        # Select appropriate employee based on expected outcome
        if "technical_specialist" in expected_outcome:
            selected = next((emp for emp in available_employees if "technical" in emp["type"]), available_employees[0])
        elif "billing_specialist" in expected_outcome:
            selected = next((emp for emp in available_employees if "billing" in emp["type"]), available_employees[0])
        elif "manager" in expected_outcome:
            selected = next((emp for emp in available_employees if "manager" in emp["type"]), available_employees[0])
        else:
            selected = available_employees[0]
        
        return {
            "assigned_employee": selected,
            "routing_strategy": "skill_based",
            "match_score": random.uniform(85, 95),
            "routing_confidence": random.uniform(0.8, 0.9),
            "estimated_resolution_time": random.randint(15, 45),
            "escalation_reason": "Quality/Frustration threshold exceeded",
        }

    def _log_demo_event(self, demo_id: str, event_type: str, event_data: Dict[str, Any]):
        """Log demonstration event"""
        
        if demo_id not in self.active_demonstrations:
            return
        
        demo = self.active_demonstrations[demo_id]
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": event_data,
        }
        
        demo["conversation_log"].append(log_entry)
        
        # Also log system decisions separately
        if event_type in ["quality_assessment", "frustration_analysis", "routing_decision"]:
            demo["system_decisions"].append(log_entry)

    def _generate_demo_summary(self, demo_id: str) -> Dict[str, Any]:
        """Generate summary of demonstration"""
        
        demo = self.active_demonstrations[demo_id]
        
        total_time = (demo.get("end_time", datetime.now()) - demo["start_time"]).total_seconds()
        
        # Count system interventions
        system_interventions = len(demo["system_decisions"])
        
        # Determine if escalation occurred
        escalated = demo.get("escalation_data") is not None
        
        # Get final satisfaction
        final_satisfaction = 8.0  # Default
        if demo.get("final_outcome"):
            final_satisfaction = demo["final_outcome"].get("resolution_result", {}).get("customer_satisfaction", 8.0)
        
        return {
            "scenario_name": demo["scenario"]["name"],
            "total_duration_seconds": total_time,
            "escalated_to_human": escalated,
            "system_interventions": system_interventions,
            "final_customer_satisfaction": final_satisfaction,
            "resolution_method": "human_agent" if escalated else "chatbot",
            "outcome_matched_expectation": True,  # Simplified for demo
            "key_events": [event["event_type"] for event in demo["conversation_log"]],
        }

    def cleanup_completed_demos(self, max_age_hours: int = 24):
        """Clean up old completed demonstrations"""
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        completed_demos = [
            demo_id for demo_id, demo in self.active_demonstrations.items()
            if demo.get("end_time") and demo["end_time"] < cutoff_time
        ]
        
        for demo_id in completed_demos:
            del self.active_demonstrations[demo_id]
        
        return len(completed_demos)


async def main():
    """Main function to demonstrate the orchestrator"""
    orchestrator = DemoOrchestrator()
    
    print("Available demo scenarios:")
    scenarios = orchestrator.list_available_scenarios()
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['name']}: {scenario['description']}")
    
    # Run a sample scenario
    print("\nStarting 'Happy Path - Simple Question' scenario...")
    demo_result = orchestrator.start_demo_scenario("Happy Path - Simple Question")
    print(f"Demo started with ID: {demo_result['demo_id']}")
    print(f"Customer query: {demo_result['customer_query']}")
    
    # Simulate chatbot response
    print("\nSimulating chatbot response...")
    chatbot_result = orchestrator.simulate_chatbot_response(demo_result['demo_id'])
    print(f"Chatbot response: {chatbot_result['chatbot_response']}")
    
    # Simulate quality assessment
    print("\nSimulating quality assessment...")
    quality_result = orchestrator.simulate_quality_assessment(demo_result['demo_id'])
    print(f"Quality assessment: {quality_result['quality_assessment']['decision']}")
    
    # Get demo log
    print("\nGetting complete demo log...")
    log = orchestrator.get_demo_log(demo_result['demo_id'])
    print(f"Demo duration: {log['duration_seconds']:.2f} seconds")
    print(f"Current stage: {log['current_stage']}")


if __name__ == "__main__":
    asyncio.run(main())