# Database Mock Data Setup

This document explains the mock insurance data that has been populated in the context database to demonstrate the HITL system's context management capabilities.

## Overview

The context database has been populated with realistic insurance support scenarios, successful resolutions, and knowledge base entries that the Context Manager Agent can retrieve and provide to other agents.

## What Was Added

### 1. Core Insurance Scenarios (`populate_context_database.py`)
- **110 total entries** added to the database
- **50 queries** representing common insurance questions
- **5 user profiles** with different interaction patterns:
  - Power user (25+ interactions)
  - New customer (3 interactions, needs guidance)
  - Frequent claimant (18 interactions)
  - Business customer (31 interactions)
  - Senior customer (12 interactions)

**Common Insurance Topics Covered:**
- Claim filing and status
- Policy questions and changes
- Billing and payment issues
- Coverage inquiries
- Emergency assistance
- Fraud prevention

### 2. Demo-Specific Scenarios (`add_demo_scenarios.py`)
- **54 demo context entries** designed for Gradio demo
- **6 main demo scenarios** with exact queries likely to be used:
  - "My claim was denied"
  - "I can't afford my premium"
  - "How long does a claim take?"
  - "I need to file a claim"
  - "This is taking too long"
  - "I want to cancel my policy"
- **Multiple similar queries** for each scenario to improve context matching
- **2 frustration examples** showing successful de-escalation

### 3. Expert Knowledge Base (`add_knowledge_base.py`)
- **16 knowledge base entries** including:
  - Response templates for common situations
  - Resolution patterns and best practices
  - De-escalation techniques
  - Product knowledge (auto & home insurance)
  - Process optimization guides
  - Quality standards and escalation criteria
- **3 detailed case studies** showing complex problem resolution

## Database Statistics

After population:
- **Total queries**: 76
- **Total users**: 35  
- **Total sessions**: 55
- **Escalation rate**: 0.0% (will increase during live demos)

## How the Context Manager Uses This Data

### 1. Similar Case Finding
When a user asks "My claim was denied", the context manager will find:
- Exact matches for the same query
- Similar queries like "Why was my claim rejected?"
- Successful resolution examples
- Related escalation cases

### 2. Knowledge Base Retrieval
The context manager can access:
- **Response templates** for handling claim denials empathetically
- **Step-by-step processes** for billing disputes
- **De-escalation techniques** for frustrated customers
- **Product knowledge** for coverage explanations

### 3. User Profile Context
For each user interaction, the context manager provides:
- **Interaction history** (frequency, types of questions)
- **Escalation patterns** (previous escalations, success rates)
- **User behavior classification** (power user, new customer, etc.)
- **Resolution preferences** based on past successful interactions

### 4. Context Summaries for Different Audiences

The populated data enables the context manager to create tailored summaries:

**For AI Agents:**
- Relevant similar cases with resolution patterns
- User interaction history highlighting important patterns
- Recommended approaches based on successful resolutions

**For Human Agents:**
- Detailed customer background and interaction history
- Similar cases with outcomes and resolution strategies
- Escalation history and customer satisfaction patterns

**For Quality Assessment:**
- Previous successful resolutions for comparison
- Customer satisfaction benchmarks
- Escalation risk factors based on historical patterns

## Testing Context Retrieval

Run `python scripts/test_context_retrieval.py` to verify:
- Database contains expected number of entries
- Context matching works for demo queries
- Knowledge base entries are retrievable
- Different entry types are properly categorized

## Demo Impact

With this populated database, the Gradio demo will now show:

1. **Realistic Context Information**: Instead of empty context panels, users will see relevant customer history, similar cases, and knowledge base matches.

2. **Better AI Responses**: The Chatbot Agent can reference successful resolution patterns and best practices from the knowledge base.

3. **Informed Quality Assessment**: The Quality Agent can compare responses against proven successful templates and identify potential issues.

4. **Realistic Human Routing**: The routing system can consider historical escalation patterns and customer profiles.

5. **Comprehensive Escalation Context**: When escalations occur, human agents receive detailed context including similar successful resolutions and customer interaction history.

## Files Created

- `scripts/populate_context_database.py` - Core insurance scenarios and user profiles
- `scripts/add_demo_scenarios.py` - Demo-specific queries and resolutions  
- `scripts/add_knowledge_base.py` - Expert knowledge templates and case studies
- `scripts/test_context_retrieval.py` - Verification and testing script
- `README_DATABASE_SETUP.md` - This documentation

The context database is now ready to provide rich, realistic data that demonstrates the full capabilities of the HITL system's context management and multi-agent collaboration.