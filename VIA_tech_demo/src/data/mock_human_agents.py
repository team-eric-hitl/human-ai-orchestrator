"""Mock human agents data for insurance support representatives."""

from datetime import datetime
from typing import List

from ..interfaces.human_agents import HumanAgent, HumanAgentStatus, Specialization, WorkloadMetrics


def create_mock_insurance_agents() -> List[HumanAgent]:
    """Create a list of mock insurance support representatives."""
    
    agents = []
    base_time = datetime.utcnow()
    
    # Senior Claims Specialists
    agents.append(HumanAgent(
        id="agent_001",
        name="Sarah Chen",
        email="sarah.chen@insuranceco.com",
        status=HumanAgentStatus.AVAILABLE,
        specializations=[Specialization.CLAIMS, Specialization.ESCALATION],
        max_concurrent_conversations=5,
        experience_level=5,
        languages=["en", "es"],
        workload=WorkloadMetrics(
            active_conversations=1,
            queue_length=0,
            avg_response_time_minutes=3.2,
            satisfaction_score=9.1,
            stress_level=2.5
        ),
        shift_start="08:00",
        shift_end="17:00",
        metadata={
            "department": "Claims",
            "team": "Complex Claims",
            "certifications": ["CPCU", "AIC"],
            "languages_spoken": "Native English, Fluent Spanish",
            "specialties": "Auto claims, Property damage, Fraud investigation"
        }
    ))
    
    agents.append(HumanAgent(
        id="agent_002", 
        name="Michael Rodriguez",
        email="michael.rodriguez@insuranceco.com",
        status=HumanAgentStatus.AVAILABLE,
        specializations=[Specialization.POLICY, Specialization.BILLING],
        max_concurrent_conversations=4,
        experience_level=4,
        languages=["en", "es"],
        workload=WorkloadMetrics(
            active_conversations=2,
            queue_length=1,
            avg_response_time_minutes=4.8,
            satisfaction_score=8.7,
            stress_level=3.8
        ),
        shift_start="09:00",
        shift_end="18:00",
        metadata={
            "department": "Policy Services",
            "team": "Premium Billing",
            "certifications": ["AINS", "CPCU"],
            "languages_spoken": "Native Spanish, Fluent English",
            "specialties": "Policy modifications, Billing disputes, Payment plans"
        }
    ))
    
    # Mid-level Agents
    agents.append(HumanAgent(
        id="agent_003",
        name="Jennifer Thompson",
        email="jennifer.thompson@insuranceco.com", 
        status=HumanAgentStatus.BUSY,
        specializations=[Specialization.GENERAL, Specialization.CLAIMS],
        max_concurrent_conversations=3,
        experience_level=3,
        languages=["en"],
        workload=WorkloadMetrics(
            active_conversations=3,
            queue_length=2,
            avg_response_time_minutes=5.5,
            satisfaction_score=8.2,
            stress_level=6.2
        ),
        shift_start="07:00",
        shift_end="16:00",
        metadata={
            "department": "Customer Service",
            "team": "General Support",
            "certifications": ["AINS"],
            "languages_spoken": "Native English",
            "specialties": "First Notice of Loss, Basic policy questions, Coverage explanations"
        }
    ))
    
    agents.append(HumanAgent(
        id="agent_004",
        name="David Kim",
        email="david.kim@insuranceco.com",
        status=HumanAgentStatus.AVAILABLE,
        specializations=[Specialization.TECHNICAL, Specialization.GENERAL],
        max_concurrent_conversations=3,
        experience_level=3,
        languages=["en", "ko"],
        workload=WorkloadMetrics(
            active_conversations=1,
            queue_length=0,
            avg_response_time_minutes=6.1,
            satisfaction_score=8.5,
            stress_level=4.1
        ),
        shift_start="10:00",
        shift_end="19:00",
        metadata={
            "department": "Technical Support", 
            "team": "Digital Services",
            "certifications": ["CompTIA A+"],
            "languages_spoken": "Native English, Fluent Korean",
            "specialties": "Mobile app support, Online account issues, Digital claims filing"
        }
    ))
    
    agents.append(HumanAgent(
        id="agent_005",
        name="Lisa Wang",
        email="lisa.wang@insuranceco.com",
        status=HumanAgentStatus.AVAILABLE,
        specializations=[Specialization.BILLING, Specialization.POLICY],
        max_concurrent_conversations=4,
        experience_level=3,
        languages=["en", "zh"],
        workload=WorkloadMetrics(
            active_conversations=1,
            queue_length=0,
            avg_response_time_minutes=4.9,
            satisfaction_score=8.8,
            stress_level=3.2
        ),
        shift_start="11:00", 
        shift_end="20:00",
        metadata={
            "department": "Billing Services",
            "team": "Payment Processing",
            "certifications": ["AINS"],
            "languages_spoken": "Native English, Fluent Mandarin",
            "specialties": "Payment processing, Premium calculations, Refund requests"
        }
    ))
    
    # Junior Level Agents
    agents.append(HumanAgent(
        id="agent_006",
        name="Marcus Johnson",
        email="marcus.johnson@insuranceco.com",
        status=HumanAgentStatus.AVAILABLE,
        specializations=[Specialization.GENERAL],
        max_concurrent_conversations=2,
        experience_level=2,
        languages=["en"],
        workload=WorkloadMetrics(
            active_conversations=0,
            queue_length=0,
            avg_response_time_minutes=7.2,
            satisfaction_score=7.9,
            stress_level=2.1
        ),
        shift_start="08:30",
        shift_end="17:30",
        metadata={
            "department": "Customer Service",
            "team": "New Customer Support",
            "certifications": ["In Progress - AINS"],
            "languages_spoken": "Native English", 
            "specialties": "New policy questions, Basic coverage information, Document requests"
        }
    ))
    
    agents.append(HumanAgent(
        id="agent_007",
        name="Emily Martinez",
        email="emily.martinez@insuranceco.com",
        status=HumanAgentStatus.AVAILABLE,
        specializations=[Specialization.GENERAL, Specialization.CLAIMS],
        max_concurrent_conversations=2,
        experience_level=2,
        languages=["en", "es"],
        workload=WorkloadMetrics(
            active_conversations=1,
            queue_length=0,
            avg_response_time_minutes=8.1,
            satisfaction_score=8.0,
            stress_level=4.5
        ),
        shift_start="12:00",
        shift_end="21:00",
        metadata={
            "department": "Claims",
            "team": "First Notice of Loss",
            "certifications": ["In Progress - AINS"],
            "languages_spoken": "Native Spanish, Fluent English",
            "specialties": "Initial claim intake, Basic claim questions, Document collection"
        }
    ))
    
    # Entry Level Agent
    agents.append(HumanAgent(
        id="agent_008",
        name="Alex Patterson",
        email="alex.patterson@insuranceco.com",
        status=HumanAgentStatus.AVAILABLE,
        specializations=[Specialization.GENERAL],
        max_concurrent_conversations=2,
        experience_level=1,
        languages=["en"],
        workload=WorkloadMetrics(
            active_conversations=0,
            queue_length=0,
            avg_response_time_minutes=9.5,
            satisfaction_score=7.6,
            stress_level=3.8
        ),
        shift_start="13:00",
        shift_end="22:00",
        metadata={
            "department": "Customer Service",
            "team": "General Inquiries",
            "certifications": ["New Hire Training Complete"],
            "languages_spoken": "Native English",
            "specialties": "Basic policy information, Contact updates, General inquiries"
        }
    ))
    
    # Specialist - Currently on Break
    agents.append(HumanAgent(
        id="agent_009",
        name="Dr. Rebecca Foster",
        email="rebecca.foster@insuranceco.com",
        status=HumanAgentStatus.BREAK,
        specializations=[Specialization.ESCALATION, Specialization.CLAIMS],
        max_concurrent_conversations=4,
        experience_level=5,
        languages=["en", "fr"],
        workload=WorkloadMetrics(
            active_conversations=0,
            queue_length=0,
            avg_response_time_minutes=2.8,
            satisfaction_score=9.4,
            stress_level=1.8
        ),
        shift_start="06:00",
        shift_end="15:00",
        metadata={
            "department": "Executive Escalations",
            "team": "Complex Resolution",
            "certifications": ["CPCU", "ARM", "PhD Risk Management"],
            "languages_spoken": "Native English, Fluent French",
            "specialties": "Executive escalations, Complex claims, Regulatory compliance, Legal liaison"
        }
    ))
    
    # Night Shift Supervisor
    agents.append(HumanAgent(
        id="agent_010",
        name="Carlos Mendoza",
        email="carlos.mendoza@insuranceco.com",
        status=HumanAgentStatus.OFFLINE,
        specializations=[Specialization.ESCALATION, Specialization.GENERAL, Specialization.CLAIMS],
        max_concurrent_conversations=5,
        experience_level=4,
        languages=["en", "es"],
        workload=WorkloadMetrics(
            active_conversations=0,
            queue_length=0,
            avg_response_time_minutes=3.9,
            satisfaction_score=8.9,
            stress_level=2.2
        ),
        shift_start="22:00",
        shift_end="07:00",
        metadata={
            "department": "Night Operations",
            "team": "Overnight Support",
            "certifications": ["CPCU", "Leadership Certificate"],
            "languages_spoken": "Native Spanish, Fluent English",
            "specialties": "Night shift supervision, Emergency claims, Escalation management"
        }
    ))
    
    # Update created_at and updated_at timestamps
    for i, agent in enumerate(agents):
        agent.created_at = base_time
        agent.updated_at = base_time
        if agent.status != HumanAgentStatus.OFFLINE:
            agent.last_activity = base_time
    
    return agents


