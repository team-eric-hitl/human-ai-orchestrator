#!/usr/bin/env python3
"""
Test script for context display functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gradio_demo import format_context_display

# Test the context display formatter with sample data
def test_context_display():
    print("Testing Context Display Functionality")
    print("=" * 50)
    
    # Test with no context
    print("Test 1: No context data")
    result = format_context_display({}, {})
    print(result)
    print()
    
    # Test with context summaries
    print("Test 2: With context summaries")
    context_summaries = {
        "for_ai_agents": "User has 3 recent interactions | Previous escalations | Found 2 similar cases",
        "for_human_agents": "CONTEXT FOR: user_123\nQuery: I'm having trouble with billing\n\nUser Profile:\n- Total interactions: 5\n- Escalation rate: 20.0%\n- Behavior pattern: regular_user",
        "for_quality_assessment": "Quality factors: frequent_user, previous_escalations",
        "for_routing_decision": "Routing considerations: user_pattern:regular_user, billing_issue"
    }
    
    result = format_context_display({}, context_summaries)
    print(result)
    print()
    
    # Test with context data
    print("Test 3: With context data")
    context_data = {
        "user_profile": {
            "total_interactions": 5,
            "escalation_rate": 0.2,
            "user_behavior_pattern": "regular_user"
        },
        "interaction_history": {
            "total_interactions": 3
        },
        "similar_cases": [
            {"similarity_score": 0.85}
        ],
        "product_context": {
            "related_products": ["billing", "api"]
        },
        "knowledge_base": {
            "relevant_entries": [
                {"relevance_score": 0.9}
            ]
        },
        "escalation_history": {
            "total_escalations": 1
        }
    }
    
    result = format_context_display(context_data, context_summaries)
    print(result)
    print()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    test_context_display()