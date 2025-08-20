import React, { createContext, useContext, useMemo, useState } from 'react';
import { Conversation, HumanAgent, Message, Metrics } from '@/types';
import { createMessage, makeAgentEvent, qualityGate, routeToHuman, simpleAnswer, frustrationScore, generateId, qualitySignalFromText, humanBestAnswer } from '@/lib/simulator';
import { isSeverelyNegative } from '@/lib/rules';

interface AppStateValue {
  agents: HumanAgent[];
  conversations: Conversation[];
  metrics: Metrics;
  currentConversationId: string;
  sendUserMessage: (text: string) => Promise<void>;
}

const AppStateCtx = createContext<AppStateValue | null>(null);

const INITIAL_AGENTS: HumanAgent[] = [
  { id: 'h1', name: 'Alex Chen', skills: ['claims', 'auto'], online: true, queueSize: 0, satisfactionScore: 92 },
  { id: 'h2', name: 'Priya Patel', skills: ['home', 'claims'], online: true, queueSize: 0, satisfactionScore: 88 },
  { id: 'h3', name: 'Diego Rivera', skills: ['billing'], online: false, queueSize: 0, satisfactionScore: 95 }
];

const initialConversation: Conversation = {
  id: generateId('conv'),
  messages: [
    createMessage(
      'system',
      'Welcome to the HITL Insurance Assistant. Ask about coverage, deductible, claims, ID cards, premium, or cancellations.'
    )
  ],
  events: [],
  assignedHumanId: null,
  open: true
};

const INITIAL_METRICS: Metrics = {
  activeConversations: 1,
  escalationsToHumans: 0,
  avgFirstResponseMs: 350,
  csat: 91,
  modelLatencyMs: 400,
  avgTokens: 80,
  sentimentSeries: [{ t: Date.now() - 60_000, value: 75 }]
};

