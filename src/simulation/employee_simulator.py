"""
Employee Simulator
Simulates human employees (agents) handling escalated customer interactions
"""

import random
from typing import Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum

from ..core.logging import get_logger


class EmployeeType(Enum):
    JUNIOR_SUPPORT = "junior_support"
    SENIOR_SUPPORT = "senior_support"
    TECHNICAL_SPECIALIST = "technical_specialist"
    BILLING_SPECIALIST = "billing_specialist"
    MANAGER = "manager"


class EmployeeSkill(Enum):
    GENERAL_SUPPORT = "general_support"
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT_MANAGEMENT = "account_management"
    CONFLICT_RESOLUTION = "conflict_resolution"
    PRODUCT_EXPERTISE = "product_expertise"


class EmployeePersonality(Enum):
    EMPATHETIC = "empathetic"
    DIRECT = "direct"
    THOROUGH = "thorough"
    EFFICIENT = "efficient"
    PATIENT = "patient"


class EmployeeSimulator:
    """Simulates human employee responses to escalated customer cases"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.employees = self._create_employee_roster()
        self.active_cases = {}
        
    def _create_employee_roster(self) -> List[Dict[str, Any]]:
        """Create a roster of simulated employees"""
        
        employees = [
            {
                "id": "emp_001",
                "name": "Sarah Chen",
                "type": EmployeeType.SENIOR_SUPPORT,
                "personality": EmployeePersonality.EMPATHETIC,
                "skills": [EmployeeSkill.GENERAL_SUPPORT, EmployeeSkill.CONFLICT_RESOLUTION],
                "skill_level": "senior",
                "frustration_tolerance": "high",
                "years_experience": 5,
                "customer_satisfaction": 4.8,
                "avg_resolution_time": 18,  # minutes
                "current_workload": 0,
                "max_concurrent": 4,
                "working_hours": {"start": "09:00", "end": "17:00"},
                "timezone": "PST",
            },
            {
                "id": "emp_002",
                "name": "Marcus Johnson",
                "type": EmployeeType.TECHNICAL_SPECIALIST,
                "personality": EmployeePersonality.THOROUGH,
                "skills": [EmployeeSkill.TECHNICAL, EmployeeSkill.PRODUCT_EXPERTISE],
                "skill_level": "senior", 
                "frustration_tolerance": "medium",
                "years_experience": 7,
                "customer_satisfaction": 4.6,
                "avg_resolution_time": 25,
                "current_workload": 0,
                "max_concurrent": 3,
                "working_hours": {"start": "08:00", "end": "16:00"},
                "timezone": "EST",
            },
            {
                "id": "emp_003",
                "name": "Lisa Rodriguez",
                "type": EmployeeType.BILLING_SPECIALIST,
                "personality": EmployeePersonality.EFFICIENT,
                "skills": [EmployeeSkill.BILLING, EmployeeSkill.ACCOUNT_MANAGEMENT],
                "skill_level": "intermediate",
                "frustration_tolerance": "high",
                "years_experience": 3,
                "customer_satisfaction": 4.5,
                "avg_resolution_time": 15,
                "current_workload": 0,
                "max_concurrent": 5,
                "working_hours": {"start": "10:00", "end": "18:00"},
                "timezone": "PST",
            },
            {
                "id": "emp_004",
                "name": "David Kim",
                "type": EmployeeType.JUNIOR_SUPPORT,
                "personality": EmployeePersonality.PATIENT,
                "skills": [EmployeeSkill.GENERAL_SUPPORT],
                "skill_level": "junior",
                "frustration_tolerance": "medium",
                "years_experience": 1,
                "customer_satisfaction": 4.2,
                "avg_resolution_time": 22,
                "current_workload": 0,
                "max_concurrent": 3,
                "working_hours": {"start": "11:00", "end": "19:00"},
                "timezone": "PST",
            },
            {
                "id": "emp_005",
                "name": "Jennifer Walsh",
                "type": EmployeeType.MANAGER,
                "personality": EmployeePersonality.DIRECT,
                "skills": [EmployeeSkill.CONFLICT_RESOLUTION, EmployeeSkill.GENERAL_SUPPORT, EmployeeSkill.ACCOUNT_MANAGEMENT],
                "skill_level": "senior",
                "frustration_tolerance": "very_high",
                "years_experience": 10,
                "customer_satisfaction": 4.9,
                "avg_resolution_time": 12,
                "current_workload": 0,
                "max_concurrent": 2,
                "working_hours": {"start": "08:00", "end": "17:00"},
                "timezone": "EST",
            },
        ]
        
        return employees
    
    def handle_escalated_case(
        self, 
        assigned_employee_id: str, 
        customer_context: Dict[str, Any],
        escalation_reason: str,
        customer_query: str,
        chatbot_response: str = None
    ) -> Dict[str, Any]:
        """Simulate employee handling an escalated customer case"""
        
        employee = self._get_employee(assigned_employee_id)
        if not employee:
            return self._handle_employee_not_available(customer_context)
        
        # Analyze the case
        case_analysis = self._analyze_case(customer_context, escalation_reason, customer_query)
        
        # Generate employee response based on their characteristics
        employee_response = self._generate_employee_response(
            employee, case_analysis, customer_context, customer_query, chatbot_response
        )
        
        # Calculate resolution metrics
        resolution_metrics = self._calculate_resolution_metrics(employee, case_analysis)
        
        # Update employee workload
        self._update_employee_workload(employee["id"], 1)
        
        case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}"
        self.active_cases[case_id] = {
            "employee_id": assigned_employee_id,
            "customer_context": customer_context,
            "start_time": datetime.now(),
            "case_analysis": case_analysis,
        }
        
        return {
            "case_id": case_id,
            "employee": employee,
            "employee_response": employee_response,
            "resolution_metrics": resolution_metrics,
            "case_analysis": case_analysis,
            "expected_resolution_time": resolution_metrics["estimated_time"],
            "escalation_handled": True,
        }
    
    def continue_conversation(
        self, case_id: str, customer_message: str, customer_frustration: int
    ) -> Dict[str, Any]:
        """Continue conversation between employee and customer"""
        
        if case_id not in self.active_cases:
            return {"error": "Case not found"}
        
        case = self.active_cases[case_id]
        employee = self._get_employee(case["employee_id"])
        
        # Generate follow-up response
        follow_up_response = self._generate_follow_up_response(
            employee, customer_message, customer_frustration, case
        )
        
        # Check if case should be resolved
        should_resolve = self._should_resolve_case(customer_message, customer_frustration, case)
        
        if should_resolve:
            resolution_result = self._resolve_case(case_id)
            return {
                "employee_response": follow_up_response,
                "case_resolved": True,
                "resolution_result": resolution_result,
            }
        
        return {
            "employee_response": follow_up_response,
            "case_resolved": False,
            "conversation_continues": True,
        }
    
    def _get_employee(self, employee_id: str) -> Dict[str, Any]:
        """Get employee by ID"""
        return next((emp for emp in self.employees if emp["id"] == employee_id), None)
    
    def _analyze_case(
        self, customer_context: Dict[str, Any], escalation_reason: str, customer_query: str
    ) -> Dict[str, Any]:
        """Analyze the escalated case"""
        
        # Determine case complexity
        complexity = "low"
        if "technical" in escalation_reason.lower() or "api" in customer_query.lower():
            complexity = "high"
        elif "billing" in escalation_reason.lower() or "frustrated" in escalation_reason.lower():
            complexity = "medium"
        
        # Determine required skills
        required_skills = []
        if "technical" in customer_query.lower() or "api" in customer_query.lower():
            required_skills.append(EmployeeSkill.TECHNICAL)
        if "billing" in customer_query.lower() or "payment" in customer_query.lower():
            required_skills.append(EmployeeSkill.BILLING)
        if "frustrated" in escalation_reason.lower() or "angry" in escalation_reason.lower():
            required_skills.append(EmployeeSkill.CONFLICT_RESOLUTION)
        if not required_skills:
            required_skills.append(EmployeeSkill.GENERAL_SUPPORT)
        
        # Determine urgency
        urgency = "medium"
        if "urgent" in customer_query.lower() or "critical" in customer_query.lower():
            urgency = "high"
        elif customer_context.get("frustration_level", 0) > 7:
            urgency = "high"
        elif customer_context.get("previous_escalations", 0) > 1:
            urgency = "high"
        
        return {
            "complexity": complexity,
            "required_skills": required_skills,
            "urgency": urgency,
            "customer_frustration": customer_context.get("frustration_level", 5),
            "previous_escalations": customer_context.get("previous_escalations", 0),
            "estimated_effort": self._estimate_effort(complexity, required_skills),
        }
    
    def _estimate_effort(self, complexity: str, required_skills: List[EmployeeSkill]) -> str:
        """Estimate effort required for case"""
        
        if complexity == "high" or len(required_skills) > 2:
            return "high"
        elif complexity == "medium" or EmployeeSkill.TECHNICAL in required_skills:
            return "medium"
        else:
            return "low"
    
    def _generate_employee_response(
        self, 
        employee: Dict[str, Any],
        case_analysis: Dict[str, Any],
        customer_context: Dict[str, Any],
        customer_query: str,
        chatbot_response: str = None
    ) -> str:
        """Generate employee response based on their characteristics"""
        
        personality = employee["personality"]
        employee_type = employee["type"]
        
        # Base greeting and acknowledgment
        if personality == EmployeePersonality.EMPATHETIC:
            greeting = f"Hi, I'm {employee['name']} and I'm here to help you today. I can see you've been having some difficulties, and I want to make sure we get this resolved for you."
        elif personality == EmployeePersonality.DIRECT:
            greeting = f"Hello, this is {employee['name']}. I've reviewed your case and I'm ready to help resolve this issue."
        elif personality == EmployeePersonality.PATIENT:
            greeting = f"Hi there, I'm {employee['name']}. I understand this has been frustrating, and I'm going to take all the time needed to work through this with you."
        else:
            greeting = f"Hello, I'm {employee['name']} from the support team. Let me help you with this issue."
        
        # Address escalation reason if customer is frustrated
        if case_analysis["customer_frustration"] > 6:
            if personality == EmployeePersonality.EMPATHETIC:
                empathy = " I sincerely apologize for the frustration you've experienced so far. Your concerns are completely valid, and I'm committed to making this right."
            else:
                empathy = " I apologize for any inconvenience you've experienced. Let's focus on getting this resolved quickly."
            greeting += empathy
        
        # Acknowledge chatbot interaction if present
        if chatbot_response:
            ack_chatbot = " I can see you've already been working with our chatbot. Let me review what's been discussed and take it from here."
            greeting += ack_chatbot
        
        # Provide solution approach based on employee type and case
        if employee_type == EmployeeType.TECHNICAL_SPECIALIST:
            approach = " I'm going to take a detailed look at the technical aspects of this issue and walk you through a comprehensive solution."
        elif employee_type == EmployeeType.BILLING_SPECIALIST:
            approach = " Let me review your account and billing details to resolve this billing concern for you."
        elif employee_type == EmployeeType.MANAGER:
            approach = " As a manager, I have additional tools and authority to resolve this issue. Let me see what options we have available."
        else:
            if case_analysis["complexity"] == "high":
                approach = " This looks like it might need some specialized attention. I may need to coordinate with our technical team, but I'll stay with you throughout the process."
            else:
                approach = " I should be able to help you resolve this directly. Let me work through this step by step."
        
        # Add specific next steps based on the query
        if "technical" in customer_query.lower() or "api" in customer_query.lower():
            next_steps = " First, let me gather some technical details about your setup so I can provide the most accurate solution."
        elif "billing" in customer_query.lower():
            next_steps = " I'm going to review your account details right now to understand exactly what happened with your billing."
        elif "access" in customer_query.lower() or "login" in customer_query.lower():
            next_steps = " Let me check your account status and walk you through getting your access restored."
        else:
            next_steps = " Can you provide me with a few more details about exactly what you're experiencing?"
        
        # Combine all parts
        full_response = greeting + approach + next_steps
        
        # Add personality-specific closing
        if personality == EmployeePersonality.PATIENT:
            full_response += " Please take your time explaining, and don't hesitate to ask if anything isn't clear."
        elif personality == EmployeePersonality.EFFICIENT:
            full_response += " I'll work to get this resolved as quickly as possible while ensuring it's done right."
        elif personality == EmployeePersonality.THOROUGH:
            full_response += " I want to make sure we address not just the immediate issue, but also prevent it from happening again."
        
        return full_response
    
    def _generate_follow_up_response(
        self, 
        employee: Dict[str, Any],
        customer_message: str,
        customer_frustration: int,
        case: Dict[str, Any]
    ) -> str:
        """Generate follow-up response from employee"""
        
        personality = employee["personality"]
        
        # Acknowledge customer message
        if customer_frustration > 7:
            if personality == EmployeePersonality.EMPATHETIC:
                acknowledgment = "I can hear that this is really frustrating for you, and I completely understand. "
            else:
                acknowledgment = "I understand your frustration. "
        elif "thank" in customer_message.lower():
            acknowledgment = "You're very welcome! "
        else:
            acknowledgment = "I see. "
        
        # Generate solution or next step
        if "still not working" in customer_message.lower():
            solution = "Let me try a different approach. I'm going to escalate this internally to get additional technical resources involved."
        elif "question" in customer_message.lower() or "?" in customer_message:
            solution = "Great question. Let me explain that in more detail and make sure it's clear."
        elif "works" in customer_message.lower() or "fixed" in customer_message.lower():
            solution = "Excellent! I'm glad we got that resolved. Let me just confirm everything is working as expected."
        else:
            solution = "Based on what you've shared, let me provide you with the next steps to resolve this."
        
        return acknowledgment + solution
    
    def _calculate_resolution_metrics(
        self, employee: Dict[str, Any], case_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate expected resolution metrics"""
        
        base_time = employee["avg_resolution_time"]
        
        # Adjust for case complexity
        if case_analysis["complexity"] == "high":
            estimated_time = base_time * 1.5
        elif case_analysis["complexity"] == "medium":
            estimated_time = base_time * 1.2
        else:
            estimated_time = base_time
        
        # Adjust for customer frustration
        if case_analysis["customer_frustration"] > 7:
            estimated_time *= 1.3  # Frustrated customers take longer
        
        # Adjust for employee experience
        if employee["skill_level"] == "senior":
            estimated_time *= 0.8
        elif employee["skill_level"] == "junior":
            estimated_time *= 1.4
        
        # Calculate success probability
        success_probability = 0.9  # Base success rate
        
        # Adjust for skill match
        required_skills = case_analysis["required_skills"]
        employee_skills = employee["skills"]
        skill_match = len(set(required_skills) & set(employee_skills)) / len(required_skills)
        success_probability *= (0.7 + 0.3 * skill_match)
        
        # Adjust for employee experience
        success_probability *= (0.8 + 0.2 * (employee["years_experience"] / 10))
        
        return {
            "estimated_time": int(estimated_time),
            "success_probability": min(0.95, success_probability),
            "expected_satisfaction": employee["customer_satisfaction"],
            "escalation_risk": max(0.05, 1 - success_probability),
        }
    
    def _should_resolve_case(
        self, customer_message: str, customer_frustration: int, case: Dict[str, Any]
    ) -> bool:
        """Determine if case should be resolved"""
        
        resolution_indicators = [
            "thank you", "that worked", "perfect", "solved", "fixed", 
            "resolved", "that's great", "excellent"
        ]
        
        if any(indicator in customer_message.lower() for indicator in resolution_indicators):
            return True
        
        # Low frustration after some time suggests resolution
        if customer_frustration < 3 and len(customer_message) < 50:
            return True
        
        # Simple acknowledgments suggest satisfaction
        if customer_message.lower() in ["ok", "okay", "thanks", "got it"]:
            return True
        
        return False
    
    def _resolve_case(self, case_id: str) -> Dict[str, Any]:
        """Resolve the case and calculate final metrics"""
        
        case = self.active_cases[case_id]
        employee = self._get_employee(case["employee_id"])
        
        resolution_time = (datetime.now() - case["start_time"]).total_seconds() / 60  # minutes
        
        # Calculate customer satisfaction (simulated)
        base_satisfaction = employee["customer_satisfaction"]
        complexity_factor = {"low": 0.1, "medium": 0.0, "high": -0.2}[case["case_analysis"]["complexity"]]
        satisfaction = min(5.0, base_satisfaction + complexity_factor + random.uniform(-0.2, 0.2))
        
        # Update employee workload
        self._update_employee_workload(employee["id"], -1)
        
        # Remove from active cases
        del self.active_cases[case_id]
        
        return {
            "resolution_time_minutes": resolution_time,
            "customer_satisfaction": round(satisfaction, 1),
            "case_complexity": case["case_analysis"]["complexity"],
            "employee_performance": "excellent" if satisfaction > 4.5 else "good" if satisfaction > 4.0 else "acceptable",
            "resolution_method": "direct_resolution",
        }
    
    def _update_employee_workload(self, employee_id: str, change: int):
        """Update employee workload"""
        for employee in self.employees:
            if employee["id"] == employee_id:
                employee["current_workload"] = max(0, employee["current_workload"] + change)
                break
    
    def _handle_employee_not_available(self, customer_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle case when assigned employee is not available"""
        return {
            "error": "Employee not available",
            "escalation_handled": False,
            "recommendation": "Queue for next available agent or escalate to manager",
            "estimated_wait_time": 15,  # minutes
        }
    
    def get_employee_status(self) -> List[Dict[str, Any]]:
        """Get current status of all employees"""
        return [
            {
                "id": emp["id"],
                "name": emp["name"],
                "type": emp["type"].value,
                "current_workload": emp["current_workload"],
                "max_concurrent": emp["max_concurrent"],
                "availability": "available" if emp["current_workload"] < emp["max_concurrent"] else "busy",
                "utilization": emp["current_workload"] / emp["max_concurrent"],
            }
            for emp in self.employees
        ]
    
    def get_active_cases_summary(self) -> Dict[str, Any]:
        """Get summary of active cases"""
        return {
            "total_active_cases": len(self.active_cases),
            "cases_by_employee": {
                emp["id"]: len([case for case in self.active_cases.values() if case["employee_id"] == emp["id"]])
                for emp in self.employees
            },
            "average_case_duration": sum(
                (datetime.now() - case["start_time"]).total_seconds() / 60
                for case in self.active_cases.values()
            ) / max(len(self.active_cases), 1),
        }