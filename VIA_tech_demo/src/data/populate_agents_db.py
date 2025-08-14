"""Script to populate the human agents database with mock data."""

import asyncio
from pathlib import Path

from ..core.human_agents_db import HumanAgentsDatabase
from ..data.human_agents_repository import SQLiteHumanAgentRepository
from ..data.mock_human_agents import create_mock_insurance_agents, get_agent_summary_stats


async def populate_database(db_path: str = None, reset: bool = True):
    """
    Populate the human agents database with mock insurance representatives.
    
    Args:
        db_path: Optional path to database file
        reset: Whether to reset the database before populating
    """
    print("🏢 Initializing Human Agents Database for Insurance Demo...")
    
    # Initialize database
    db_manager = HumanAgentsDatabase(db_path)
    
    if reset:
        print("🔄 Resetting database...")
        db_manager.reset_database()
    else:
        print("📊 Initializing database schema...")
        db_manager.initialize_database()
    
    # Initialize repository
    repository = SQLiteHumanAgentRepository(db_path)
    
    # Create mock agents
    print("👥 Creating mock insurance support representatives...")
    mock_agents = create_mock_insurance_agents()
    
    # Populate database
    print(f"💾 Inserting {len(mock_agents)} agents into database...")
    for agent in mock_agents:
        try:
            await repository.create(agent)
            print(f"  ✅ Created agent: {agent.name} ({agent.id})")
        except Exception as e:
            print(f"  ❌ Failed to create agent {agent.id}: {e}")
    
    # Verify population
    print("\n📈 Verifying database population...")
    all_agents = await repository.get_all()
    print(f"✅ Successfully populated database with {len(all_agents)} agents")
    
    # Display summary statistics
    print("\n📊 Agent Summary Statistics:")
    stats = get_agent_summary_stats()
    
    print(f"  Total Agents: {stats['total_agents']}")
    print(f"  Status Distribution:")
    for status, count in stats['status_distribution'].items():
        print(f"    - {status.title()}: {count}")
    
    print(f"  Workload:")
    print(f"    - Active Conversations: {stats['workload']['total_active_conversations']}")
    print(f"    - Total Capacity: {stats['workload']['total_capacity']}")
    print(f"    - Utilization: {stats['workload']['utilization_percentage']}%")
    
    print(f"  Performance:")
    print(f"    - Avg Satisfaction: {stats['performance']['average_satisfaction_score']}/10")
    print(f"    - Avg Stress Level: {stats['performance']['average_stress_level']}/10")
    
    print(f"  Experience Levels:")
    for level, count in stats['experience_levels'].items():
        print(f"    - {level.replace('_', ' ').title()}: {count}")
    
    print(f"  Specializations:")
    for spec, count in stats['specialization_distribution'].items():
        print(f"    - {spec.title()}: {count} agents")
    
    print(f"  Language Support:")
    for lang, count in stats['language_support'].items():
        print(f"    - {lang.title()}: {count} agents")
    
    print(f"\n🎯 Database populated successfully!")
    print(f"📍 Database location: {db_manager.db_path}")
    
    return len(all_agents)


async def verify_database_functionality(db_path: str = None):
    """
    Test basic database functionality with sample queries.
    
    Args:
        db_path: Optional path to database file
    """
    print("\n🧪 Testing database functionality...")
    
    repository = SQLiteHumanAgentRepository(db_path)
    
    # Test 1: Get available agents
    print("  Test 1: Getting available agents...")
    available_agents = await repository.get_available_agents()
    print(f"    ✅ Found {len(available_agents)} available agents")
    
    # Test 2: Get agents by specialization
    print("  Test 2: Getting claims specialists...")
    from ..interfaces.human_agents import Specialization
    claims_agents = await repository.get_by_specialization(Specialization.CLAIMS)
    print(f"    ✅ Found {len(claims_agents)} claims specialists")
    
    # Debug: Check what's in the database for first agent
    if claims_agents:
        print(f"      First claims agent: {claims_agents[0].name} - Specializations: {claims_agents[0].specializations}")
    else:
        all_agents = await repository.get_all()
        if all_agents:
            print(f"      Debug - First agent specializations: {all_agents[0].specializations}")
    
    # Test 3: Find best available agent
    print("  Test 3: Finding best available agent...")
    best_agent = await repository.get_best_available_agent()
    if best_agent:
        print(f"    ✅ Best agent: {best_agent.name} (Stress: {best_agent.workload.stress_level})")
    else:
        print(f"    ⚠️  No available agents found")
    
    # Test 4: Update agent status
    if available_agents:
        print("  Test 4: Updating agent status...")
        test_agent = available_agents[0]
        from ..interfaces.human_agents import HumanAgentStatus
        success = await repository.update_status(test_agent.id, HumanAgentStatus.BUSY)
        if success:
            print(f"    ✅ Updated {test_agent.name} status to BUSY")
            # Revert change
            await repository.update_status(test_agent.id, HumanAgentStatus.AVAILABLE)
            print(f"    ✅ Reverted {test_agent.name} status to AVAILABLE")
        else:
            print(f"    ❌ Failed to update agent status")
    
    print("🎉 Database functionality tests completed!")


async def display_sample_agents(db_path: str = None, limit: int = 3):
    """
    Display sample agent details for verification.
    
    Args:
        db_path: Optional path to database file
        limit: Number of agents to display
    """
    print(f"\n👤 Sample Agent Details (showing {limit} agents):")
    
    repository = SQLiteHumanAgentRepository(db_path)
    agents = await repository.get_all()
    
    for i, agent in enumerate(agents[:limit]):
        print(f"\n  Agent {i+1}: {agent.name}")
        print(f"    ID: {agent.id}")
        print(f"    Email: {agent.email}")
        print(f"    Status: {agent.status if isinstance(agent.status, str) else agent.status.value}")
        print(f"    Experience: Level {agent.experience_level}")
        print(f"    Specializations: {[s if isinstance(s, str) else s.value for s in agent.specializations]}")
        print(f"    Max Conversations: {agent.max_concurrent_conversations}")
        print(f"    Current Workload: {agent.workload.active_conversations} active")
        print(f"    Satisfaction Score: {agent.workload.satisfaction_score}/10")
        print(f"    Stress Level: {agent.workload.stress_level}/10")
        print(f"    Languages: {agent.languages}")
        print(f"    Shift: {agent.shift_start} - {agent.shift_end}")
        if agent.metadata:
            print(f"    Department: {agent.metadata.get('department', 'N/A')}")
            print(f"    Team: {agent.metadata.get('team', 'N/A')}")


async def main():
    """Main function to populate and test the database."""
    print("🚀 Human Agents Database Setup - Insurance Company Demo")
    print("=" * 60)
    
    # Populate database
    agent_count = await populate_database(reset=True)
    
    # Test functionality
    await verify_database_functionality()
    
    # Display sample agents
    await display_sample_agents()
    
    print("\n" + "=" * 60)
    print("✨ Setup completed successfully!")
    print(f"🎯 Ready for human routing demo with {agent_count} insurance agents")


if __name__ == "__main__":
    asyncio.run(main())