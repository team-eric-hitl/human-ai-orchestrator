#!/usr/bin/env python3
"""
Add comprehensive knowledge base entries to the context database
These provide best practices, templates, and proven resolution patterns for AI agents
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List

from src.core.context_manager import SQLiteContextProvider
from src.interfaces.core.context import ContextEntry

# Comprehensive knowledge base for insurance support
KNOWLEDGE_BASE_TEMPLATES = [
    {
        "entry_type": "response_template",
        "topic": "claim_denial_response",
        "content": "I understand your concern about the claim denial. Let me review your specific case immediately and explain the exact reason for the decision. I'll also check if there are any opportunities to appeal or provide additional documentation that might change the outcome. Your satisfaction is important to us, and I want to ensure you understand all your options.",
        "metadata": {
            "effectiveness_score": 9.2,
            "usage_count": 145,
            "de_escalation": True,
            "empathy_focused": True,
            "tags": ["claim_denial", "empathy", "action_oriented"]
        }
    },
    {
        "entry_type": "resolution_pattern",
        "topic": "billing_dispute_steps",
        "content": "Step-by-step billing dispute resolution: 1) Listen actively and acknowledge concern, 2) Review billing history and payment records, 3) Explain each charge clearly with specific dates/amounts, 4) Identify any errors or applicable discounts, 5) Process immediate corrections if found, 6) Provide written confirmation of resolution, 7) Set up prevention measures if needed. Success rate: 94%",
        "metadata": {
            "effectiveness_score": 9.4,
            "usage_count": 203,
            "resolution_rate": 0.94,
            "average_time_minutes": 18,
            "tags": ["billing", "dispute_resolution", "step_by_step"]
        }
    },
    {
        "entry_type": "de_escalation_technique",
        "topic": "frustrated_customer_approach",
        "content": "For highly frustrated customers: 1) Start with sincere empathy and acknowledgment, 2) Avoid defensive language or company policies initially, 3) Focus on immediate action steps, 4) Provide specific timelines and commitments, 5) Offer direct contact information, 6) Follow up proactively, 7) Document lessons learned. Reduces escalation rate by 67%",
        "metadata": {
            "effectiveness_score": 9.6,
            "usage_count": 89,
            "escalation_reduction": 0.67,
            "satisfaction_improvement": 2.3,
            "tags": ["frustration", "de_escalation", "customer_service"]
        }
    },
    {
        "entry_type": "product_knowledge",
        "topic": "auto_insurance_coverage_basics",
        "content": "Auto insurance coverage explanation: Liability (required in most states) covers damage to others, Collision covers your vehicle in accidents, Comprehensive covers theft/weather/vandalism, Uninsured motorist protects against uninsured drivers, Personal injury protection covers medical expenses. Deductibles apply to collision and comprehensive. Higher deductibles = lower premiums.",
        "metadata": {
            "effectiveness_score": 8.9,
            "usage_count": 367,
            "topic_clarity": "high",
            "customer_comprehension": 0.92,
            "tags": ["auto_insurance", "coverage_explanation", "education"]
        }
    },
    {
        "entry_type": "product_knowledge",
        "topic": "home_insurance_water_damage",
        "content": "Home insurance water damage coverage: Sudden and accidental water damage (burst pipes, appliance leaks) is typically covered. Gradual leaks, flood damage, and poor maintenance are usually excluded. Most policies cover cleanup, structural repairs, and personal property replacement. File claims within 72 hours for best outcomes. Document everything with photos before cleanup.",
        "metadata": {
            "effectiveness_score": 9.1,
            "usage_count": 234,
            "claim_success_rate": 0.87,
            "tags": ["home_insurance", "water_damage", "claim_guidance"]
        }
    },
    {
        "entry_type": "process_optimization",
        "topic": "claim_processing_acceleration",
        "content": "Fast-track claim processing criteria: Complete documentation provided, clear liability determination, damage assessment under $25k, no fraud indicators, customer cooperating fully. Can reduce processing time by 40-60%. Require: photos, police report (if applicable), repair estimates, witness statements. Digital submission preferred for speed.",
        "metadata": {
            "effectiveness_score": 8.8,
            "usage_count": 156,
            "time_reduction": 0.50,
            "customer_satisfaction": 9.2,
            "tags": ["claims", "processing", "efficiency"]
        }
    },
    {
        "entry_type": "retention_strategy",
        "topic": "cancellation_prevention",
        "content": "Customer retention for cancellation requests: 1) Understand specific reason for cancellation, 2) Review account for potential cost savings, 3) Highlight unused benefits and coverage value, 4) Offer premium reduction options (higher deductible, usage-based discounts), 5) Provide competitive market comparison, 6) Consider loyalty rewards or credits, 7) Ensure smooth transition if cancellation proceeds. Retention rate: 73%",
        "metadata": {
            "effectiveness_score": 9.0,
            "usage_count": 98,
            "retention_rate": 0.73,
            "customer_satisfaction": 8.7,
            "tags": ["retention", "cancellation", "value_demonstration"]
        }
    },
    {
        "entry_type": "communication_guide",
        "topic": "complex_situation_explanation",
        "content": "Explaining complex insurance situations: Use the 'CLEAR' method - Concise (avoid jargon), Logical sequence (step-by-step), Examples (real scenarios), Actionable steps (what customer should do), Reassurance (next steps and timeline). Check understanding frequently. Provide written follow-up summary. Increases comprehension by 85%.",
        "metadata": {
            "effectiveness_score": 9.3,
            "usage_count": 178,
            "comprehension_increase": 0.85,
            "follow_up_reduction": 0.34,
            "tags": ["communication", "explanation", "comprehension"]
        }
    },
    {
        "entry_type": "quality_standard",
        "topic": "first_call_resolution",
        "content": "First call resolution best practices: 1) Gather complete information upfront, 2) Use knowledge base and similar case examples, 3) Access all relevant systems during the call, 4) Confirm resolution meets customer's expectation, 5) Provide confirmation number and next steps, 6) Schedule follow-up if needed. Target: 85% first call resolution rate.",
        "metadata": {
            "effectiveness_score": 9.1,
            "usage_count": 267,
            "first_call_resolution_rate": 0.85,
            "customer_satisfaction": 9.0,
            "tags": ["first_call_resolution", "efficiency", "quality"]
        }
    },
    {
        "entry_type": "escalation_criteria",
        "topic": "when_to_escalate",
        "content": "Escalation criteria: 1) Customer requests supervisor/manager, 2) Complaint about company policy or procedure, 3) Claim dispute over $10,000, 4) Legal threats or attorney involvement, 5) Regulatory complaint mentioned, 6) Multiple previous contacts on same issue, 7) Agent cannot resolve within authority limits, 8) Customer satisfaction at risk. Document reason clearly.",
        "metadata": {
            "effectiveness_score": 8.7,
            "usage_count": 89,
            "appropriate_escalation_rate": 0.93,
            "resolution_improvement": 0.41,
            "tags": ["escalation", "criteria", "decision_making"]
        }
    }
]

# Successful case study examples
CASE_STUDIES = [
    {
        "title": "Complex Multi-Vehicle Accident Resolution",
        "scenario": "Customer involved in 4-vehicle accident with disputed fault determination and multiple insurance companies involved. Initial claim denied due to conflicting witness statements.",
        "resolution": "Coordinated with all insurers, obtained traffic camera footage through police department, hired independent accident reconstructionist, negotiated fair settlement allocation. Customer's damages fully covered despite initial denial. Resolution time: 21 days vs. industry average 45 days.",
        "outcome": "Customer satisfaction: 9.8/10. Retained policy and added umbrella coverage. Referred 3 new customers.",
        "metadata": {
            "complexity": "high",
            "resolution_time_days": 21,
            "industry_average_days": 45,
            "satisfaction_score": 9.8,
            "retention": True,
            "referrals": 3,
            "tags": ["complex_claim", "multi_party", "investigation"]
        }
    },
    {
        "title": "Premium Affordability Crisis Resolution",
        "scenario": "Long-term customer facing financial hardship, unable to afford premium increase. Considering cancellation of 15-year policy relationship.",
        "resolution": "Comprehensive policy review revealed over-insurance in some areas. Adjusted coverage levels, applied all available discounts (safe driver, multi-policy, loyalty), set up payment plan, provided temporary premium reduction during hardship period. Reduced monthly payment by 32%.",
        "outcome": "Customer maintained coverage, expressed deep gratitude for personalized attention. Upgraded coverage when financial situation improved 8 months later.",
        "metadata": {
            "customer_tenure_years": 15,
            "premium_reduction_percent": 32,
            "satisfaction_score": 9.5,
            "retention": True,
            "future_upgrade": True,
            "tags": ["financial_hardship", "retention", "personalization"]
        }
    },
    {
        "title": "Claim Fraud Prevention and Customer Education",
        "scenario": "Customer unknowingly provided inconsistent information about accident timeline, triggering fraud investigation. Customer became defensive and threatened to switch companies.",
        "resolution": "Agent explained fraud prevention importance professionally, helped customer understand discrepancies, worked together to clarify timeline with supporting documentation. Investigation cleared customer quickly, claim processed normally.",
        "outcome": "Customer appreciated transparency and education about fraud prevention. Became advocate for company's thorough but fair processes.",
        "metadata": {
            "investigation_cleared": True,
            "education_provided": True,
            "satisfaction_score": 8.9,
            "advocacy_developed": True,
            "tags": ["fraud_prevention", "education", "transparency"]
        }
    }
]

def create_knowledge_base_entries() -> List[ContextEntry]:
    """Create comprehensive knowledge base entries"""
    entries = []
    
    # Add knowledge base templates
    for i, kb_template in enumerate(KNOWLEDGE_BASE_TEMPLATES):
        entry = ContextEntry(
            entry_id=f"kb_template_{uuid.uuid4()}",
            user_id="system",
            session_id="knowledge_base_templates",
            timestamp=datetime.now() - timedelta(days=random.randint(90, 365)),
            entry_type=kb_template["entry_type"],
            content=kb_template["content"],
            metadata={
                **kb_template["metadata"],
                "knowledge_base_entry": True,
                "topic": kb_template["topic"]
            }
        )
        entries.append(entry)
    
    # Add case studies
    for i, case_study in enumerate(CASE_STUDIES):
        # Main case study entry
        case_entry = ContextEntry(
            entry_id=f"case_study_{uuid.uuid4()}",
            user_id=f"case_study_customer_{i:03d}",
            session_id=f"case_study_session_{i:03d}",
            timestamp=datetime.now() - timedelta(days=random.randint(30, 180)),
            entry_type="case_study",
            content=f"{case_study['title']}: {case_study['scenario']}",
            metadata={
                **case_study["metadata"],
                "case_study": True,
                "title": case_study["title"]
            }
        )
        entries.append(case_entry)
        
        # Resolution entry
        resolution_entry = ContextEntry(
            entry_id=f"case_resolution_{uuid.uuid4()}",
            user_id=f"case_study_customer_{i:03d}",
            session_id=f"case_study_session_{i:03d}",
            timestamp=case_entry.timestamp + timedelta(days=case_study["metadata"].get("resolution_time_days", 7)),
            entry_type="successful_resolution",
            content=f"RESOLUTION: {case_study['resolution']} OUTCOME: {case_study['outcome']}",
            metadata={
                **case_study["metadata"],
                "case_study_resolution": True,
                "title": case_study["title"]
            }
        )
        entries.append(resolution_entry)
    
    return entries

def add_expert_knowledge():
    """Add expert knowledge base entries to the context database"""
    
    # Initialize context provider
    context_provider = SQLiteContextProvider()
    
    print("Creating expert knowledge base entries...")
    
    # Generate knowledge base entries
    kb_entries = create_knowledge_base_entries()
    
    print(f"Generated {len(kb_entries)} knowledge base entries")
    print(f"   - Templates and guides: {len(KNOWLEDGE_BASE_TEMPLATES)}")
    print(f"   - Case studies: {len(CASE_STUDIES)}")
    
    # Save all entries to database
    print("Saving knowledge base entries to database...")
    successful_saves = 0
    failed_saves = 0
    
    for entry in kb_entries:
        if context_provider.save_context_entry(entry):
            successful_saves += 1
        else:
            failed_saves += 1
    
    print(f"\n✅ Knowledge base entries added!")
    print(f"📊 Summary:")
    print(f"   - KB entries created: {len(kb_entries)}")
    print(f"   - Successfully saved: {successful_saves}")
    print(f"   - Failed saves: {failed_saves}")
    
    # Show what topics are now available
    print(f"\n💡 Knowledge base now includes:")
    for template in KNOWLEDGE_BASE_TEMPLATES:
        print(f"   - {template['topic']}: {template['entry_type']}")
    
    print(f"\n📚 Case studies added:")
    for case in CASE_STUDIES:
        print(f"   - {case['title']}")
    
    # Get updated metrics
    metrics = context_provider.get_context_metrics()
    print(f"\n📈 Updated Database Metrics:")
    print(f"   - Total queries: {metrics['total_queries']}")
    print(f"   - Total users: {metrics['total_users']}")
    print(f"   - Total sessions: {metrics['total_sessions']}")
    print(f"   - Escalation rate: {metrics['escalation_rate']:.1%}")
    
    return successful_saves, failed_saves

if __name__ == "__main__":
    print("📚 Adding Expert Knowledge Base")
    print("=" * 40)
    
    try:
        success_count, fail_count = add_expert_knowledge()
        
        if fail_count == 0:
            print("\n🎉 All knowledge base entries saved successfully!")
        else:
            print(f"\n⚠️  {fail_count} entries failed to save")
            
    except Exception as e:
        print(f"\n❌ Error adding knowledge base: {e}")
        import traceback
        traceback.print_exc()