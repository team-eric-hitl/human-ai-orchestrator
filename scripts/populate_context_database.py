#!/usr/bin/env python3
"""
Populate the context database with mock insurance data
Provides realistic scenarios that the context manager can retrieve and provide
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List
import random

from src.core.context_manager import SQLiteContextProvider
from src.interfaces.core.context import ContextEntry

# Common insurance queries and successful resolutions
INSURANCE_SCENARIOS = [
    {
        "category": "claim_filing",
        "query": "How do I file a claim for my car accident?",
        "resolution": "Successfully guided customer through online claim filing process. Steps: 1) Log into member portal, 2) Navigate to 'File New Claim', 3) Select 'Auto Claim', 4) Upload photos and police report, 5) Submit for review. Claim #AC-2023-45678 created. Estimated processing time: 3-5 business days.",
        "metadata": {
            "resolution_time_minutes": 8,
            "escalated": False,
            "satisfaction_score": 9.2,
            "tags": ["auto_insurance", "claim_filing", "self_service"]
        }
    },
    {
        "category": "policy_questions",
        "query": "What's covered under my homeowner's policy for water damage?",
        "resolution": "Reviewed customer's policy #HO-8834567. Water damage coverage includes: sudden/accidental water damage (burst pipes, appliance leaks), but excludes flood damage and gradual leaks. Customer's policy includes $50k water damage coverage with $500 deductible. Recommended adding flood insurance for complete protection.",
        "metadata": {
            "resolution_time_minutes": 12,
            "escalated": False,
            "satisfaction_score": 8.7,
            "tags": ["home_insurance", "coverage_inquiry", "water_damage"]
        }
    },
    {
        "category": "billing_payment",
        "query": "Why did my premium increase this month?",
        "resolution": "Premium increase due to recent claim filing and general rate adjustment in customer's zip code. Breakdown: Base premium $845/month, claim surcharge +$67/month (temporary, 36 months), area rate adjustment +$23/month. Suggested defensive driving course for 5% discount. Customer enrolled in course online.",
        "metadata": {
            "resolution_time_minutes": 15,
            "escalated": False,
            "satisfaction_score": 7.8,
            "tags": ["billing", "premium_increase", "rate_explanation"]
        }
    },
    {
        "category": "claim_status",
        "query": "What's the status of my claim #AC-2023-44291?",
        "resolution": "Claim status updated to 'Under Review - Adjuster Assigned'. Adjuster Jennifer Martinez will contact customer within 24 hours to schedule vehicle inspection. All required documents received. Estimated settlement timeline: 7-10 business days after inspection. Customer provided direct contact for adjuster.",
        "metadata": {
            "resolution_time_minutes": 5,
            "escalated": False,
            "satisfaction_score": 9.5,
            "tags": ["claim_status", "auto_insurance", "adjuster_assignment"]
        }
    },
    {
        "category": "policy_changes",
        "query": "I want to add my teenager to my auto policy",
        "resolution": "Added 16-year-old driver to policy #AU-7723456. Required information collected: Driver's license number, completion of driver's ed course (10% discount applied), good student status verified (additional 5% discount). Monthly premium increase: +$156. Coverage matches parent's limits. Policy effective immediately.",
        "metadata": {
            "resolution_time_minutes": 18,
            "escalated": False,
            "satisfaction_score": 8.9,
            "tags": ["policy_modification", "teen_driver", "auto_insurance"]
        }
    },
    {
        "category": "complex_claim",
        "query": "My claim was denied and I don't understand why",
        "resolution": "Escalated to senior claims specialist. Denial reason: Damage occurred outside policy coverage period (lapse in coverage 3/15-3/22). However, discovered system error in payment processing that caused lapse. Overturned denial, reinstated coverage retroactively, approved claim #HO-2023-78945 for $12,400. Customer extremely satisfied with resolution.",
        "metadata": {
            "resolution_time_minutes": 45,
            "escalated": True,
            "satisfaction_score": 9.8,
            "escalation_reason": "claim_denial_dispute",
            "tags": ["claim_denial", "coverage_dispute", "system_error"]
        }
    },
    {
        "category": "discount_eligibility",
        "query": "What discounts am I eligible for?",
        "resolution": "Customer audit revealed multiple eligible discounts: Multi-policy (auto+home): 15% applied, Safe driver (5+ years no claims): 10% applied, Electronic billing: 2% applied, Anti-theft device: 5% applied. Total monthly savings: $89. Customer also qualified for loyalty discount starting next renewal cycle.",
        "metadata": {
            "resolution_time_minutes": 22,
            "escalated": False,
            "satisfaction_score": 9.4,
            "tags": ["discounts", "policy_optimization", "customer_savings"]
        }
    },
    {
        "category": "coverage_recommendation",
        "query": "Do I have enough life insurance coverage?",
        "resolution": "Conducted coverage needs analysis. Current coverage: $250k term life. Recommended: $450k based on income replacement (10x annual salary), debt obligations ($180k mortgage), children's education costs ($120k), final expenses ($15k). Provided quotes for additional $200k term policy. Customer scheduled follow-up with agent.",
        "metadata": {
            "resolution_time_minutes": 35,
            "escalated": False,
            "satisfaction_score": 8.6,
            "tags": ["life_insurance", "coverage_analysis", "needs_assessment"]
        }
    },
    {
        "category": "emergency_assistance",
        "query": "I'm stranded on the highway, can you help?",
        "resolution": "Emergency roadside assistance dispatched immediately. Tow truck en route to I-95 Exit 23 (ETA: 25 minutes). Service covered under comprehensive plan at no charge. Provided tow truck company contact (Atlantic Towing: 555-0142) and service ticket #RSA-78234. Customer reached safely to repair shop.",
        "metadata": {
            "resolution_time_minutes": 7,
            "escalated": False,
            "satisfaction_score": 9.7,
            "tags": ["roadside_assistance", "emergency_service", "towing"]
        }
    },
    {
        "category": "fraud_prevention",
        "query": "Someone called claiming to be from your company asking for my policy info",
        "resolution": "Confirmed fraudulent call attempt - company never requests sensitive info via unsolicited calls. Customer's policy secured with additional verification required. Added fraud alert to account. Provided official company contact numbers. Reported attempted fraud to security team (Case #FRAUD-2023-3421). Customer educated on verification procedures.",
        "metadata": {
            "resolution_time_minutes": 16,
            "escalated": False,
            "satisfaction_score": 9.1,
            "tags": ["fraud_prevention", "security", "customer_protection"]
        }
    }
]

# Additional knowledge base entries
KNOWLEDGE_BASE_ENTRIES = [
    {
        "entry_type": "resolution",
        "content": "For water damage claims, customers must report within 72 hours for optimal coverage. Document everything with photos, stop additional damage if possible, and keep receipts for emergency repairs. Standard deductible applies unless otherwise specified in policy.",
        "metadata": {
            "topic": "water_damage_claims",
            "effectiveness_score": 8.9,
            "usage_count": 234
        }
    },
    {
        "entry_type": "resolution", 
        "content": "Teen drivers can reduce premiums through: defensive driving courses (10% discount), good student discounts (3.0+ GPA, 5-15% discount), driver monitoring apps (up to 20% discount), and limiting usage to school/work only (10-15% discount).",
        "metadata": {
            "topic": "teen_driver_discounts",
            "effectiveness_score": 9.2,
            "usage_count": 156
        }
    },
    {
        "entry_type": "resolution",
        "content": "Claim processing times: Simple auto claims (5-7 days), complex auto claims (10-14 days), property claims (7-21 days), total loss claims (14-30 days). Delays typically due to investigation requirements, third-party coordination, or incomplete documentation.",
        "metadata": {
            "topic": "claim_processing_times",
            "effectiveness_score": 8.7,
            "usage_count": 298
        }
    },
    {
        "entry_type": "response",
        "content": "I understand you're frustrated with the claim process. Let me look into your specific case immediately and connect you with a specialist who can expedite your claim and provide clear timeline expectations.",
        "metadata": {
            "sentiment": "frustrated_customer",
            "effectiveness_score": 9.3,
            "de_escalation": True
        }
    },
    {
        "entry_type": "response",
        "content": "For policy questions, I can review your specific coverage right now. Let me pull up your policy details and explain exactly what's covered, what's excluded, and any available options to enhance your protection.",
        "metadata": {
            "topic": "policy_coverage_inquiry", 
            "effectiveness_score": 8.8,
            "personalization": True
        }
    }
]

def create_mock_users() -> List[Dict]:
    """Create diverse mock user profiles"""
    return [
        {
            "user_id": "user_001_power",
            "profile": "power_user",
            "interaction_count": 25,
            "escalation_rate": 0.12,
            "preferred_topics": ["policy_changes", "coverage_optimization", "discounts"],
            "behavior": "detail_oriented"
        },
        {
            "user_id": "user_002_new", 
            "profile": "new_customer",
            "interaction_count": 3,
            "escalation_rate": 0.33,
            "preferred_topics": ["basic_coverage", "billing_questions", "how_to_guides"],
            "behavior": "needs_guidance"
        },
        {
            "user_id": "user_003_claim",
            "profile": "frequent_claimant",
            "interaction_count": 18,
            "escalation_rate": 0.22,
            "preferred_topics": ["claim_status", "claim_filing", "repair_process"],
            "behavior": "results_focused"
        },
        {
            "user_id": "user_004_business",
            "profile": "business_customer",
            "interaction_count": 31,
            "escalation_rate": 0.06,
            "preferred_topics": ["commercial_coverage", "liability", "business_protection"],
            "behavior": "efficiency_focused"
        },
        {
            "user_id": "user_005_senior",
            "profile": "senior_customer",
            "interaction_count": 12,
            "escalation_rate": 0.08,
            "preferred_topics": ["life_insurance", "medicare_supplement", "retirement_planning"],
            "behavior": "cautious_methodical"
        }
    ]

def generate_user_history(user_data: Dict, scenarios: List[Dict]) -> List[ContextEntry]:
    """Generate realistic interaction history for a user"""
    entries = []
    user_id = user_data["user_id"]
    
    # Generate multiple sessions
    num_sessions = random.randint(3, 8)
    
    for session_num in range(num_sessions):
        session_id = f"session_{user_id}_{session_num:03d}"
        
        # Generate interactions within each session
        interactions_in_session = random.randint(1, 4)
        session_start = datetime.now() - timedelta(days=random.randint(1, 90))
        
        for interaction_num in range(interactions_in_session):
            timestamp = session_start + timedelta(minutes=interaction_num * random.randint(2, 10))
            
            # Choose scenario based on user preferences
            relevant_scenarios = [s for s in scenarios if any(topic in s["category"] for topic in user_data["preferred_topics"])]
            if not relevant_scenarios:
                relevant_scenarios = scenarios
                
            scenario = random.choice(relevant_scenarios)
            
            # Query entry
            query_entry = ContextEntry(
                entry_id=f"query_{uuid.uuid4()}",
                user_id=user_id,
                session_id=session_id,
                timestamp=timestamp,
                entry_type="query",
                content=scenario["query"],
                metadata={
                    "category": scenario["category"],
                    "user_profile": user_data["profile"],
                    "interaction_number": len(entries) + 1
                }
            )
            entries.append(query_entry)
            
            # Response entry
            response_entry = ContextEntry(
                entry_id=f"response_{uuid.uuid4()}",
                user_id=user_id,
                session_id=session_id,
                timestamp=timestamp + timedelta(minutes=random.randint(1, 3)),
                entry_type="response",
                content=scenario["resolution"],
                metadata=scenario["metadata"]
            )
            entries.append(response_entry)
            
            # Possibly add escalation entry
            if scenario["metadata"].get("escalated", False):
                escalation_entry = ContextEntry(
                    entry_id=f"escalation_{uuid.uuid4()}",
                    user_id=user_id,
                    session_id=session_id,
                    timestamp=timestamp + timedelta(minutes=random.randint(5, 15)),
                    entry_type="escalation",
                    content=f"Escalated: {scenario['query']}",
                    metadata={
                        "escalation_reason": scenario["metadata"].get("escalation_reason", "customer_request"),
                        "original_query": scenario["query"],
                        "resolution_time_minutes": scenario["metadata"]["resolution_time_minutes"]
                    }
                )
                entries.append(escalation_entry)
    
    return entries

def add_knowledge_base_entries() -> List[ContextEntry]:
    """Add knowledge base entries with system-wide context"""
    entries = []
    
    for i, kb_entry in enumerate(KNOWLEDGE_BASE_ENTRIES):
        entry = ContextEntry(
            entry_id=f"kb_{uuid.uuid4()}",
            user_id="system",
            session_id="knowledge_base",
            timestamp=datetime.now() - timedelta(days=random.randint(30, 365)),
            entry_type=kb_entry["entry_type"],
            content=kb_entry["content"],
            metadata=kb_entry["metadata"]
        )
        entries.append(entry)
    
    return entries

def populate_database(clear_existing: bool = False):
    """Populate the context database with realistic insurance data"""
    
    # Initialize context provider
    context_provider = SQLiteContextProvider()
    
    if clear_existing:
        print("Clearing existing context data...")
        # This would require adding a clear method to the context provider
        # For now, we'll just add to existing data
    
    print("Creating mock user profiles...")
    users = create_mock_users()
    
    print("Generating user interaction history...")
    all_entries = []
    
    # Generate entries for each user
    for user_data in users:
        user_entries = generate_user_history(user_data, INSURANCE_SCENARIOS)
        all_entries.extend(user_entries)
        print(f"Generated {len(user_entries)} entries for {user_data['user_id']} ({user_data['profile']})")
    
    # Add knowledge base entries
    print("Adding knowledge base entries...")
    kb_entries = add_knowledge_base_entries()
    all_entries.extend(kb_entries)
    print(f"Added {len(kb_entries)} knowledge base entries")
    
    # Save all entries to database
    print("Saving entries to database...")
    successful_saves = 0
    failed_saves = 0
    
    for entry in all_entries:
        if context_provider.save_context_entry(entry):
            successful_saves += 1
        else:
            failed_saves += 1
    
    print(f"\n✅ Database population complete!")
    print(f"📊 Summary:")
    print(f"   - Total entries created: {len(all_entries)}")
    print(f"   - Successfully saved: {successful_saves}")
    print(f"   - Failed saves: {failed_saves}")
    print(f"   - User profiles: {len(users)}")
    print(f"   - Insurance scenarios: {len(INSURANCE_SCENARIOS)}")
    print(f"   - Knowledge base entries: {len(kb_entries)}")
    
    # Get some metrics
    metrics = context_provider.get_context_metrics()
    print(f"\n📈 Database Metrics:")
    print(f"   - Total queries: {metrics['total_queries']}")
    print(f"   - Total users: {metrics['total_users']}")
    print(f"   - Total sessions: {metrics['total_sessions']}")
    print(f"   - Escalation rate: {metrics['escalation_rate']:.1%}")
    
    return successful_saves, failed_saves

if __name__ == "__main__":
    print("🔧 Populating Context Database with Insurance Mock Data")
    print("=" * 60)
    
    try:
        success_count, fail_count = populate_database(clear_existing=False)
        
        if fail_count == 0:
            print("\n🎉 All entries saved successfully!")
        else:
            print(f"\n⚠️  {fail_count} entries failed to save")
            
    except Exception as e:
        print(f"\n❌ Error populating database: {e}")
        import traceback
        traceback.print_exc()