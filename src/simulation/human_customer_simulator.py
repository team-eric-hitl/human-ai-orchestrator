"""
Human Customer Simulator
Simulates various types of customer interactions for testing the system
"""

import random
from typing import Dict, List, Any
from datetime import datetime
from enum import Enum

from ..core.logging import get_logger


class CustomerPersonality(Enum):
    POLITE = "polite"
    IMPATIENT = "impatient"
    TECHNICAL = "technical"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    BUSINESS = "business"


class CustomerScenario(Enum):
    SIMPLE_QUESTION = "simple_question"
    TECHNICAL_ISSUE = "technical_issue"
    BILLING_PROBLEM = "billing_problem"
    ACCOUNT_ACCESS = "account_access"
    COMPLEX_INTEGRATION = "complex_integration"
    REPEAT_ISSUE = "repeat_issue"
    ESCALATION_REQUEST = "escalation_request"


class HumanCustomerSimulator:
    """Simulates human customer interactions with various personalities and scenarios"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.conversation_history = []
        self.current_personality = None
        self.current_scenario = None
        self.frustration_level = 0  # 0-10 scale
        
    def create_customer_interaction(
        self, 
        personality: CustomerPersonality = None,
        scenario: CustomerScenario = None,
        frustration_level: int = None
    ) -> Dict[str, Any]:
        """Create a simulated customer interaction"""
        
        # Randomize if not specified
        if personality is None:
            personality = random.choice(list(CustomerPersonality))
        if scenario is None:
            scenario = random.choice(list(CustomerScenario))
        if frustration_level is None:
            frustration_level = random.randint(0, 3)  # Most customers start with low frustration
            
        self.current_personality = personality
        self.current_scenario = scenario
        self.frustration_level = frustration_level
        
        # Generate initial query
        initial_query = self._generate_initial_query(personality, scenario, frustration_level)
        
        interaction = {
            "customer_id": f"sim_customer_{random.randint(1000, 9999)}",
            "session_id": f"sim_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "personality": personality.value,
            "scenario": scenario.value,
            "initial_frustration_level": frustration_level,
            "initial_query": initial_query,
            "conversation_context": self._get_conversation_context(scenario),
            "expected_escalation": self._should_escalate(personality, scenario, frustration_level),
            "customer_goals": self._get_customer_goals(scenario),
        }
        
        self.conversation_history.append(interaction)
        return interaction
    
    def respond_to_chatbot(self, chatbot_response: str, current_interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Generate customer response to chatbot message"""
        
        # Analyze chatbot response quality from customer perspective
        response_quality = self._analyze_response_quality(chatbot_response, current_interaction)
        
        # Update frustration level based on response
        frustration_change = self._calculate_frustration_change(response_quality, current_interaction)
        self.frustration_level = max(0, min(10, self.frustration_level + frustration_change))
        
        # Generate customer response
        customer_response = self._generate_customer_response(
            chatbot_response, current_interaction, response_quality
        )
        
        # Determine if customer wants to escalate
        wants_escalation = self._wants_escalation(current_interaction, response_quality)
        
        return {
            "customer_response": customer_response,
            "updated_frustration_level": self.frustration_level,
            "satisfaction_with_response": response_quality["satisfaction_score"],
            "wants_escalation": wants_escalation,
            "conversation_should_continue": not self._is_satisfied(response_quality),
            "frustration_change": frustration_change,
        }
    
    def _generate_initial_query(
        self, personality: CustomerPersonality, scenario: CustomerScenario, frustration: int
    ) -> str:
        """Generate initial customer query based on personality and scenario"""
        
        # Base queries by scenario
        base_queries = {
            CustomerScenario.SIMPLE_QUESTION: [
                "How do I reset my password?",
                "What are your business hours?",
                "How do I update my billing information?",
                "Can you explain your pricing plans?",
            ],
            CustomerScenario.TECHNICAL_ISSUE: [
                "I'm having trouble with the API integration",
                "The webhook isn't working properly",
                "I'm getting a 500 error when making requests",
                "The authentication system seems to be down",
            ],
            CustomerScenario.BILLING_PROBLEM: [
                "I was charged twice this month",
                "My subscription seems to have the wrong plan",
                "I need to update my payment method",
                "Can you explain this charge on my bill?",
            ],
            CustomerScenario.ACCOUNT_ACCESS: [
                "I can't log into my account",
                "I think my account has been suspended",
                "I need to add users to my organization",
                "How do I change my account permissions?",
            ],
            CustomerScenario.COMPLEX_INTEGRATION: [
                "I need help setting up SSO for my enterprise account",
                "How do I configure real-time data sync between systems?",
                "I need custom reporting for our compliance requirements",
                "Can you help with our multi-tenant setup?",
            ],
            CustomerScenario.REPEAT_ISSUE: [
                "I'm still having the same problem I contacted you about last week",
                "This issue keeps happening even after your last fix",
                "I've tried everything you suggested but it's not working",
                "Why does this keep breaking?",
            ],
            CustomerScenario.ESCALATION_REQUEST: [
                "I need to speak to a manager about this issue",
                "Can you escalate this to your technical team?",
                "I want to file a formal complaint",
                "This needs immediate attention from someone senior",
            ],
        }
        
        # Select base query
        base_query = random.choice(base_queries[scenario])
        
        # Modify based on personality and frustration level
        query = self._apply_personality_to_query(base_query, personality, frustration)
        
        return query
    
    def _apply_personality_to_query(
        self, base_query: str, personality: CustomerPersonality, frustration: int
    ) -> str:
        """Apply personality traits to the query"""
        
        if personality == CustomerPersonality.POLITE:
            return f"Hello, I hope you can help me. {base_query} Thank you for your time."
        
        elif personality == CustomerPersonality.IMPATIENT:
            urgency_phrases = ["I need this fixed ASAP", "This is urgent", "I need an immediate response"]
            if frustration > 3:
                return f"{base_query} {random.choice(urgency_phrases)}!"
            return f"{base_query} Please respond quickly."
        
        elif personality == CustomerPersonality.TECHNICAL:
            return f"{base_query} I've already checked the documentation and tried basic troubleshooting."
        
        elif personality == CustomerPersonality.FRUSTRATED:
            if frustration > 5:
                return f"This is ridiculous! {base_query} Why is this so complicated?!"
            return f"I'm getting frustrated here. {base_query}"
        
        elif personality == CustomerPersonality.CONFUSED:
            return f"I'm really confused about something. {base_query} Can you explain this in simple terms?"
        
        elif personality == CustomerPersonality.BUSINESS:
            return f"Hello, I'm reaching out regarding a business matter. {base_query} Please advise on the appropriate next steps."
        
        return base_query
    
    def _get_conversation_context(self, scenario: CustomerScenario) -> Dict[str, Any]:
        """Get conversation context for the scenario"""
        
        contexts = {
            CustomerScenario.SIMPLE_QUESTION: {
                "previous_interactions": random.randint(0, 2),
                "account_type": "basic",
                "urgency": "low",
            },
            CustomerScenario.TECHNICAL_ISSUE: {
                "previous_interactions": random.randint(1, 3),
                "account_type": random.choice(["pro", "enterprise"]),
                "urgency": "medium",
                "technical_level": "intermediate",
            },
            CustomerScenario.BILLING_PROBLEM: {
                "previous_interactions": random.randint(0, 1),
                "account_type": random.choice(["basic", "pro"]),
                "urgency": "medium",
                "involves_money": True,
            },
            CustomerScenario.ACCOUNT_ACCESS: {
                "previous_interactions": random.randint(0, 2),
                "account_type": "any",
                "urgency": "high",
                "blocking_work": True,
            },
            CustomerScenario.COMPLEX_INTEGRATION: {
                "previous_interactions": random.randint(2, 5),
                "account_type": "enterprise",
                "urgency": "medium",
                "technical_level": "advanced",
                "requires_specialist": True,
            },
            CustomerScenario.REPEAT_ISSUE: {
                "previous_interactions": random.randint(3, 8),
                "account_type": "any",
                "urgency": "high",
                "previous_escalations": random.randint(1, 2),
                "customer_patience": "low",
            },
            CustomerScenario.ESCALATION_REQUEST: {
                "previous_interactions": random.randint(2, 6),
                "account_type": "any", 
                "urgency": "high",
                "previous_escalations": random.randint(0, 1),
                "explicit_escalation": True,
            },
        }
        
        return contexts.get(scenario, {"previous_interactions": 0, "urgency": "low"})
    
    def _should_escalate(
        self, personality: CustomerPersonality, scenario: CustomerScenario, frustration: int
    ) -> bool:
        """Determine if this interaction should result in escalation"""
        
        escalation_scenarios = [
            CustomerScenario.COMPLEX_INTEGRATION,
            CustomerScenario.REPEAT_ISSUE,
            CustomerScenario.ESCALATION_REQUEST,
        ]
        
        if scenario in escalation_scenarios:
            return True
        
        if frustration > 6:
            return True
        
        if personality == CustomerPersonality.IMPATIENT and frustration > 4:
            return True
        
        return False
    
    def _get_customer_goals(self, scenario: CustomerScenario) -> List[str]:
        """Get customer goals for the scenario"""
        
        goals = {
            CustomerScenario.SIMPLE_QUESTION: ["Get clear answer", "Quick resolution"],
            CustomerScenario.TECHNICAL_ISSUE: ["Fix the problem", "Understand root cause", "Prevent recurrence"],
            CustomerScenario.BILLING_PROBLEM: ["Correct billing", "Understand charges", "Update payment info"],
            CustomerScenario.ACCOUNT_ACCESS: ["Regain access", "Secure account", "Prevent future lockouts"],
            CustomerScenario.COMPLEX_INTEGRATION: ["Complete integration", "Get expert guidance", "Ensure best practices"],
            CustomerScenario.REPEAT_ISSUE: ["Permanent fix", "Escalate to prevent recurrence", "Get explanation"],
            CustomerScenario.ESCALATION_REQUEST: ["Speak to manager", "File complaint", "Get executive attention"],
        }
        
        return goals.get(scenario, ["Resolve issue"])
    
    def _analyze_response_quality(self, response: str, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chatbot response quality from customer perspective"""
        
        quality_score = 7.0  # Base score
        satisfaction_score = 7.0
        
        # Length analysis
        if len(response) < 20:
            quality_score -= 2.0
            satisfaction_score -= 1.5
        elif len(response) > 500:
            quality_score -= 0.5
        
        # Politeness indicators
        polite_phrases = ["thank you", "please", "i understand", "i apologize", "i'm sorry"]
        if any(phrase in response.lower() for phrase in polite_phrases):
            satisfaction_score += 1.0
        
        # Solution indicators
        solution_phrases = ["here's how", "you can", "try this", "step by step", "solution"]
        if any(phrase in response.lower() for phrase in solution_phrases):
            quality_score += 1.5
            satisfaction_score += 1.0
        
        # Empathy indicators
        empathy_phrases = ["understand", "frustration", "sorry", "apologize"]
        if self.current_personality == CustomerPersonality.FRUSTRATED:
            if any(phrase in response.lower() for phrase in empathy_phrases):
                satisfaction_score += 2.0
            else:
                satisfaction_score -= 1.0
        
        # Technical appropriateness
        if self.current_personality == CustomerPersonality.TECHNICAL:
            tech_phrases = ["api", "integration", "configuration", "technical"]
            if any(phrase in response.lower() for phrase in tech_phrases):
                quality_score += 1.0
            elif self.current_scenario in [CustomerScenario.TECHNICAL_ISSUE, CustomerScenario.COMPLEX_INTEGRATION]:
                quality_score -= 1.0
        
        return {
            "quality_score": max(1.0, min(10.0, quality_score)),
            "satisfaction_score": max(1.0, min(10.0, satisfaction_score)),
            "meets_expectations": quality_score >= 6.0,
            "addresses_concern": "solution" in response.lower() or "help" in response.lower(),
        }
    
    def _calculate_frustration_change(
        self, response_quality: Dict[str, Any], interaction: Dict[str, Any]
    ) -> int:
        """Calculate change in frustration level based on response"""
        
        change = 0
        
        # Good responses reduce frustration
        if response_quality["satisfaction_score"] > 8.0:
            change -= 2
        elif response_quality["satisfaction_score"] > 6.0:
            change -= 1
        
        # Poor responses increase frustration
        if response_quality["satisfaction_score"] < 4.0:
            change += 3
        elif response_quality["satisfaction_score"] < 6.0:
            change += 1
        
        # Personality modifiers
        if self.current_personality == CustomerPersonality.IMPATIENT:
            if not response_quality["addresses_concern"]:
                change += 1
        
        if self.current_personality == CustomerPersonality.FRUSTRATED:
            change += 1  # Already frustrated customers escalate faster
        
        return change
    
    def _generate_customer_response(
        self, chatbot_response: str, interaction: Dict[str, Any], quality: Dict[str, Any]
    ) -> str:
        """Generate customer response to chatbot"""
        
        if quality["satisfaction_score"] > 8.0:
            responses = [
                "Perfect, thank you so much for the help!",
                "That's exactly what I needed, thanks!",
                "Great, that solved my problem. I appreciate it!",
            ]
            return random.choice(responses)
        
        elif quality["satisfaction_score"] > 6.0:
            responses = [
                "Thanks, that's helpful. Let me try that.",
                "Okay, I think I understand. Thank you.",
                "That makes sense, I'll give it a try.",
            ]
            return random.choice(responses)
        
        elif quality["satisfaction_score"] > 4.0:
            responses = [
                "I'm still not sure I understand. Can you explain more?",
                "That doesn't quite address my specific issue.",
                "I tried something similar before. Is there another option?",
            ]
            return random.choice(responses)
        
        else:
            if self.frustration_level > 6:
                responses = [
                    "This is not helpful at all! I need to speak to someone else.",
                    "I'm getting more frustrated. Can you escalate this please?",
                    "This isn't working. I want to talk to a human agent.",
                ]
            else:
                responses = [
                    "I don't think this is going to work for my situation.",
                    "I'm still having trouble. Is there someone else who can help?",
                    "This doesn't seem right. Can you double-check?",
                ]
            return random.choice(responses)
    
    def _wants_escalation(self, interaction: Dict[str, Any], quality: Dict[str, Any]) -> bool:
        """Determine if customer wants escalation"""
        
        # Explicit escalation scenarios
        if self.current_scenario == CustomerScenario.ESCALATION_REQUEST:
            return True
        
        # High frustration leads to escalation
        if self.frustration_level > 7:
            return True
        
        # Poor quality responses with impatient customers
        if (self.current_personality == CustomerPersonality.IMPATIENT and 
            quality["satisfaction_score"] < 5.0):
            return True
        
        # Repeat issues with no clear solution
        if (self.current_scenario == CustomerScenario.REPEAT_ISSUE and 
            quality["satisfaction_score"] < 6.0):
            return True
        
        # Complex scenarios that need specialist help
        if (self.current_scenario == CustomerScenario.COMPLEX_INTEGRATION and
            quality["satisfaction_score"] < 7.0):
            return True
        
        return False
    
    def _is_satisfied(self, quality: Dict[str, Any]) -> bool:
        """Determine if customer is satisfied and conversation should end"""
        
        return quality["satisfaction_score"] > 8.0 and quality["meets_expectations"]