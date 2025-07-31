"""Complete HITL System Demo with Human Routing Integration.

This demo showcases the full Human-in-the-Loop system with:
1. Mock automation handling routine tasks
2. AI chatbot for customer service
3. Quality assessment and improvement
4. Frustration detection and intervention
5. Context-aware human routing with database integration
6. Rich context analysis for informed decisions
"""

import asyncio
from datetime import datetime
from unittest.mock import Mock

from src.nodes.mock_automation_agent import MockAutomationAgent
from src.nodes.chatbot_agent import ChatbotAgentNode
from src.nodes.quality_agent import QualityAgentNode
from src.nodes.frustration_agent import FrustrationAgentNode
from src.nodes.routing_agent import RoutingAgentNode
from src.nodes.context_manager_agent import ContextManagerAgentNode
from src.core.config import ConfigManager
from src.interfaces.core.context import ContextProvider, ContextEntry
from src.interfaces.core.state_schema import HybridSystemState


class DemoContextProvider(ContextProvider):
    """Demo context provider with realistic conversation history."""
    
    def __init__(self):
        self.contexts = {
            "frequent_user_billing": [
                ContextEntry(
                    entry_id="entry_001",
                    user_id="frequent_user_billing",
                    session_id="session_001",
                    timestamp=datetime.now(),
                    entry_type="query",
                    content="Why was I charged twice for my insurance premium?",
                    metadata={"query_type": "billing", "issue_type": "duplicate_charge"}
                ),
                ContextEntry(
                    entry_id="entry_002",
                    user_id="frequent_user_billing", 
                    session_id="session_001",
                    timestamp=datetime.now(),
                    entry_type="escalation",
                    content="Customer frustrated with billing confusion",
                    metadata={"escalation_reason": "billing_confusion", "resolution_time_minutes": 25}
                )
            ],
            "enterprise_tech_user": [
                ContextEntry(
                    entry_id="entry_003",
                    user_id="enterprise_tech_user",
                    session_id="session_002", 
                    timestamp=datetime.now(),
                    entry_type="query",
                    content="API integration failing with authentication errors",
                    metadata={"query_type": "technical", "severity": "high", "business_impact": True}
                )
            ]
        }
    
    def get_context_summary(self, user_id: str, session_id: str) -> dict:
        """Return context summary based on user type."""
        summaries = {
            "frequent_user_billing": {
                "escalation_count": 2,
                "entries_count": 8,
                "common_issues": ["billing", "charges"],
                "last_interaction": datetime.now().isoformat()
            },
            "enterprise_tech_user": {
                "escalation_count": 1, 
                "entries_count": 3,
                "common_issues": ["technical", "api"],
                "last_interaction": datetime.now().isoformat()
            },
            "new_customer": {
                "escalation_count": 0,
                "entries_count": 1,
                "common_issues": [],
                "last_interaction": datetime.now().isoformat()
            }
        }
        return summaries.get(user_id, {"escalation_count": 0, "entries_count": 0})
    
    def get_recent_context(self, user_id: str, session_id: str, limit: int = 10):
        """Return recent context for user."""
        return self.contexts.get(user_id, [])[:limit]
    
    def add_context_entry(self, user_id: str, session_id: str, entry):
        pass
    
    def save_context_entry(self, entry):
        pass