def get_agent_summary_stats() -> dict:
    """Get summary statistics for the mock agents."""
    agents = create_mock_insurance_agents()
    
    total_agents = len(agents)
    available_count = sum(1 for agent in agents if agent.status == HumanAgentStatus.AVAILABLE)
    busy_count = sum(1 for agent in agents if agent.status == HumanAgentStatus.BUSY)
    break_count = sum(1 for agent in agents if agent.status == HumanAgentStatus.BREAK)
    offline_count = sum(1 for agent in agents if agent.status == HumanAgentStatus.OFFLINE)
    
    total_conversations = sum(agent.workload.active_conversations for agent in agents)
    total_capacity = sum(agent.max_concurrent_conversations for agent in agents)
    
    avg_satisfaction = sum(agent.workload.satisfaction_score for agent in agents) / total_agents
    avg_stress = sum(agent.workload.stress_level for agent in agents) / total_agents
    
    specialization_counts = {}
    for agent in agents:
        for spec in agent.specializations:
            spec_value = spec if isinstance(spec, str) else spec.value
            specialization_counts[spec_value] = specialization_counts.get(spec_value, 0) + 1
    
    return {
        "total_agents": total_agents,
        "status_distribution": {
            "available": available_count,
            "busy": busy_count,
            "on_break": break_count,
            "offline": offline_count
        },
        "workload": {
            "total_active_conversations": total_conversations,
            "total_capacity": total_capacity,
            "utilization_percentage": round((total_conversations / total_capacity) * 100, 1)
        },
        "performance": {
            "average_satisfaction_score": round(avg_satisfaction, 2),
            "average_stress_level": round(avg_stress, 2)
        },
        "specialization_distribution": specialization_counts,
        "experience_levels": {
            "junior": sum(1 for agent in agents if agent.experience_level <= 2),
            "mid_level": sum(1 for agent in agents if agent.experience_level == 3),
            "senior": sum(1 for agent in agents if agent.experience_level >= 4)
        },
        "language_support": {
            "english": sum(1 for agent in agents if "en" in agent.languages),
            "spanish": sum(1 for agent in agents if "es" in agent.languages),
            "other": sum(1 for agent in agents if any(lang not in ["en", "es"] for lang in agent.languages))
        }
    }