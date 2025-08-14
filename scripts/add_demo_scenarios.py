#!/usr/bin/env python3
"""
Add specific demo scenarios to the context database
These are designed to be found by the context manager during common demo queries
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List

from src.core.context_manager import SQLiteContextProvider
from src.interfaces.core.context import ContextEntry

# Demo-specific scenarios that will be found during common queries
DEMO_SCENARIOS = [
    {
        "demo_query": "My claim was denied",
        "similar_queries": [
            "Why was my claim rejected?",
            "I don't understand my claim denial",
            "My insurance claim got denied and I need help"
        ],
        "successful_resolution": "Claim denial successfully overturned after review. Issue: Initial denial due to missing documentation, but customer had submitted via mobile app with technical glitch. Retrieved documents from app logs, reprocessed claim, approved for $8,750. Customer satisfaction: 9.5/10.",
        "metadata": {
            "resolution_time_minutes": 35,
            "escalated": True,
            "satisfaction_score": 9.5,
            "tags": ["claim_denial", "technical_issue", "successful_appeal"],
            "escalation_reason": "claim_denial_dispute"
        }
    },
    {
        "demo_query": "I can't afford my premium",
        "similar_queries": [
            "My insurance is too expensive",
            "Can I lower my premium payments?",
            "I need cheaper insurance options"
        ],
        "successful_resolution": "Reduced customer's premium by 28% through discount optimization and coverage adjustments. Applied: safe driver discount (12%), multi-policy discount (15%), electronic billing (2%), raised deductible from $250 to $500 (-18% premium). New monthly payment: $127 vs. previous $176. Customer very satisfied with savings.",
        "metadata": {
            "resolution_time_minutes": 22,
            "escalated": False,
            "satisfaction_score": 9.2,
            "tags": ["premium_reduction", "discount_optimization", "financial_assistance"]
        }
    },
    {
        "demo_query": "How long does a claim take?",
        "similar_queries": [
            "What's the status of my claim?",
            "When will my claim be processed?",
            "How long until I get paid for my claim?"
        ],
        "successful_resolution": "Provided detailed claim timeline and expedited processing. Standard timeline: 7-10 business days for straightforward claims. Customer's claim #AC-2024-15678 fast-tracked due to total loss situation. Adjuster assigned same day, inspection scheduled within 48 hours, settlement processed in 4 business days. Customer appreciated proactive communication.",
        "metadata": {
            "resolution_time_minutes": 8,
            "escalated": False,
            "satisfaction_score": 9.0,
            "tags": ["claim_timeline", "expedited_processing", "proactive_service"]
        }
    },
    {
        "demo_query": "I need to file a claim",
        "similar_queries": [
            "How do I report an accident?",
            "I need to start a claim",
            "My car was damaged, what do I do?"
        ],
        "successful_resolution": "Guided customer through streamlined claim filing process. Collected incident details, photos uploaded via mobile app, police report reference obtained, witness contact info recorded. Claim #AC-2024-16789 created and assigned to fast-track queue. Adjuster will contact within 24 hours. Customer felt confident about next steps.",
        "metadata": {
            "resolution_time_minutes": 12,
            "escalated": False,
            "satisfaction_score": 8.8,
            "tags": ["claim_filing", "mobile_app", "customer_guidance"]
        }
    },
    {
        "demo_query": "This is taking too long",
        "similar_queries": [
            "Why is this so slow?",
            "I've been waiting forever",
            "This process is frustrating"
        ],
        "successful_resolution": "Acknowledged customer frustration and provided immediate escalation to priority handling. Identified bottleneck in system processing, manually expedited case, provided senior specialist contact, established daily update schedule. Issue resolved 3 days ahead of standard timeline. Customer expressed appreciation for responsive service.",
        "metadata": {
            "resolution_time_minutes": 18,
            "escalated": True,
            "satisfaction_score": 8.9,
            "tags": ["customer_frustration", "expedited_service", "priority_handling"],
            "escalation_reason": "process_delay_complaint"
        }
    },
    {
        "demo_query": "I want to cancel my policy",
        "similar_queries": [
            "How do I cancel my insurance?",
            "I don't need this coverage anymore",
            "I want to end my policy"
        ],
        "successful_resolution": "Customer retention successful through coverage review and cost reduction. Discovered customer was paying for unnecessary coverage, reduced premium by 35%, updated to more suitable plan, added additional benefits at no cost. Customer decided to maintain policy with new terms. Satisfaction score: 9.3/10.",
        "metadata": {
            "resolution_time_minutes": 28,
            "escalated": False,
            "satisfaction_score": 9.3,
            "tags": ["retention", "policy_optimization", "cost_reduction"]
        }
    }
]

# Additional frustrated customer examples
FRUSTRATION_EXAMPLES = [
    {
        "query": "This is ridiculous, I've called 5 times about the same issue",
        "resolution": "Immediately escalated to senior specialist. Reviewed all previous interactions, identified communication breakdown in claim processing system. Personally handled case end-to-end, provided direct contact number, resolved issue within same business day. Customer received follow-up call to ensure satisfaction.",
        "metadata": {
            "resolution_time_minutes": 45,
            "escalated": True,
            "satisfaction_score": 9.4,
            "initial_frustration_level": "critical",
            "escalation_reason": "repeated_contact_same_issue",
            "tags": ["repeat_caller", "system_breakdown", "personal_attention"]
        }
    },
    {
        "query": "Your customer service is terrible",
        "resolution": "Service recovery initiated immediately. Supervisor personally apologized, conducted full case review, identified service gaps, implemented corrective measures, provided service credit, established priority customer status. Follow-up survey showed customer willing to recommend company to friends.",
        "metadata": {
            "resolution_time_minutes": 52,
            "escalated": True,
            "satisfaction_score": 8.7,
            "initial_frustration_level": "critical",
            "escalation_reason": "service_complaint",
            "tags": ["service_recovery", "supervisor_escalation", "relationship_repair"]
        }
    }
]

def add_demo_context_entries() -> List[ContextEntry]:
    """Create context entries that will be found during demo scenarios"""
    entries = []
    
    # Create entries for main demo scenarios
    for i, scenario in enumerate(DEMO_SCENARIOS):
        demo_user_id = f"demo_user_{i:03d}"
        session_id = f"demo_session_{i:03d}"
        base_timestamp = datetime.now() - timedelta(days=random.randint(7, 45))
        
        # Add the original query
        query_entry = ContextEntry(
            entry_id=f"demo_query_{uuid.uuid4()}",
            user_id=demo_user_id,
            session_id=session_id,
            timestamp=base_timestamp,
            entry_type="query",
            content=scenario["demo_query"],
            metadata={
                "demo_scenario": True,
                "query_type": "primary_demo_query"
            }
        )
        entries.append(query_entry)
        
        # Add successful resolution
        resolution_entry = ContextEntry(
            entry_id=f"demo_resolution_{uuid.uuid4()}",
            user_id=demo_user_id,
            session_id=session_id,
            timestamp=base_timestamp + timedelta(minutes=scenario["metadata"]["resolution_time_minutes"]),
            entry_type="resolution",
            content=scenario["successful_resolution"],
            metadata=scenario["metadata"]
        )
        entries.append(resolution_entry)
        
        # Add similar queries from other users
        for j, similar_query in enumerate(scenario["similar_queries"]):
            similar_user_id = f"similar_user_{i:03d}_{j:02d}"
            similar_session_id = f"similar_session_{i:03d}_{j:02d}"
            similar_timestamp = datetime.now() - timedelta(days=random.randint(1, 30))
            
            similar_query_entry = ContextEntry(
                entry_id=f"similar_query_{uuid.uuid4()}",
                user_id=similar_user_id,
                session_id=similar_session_id,
                timestamp=similar_timestamp,
                entry_type="query",
                content=similar_query,
                metadata={
                    "demo_scenario": True,
                    "similarity_to_demo": True,
                    "primary_demo_query": scenario["demo_query"]
                }
            )
            entries.append(similar_query_entry)
            
            # Add response for similar query
            similar_response_entry = ContextEntry(
                entry_id=f"similar_response_{uuid.uuid4()}",
                user_id=similar_user_id,
                session_id=similar_session_id,
                timestamp=similar_timestamp + timedelta(minutes=random.randint(5, 20)),
                entry_type="response",
                content=f"Similar issue resolved successfully. {scenario['successful_resolution'][:100]}...",
                metadata={
                    "demo_scenario": True,
                    "resolution_time_minutes": random.randint(10, 30),
                    "satisfaction_score": random.uniform(8.0, 9.5)
                }
            )
            entries.append(similar_response_entry)
    
    # Add frustration examples
    for i, frustration_example in enumerate(FRUSTRATION_EXAMPLES):
        frustrated_user_id = f"frustrated_user_{i:03d}"
        frustrated_session_id = f"frustrated_session_{i:03d}"
        frustrated_timestamp = datetime.now() - timedelta(days=random.randint(5, 20))
        
        # Frustrated query
        frustrated_query_entry = ContextEntry(
            entry_id=f"frustrated_query_{uuid.uuid4()}",
            user_id=frustrated_user_id,
            session_id=frustrated_session_id,
            timestamp=frustrated_timestamp,
            entry_type="query",
            content=frustration_example["query"],
            metadata={
                "demo_scenario": True,
                "frustration_example": True,
                "initial_frustration_level": frustration_example["metadata"]["initial_frustration_level"]
            }
        )
        entries.append(frustrated_query_entry)
        
        # Successful resolution of frustration
        resolution_entry = ContextEntry(
            entry_id=f"frustrated_resolution_{uuid.uuid4()}",
            user_id=frustrated_user_id,
            session_id=frustrated_session_id,
            timestamp=frustrated_timestamp + timedelta(minutes=frustration_example["metadata"]["resolution_time_minutes"]),
            entry_type="resolution",
            content=frustration_example["resolution"],
            metadata=frustration_example["metadata"]
        )
        entries.append(resolution_entry)
        
        # Add escalation entry if escalated
        if frustration_example["metadata"]["escalated"]:
            escalation_entry = ContextEntry(
                entry_id=f"frustrated_escalation_{uuid.uuid4()}",
                user_id=frustrated_user_id,
                session_id=frustrated_session_id,
                timestamp=frustrated_timestamp + timedelta(minutes=10),
                entry_type="escalation",
                content=f"Escalated frustrated customer: {frustration_example['query']}",
                metadata={
                    "demo_scenario": True,
                    "escalation_reason": frustration_example["metadata"]["escalation_reason"],
                    "original_frustration_level": frustration_example["metadata"]["initial_frustration_level"],
                    "resolution_time_minutes": frustration_example["metadata"]["resolution_time_minutes"]
                }
            )
            entries.append(escalation_entry)
    
    return entries

def populate_demo_scenarios():
    """Add demo-specific scenarios to the context database"""
    
    # Initialize context provider
    context_provider = SQLiteContextProvider()
    
    print("Creating demo-specific context entries...")
    
    # Generate demo entries
    demo_entries = add_demo_context_entries()
    
    print(f"Generated {len(demo_entries)} demo context entries")
    
    # Save all entries to database
    print("Saving demo entries to database...")
    successful_saves = 0
    failed_saves = 0
    
    for entry in demo_entries:
        if context_provider.save_context_entry(entry):
            successful_saves += 1
        else:
            failed_saves += 1
    
    print(f"\n✅ Demo scenarios added!")
    print(f"📊 Summary:")
    print(f"   - Demo entries created: {len(demo_entries)}")
    print(f"   - Successfully saved: {successful_saves}")
    print(f"   - Failed saves: {failed_saves}")
    print(f"   - Main demo scenarios: {len(DEMO_SCENARIOS)}")
    print(f"   - Frustration examples: {len(FRUSTRATION_EXAMPLES)}")
    
    # Get updated metrics
    metrics = context_provider.get_context_metrics()
    print(f"\n📈 Updated Database Metrics:")
    print(f"   - Total queries: {metrics['total_queries']}")
    print(f"   - Total users: {metrics['total_users']}")
    print(f"   - Total sessions: {metrics['total_sessions']}")
    print(f"   - Escalation rate: {metrics['escalation_rate']:.1%}")
    
    return successful_saves, failed_saves

if __name__ == "__main__":
    print("🎯 Adding Demo-Specific Context Scenarios")
    print("=" * 50)
    
    try:
        success_count, fail_count = populate_demo_scenarios()
        
        if fail_count == 0:
            print("\n🎉 All demo entries saved successfully!")
            print("\n💡 The context manager will now find relevant examples for:")
            for scenario in DEMO_SCENARIOS:
                print(f"   - '{scenario['demo_query']}'")
        else:
            print(f"\n⚠️  {fail_count} entries failed to save")
            
    except Exception as e:
        print(f"\n❌ Error adding demo scenarios: {e}")
        import traceback
        traceback.print_exc()