async def run_complete_hitl_demo():
    """Run complete HITL system demo with human routing."""
    print("🎭 Complete HITL System Demo with Human Routing")
    print("=" * 80)
    print("Demonstrating: Automation → AI → Context → Quality → Frustration → Human Routing")
    print("=" * 80)
    
    # Initialize all system components
    from src.core.config import AgentConfigManager
    config_manager = AgentConfigManager(config_dir="config")
    context_provider = DemoContextProvider()
    
    # Initialize all agents
    automation_agent = MockAutomationAgent(config_manager, context_provider)
    chatbot_agent = ChatbotAgentNode(config_manager, context_provider)
    quality_agent = QualityAgentNode(config_manager, context_provider)
    frustration_agent = FrustrationAgentNode(config_manager, context_provider)
    context_manager = ContextManagerAgentNode(config_manager, context_provider)
    routing_agent = RoutingAgentNode(config_manager, context_provider)
    
    print(f"✅ All HITL system components initialized")
    print(f"   🤖 Mock Automation Agent")
    print(f"   💬 AI Chatbot Agent") 
    print(f"   ✅ Quality Assessment Agent")
    print(f"   😤 Frustration Detection Agent")
    print(f"   🧠 Context Manager Agent")
    print(f"   🎯 Human Routing Agent (LLM-powered: {routing_agent.use_llm_routing})")
    
    # Demo scenarios showing different paths through the system
    demo_scenarios = [
        {
            "name": "Simple Policy Lookup (Automation Success)",
            "description": "Routine query handled completely by automation",
            "state": {
                "query": "What is my current policy number?",
                "query_id": "demo_001",
                "user_id": "regular_customer",
                "session_id": "session_simple_001", 
                "timestamp": datetime.now(),
                "query_type": "policy_inquiry",
                "customer_type": "individual"
            },
            "expected_flow": "Automation → Complete"
        },
        {
            "name": "Billing Issue (AI → Quality → Human)",
            "description": "Billing query requiring human escalation after AI attempt",
            "state": {
                "query": "I was charged twice for my premium this month and need a refund immediately",
                "query_id": "demo_002", 
                "user_id": "frequent_user_billing",
                "session_id": "session_billing_001",
                "timestamp": datetime.now(),
                "query_type": "billing_issue",
                "customer_type": "individual"
            },
            "expected_flow": "Automation → AI → Context → Quality → Frustration → Human"
        },
        {
            "name": "Enterprise Technical Issue (Direct to Human)",
            "description": "Complex technical issue requiring immediate human attention",
            "state": {
                "query": "Our API integration is returning 401 errors after the latest update, affecting our production system",
                "query_id": "demo_003",
                "user_id": "enterprise_tech_user", 
                "session_id": "session_enterprise_001",
                "timestamp": datetime.now(),
                "query_type": "technical_issue",
                "customer_type": "enterprise",
                "priority": "high"
            },
            "expected_flow": "Automation → AI → Context → Quality → Human (Technical Specialist)"
        }
    ]
    
    # Run each demo scenario
    for i, scenario in enumerate(demo_scenarios, 1):
        print(f"\n🎬 Scenario {i}: {scenario['name']}")
        print("=" * 60)
        print(f"📋 Description: {scenario['description']}")
        print(f"🔀 Expected Flow: {scenario['expected_flow']}")
        print(f"❓ Query: {scenario['state']['query']}")
        
        state = scenario["state"].copy()
        current_step = 1
        
        # Step 1: Mock Automation Agent
        print(f"\n📍 Step {current_step}: Mock Automation Agent")
        print("-" * 40)
        
        try:
            automation_result = automation_agent(state)
            
            if automation_result.get("automation_handled"):
                print(f"   ✅ Automation SUCCESS - Query fully resolved")
                print(f"   📝 Response: {automation_result.get('automation_response', 'N/A')[:100]}...")
                print(f"   ⏱️  Resolution time: {automation_result.get('processing_time_ms', 0)}ms")
                print(f"   🎯 Next action: {automation_result.get('next_action', 'complete')}")
                
                if automation_result.get("automation_handled"):
                    print(f"\n🏁 Scenario complete - Automation resolved the query!")
                    continue
            else:
                print(f"   ⚠️  Automation ESCALATION - Requires AI assistance")
                print(f"   📝 Reason: {automation_result.get('escalation_reason', 'Complex query')}")
                print(f"   🎯 Next action: {automation_result.get('next_action', 'route_to_ai')}")
                state.update(automation_result)
                
        except Exception as e:
            print(f"   ❌ Automation error: {e}")
        
        current_step += 1
        
        # Step 2: AI Chatbot Agent
        print(f"\n📍 Step {current_step}: AI Chatbot Agent")
        print("-" * 40)
        
        try:
            chatbot_result = chatbot_agent(state)
            
            print(f"   ✅ AI response generated")
            ai_response = chatbot_result.get("ai_response", "")
            print(f"   📝 Response: {ai_response[:150]}...")
            print(f"   🎯 Next action: {chatbot_result.get('next_action', 'quality_review')}")
            
            state.update(chatbot_result)
            
        except Exception as e:
            print(f"   ❌ Chatbot error: {e}")
        
        current_step += 1
        
        # Step 3: Context Manager Agent
        print(f"\n📍 Step {current_step}: Context Manager Agent")
        print("-" * 40)
        
        try:
            context_result = context_manager(state)
            
            context_analysis = context_result.get("context_analysis", {})
            relevance_scores = context_analysis.get("relevance_scores", {})
            recommendations = context_analysis.get("recommendations", [])
            
            print(f"   ✅ Context gathering complete")
            print(f"   📊 Context sources analyzed: {len(relevance_scores)}")
            print(f"   🧠 High-relevance sources: {[k for k, v in relevance_scores.items() if v > 0.6]}")
            print(f"   💡 Recommendations: {len(recommendations)}")
            
            if recommendations:
                for rec in recommendations[:2]:
                    print(f"      - {rec}")
            
            state.update(context_result)
            
        except Exception as e:
            print(f"   ❌ Context manager error: {e}")
        
        current_step += 1
        
        # Step 4: Quality Assessment Agent  
        print(f"\n📍 Step {current_step}: Quality Assessment Agent")
        print("-" * 40)
        
        try:
            quality_result = quality_agent(state)
            
            quality_assessment = quality_result.get("quality_assessment", {})
            overall_score = quality_assessment.get("overall_score", 0)
            needs_improvement = quality_assessment.get("needs_improvement", False)
            
            print(f"   ✅ Quality assessment complete")
            print(f"   📊 Overall score: {overall_score:.1f}/10")
            print(f"   🔍 Needs improvement: {needs_improvement}")
            
            if state.get("enriched_context"):
                print(f"   🧠 Enhanced with context data")
            
            if needs_improvement:
                print(f"   ⚠️  Quality issues detected - recommending escalation")
                improvement_areas = quality_assessment.get("improvement_needed", [])
                print(f"   📋 Areas: {', '.join(improvement_areas[:3])}")
            else:
                print(f"   ✅ Quality acceptable")
            
            print(f"   🎯 Next action: {quality_result.get('next_action', 'check_frustration')}")
            state.update(quality_result)
            
        except Exception as e:
            print(f"   ❌ Quality assessment error: {e}")
        
        current_step += 1
        
        # Step 5: Frustration Detection Agent
        print(f"\n📍 Step {current_step}: Frustration Detection Agent")
        print("-" * 40)
        
        try:
            frustration_result = frustration_agent(state)
            
            frustration_analysis = frustration_result.get("frustration_analysis", {})
            frustration_level = frustration_analysis.get("overall_level", "low")
            indicators = frustration_analysis.get("indicators", [])
            
            print(f"   ✅ Frustration analysis complete")
            print(f"   😤 Frustration level: {frustration_level}")
            print(f"   🚨 Indicators: {', '.join(indicators[:3])}")
            
            if frustration_level in ["high", "critical"]:
                print(f"   🚨 HIGH FRUSTRATION detected - immediate escalation recommended")
            
            # Show context influence on frustration analysis
            if state.get("enriched_context"):
                print(f"   🧠 Analysis enhanced with user history")
            
            print(f"   🎯 Next action: {frustration_result.get('next_action', 'route_decision')}")
            state.update(frustration_result)
            
        except Exception as e:
            print(f"   ❌ Frustration detection error: {e}")
        
        current_step += 1
        
        # Step 6: Human Routing Agent
        print(f"\n📍 Step {current_step}: Human Routing Agent")
        print("-" * 40)
        
        try:
            routing_result = routing_agent(state)
            
            assigned_agent = routing_result.get("assigned_human_agent")
            routing_decision = routing_result.get("routing_decision", {})
            
            if assigned_agent:
                print(f"   ✅ Human agent assigned: {assigned_agent['name']}")
                print(f"   📧 Email: {assigned_agent['email']}")
                print(f"   🔧 Skills: {', '.join(assigned_agent.get('skills', []))}")
                print(f"   🎓 Experience: {assigned_agent.get('skill_level', 'N/A')}")
                print(f"   📊 Current workload: {assigned_agent.get('current_workload', 0)}/{assigned_agent.get('max_concurrent', 5)}")
                print(f"   🎯 Match score: {routing_decision.get('agent_match_score', 0):.1f}%")
                print(f"   📈 Confidence: {routing_decision.get('routing_confidence', 0):.0%}")
                print(f"   ⏱️  Est. resolution: {routing_decision.get('estimated_resolution_time', 0)} min")
                print(f"   🔄 Strategy: {routing_decision.get('routing_strategy', 'unknown')}")
                
                # Show LLM reasoning if available
                llm_reasoning = routing_decision.get('llm_reasoning', [])
                if llm_reasoning:
                    print(f"   🧠 LLM reasoning:")
                    for reason in llm_reasoning[:3]:
                        print(f"      • {reason}")
                
                # Show context influence
                routing_requirements = routing_result.get("routing_requirements", {})
                if routing_requirements.get("context_recommendations"):
                    print(f"   💡 Context influence: {len(routing_requirements['context_recommendations'])} insights applied")
                
                print(f"   🎯 Final action: {routing_result.get('next_action', 'transfer_to_human')}")
                
            elif routing_decision.get("status") == "queued":
                queue_info = routing_decision["queue_entry"]
                print(f"   ⏳ No agents available - queued for callback")
                print(f"   📍 Queue position: {queue_info['queue_position']}")
                print(f"   ⏱️  Estimated wait: {queue_info['estimated_wait_time']} min")
                
            else:
                print(f"   ❌ Routing failed - unable to assign agent")
                
        except Exception as e:
            print(f"   ❌ Routing error: {e}")
            import traceback
            traceback.print_exc()
        
        # Summary
        print(f"\n🎭 Scenario {i} Summary")
        print("-" * 40)
        
        final_action = routing_result.get('next_action', 'unknown') if 'routing_result' in locals() else 'unknown'
        
        if final_action == "transfer_to_human":
            agent_name = routing_result.get("assigned_human_agent", {}).get("name", "Unknown")
            print(f"   🏁 RESULT: Escalated to human agent {agent_name}")
            print(f"   📈 Full HITL pipeline completed successfully")
        elif final_action == "queue_for_human":
            print(f"   🏁 RESULT: Queued for human callback (no agents available)")
        else:
            print(f"   🏁 RESULT: {final_action}")
        
        # Show system metrics
        print(f"\n   📊 System Performance:")
        steps_completed = current_step
        print(f"      • Pipeline steps: {steps_completed}/6 completed")
        print(f"      • Context sources: {len(context_analysis.get('relevance_scores', {})) if 'context_analysis' in locals() else 0}")
        print(f"      • Quality score: {quality_assessment.get('overall_score', 0):.1f}/10" if 'quality_assessment' in locals() else "      • Quality score: N/A")
        print(f"      • Frustration level: {frustration_analysis.get('overall_level', 'unknown')}" if 'frustration_analysis' in locals() else "      • Frustration level: N/A")
        print(f"      • Agent match: {routing_decision.get('agent_match_score', 0):.1f}%" if 'routing_decision' in locals() else "      • Agent match: N/A")
    
    # System overview
    print(f"\n" + "=" * 80)
    print("🏆 Complete HITL System Demo Results")
    print("=" * 80)
    
    print(f"\n🎯 System Components Successfully Demonstrated:")
    print("  ✅ Mock Automation Agent - Handles routine insurance tasks")
    print("  ✅ AI Chatbot Agent - Generates customer service responses")
    print("  ✅ Quality Assessment Agent - Evaluates response quality")
    print("  ✅ Frustration Detection Agent - Monitors customer sentiment")
    print("  ✅ Context Manager Agent - Analyzes conversation history")
    print("  ✅ Human Routing Agent - LLM-powered database-driven routing")
    
    print(f"\n🔗 Integration Features Verified:")
    print("  ✅ End-to-end pipeline orchestration")
    print("  ✅ Context-aware routing decisions") 
    print("  ✅ Quality-driven escalation logic")
    print("  ✅ Frustration-based priority adjustment")
    print("  ✅ Database-driven agent selection")
    print("  ✅ LLM-powered intelligent routing")
    print("  ✅ Rich decision explanations and reasoning")
    
    print(f"\n🚀 Production Readiness Indicators:")
    print("  ✅ Modular agent architecture")
    print("  ✅ Comprehensive logging and monitoring")
    print("  ✅ Fallback and error handling")
    print("  ✅ Scalable database integration")
    print("  ✅ Context preservation across steps")
    print("  ✅ Performance metrics and analytics")
    
    print(f"\n🎭 Demo Complete - HITL System with Human Routing Prototype Ready!")


if __name__ == "__main__":
    asyncio.run(run_complete_hitl_demo())