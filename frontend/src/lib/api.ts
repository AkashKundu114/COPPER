import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE, timeout: 15000 });

export interface AgentStats {
  id: string;
  name: string;
  tier: string;
  tier_label: string;
  color: string;
  domain: string;
  blurb: string;
  times_invoked: number;
  familiarity_score: number;
  familiarity_tier: string;
  glow: number;
  last_active: string | null;
}

export interface InteractionRecord {
  id: number;
  agent_id: string;
  user_message: string;
  response: string;
  timestamp: string;
  duration_ms: number;
}

export interface ProfileFact {
  key: string;
  value: string;
  confidence: number;
  observed_n: number;
  updated_at: string;
}

export interface ProfileResponse {
  facts: ProfileFact[];
  total_interactions: number;
  relationship_tier: string;
  most_used_agent: string | null;
  agents_met: number;
  agents_total: number;
}

export const fetchAgents = () => api.get<AgentStats[]>("/api/agents").then((r) => r.data);
export const fetchAgentHistory = (id: string, limit = 20) =>
  api.get<InteractionRecord[]>(`/api/agents/${id}/history`, { params: { limit } }).then((r) => r.data);
export const fetchProfile = () => api.get<ProfileResponse>("/api/memory/profile").then((r) => r.data);
export const resetProfile = () => api.post("/api/memory/reset").then((r) => r.data);
export const sendMessage = (message: string) =>
  api.post("/api/chat/message", { message }).then((r) => r.data);
