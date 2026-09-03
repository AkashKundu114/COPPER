import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE, timeout: 15000 });

export interface MessageMetrics {
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  tokens_per_sec: number;
  ttft_ms: number;
  total_time_sec: number;
  total_time_ms?: number;
}

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

export const fetchAgents = () =>
  api.get<AgentStats[]>("/api/v1/agents").then((r) => r.data);
export const fetchAgentHistory = (id: string, limit = 20) =>
  api
    .get<InteractionRecord[]>(`/api/v1/agents/${id}/history`, {
      params: { limit },
    })
    .then((r) => r.data);
export const fetchProfile = () =>
  api.get<ProfileResponse>("/api/v1/memory/profile").then((r) => r.data);
export const resetProfile = () =>
  api.post("/api/v1/memory/reset").then((r) => r.data);
export const sendMessage = (message: string) =>
  api.post("/api/v1/chat/message", { message }).then((r) => r.data);
export const fetchLogs = (filter?: string) =>
  api
    .get("/api/v1/audit/logs", { params: { filter } })
    .then((r) => r.data)
    .catch(() => []);
export const fetchStats = () =>
  api
    .get("/api/v1/audit/stats")
    .then((r) => r.data)
    .catch(() => ({}));

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
  api
    .get<EpisodeRecord[]>("/api/v1/episodes", { params: { context, limit } })
    .then((r) => r.data);
export const fetchEpisodeById = (id: number) =>
  api.get<EpisodeRecord>(`/api/v1/episodes/${id}`).then((r) => r.data);
export const searchSimilarEpisodes = (query: string, limit = 5) =>
  api
    .get("/api/v1/episodes/similar", { params: { query, limit } })
    .then((r) => r.data);

export interface DocumentPage {
  page_number: number;
  text: string;
  word_count: number;
  char_count: number;
}

export interface ParsedDocument {
  filename: string;
  extension: string;
  category: string;
  size_bytes: number;
  size_formatted: string;
  page_count: number;
  line_count: number;
  word_count: number;
  char_count: number;
  estimated_tokens: number;
  indexed_chunks: number;
  pages: DocumentPage[];
  full_text: string;
  preview_text: string;
  structured_data?: {
    headers?: string[];
    preview_rows?: string[][];
    total_rows?: number;
    column_count?: number;
    is_array?: boolean;
    is_object?: boolean;
    top_level_keys?: string[];
    item_count?: number;
  } | null;
  error?: string | null;
  status: "success" | "partial" | "error";
}

export const parseDocumentFile = async (
  file: File,
  indexToMemory: boolean = true,
): Promise<ParsedDocument> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("index_to_memory", String(indexToMemory));
  const res = await api.post<ParsedDocument>(
    "/api/v1/documents/parse",
    formData,
  );
  return res.data;
};

export const searchDocuments = async (query: string, limit = 5) => {
  const res = await api.post("/api/v1/documents/search", { query, limit });
  return res.data;
};

export interface GeneratedDocumentRecord {
  filename: string;
  filepath: string;
  extension: string;
  category: string;
  size_bytes: number;
  size_formatted: string;
  modified_at: string;
  download_url: string;
}

export interface DocumentGeneratePayload {
  title: string;
  format?: string;
  prompt?: string;
  template_type?: string;
  sections?: Array<{
    heading?: string;
    subheading?: string;
    content?: string;
    bullets?: string[];
    table?: { headers?: string[]; rows?: any[][] };
  }>;
  author?: string;
  index_to_memory?: boolean;
}

export const generateDocument = async (payload: DocumentGeneratePayload) => {
  const res = await api.post("/api/v1/documents/generate", payload);
  return res.data;
};

export const fetchDocumentTemplates = async () => {
  const res = await api.get("/api/v1/documents/templates");
  return res.data;
};

export const fetchGeneratedDocuments = async () => {
  const res = await api.get<{ documents: GeneratedDocumentRecord[]; total: number }>(
    "/api/v1/documents/generated",
  );
  return res.data;
};

