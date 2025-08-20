export type Role = 'user' | 'bot' | 'agent' | 'system';

export interface Message {
  id: string;
  role: Role;
  text: string;
  timestamp: number;
  meta?: Record<string, unknown>;
}

export interface HumanAgent {
  id: string;
  name: string;
  skills: string[];
  online: boolean;
  queueSize: number;
  satisfactionScore: number; // 0..100
}

export interface AgentEvent {
  id: string;
  kind: 'quality' | 'frustration' | 'routing' | 'context' | 'automation';
  description: string;
  score?: number;
  timestamp: number;
}

export interface Conversation {
  id: string;
  messages: Message[];
  events: AgentEvent[];
  assignedHumanId?: string | null;
  humanState?: {
    flow?: 'claim' | 'generic';
    step: number;
  };
  open: boolean;
}

export interface Metrics {
  activeConversations: number;
  escalationsToHumans: number;
  avgFirstResponseMs: number;
  csat: number; // 0..100
  modelLatencyMs: number;
  avgTokens: number;
  sentimentSeries: { t: number; value: number }[];
}