export function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [agents, setAgents] = useState<HumanAgent[]>(INITIAL_AGENTS);
  const [conversations, setConversations] = useState<Conversation[]>([initialConversation]);
  const [metrics, setMetrics] = useState<Metrics>(INITIAL_METRICS);
  const currentConversationId = conversations[0].id;

  async function sendUserMessage(text: string) {
    const convId = currentConversationId;
    const newUserMsg = createMessage('user', text);
    setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, newUserMsg] } : c)));

    // If a human agent is already assigned to this conversation, keep the dialogue with the human only
    const existingConv = conversations.find((c) => c.id === convId);
    if (existingConv?.assignedHumanId) {
      const agent = agents.find((a) => a.id === existingConv.assignedHumanId);
      if (agent) {
        let nextStep = 0;
        setConversations((prev) => {
          return prev.map((c) => {
            if (c.id !== convId) return c;
            nextStep = (c.humanState?.step ?? 0) + 1;
            return { ...c, humanState: { flow: c.humanState?.flow ?? 'generic', step: nextStep } };
          });
        });

        const flow = existingConv.humanState?.flow ?? 'generic';
        let reply: string;
        if (flow === 'claim') {
          if (nextStep === 1) {
            reply = `Hi, this is ${agent.name}. I can file your claim. Please share: policy number, date of loss, what happened, and photos if available.`;
          } else {
            reply = `Hi, this is ${agent.name}. Thanks, I have what I need. I am filing your claim now. You will receive a confirmation shortly, and we'll contact you if any additional information is needed.`;
          }
        } else {
          reply = `Hi, this is ${agent.name}. What can I help you with?`;
        }
        const humanMsg = createMessage('agent', reply, { agentName: agent.name });
        setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, humanMsg] } : c)));
        return;
      }
    }

    // Frustration agent
    const frScore = await frustrationScore(text);
    const severe = isSeverelyNegative(text);
    const frEvent = makeAgentEvent('frustration', frScore >= 60 || severe ? 'High user frustration detected' : 'Frustration within normal range', frScore);
    setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, events: [frEvent, ...c.events] } : c)));
    setMetrics((m) => {
      const next = [...m.sentimentSeries, { t: Date.now(), value: Math.max(0, Math.min(100, 100 - frScore)) }];
      const trimmed = next.slice(-100); // keep last 100 points
      return { ...m, sentimentSeries: trimmed };
    });

    // Chatbot drafts an answer
    const draft = await simpleAnswer(text);
    setMetrics((m) => ({ ...m, modelLatencyMs: draft.latencyMs, avgTokens: Math.round((m.avgTokens + draft.tokens) / 2) }));

    // Quality gate checks draft
    // Adjust quality signal based on the most recent user tone; penalize if hallucinated
    const toneDelta = qualitySignalFromText(text);
    const q = await qualityGate(draft.answer);
    const hallucinated = Boolean((draft as any).flags?.hallucinated);
    const hallucinationStep = Number((draft as any).flags?.step ?? 0);
    const qConfidence = Math.max(0, Math.min(1, (q.confidence ?? 0.8) + toneDelta / 100 - (hallucinated ? 0.5 : 0)));
    const qDesc = q.action === 'pass' ? 'Quality check passed' : q.action === 'adjust' ? 'Answer adjusted for clarity' : 'Escalated to human by quality gate';
    const qEvent = makeAgentEvent('quality', qDesc, qConfidence);
    setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, events: [qEvent, ...c.events] } : c)));

    // Escalation policy (user-requested):
    // - Primary: escalate when customer sentiment (frustration) reaches threshold
    // - Secondary: if the bot keeps hallucinating (>= 3 times), escalate due to poor quality
    const FR_THRESHOLD = 60;
    const shouldEscalate = severe || frScore >= FR_THRESHOLD || (hallucinated && hallucinationStep >= 3);
    if (shouldEscalate) {
      // Route to human with context from recent user messages to preserve domain hints (e.g., 'house fire')
      const recentUserContext = conversations
        .find((c) => c.id === convId)?.messages
        .filter((m) => m.role === 'user')
        .slice(-5)
        .map((m) => m.text)
        .join(' ') ?? '';
      const routingHint = `${text} ${recentUserContext}`.toLowerCase();
      const agent = routeToHuman(agents, routingHint);
      const routeEvent = makeAgentEvent('routing', agent ? `Routed to ${agent.name}` : 'No human available');
      // Detect intent for human flow (strict: only when user wants to file a claim)
      const mentionsClaim = /(file|start|open|report|submit)\s+(an?\s+)?(home\s+|auto\s+)?claim/i.test(routingHint);
      const flow: 'claim' | 'generic' = mentionsClaim ? 'claim' : 'generic';
      setConversations((prev) =>
        prev.map((c) =>
          c.id === convId
            ? {
                ...c,
                events: [routeEvent, ...c.events],
                assignedHumanId: agent?.id ?? null,
                humanState: { flow, step: 0 }
              }
            : c
        )
      );
      if (agent) {
        // Increment their queue briefly
        setAgents((list) => list.map((a) => (a.id === agent.id ? { ...a, queueSize: a.queueSize + 1 } : a)));
        setMetrics((m) => ({ ...m, escalationsToHumans: m.escalationsToHumans + 1 }));

        // Simulate human response
        await new Promise((r) => setTimeout(r, 800 + Math.random() * 1000));
        // Human guided claim flow: ask for info, then confirm filing upon receiving details
        let nextStep = 0;
        const currentFlow = conversations.find((c) => c.id === convId)?.humanState?.flow ?? flow;
        setConversations((prev) => {
          return prev.map((c) => {
            if (c.id !== convId) return c;
            nextStep = (c.humanState?.step ?? 0) + 1;
            return { ...c, humanState: { flow: currentFlow, step: nextStep } };
          });
        });

        let reply: string;
        const flowCurrent = conversations.find((c) => c.id === convId)?.humanState?.flow ?? currentFlow ?? 'generic';
        if (flowCurrent === 'claim') {
          if (nextStep === 1) {
            reply = `Hi, this is ${agent.name}. I can file your claim. Please share: policy number, date of loss, what happened, and photos if available.`;
          } else {
            reply = `Hi, this is ${agent.name}. Thanks, I have what I need. I am filing your claim now. You will receive a confirmation shortly, and we'll contact you if any additional information is needed.`;
          }
        } else {
          reply = `Hi, this is ${agent.name}. What can I help you with?`;
        }
        const humanMsg = createMessage('agent', reply, { agentName: agent.name });

        setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, humanMsg] } : c)));
        // Decrement queue
        setAgents((list) => list.map((a) => (a.id === agent.id ? { ...a, queueSize: Math.max(0, a.queueSize - 1) } : a)));
      }
      return;
    }

    const finalAnswer = q.action === 'adjust' && q.adjusted ? q.adjusted : draft.answer;
    const botMsg = createMessage('bot', finalAnswer, { qualityConfidence: q.confidence });
    setConversations((prev) => prev.map((c) => (c.id === convId ? { ...c, messages: [...c.messages, botMsg] } : c)));
  }

  const value = useMemo<AppStateValue>(
    () => ({ agents, conversations, metrics, currentConversationId, sendUserMessage }),
    [agents, conversations, metrics]
  );

  return <AppStateCtx.Provider value={value}>{children}</AppStateCtx.Provider>;
}

export function useAppState(): AppStateValue {
  const ctx = useContext(AppStateCtx);
  if (!ctx) throw new Error('useAppState must be used within AppStateProvider');
  return ctx;
}


