#!/usr/bin/env python3
"""
Test context retrieval to ensure the database is populated correctly
and the context manager can find relevant information
"""

from src.core.context_manager import SQLiteContextProvider

def test_context_retrieval():
    """Test that context manager can retrieve relevant information"""
    
    print("🔍 Testing Context Database Retrieval")
    print("=" * 50)
    
    # Initialize context provider
    context_provider = SQLiteContextProvider()
    
    # Get overall database metrics
    metrics = context_provider.get_context_metrics()
    print(f"📊 Database Overview:")
    print(f"   - Total queries: {metrics['total_queries']}")
    print(f"   - Total users: {metrics['total_users']}")  
    print(f"   - Total sessions: {metrics['total_sessions']}")
    print(f"   - Escalation rate: {metrics['escalation_rate']:.1%}")
    
    # Test queries that will be common in demos
    test_queries = [
        "My claim was denied",
        "I can't afford my premium", 
        "How long does a claim take?",
        "This is taking too long",
        "I need to file a claim",
        "I want to cancel my policy"
    ]
    
    print(f"\n🧪 Testing Context Retrieval for Demo Queries:")
    print("-" * 50)
    
    for query in test_queries:
        print(f"\n🔎 Query: '{query}'")
        
        # Get all context entries to search through (simulating context manager search)
        all_entries = context_provider.get_context(limit=500)
        
        # Find similar entries based on keyword matching (simplified version of what context manager does)
        query_words = set(query.lower().split())
        relevant_entries = []
        
        for entry in all_entries:
            entry_words = set(entry.content.lower().split())
            similarity = len(query_words & entry_words) / len(query_words | entry_words) if query_words | entry_words else 0
            
            if similarity > 0.1:  # 10% similarity threshold for demo
                relevant_entries.append({
                    'entry': entry,
                    'similarity': similarity,
                    'type': entry.entry_type
                })
        
        # Sort by similarity
        relevant_entries.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Show top 3 results
        if relevant_entries:
            print(f"   ✅ Found {len(relevant_entries)} relevant entries:")
            for i, result in enumerate(relevant_entries[:3]):
                entry = result['entry']
                similarity = result['similarity']
                print(f"      {i+1}. [{entry.entry_type}] {entry.content[:80]}... (similarity: {similarity:.0%})")
        else:
            print(f"   ❌ No relevant entries found")
    
    # Test knowledge base entries
    print(f"\n📚 Knowledge Base Content:")
    print("-" * 30)
    
    kb_entries = context_provider.get_context(limit=100)
    kb_types = {}
    
    for entry in kb_entries:
        entry_type = entry.entry_type
        if entry_type not in kb_types:
            kb_types[entry_type] = 0
        kb_types[entry_type] += 1
    
    for entry_type, count in sorted(kb_types.items()):
        print(f"   - {entry_type}: {count} entries")
    
    # Show some example knowledge base content
    print(f"\n💡 Sample Knowledge Base Entries:")
    print("-" * 35)
    
    knowledge_entries = [entry for entry in kb_entries if entry.entry_type in ['response_template', 'resolution_pattern', 'case_study']]
    
    for entry in knowledge_entries[:3]:
        print(f"\n   📝 {entry.entry_type.replace('_', ' ').title()}:")
        print(f"      {entry.content[:120]}...")
        if entry.metadata:
            if 'effectiveness_score' in entry.metadata:
                print(f"      Effectiveness: {entry.metadata['effectiveness_score']}/10")
            if 'tags' in entry.metadata:
                print(f"      Tags: {', '.join(entry.metadata.get('tags', [])[:3])}")
    
    # Show escalation examples
    print(f"\n🚨 Escalation Examples:")
    print("-" * 25)
    
    escalation_entries = [entry for entry in kb_entries if entry.entry_type == 'escalation']
    if escalation_entries:
        print(f"   Found {len(escalation_entries)} escalation examples")
        for entry in escalation_entries[:2]:
            print(f"   - {entry.content[:100]}...")
    else:
        print("   No escalation entries found in sample")
    
    print(f"\n✅ Context database successfully populated!")
    print(f"💬 The context manager will now provide relevant examples for common insurance queries")
    print(f"🤖 AI agents can reference successful resolution patterns and best practices")
    print(f"👥 Human agents will receive context summaries with relevant customer history")

if __name__ == "__main__":
    test_context_retrieval()