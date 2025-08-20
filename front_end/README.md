# VIA Insurance Assistant (Frontend)

React + TypeScript demo showcasing a Human-in-the-Loop (HITL) improvement module around an insurance chatbot.

## Features

- **Semantic Similarity Chatbot**: Pre-written knowledge base with TF-IDF matching
- **Rule-based Sentiment Analysis**: Detects frustration and quality signals
- **Human-in-the-Loop Agents**: Quality, Frustration, Routing, and Context Manager
- **Skill-based Routing**: Routes to appropriate human agents based on conversation topic
- **Claim Hallucination Flow**: Demonstrates bot limitations and human escalation
- **Live Performance Dashboard**: Real-time metrics and agent status

## Getting Started

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Start the dev server**
   ```bash
   npm run dev
   ```

3. **Open the app**
   - Chat: `http://localhost:5173/` (or next available port)
   - Dashboard: `http://localhost:5173/dashboard`

## Structure

- `src/pages/ChatbotPage.tsx`: Chat experience
- `src/components/ChatWindow.tsx`: Chat interface
- `src/state/AppState.tsx`: App state and agent simulations
- `src/pages/DashboardPage.tsx`: KPI cards, charts, and human agent table
- `src/lib/simulator.ts`: Core simulation logic and semantic matching
- `src/data/kb.ts`: Knowledge base for chatbot responses
- `src/lib/rules.ts`: Sentiment analysis rules

## Demo Scenarios

- **Normal Interaction**: Ask about coverage, deductibles, billing
- **Frustration Escalation**: Use negative language or all caps to trigger human routing
- **Claim Filing**: Try to "file a claim" to see the hallucination flow
- **Skill-based Routing**: Mention "home" or "auto" to see appropriate agent assignment

This is a front-end-only simulation; replace `src/lib/simulator.ts` with real APIs to integrate your backend.