export interface VramStatusResponse {
  always_on_mini_model: string;
  loaded_models_count: number;
  loaded_models: Array<{ name: string; size?: number; size_vram?: number }>;
  vram_policy: {
    always_on_mini_model: string;
    mini_model_keep_alive: number | string;
    heavy_model_keep_alive: string;
    auto_unload_heavy_after_turn: boolean;
    target_idle_vram_gb: number;
  };
  status: "optimized" | "multi_loaded";
}

export const fetchVramModelsStatus = async () => {
  const res = await api.get<VramStatusResponse>("/api/v1/system/models/vram");
  return res.data;
};

export const enforceKeepOnlyMiniModel = async () => {
  const res = await api.post("/api/v1/system/models/keep-mini");
  return res.data;
};

export const workspaceAPI = {
  list: <T>(kind: "task" | "project" | "event" | "meal" | "grocery" | "memory") =>
    api.get<T[]>(`/api/v1/workspace/${kind}`).then((r) => r.data),
  create: <T>(kind: string, payload: Record<string, unknown>) =>
    api.post<T>(`/api/v1/workspace/${kind}`, { payload }).then((r) => r.data),
  update: <T>(kind: string, id: string, payload: Record<string, unknown>) =>
    api.patch<T>(`/api/v1/workspace/${kind}/${id}`, { payload }).then((r) => r.data),
  remove: (kind: string, id: string) => api.delete(`/api/v1/workspace/${kind}/${id}`),
};

export interface KnowledgeEntityItem {
  id: number;
  name: string;
  canonical_name: string;
  type: string;
  confidence: number;
  context: string;
  evidence_count: number;
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface KnowledgeRelationshipItem {
  id: number;
  source_id?: number;
  target_id?: number;
  source: string;
  target: string;
  type: string;
  confidence: number;
  context?: string;
  evidence_count: number;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeSubgraphResponse {
  nodes: KnowledgeEntityItem[];
  links: KnowledgeRelationshipItem[];
  edges?: KnowledgeRelationshipItem[];
  center?: string;
}

export interface KnowledgeStatsResponse {
  status: string;
  stats: {
    total_entities: number;
    total_relationships: number;
    entities_by_type: Record<string, number>;
    relationships_by_type: Record<string, number>;
  };
}

export const knowledgeAPI = {
  getEntities: (params?: { type?: string; min_confidence?: number; search?: string; limit?: number }) =>
    api.get<{ data: KnowledgeEntityItem[]; count: number }>("/api/v1/knowledge/entities", { params }).then((r) => r.data),
  createEntity: (payload: { name: string; type: string; confidence?: number; context?: string }) =>
    api.post<{ status: string; entity: KnowledgeEntityItem }>("/api/v1/knowledge/entities", payload).then((r) => r.data),
  deleteEntity: (id: number) =>
    api.delete<{ status: string; message: string }>(`/api/v1/knowledge/entities/${id}`).then((r) => r.data),
  getRelationships: (params?: { type?: string; source?: string; target?: string; min_confidence?: number; limit?: number }) =>
    api.get<{ data: KnowledgeRelationshipItem[]; count: number }>("/api/v1/knowledge/relationships", { params }).then((r) => r.data),
  createRelationship: (payload: { source: string; target: string; type: string; confidence?: number; context?: string }) =>
    api.post<{ status: string; relationship: KnowledgeRelationshipItem }>("/api/v1/knowledge/relationships", payload).then((r) => r.data),
  getSubgraph: (params?: { entity?: string; depth?: number; max_nodes?: number }) =>
    api.get<KnowledgeSubgraphResponse>("/api/v1/knowledge/subgraph", { params }).then((r) => r.data),
  getPath: (source: string, target: string) =>
    api.get<{ source: string; target: string; path: any[] }>("/api/v1/knowledge/path", { params: { source, target } }).then((r) => r.data),
  extractFromText: (text: string, sessionId?: string) =>
    api.post<{ status: string; extracted: { entities: KnowledgeEntityItem[]; relationships: KnowledgeRelationshipItem[] } }>(
      "/api/v1/knowledge/extract",
      { text, session_id: sessionId }
    ).then((r) => r.data),
  getStats: () =>
    api.get<KnowledgeStatsResponse>("/api/v1/knowledge/stats").then((r) => r.data),
};
