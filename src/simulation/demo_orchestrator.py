"""
Demo Orchestrator
Coordinates simulation of customer/chatbot/employee interactions for demonstration purposes
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Any, Optional

from ..core.config import ConfigManager
from ..core.logging import get_logger
from ..core.trace_collector import TraceCollector
from ..interfaces.core.context import ContextProvider
from ..interfaces.core.trace import TraceCollectorInterface
from ..core.context_manager import SQLiteContextProvider
from .employee_simulator import EmployeeSimulator
from .human_customer_simulator import (
    CustomerPersonality,
    CustomerScenario,
    HumanCustomerSimulator,
)
from ..nodes.chatbot_agent import ChatbotAgentNode
from ..nodes.quality_agent import QualityAgentNode
from ..nodes.frustration_agent import FrustrationAgentNode
from ..nodes.mock_automation_agent import MockAutomationAgent
from ..nodes.human_routing_agent import HumanRoutingAgentNode
from ..interfaces.core.state_schema import HybridSystemState


class DemoOrchestrator:
    """Orchestrates demonstration scenarios of the human-in-the-loop system"""

    def __init__(self, config_manager: Optional[ConfigManager] = None, context_provider: Optional[ContextProvider] = None, use_real_agents: bool = True, enable_trace_collection: bool = True, trace_collector: Optional[TraceCollectorInterface] = None):
        self.logger = get_logger(__name__)
        
        # Initialize config and context systems
        self.config_manager = config_manager or ConfigManager("config")
        self.context_provider = context_provider or SQLiteContextProvider(config_manager=self.config_manager)
        
        # Initialize trace collection
        self.enable_trace_collection = enable_trace_collection
        self.trace_collector = trace_collector or TraceCollector() if enable_trace_collection else None
        
        # Initialize simulators with system integration
        self.customer_simulator = HumanCustomerSimulator()
        self.employee_simulator = EmployeeSimulator()
        
        # Initialize real LLM agents if requested
        self.use_real_agents = use_real_agents
        if self.use_real_agents:
            self._initialize_real_agents()
        
        # Track active demonstrations and scenarios
        self.active_demonstrations = {}
        self.demo_scenarios = self._create_demo_scenarios()

    def _initialize_real_agents(self):
        """Initialize real LLM-powered agents"""
        try:
            self.chatbot_agent = ChatbotAgentNode(self.config_manager, self.context_provider)
            self.quality_agent = QualityAgentNode(self.config_manager, self.context_provider)
            self.frustration_agent = FrustrationAgentNode(self.config_manager, self.context_provider)
            self.automation_agent = MockAutomationAgent(self.config_manager, self.context_provider)
            self.human_routing_agent = HumanRoutingAgentNode(self.config_manager, self.context_provider)
            
            self.logger.info("Real LLM agents initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize real agents: {e}")
            self.use_real_agents = False
            self.chatbot_agent = None
            self.quality_agent = None
            self.frustration_agent = None
            self.automation_agent = None
            self.human_routing_agent = None

    def _create_demo_scenarios(self) -> list[dict[str, Any]]:
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
            {
                "name": "Automation - Balance Inquiry",
                "description": "Simple balance inquiry that can be handled by automation",
                "customer_personality": CustomerPersonality.POLITE,
                "customer_scenario": CustomerScenario.SIMPLE_QUESTION,
                "initial_frustration": 0,
                "expected_outcome": "resolved_by_automation",
                "chatbot_quality": "high",
                "automation_eligible": True,
            },
        ]

        return scenarios

    def start_demo_scenario(self, scenario_name: str = None) -> dict[str, Any]:
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
        
        # Override query for automation scenarios
        if scenario.get("automation_eligible", False):
            automation_queries = [
                "What's my account balance?",
                "How much do I owe on my policy?", 
                "What's my current premium amount?",
                "Can you tell me my policy number?",
                "What are your business hours?",
                "What's your customer service phone number?",
                "What's the status of my claim?"
            ]
            customer_interaction["initial_query"] = random.choice(automation_queries)

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

        # Start trace collection if enabled
        if self.trace_collector:
            initial_query_data = {
                "query_text": customer_interaction["initial_query"],
                "customer_personality": customer_interaction["personality"],
                "frustration_level": customer_interaction["initial_frustration_level"],
                "scenario": customer_interaction["scenario"],
                "scenario_name": scenario["name"]
            }
            trace_id = self.trace_collector.start_trace(
                session_id=demo_id,
                user_id=f"demo_customer_{demo_id}",
                query_id=f"{demo_id}_query",
                initial_query=initial_query_data
            )
            demo_session["trace_id"] = trace_id

        # Log initial customer query and save to context
        event_data = {
            "query": customer_interaction["initial_query"],
            "customer_state": {
                "personality": customer_interaction["personality"],
                "frustration_level": customer_interaction["initial_frustration_level"],
                "scenario": customer_interaction["scenario"],
            }
        }
        self._log_demo_event(demo_id, "customer_query", event_data)
        self._save_to_context(demo_id, "customer_query", event_data)

        return {
            "demo_id": demo_id,
            "scenario": scenario,
            "customer_query": customer_interaction["initial_query"],
            "customer_context": customer_interaction,
            "next_step": "chatbot_response",
        }

    def simulate_chatbot_response(self, demo_id: str) -> dict[str, Any]:
        """Generate chatbot response using real LLM agent or simulation"""

        if demo_id not in self.active_demonstrations:
            raise ValueError(f"Demo {demo_id} not found")

        demo = self.active_demonstrations[demo_id]
        scenario = demo["scenario"]
        customer_interaction = demo["customer_interaction"]

        if self.use_real_agents and self.chatbot_agent:
            # Use real LLM chatbot agent
            chatbot_response = self._generate_real_chatbot_response(
                customer_interaction["initial_query"],
                demo_id,
                customer_interaction
            )
        else:
            # Fallback to simulated response
            chatbot_response = self._generate_simulated_chatbot_response(
                customer_interaction["initial_query"],
                scenario["chatbot_quality"],
                customer_interaction["personality"]
            )

        demo["chatbot_responses"].append(chatbot_response)
        demo["current_stage"] = "chatbot_responded"

        response_data = {
            "response": chatbot_response["response"],
            "quality_level": scenario.get("chatbot_quality", "unknown"),
            "confidence": chatbot_response.get("confidence", 0.0),
        }
        self._log_demo_event(demo_id, "chatbot_response", response_data)
        self._save_to_context(demo_id, "chatbot_response", response_data)
        
        # Record workflow stage
        self._record_workflow_stage_trace(demo_id, "chatbot_response_complete")

        return {
            "demo_id": demo_id,
            "chatbot_response": chatbot_response["response"],
            "response_metadata": chatbot_response,
            "next_step": "quality_assessment",
        }

    def simulate_quality_assessment(self, demo_id: str) -> dict[str, Any]:
        """Perform quality assessment using real LLM agent or simulation"""

        demo = self.active_demonstrations[demo_id]
        scenario = demo["scenario"]
        chatbot_response = demo["chatbot_responses"][-1]
        customer_interaction = demo["customer_interaction"]

        if self.use_real_agents and self.quality_agent:
            # Use real LLM quality agent
            quality_assessment = self._perform_real_quality_assessment(
                customer_interaction["initial_query"],
                chatbot_response["response"],
                demo_id
            )
        else:
            # Fallback to simulated assessment
            quality_assessment = self._simulate_quality_agent_decision(
                customer_interaction["initial_query"],
                chatbot_response["response"],
                scenario["chatbot_quality"]
            )

        demo["current_stage"] = "quality_assessed"

        self._log_demo_event(demo_id, "quality_assessment", quality_assessment)
        self._save_to_context(demo_id, "quality_assessment", quality_assessment)
        
        # Record workflow stage
        self._record_workflow_stage_trace(demo_id, "quality_assessment_complete")

        return {
            "demo_id": demo_id,
            "quality_assessment": quality_assessment,
            "next_step": quality_assessment.get("next_action", "continue"),
        }

    def simulate_frustration_analysis(self, demo_id: str) -> dict[str, Any]:
        """Perform frustration analysis using real LLM agent or simulation"""

        demo = self.active_demonstrations[demo_id]
        scenario = demo["scenario"]
        customer_interaction = demo["customer_interaction"]
        
        # Record start time for trace
        start_time = datetime.now()

        if self.use_real_agents and self.frustration_agent:
            # Use real LLM frustration agent
            frustration_analysis = self._perform_real_frustration_analysis(
                customer_interaction["initial_query"],
                demo_id
            )
        else:
            # Fallback to simulated analysis
            frustration_analysis = self._simulate_frustration_agent_analysis(
                customer_interaction["initial_query"],
                customer_interaction["initial_frustration_level"],
                customer_interaction["personality"]
            )

        # Record end time and trace the interaction
        end_time = datetime.now()
        
        # Record agent trace
        self._record_agent_trace(
            demo_id=demo_id,
            agent_name="frustration_agent",
            input_data={
                "query": customer_interaction["initial_query"],
                "customer_personality": customer_interaction["personality"],
                "initial_frustration": customer_interaction["initial_frustration_level"]
            },
            output_data=frustration_analysis,
            start_time=start_time,
            end_time=end_time,
            next_action="routing_decision" if frustration_analysis.get("intervention_needed", False) else "continue",
            metadata={
                "agent_type": "real_llm" if self.use_real_agents and self.frustration_agent else "simulated"
            }
        )
        
        # Record system decision if intervention is needed
        if frustration_analysis.get("intervention_needed", False):
            self._record_system_decision_trace(
                demo_id=demo_id,
                decision_point="frustration_intervention",
                decision="escalate_for_frustration",
                reasoning=f"Frustration level {frustration_analysis.get('overall_score', 0)} exceeds threshold",
                factors=frustration_analysis.get("contributing_factors", []),
                confidence=frustration_analysis.get("confidence", None)
            )

        self._log_demo_event(demo_id, "frustration_analysis", frustration_analysis)
        self._save_to_context(demo_id, "frustration_analysis", frustration_analysis)

        return {
            "demo_id": demo_id,
            "frustration_analysis": frustration_analysis,
            "intervention_needed": frustration_analysis.get("intervention_needed", False),
            "next_step": "routing_decision" if frustration_analysis.get("intervention_needed", False) else "respond_to_customer",
        }

    def simulate_automation_check(self, demo_id: str) -> dict[str, Any]:
        """Check if query can be handled by automation and process if eligible"""
        
        demo = self.active_demonstrations[demo_id]
        customer_interaction = demo["customer_interaction"]
        query = customer_interaction["initial_query"]
        
        # Record start time for trace
        start_time = datetime.now()
        
        if self.use_real_agents and self.automation_agent:
            # Use real automation agent to check eligibility
            automation_result = self._perform_real_automation_check(
                query,
                demo_id
            )
        else:
            # Fallback to simulated automation check
            automation_result = self._simulate_automation_check(query)
        
        # Record end time and trace the interaction
        end_time = datetime.now()
        
        # Record agent trace
        self._record_agent_trace(
            demo_id=demo_id,
            agent_name="automation_agent",
            input_data={
                "query": query,
                "customer_personality": customer_interaction["personality"],
            },
            output_data=automation_result,
            start_time=start_time,
            end_time=end_time,
            next_action="automation_response" if automation_result.get("can_handle", False) else "continue_to_chatbot",
            metadata={
                "agent_type": "real_automation" if self.use_real_agents and self.automation_agent else "simulated"
            }
        )
        
        # Record workflow stage
        self._record_workflow_stage_trace(demo_id, "automation_agent_complete", end_time)
        
        demo["current_stage"] = "automation_checked"
        
        self._log_demo_event(demo_id, "automation_check", automation_result)
        self._save_to_context(demo_id, "automation_check", automation_result)
        
        return {
            "demo_id": demo_id,
            "automation_result": automation_result,
            "can_handle": automation_result.get("can_handle", False),
            "next_step": "automation_response" if automation_result.get("can_handle", False) else "continue_to_chatbot",
        }

    def simulate_automation_response(self, demo_id: str) -> dict[str, Any]:
        """Generate automated response for eligible queries"""
        
        demo = self.active_demonstrations[demo_id]
        customer_interaction = demo["customer_interaction"]
        query = customer_interaction["initial_query"]
        
        # Record start time for trace
        start_time = datetime.now()
        
        if self.use_real_agents and self.automation_agent:
            # Use real automation agent to generate response
            automation_response = self._generate_real_automation_response(
                query,
                demo_id
            )
        else:
            # Fallback to simulated automation response
            automation_response = self._generate_simulated_automation_response(query)
        
        # Record end time and trace the interaction
        end_time = datetime.now()
        
        # Record agent trace
        self._record_agent_trace(
            demo_id=demo_id,
            agent_name="automation_response",
            input_data={
                "query": query,
            },
            output_data=automation_response,
            start_time=start_time,
            end_time=end_time,
            next_action="complete",
            metadata={
                "agent_type": "real_automation" if self.use_real_agents and self.automation_agent else "simulated"
            }
        )
        
        demo["current_stage"] = "automation_completed"
        demo["automation_response"] = automation_response
        
        self._log_demo_event(demo_id, "automation_response", automation_response)
        self._save_to_context(demo_id, "automation_response", automation_response)
        
        # Record workflow stage
        self._record_workflow_stage_trace(demo_id, "automation_response_complete")
        
        return {
            "demo_id": demo_id,
            "automation_response": automation_response,
            "query_resolved": True,
            "next_step": "resolution",
        }

    def simulate_routing_decision(self, demo_id: str) -> dict[str, Any]:
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
        self._save_to_context(demo_id, "routing_decision", routing_decision)

        return {
            "demo_id": demo_id,
            "routing_decision": routing_decision,
            "assigned_employee": routing_decision["assigned_employee"],
            "escalation_message": self._generate_escalation_message(routing_decision),
            "next_step": "human_agent_response",
        }

    def _generate_escalation_message(self, routing_decision: dict[str, Any]) -> str:
        """Generate customer notification message for escalation"""
        if "assigned_employee" in routing_decision:
            employee = routing_decision["assigned_employee"]
            employee_type = employee.get("type", "representative").replace("_", " ")
            return f"Please wait a moment while I connect you to a {employee_type} who can better assist you with your request."
        elif routing_decision.get("status") == "queued":
            wait_time = routing_decision.get("estimated_wait_time", 15)
            return f"I'm connecting you to a human representative. Your estimated wait time is {wait_time} minutes. Thank you for your patience."
        else:
            return "Please hold while I transfer you to a representative who can help resolve your concern."

    def simulate_human_agent_response(self, demo_id: str) -> dict[str, Any]:
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
        self._save_to_context(demo_id, "human_agent_response", employee_response)

        return {
            "demo_id": demo_id,
            "employee_response": employee_response,
            "next_step": "customer_response_to_human",
        }

    def simulate_customer_response_to_human(self, demo_id: str) -> dict[str, Any]:
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
        self._save_to_context(demo_id, "customer_response_to_human", customer_response)

        return {
            "demo_id": demo_id,
            "customer_response": customer_response,
            "next_step": "resolution",
        }

    def simulate_resolution(self, demo_id: str) -> dict[str, Any]:
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
        self._save_to_context(demo_id, "resolution", resolution_result)
        
        # Finalize trace collection
        outcome_data = {
            "final_resolution": "human_agent" if employee_interaction else "chatbot_direct",
            "customer_satisfaction": resolution_result.get("resolution_result", {}).get("customer_satisfaction", 8.0),
            "resolution_time_minutes": resolution_result.get("resolution_result", {}).get("resolution_time_minutes", 3),
            "case_resolved": resolution_result.get("case_resolved", True),
            "escalation_occurred": employee_interaction is not None
        }
        self._finalize_trace(demo_id, outcome_data)

        return {
            "demo_id": demo_id,
            "resolution_result": resolution_result,
            "demo_completed": True,
            "summary": self._generate_demo_summary(demo_id),
        }

    def get_demo_log(self, demo_id: str) -> dict[str, Any]:
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

    def list_available_scenarios(self) -> list[dict[str, Any]]:
        """List all available demonstration scenarios"""
        return [
            {
                "name": scenario["name"],
                "description": scenario["description"],
                "expected_outcome": scenario["expected_outcome"],
            }
            for scenario in self.demo_scenarios
        ]

    def get_active_demos(self) -> list[str]:
        """Get list of active demonstration IDs"""
        return list(self.active_demonstrations.keys())

    def _generate_real_chatbot_response(
        self, query: str, demo_id: str, customer_interaction: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate chatbot response using real LLM agent"""
        try:
            # Create state for the chatbot agent
            state = HybridSystemState(
                query_id=f"{demo_id}_chatbot",
                query=query,
                session_id=demo_id,
                user_id=f"demo_customer_{demo_id}",
                timestamp=datetime.now(),
                conversation_history=[],
                customer_context=customer_interaction
            )
            
            # Call the real chatbot agent
            response_state = self.chatbot_agent(state)
            
            # Extract response and metadata
            ai_response = response_state.get("ai_response", "")
            metadata = response_state.get("response_metadata", {})
            
            return {
                "response": ai_response,
                "confidence": metadata.get("confidence", 0.0),
                "quality_level": "real_llm",
                "response_time": metadata.get("response_time", 0.0),
                "model_used": metadata.get("model_name", "unknown"),
                "metadata": metadata
            }
            
        except Exception as e:
            self.logger.error(f"Real chatbot agent failed: {e}")
            # Fallback to simulation
            return self._generate_simulated_chatbot_response(query, "medium", customer_interaction.get("personality", "polite"))

    def _perform_real_quality_assessment(
        self, query: str, response: str, demo_id: str
    ) -> dict[str, Any]:
        """Perform quality assessment using real LLM agent"""
        try:
            # Create state for the quality agent
            state = HybridSystemState(
                query_id=f"{demo_id}_quality",
                query=query,
                ai_response=response,
                session_id=demo_id,
                user_id=f"demo_customer_{demo_id}",
                timestamp=datetime.now()
            )
            
            # Call the real quality agent
            assessment_state = self.quality_agent(state)
            
            # Extract quality assessment
            quality_assessment = assessment_state.get("quality_assessment", {})
            
            return {
                "decision": quality_assessment.get("decision", "adequate"),
                "overall_score": quality_assessment.get("overall_score", 7.0),
                "confidence": quality_assessment.get("confidence", 0.0),
                "reasoning": quality_assessment.get("reasoning", "LLM assessment"),
                "next_action": assessment_state.get("next_action", "respond_to_customer")
            }
            
        except Exception as e:
            self.logger.error(f"Real quality agent failed: {e}")
            # Fallback to simulation
            return self._simulate_quality_agent_decision(query, response, "medium")

    def _perform_real_frustration_analysis(
        self, query: str, demo_id: str
    ) -> dict[str, Any]:
        """Perform frustration analysis using real LLM agent"""
        try:
            # Create state for the frustration agent
            state = HybridSystemState(
                query_id=f"{demo_id}_frustration",
                query=query,
                session_id=demo_id,
                user_id=f"demo_customer_{demo_id}",
                timestamp=datetime.now()
            )
            
            # Call the real frustration agent
            analysis_state = self.frustration_agent(state)
            
            # Extract frustration analysis
            frustration_analysis = analysis_state.get("frustration_analysis", {})
            
            return {
                "overall_score": frustration_analysis.get("overall_score", 0.0),
                "overall_level": frustration_analysis.get("overall_level", "low"),
                "confidence": frustration_analysis.get("confidence", 0.0),
                "intervention_needed": analysis_state.get("escalate_for_frustration", False),
                "contributing_factors": frustration_analysis.get("contributing_factors", ["llm_analysis"])
            }
            
        except Exception as e:
            self.logger.error(f"Real frustration agent failed: {e}")
            # Fallback to simulation
            return {"overall_score": 0.0, "overall_level": "low", "confidence": 0.0, "intervention_needed": False}

    def _perform_real_automation_check(self, query: str, demo_id: str) -> dict[str, Any]:
        """Check if query can be handled by automation using real agent"""
        try:
            # Create state for the automation agent
            state = HybridSystemState(
                query_id=f"{demo_id}_automation_check",
                query=query,
                session_id=demo_id,
                user_id=f"demo_customer_{demo_id}",
                timestamp=datetime.now()
            )
            
            # Call the real automation agent to check eligibility
            result_state = self.automation_agent(state)
            
            # Extract automation result
            automation_result = result_state.get("automation_result", {})
            
            return {
                "can_handle": automation_result.get("can_handle", False),
                "task_type": automation_result.get("task_type", "unknown"),
                "confidence": automation_result.get("confidence", 0.0),
                "reasoning": automation_result.get("reasoning", "Real automation agent assessment")
            }
            
        except Exception as e:
            self.logger.error(f"Real automation agent failed: {e}")
            # Fallback to simulation
            return self._simulate_automation_check(query)

    def _generate_real_automation_response(self, query: str, demo_id: str) -> dict[str, Any]:
        """Generate automated response using real agent"""
        try:
            # Create state for the automation agent
            state = HybridSystemState(
                query_id=f"{demo_id}_automation_response",
                query=query,
                session_id=demo_id,
                user_id=f"demo_customer_{demo_id}",
                timestamp=datetime.now()
            )
            
            # Call the real automation agent to generate response
            result_state = self.automation_agent(state)
            
            # Extract automation response
            automation_response = result_state.get("automation_response", {})
            
            return {
                "response": automation_response.get("response", "I was able to process your request automatically."),
                "data": automation_response.get("data", {}),
                "response_time": automation_response.get("response_time", 0.5),
                "success": automation_response.get("success", True)
            }
            
        except Exception as e:
            self.logger.error(f"Real automation response failed: {e}")
            # Fallback to simulation
            return self._generate_simulated_automation_response(query)

    def _simulate_automation_check(self, query: str) -> dict[str, Any]:
        """Simulate automation eligibility check"""
        query_lower = query.lower()
        
        # Simple rules for automation eligibility
        automation_keywords = [
            "balance", "account balance", "how much do i owe", "payment due",
            "policy number", "coverage details", "claim status", "premium",
            "deductible", "phone number", "hours", "business hours", "contact"
        ]
        
        can_handle = any(keyword in query_lower for keyword in automation_keywords)
        
        if can_handle:
            # Determine task type based on keywords
            if any(word in query_lower for word in ["balance", "owe", "payment", "premium"]):
                task_type = "account_balance"
            elif any(word in query_lower for word in ["policy", "coverage", "deductible"]):
                task_type = "policy_lookup"
            elif any(word in query_lower for word in ["claim", "status"]):
                task_type = "claim_status"
            elif any(word in query_lower for word in ["hours", "contact", "phone"]):
                task_type = "business_info"
            else:
                task_type = "general_info"
            
            confidence = random.uniform(0.8, 0.95)
        else:
            task_type = "complex_query"
            confidence = random.uniform(0.1, 0.3)
        
        return {
            "can_handle": can_handle,
            "task_type": task_type,
            "confidence": confidence,
            "reasoning": f"Query classified as {task_type} with {confidence:.2f} confidence"
        }

    def _generate_simulated_automation_response(self, query: str) -> dict[str, Any]:
        """Generate simulated automated response"""
        query_lower = query.lower()
        
        # Generate appropriate response based on query type
        if any(word in query_lower for word in ["balance", "owe", "payment", "premium"]):
            response = "Your current account balance is $247.50. Your next payment of $89.25 is due on March 15th."
            data = {"balance": 247.50, "next_payment": 89.25, "due_date": "2025-03-15"}
        elif any(word in query_lower for word in ["policy", "coverage", "deductible"]):
            response = "Your policy #INS-789456 includes comprehensive coverage with a $500 deductible."
            data = {"policy_number": "INS-789456", "deductible": 500, "coverage": "comprehensive"}
        elif any(word in query_lower for word in ["claim", "status"]):
            response = "Your claim #CLM-123456 is currently being processed. Expected completion: 5-7 business days."
            data = {"claim_number": "CLM-123456", "status": "processing", "eta": "5-7 days"}
        elif any(word in query_lower for word in ["hours", "business hours", "contact", "phone"]):
            response = "Our customer service hours are Monday-Friday 8AM-8PM EST. You can reach us at 1-800-555-0123."
            data = {"hours": "Mon-Fri 8AM-8PM EST", "phone": "1-800-555-0123"}
        else:
            response = "I was able to process your request. Here's the information you requested."
            data = {"general_info": True}
        
        return {
            "response": response,
            "data": data,
            "response_time": random.uniform(0.2, 0.8),
            "success": True
        }

    def _generate_simulated_chatbot_response(
        self, query: str, quality_level: str, personality: str
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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
        self, customer_interaction: dict[str, Any], expected_outcome: str
    ) -> dict[str, Any]:
        """Simulate routing agent decision"""

        # Get available employees (this now uses the integrated database)
        employees = self.employee_simulator.get_employee_status()
        available_employees = [emp for emp in employees if emp["availability"] == "available"]

        if not available_employees:
            return {
                "status": "queued",
                "estimated_wait_time": 15,
                "queue_position": 3,
            }

        # Select appropriate employee based on expected outcome and specializations
        selected = None
        
        if "technical_specialist" in expected_outcome:
            selected = next((emp for emp in available_employees if "technical" in emp["type"].lower()), None)
        elif "billing_specialist" in expected_outcome:
            selected = next((emp for emp in available_employees if "billing" in emp["type"].lower()), None)
        elif "manager" in expected_outcome:
            selected = next((emp for emp in available_employees if "manager" in emp["type"].lower()), None)
        
        # Fallback to first available if no specific match
        if not selected and available_employees:
            selected = available_employees[0]
        
        if not selected:
            return {
                "status": "no_agents_available",
                "estimated_wait_time": 30,
                "queue_position": 5,
            }

        return {
            "assigned_employee": selected,
            "routing_strategy": "skill_based",
            "match_score": random.uniform(85, 95),
            "routing_confidence": random.uniform(0.8, 0.9),
            "estimated_resolution_time": random.randint(15, 45),
            "escalation_reason": "Quality/Frustration threshold exceeded",
        }

    def _log_demo_event(self, demo_id: str, event_type: str, event_data: dict[str, Any]):
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

    def _save_to_context(self, demo_id: str, event_type: str, event_data: dict[str, Any]):
        """Save demonstration event to context provider"""
        if not self.context_provider:
            return
            
        try:
            from ..interfaces.core.context import ContextEntry
            
            # Create context entry
            entry = ContextEntry(
                entry_id=f"{demo_id}_{event_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                user_id=f"demo_customer_{demo_id}",
                session_id=demo_id,
                timestamp=datetime.now(),
                entry_type=f"demo_{event_type}",
                content=str(event_data),
                metadata={
                    "demo_id": demo_id,
                    "event_type": event_type,
                    "simulation": True,
                    **event_data
                }
            )
            
            # Save to context (async call)
            if hasattr(self.context_provider, 'save_context_entry'):
                self.context_provider.save_context_entry(entry)
                
        except Exception as e:
            self.logger.warning(f"Could not save demo event to context: {e}")

    def _generate_demo_summary(self, demo_id: str) -> dict[str, Any]:
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

    def _record_agent_trace(self, demo_id: str, agent_name: str, input_data: dict[str, Any], output_data: dict[str, Any], start_time: datetime, end_time: datetime, next_action: str = "", metadata: Optional[dict[str, Any]] = None) -> None:
        """Record agent interaction in trace if trace collection is enabled"""
        if not self.trace_collector:
            return
        
        demo = self.active_demonstrations.get(demo_id)
        if not demo or "trace_id" not in demo:
            return
        
        try:
            self.trace_collector.record_agent_interaction(
                trace_id=demo["trace_id"],
                agent_name=agent_name,
                input_data=input_data,
                output_data=output_data,
                start_time=start_time,
                end_time=end_time,
                metadata=metadata or {},
                next_action=next_action
            )
        except Exception as e:
            self.logger.warning(f"Failed to record agent trace for {agent_name}: {e}")

    def _record_system_decision_trace(self, demo_id: str, decision_point: str, decision: str, reasoning: str, factors: Optional[list[str]] = None, confidence: Optional[float] = None) -> None:
        """Record system decision in trace if trace collection is enabled"""
        if not self.trace_collector:
            return
        
        demo = self.active_demonstrations.get(demo_id)
        if not demo or "trace_id" not in demo:
            return
        
        try:
            self.trace_collector.record_system_decision(
                trace_id=demo["trace_id"],
                decision_point=decision_point,
                decision=decision,
                reasoning=reasoning,
                factors=factors,
                confidence=confidence
            )
        except Exception as e:
            self.logger.warning(f"Failed to record system decision trace: {e}")

    def _record_workflow_stage_trace(self, demo_id: str, stage: str, timestamp: Optional[datetime] = None) -> None:
        """Record workflow stage in trace if trace collection is enabled"""
        if not self.trace_collector:
            return
        
        demo = self.active_demonstrations.get(demo_id)
        if not demo or "trace_id" not in demo:
            return
        
        try:
            self.trace_collector.record_workflow_stage(
                trace_id=demo["trace_id"],
                stage=stage,
                timestamp=timestamp
            )
        except Exception as e:
            self.logger.warning(f"Failed to record workflow stage trace: {e}")

    def _finalize_trace(self, demo_id: str, outcome: dict[str, Any]) -> None:
        """Finalize trace if trace collection is enabled"""
        if not self.trace_collector:
            return
        
        demo = self.active_demonstrations.get(demo_id)
        if not demo or "trace_id" not in demo:
            return
        
        try:
            trace = self.trace_collector.finalize_trace(
                trace_id=demo["trace_id"],
                outcome=outcome
            )
            demo["final_trace"] = trace
        except Exception as e:
            self.logger.warning(f"Failed to finalize trace: {e}")

    def export_demo_trace(self, demo_id: str, format: str = "detailed_json", output_file: Optional[str] = None) -> str:
        """Export trace for a specific demo
        
        Args:
            demo_id: Demo to export trace for
            format: Export format ('detailed_json', 'summary_json', 'csv_timeline', 'performance_only')
            output_file: Optional file path to write results
            
        Returns:
            Formatted trace data as string
        """
        if not self.trace_collector:
            return json.dumps({"error": "Trace collection not enabled"})
        
        demo = self.active_demonstrations.get(demo_id)
        if not demo or "trace_id" not in demo:
            return json.dumps({"error": f"Demo {demo_id} not found or has no trace"})
        
        try:
            from ..interfaces.core.trace import OutputFormat
            
            # Map string format to enum
            format_mapping = {
                "detailed_json": OutputFormat.DETAILED_JSON,
                "summary_json": OutputFormat.SUMMARY_JSON, 
                "csv_timeline": OutputFormat.CSV_TIMELINE,
                "performance_only": OutputFormat.PERFORMANCE_ONLY
            }
            
            output_format = format_mapping.get(format, OutputFormat.DETAILED_JSON)
            
            result = self.trace_collector.export_trace(demo["trace_id"], output_format)
            
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                self.logger.info(f"Demo trace exported to {output_file}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to export demo trace: {e}")
            return json.dumps({"error": f"Export failed: {str(e)}"})


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
