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

export const fetchAgents = () => api.get<AgentStats[]>("/api/v1/agents").then((r) => r.data);
export const fetchAgentHistory = (id: string, limit = 20) =>
  api.get<InteractionRecord[]>(`/api/v1/agents/${id}/history`, { params: { limit } }).then((r) => r.data);
export const fetchProfile = () => api.get<ProfileResponse>("/api/v1/memory/profile").then((r) => r.data);
export const resetProfile = () => api.post("/api/v1/memory/reset").then((r) => r.data);
export const sendMessage = (message: string) =>
  api.post("/api/v1/chat/message", { message }).then((r) => r.data);
export const fetchLogs = (filter?: string) =>
  api.get("/api/v1/audit/logs", { params: { filter } }).then((r) => r.data).catch(() => []);
export const fetchStats = () =>
  api.get("/api/v1/audit/stats").then((r) => r.data).catch(() => ({}));

export interface SystemTelemetryData {
  status: string;
  uptime_seconds: number;
  cpu: {
    model: string;
    usage_percent: number;
    cores: number;
    temperature_c: number;
  };
  gpu: {
    model: string;
    vram_total_gb: number;
    vram_used_gb: number;
    vram_free_gb: number;
    vram_percent: number;
    core_temp_c: number;
    hotspot_temp_c: number;
    power_watts: number;
    fan_speed_percent: number;
  };
  memory: {
    system_total_gb: number;
    system_used_gb: number;
    system_percent: number;
    app_footprint_mb: number;
    suite_total_mb: number;
  };
  tokens: {
    prompt_tokens_processed: number;
    completion_tokens_generated: number;
    total_tokens: number;
    generation_speed_tps: number;
    prompt_eval_speed_tps: number;
  };
}

export const fetchSystemTelemetry = () =>
  api.get<SystemTelemetryData>("/api/v1/system/telemetry").then((r) => r.data);

export interface EpisodeRecord {
  id: number;
  context: string;
  project: string | null;
  task: string | null;
  goal: string | null;
  problem: string | null;
  decision: string | null;
  outcome: string | null;
  confidence: number;
  tags: string[] | null;
  related_episode_id: number | null;
  created_at: string | null;
}

export const fetchEpisodes = (context?: string, limit = 20) =>
  api.get<EpisodeRecord[]>("/api/v1/episodes", { params: { context, limit } }).then((r) => r.data);
export const fetchEpisodeById = (id: number) =>
  api.get<EpisodeRecord>(`/api/v1/episodes/${id}`).then((r) => r.data);
export const searchSimilarEpisodes = (query: string, limit = 5) =>
  api.get("/api/v1/episodes/similar", { params: { query, limit } }).then((r) => r.data);
