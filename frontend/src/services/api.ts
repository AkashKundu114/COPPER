import { api } from "../lib/api";

const BASE_URL = api.defaults.baseURL || "http://localhost:8000/api/v1";

export { api };

export const chatAPI = {
  sendMessage: (message: string, sessionId?: string, provider = "ollama") =>
    api.post("/chat/message", { message, session_id: sessionId, provider }),

  getHistory: (sessionId: string) => api.get(`/chat/history/${sessionId}`),

  clearHistory: (sessionId: string) => api.delete(`/chat/history/${sessionId}`),

  streamUrl: (message: string, sessionId: string) =>
    `${BASE_URL}/chat/stream?message=${encodeURIComponent(message)}&session_id=${sessionId}`,
};

export const voiceAPI = {
  transcribe: (audioBlob: Blob, language?: string) => {
    const fd = new FormData();
    fd.append("audio", audioBlob, "recording.wav");
    if (language) fd.append("language", language);
    return api.post("/voice/transcribe", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  synthesize: async (text: string, voice?: string): Promise<string> => {
    const fd = new FormData();
    fd.append("text", text);
    if (voice) fd.append("voice", voice);
    const res = await api.post("/voice/synthesize", fd, {
      headers: { "Content-Type": "multipart/form-data" },
      responseType: "blob",
    });
    return URL.createObjectURL(res.data);
  },

  getVoices: () => api.get("/voice/voices"),
};

export const memoryAPI = {
  search: (query: string, limit = 10) =>
    api.post("/memory/search", { query, limit }),
  add: (key: string, content: string, source = "manual") =>
    api.post("/memory/add", { key, content, source }),
  getAll: (skip = 0, limit = 50) =>
    api.get(`/memory/all?skip=${skip}&limit=${limit}`),
  delete: (id: number) => api.delete(`/memory/${id}`),
  getStats: () => api.get("/memory/stats"),
};

export const remindersAPI = {
  create: (data: object) => api.post("/reminders/", data),
  parseFromText: (text: string) => api.post("/reminders/parse", { text }),
  list: (completed = false) => api.get(`/reminders/?completed=${completed}`),
  complete: (id: number) => api.patch(`/reminders/${id}/complete`),
  delete: (id: number) => api.delete(`/reminders/${id}`),
};

export const automationAPI = {
  getStats: () => api.get("/automation/system/stats"),
  getProcesses: () => api.get("/automation/system/processes"),
  runCommand: (command: string) =>
    api.post("/automation/system/command", { command }),
  launchApp: (app_name: string) =>
    api.post("/automation/app/launch", { app_name }),
  openUrl: (url: string) => api.post("/automation/app/url", { url }),
  browseDirectory: (path: string) =>
    api.get(`/automation/files/browse?path=${encodeURIComponent(path)}`),
  organizeFiles: (source: string, destination: string) =>
    api.post("/automation/files/organize", { source, destination }),
};

export const visionAPI = {
  analyzeImage: (imageBlob: Blob, prompt?: string) => {
    const fd = new FormData();
    fd.append("image", imageBlob);
    if (prompt) fd.append("prompt", prompt);
    return api.post("/vision/analyze", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  captureScreen: () =>
    api.get("/vision/screen/capture", { responseType: "blob" }),
  analyzeScreen: (prompt?: string) =>
    api.get(
      `/vision/screen/analyze${prompt ? `?prompt=${encodeURIComponent(prompt)}` : ""}`,
    ),
};

export const guardianAPI = {
  acknowledge: (
    sessionId: string,
    decision: "follow" | "proceed" | "discuss",
  ) => api.post("/guardian/acknowledge", { session_id: sessionId, decision }),
  confirmSafetyAction: (sessionId: string, confirmationText: string) =>
    api.post("/guardian/confirm", {
      session_id: sessionId,
      confirmation_text: confirmationText,
    }),
};

export const agentRegistryAPI = {
  list: () => api.get("/agents/"),
  getVersions: (agentId: string) => api.get(`/agents/${agentId}/versions`),
  activate: (agentId: string, versionId: number) =>
    api.post(`/agents/${agentId}/activate`, { version_id: versionId }),
  rollback: (agentId: string) => api.post(`/agents/${agentId}/rollback`),
  disable: (agentId: string) => api.post(`/agents/${agentId}/disable`),
  runHealthCheck: (agentId: string, versionId: number) =>
    api.post(`/agents/${agentId}/health-check`, { version_id: versionId }),
};

export const auditAPI = {
  list: (category?: string, limit = 100) =>
    api.get(
      `/audit/${category ? `?category=${category}&limit=${limit}` : `?limit=${limit}`}`,
    ),
  exportData: () => api.get("/audit/export", { responseType: "blob" }),
  deleteAllData: (confirm: boolean) =>
    api.post("/audit/delete-all", { confirm }),
};

export const selfMemoryAPI = {
    getAll: async (category?: string, limit: number = 50) => {
        const params = new URLSearchParams();
        if (category) params.set('category', category);
        params.set('limit', String(limit));
        const { data } = await api.get(`/self-memory?${params}`);
        return data;
    },
    resolve: async (memoryId: string) => {
        const { data } = await api.post(`/self-memory/${memoryId}/resolve`);
        return data;
    },
};

export const selfImprovementAPI = {
  getMetrics: async (days: number = 7) => {
    const { data } = await api.get(`/self-improvement/metrics?days=${days}`);
    return data;
  },
  getFailures: async (limit: number = 20) => {
    const { data } = await api.get(`/self-improvement/failures?limit=${limit}`);
    return data;
  },
  getProposedEdits: async () => {
    const { data } = await api.get("/self-improvement/proposed-edits");
    return data;
  },
  applyEdit: async (editId: number) => {
    const { data } = await api.post(`/self-improvement/apply-edit/${editId}`);
    return data;
  },
  runBenchmark: async () => {
    const { data } = await api.post("/self-improvement/run-benchmark");
    return data;
  },
  optimizePrompts: async () => {
    const { data } = await api.post("/self-improvement/optimize-prompts");
    return data;
  },
  getModelRankings: async () => {
    const { data } = await api.get("/self-improvement/model-rankings");
    return data;
  },
};

export const trainingAPI = {
  getStats: async () => {
    const { data } = await api.get("/training/stats");
    return data;
  },
  curate: async (minScore: number = 0.85, limit: number = 50) => {
    const { data } = await api.post("/training/curate", { min_score: minScore, limit });
    return data;
  },
  startTraining: async (baseModel: string = "llama3.1:8b", targetAgent: string = "all") => {
    const { data } = await api.post("/training/start", { base_model: baseModel, target_agent: targetAgent });
    return data;
  },
  getStatus: async (jobId?: number) => {
    const query = jobId ? `?job_id=${jobId}` : "";
    const { data } = await api.get(`/training/status${query}`);
    return data;
  },
  getAdapters: async () => {
    const { data } = await api.get("/training/adapters");
    return data;
  },
  activateAdapter: async (adapterId: number) => {
    const { data } = await api.post(`/training/adapters/${adapterId}/activate`);
    return data;
  },
  deactivateAdapter: async (adapterId: number) => {
    const { data } = await api.post(`/training/adapters/${adapterId}/deactivate`);
    return data;
  },
  startABTest: async (adapterId: number, percentage: number = 20) => {
    const { data } = await api.post(`/training/adapters/${adapterId}/ab-test`, { percentage });
    return data;
  },
  mergeAdapter: async (adapterId: number) => {
    const { data } = await api.post(`/training/adapters/${adapterId}/merge`);
    return data;
  },
};

export interface BranchItem {
  branch_id: string;
  parent_session_id?: string | null;
  root_session_id?: string;
  divergence_index?: number;
  divergence_message?: { role: string; content: string } | null;
  title: string;
  messages_count?: number;
  status: "active" | "merged";
  is_main?: boolean;
  created_at?: string;
}

export interface DiffComparison {
  branch_a_id: string;
  branch_b_id: string;
  branch_a_title: string;
  branch_b_title: string;
  divergence_point: string;
  branch_a_summary: string;
  branch_b_summary: string;
  key_differences: { aspect: string; branch_a: string; branch_b: string }[];
  recommendation: string;
  mergeable_insights: string[];
}

export const branchingAPI = {
  createBranch: async (sessionId: string, messageIndex: number, title?: string) => {
    const { data } = await api.post("/chat/branch", {
      session_id: sessionId,
      message_index: messageIndex,
      title,
    });
    return data;
  },
  getBranches: async (sessionId: string) => {
    const { data } = await api.get(`/chat/branches/${sessionId}`);
    return data;
  },
  compareBranches: async (branchAId: string, branchBId: string) => {
    const { data } = await api.get(
      `/chat/branches/compare?a=${encodeURIComponent(branchAId)}&b=${encodeURIComponent(branchBId)}`
    );
    return data;
  },
  mergeBranch: async (branchId: string, targetSessionId?: string) => {
    const { data } = await api.post(`/chat/branches/${encodeURIComponent(branchId)}/merge`, {
      target_session_id: targetSessionId,
    });
    return data;
  },
};

// ==========================================
// Ambient Intelligence & Phase 1-5 API Layer
// ==========================================

export const ambientAPI = {
  getTimeline: (hours = 24) => api.get(`/ambient/timeline?hours=${hours}`),
  getSessions: (hours = 24) => api.get(`/ambient/sessions?hours=${hours}`),
  getStats: (hours = 24) => api.get(`/ambient/stats?hours=${hours}`),
  getCurrentContext: () => api.get("/ambient/current"),
  getSummary: (date?: string) => api.get(`/ambient/summary${date ? `?date=${date}` : ""}`),
};

export const briefingAPI = {
  getMorning: () => api.get("/briefing/morning"),
  getEod: () => api.get("/briefing/eod"),
  generateMorning: () => api.post("/briefing/generate/morning"),
  generateEod: () => api.post("/briefing/generate/eod"),
};

export const clipboardAPI = {
  getHistory: (skip = 0, limit = 50) => api.get(`/clipboard/history?skip=${skip}&limit=${limit}`),
  getCurrent: () => api.get("/clipboard/current"),
  processEntry: (id: string) => api.post(`/clipboard/process/${id}`),
  clearHistory: () => api.delete("/clipboard/history"),
};

export const cognitiveAPI = {
  getState: () => api.get("/cognitive/state"),
  getHistory: (hours = 24) => api.get(`/cognitive/history?hours=${hours}`),
  getShouldSuppress: () => api.get("/cognitive/should-suppress"),
};

export const contextSwitchAPI = {
  getCurrent: () => api.get("/context/current"),
  getProjects: () => api.get("/context/projects"),
  switchTo: (projectName: string) => api.post(`/context/switch/${encodeURIComponent(projectName)}`),
  parkCurrent: () => api.post("/context/park"),
  getParked: () => api.get("/context/parked"),
};

export const predictionsAPI = {
  getToday: () => api.get("/predictions/today"),
  getPatterns: () => api.get("/predictions/patterns"),
  triggerAnalysis: () => api.post("/predictions/analyze"),
  updatePrediction: (id: string, status: string) => api.patch(`/predictions/${id}`, { status }),
};

export const privacyAPI = {
  getBudget: () => api.get("/privacy/budget"),
  configure: (epsilon: number, delta: number, budget_limit: number) =>
    api.post("/privacy/configure", { epsilon, delta, budget_limit }),
  resetBudget: () => api.post("/privacy/reset"),
  getGuarantee: () => api.get("/privacy/guarantee"),
  noiseDemo: (embedding: number[]) => api.post("/privacy/noise-demo", { embedding }),
};

export const causalAPI = {
  recordEvent: (data: { description: string; category: string; source: string; entities?: string[]; metadata?: any }) =>
    api.post("/causal/events", data),
  getEvents: (hours = 24, category?: string, limit = 100) =>
    api.get(`/causal/events?hours=${hours}${category ? `&category=${category}` : ""}&limit=${limit}`),
  addLink: (data: { cause_id: string; effect_id: string; relationship: string; confidence: number; evidence?: string }) =>
    api.post("/causal/links", data),
  inferLinks: () => api.post("/causal/infer"),
  queryWhy: (question: string) => api.post("/causal/why", { question }),
  getCauses: (eventId: string) => api.get(`/causal/events/${eventId}/causes`),
  getEffects: (eventId: string) => api.get(`/causal/events/${eventId}/effects`),
  getStats: () => api.get("/causal/stats"),
};

export const provenanceAPI = {
  recordFact: (fact: { fact: string; source_type: string; source_id: string; confidence?: number; tags?: string[] }) =>
    api.post("/provenance/facts", fact),
  searchFacts: (q = "", min_confidence = 0.0, status = "all", limit = 50) =>
    api.get(`/provenance/facts?q=${encodeURIComponent(q)}&min_confidence=${min_confidence}&status=${status}&limit=${limit}`),
  getFact: (recordId: string) => api.get(`/provenance/facts/${recordId}`),
  confirmFact: (recordId: string, sourceId: string, confidence = 0.9) =>
    api.post(`/provenance/facts/${recordId}/confirm`, { source_id: sourceId, confidence }),
  contradictFact: (recordId: string, sourceId: string, counterEvidence: string, confidence = 0.7) =>
    api.post(`/provenance/facts/${recordId}/contradict`, { source_id: sourceId, counter_evidence: counterEvidence, confidence }),
  reviseFact: (recordId: string, newFact: string, reason: string, sourceId: string) =>
    api.post(`/provenance/facts/${recordId}/revise`, { new_fact: newFact, reason, source_id: sourceId }),
  explainBelief: (fact: string) => api.get(`/provenance/explain?fact=${encodeURIComponent(fact)}`),
  getUncertain: () => api.get("/provenance/uncertain"),
  getStats: () => api.get("/provenance/stats"),
};

export const meetingsAPI = {
  start: (title?: string) => api.post("/meetings/start", { title: title || "Untitled Meeting" }),
  stop: (id: string) => api.post(`/meetings/${id}/stop`),
  list: (limit = 20) => api.get(`/meetings?limit=${limit}`),
  get: (id: string) => api.get(`/meetings/${id}`),
  getNotes: (id: string) => api.get(`/meetings/${id}/notes`),
  getTasks: (id: string) => api.get(`/meetings/${id}/tasks`),
};

export const emailAPI = {
  configure: (data: { host: string; port: number; username: string; password: string; use_ssl?: boolean }) =>
    api.post("/email/configure", data),
  isConfigured: () => api.get("/email/configured"),
  fetch: (limit = 20) => api.post(`/email/fetch?limit=${limit}`),
  getInbox: (priority?: string) => api.get(`/email/inbox${priority ? `?priority=${priority}` : ""}`),
  getEmail: (id: string) => api.get(`/email/inbox/${id}`),
  draftResponse: (id: string) => api.post(`/email/draft/${id}`),
  getDrafts: () => api.get("/email/drafts"),
  approveDraft: (id: string) => api.post(`/email/draft/${id}/approve`),
  rejectDraft: (id: string) => api.post(`/email/draft/${id}/reject`),
};

export const codeReviewAPI = {
  analyze: (data: { repo_path: string; base_branch?: string; head_branch?: string }) =>
    api.post("/code-review/analyze", data),
  analyzeCommit: (data: { repo_path: string; commit_hash: string }) =>
    api.post("/code-review/analyze-commit", data),
  getReviews: (repoPath?: string, limit = 20) =>
    api.get(`/code-review/reviews?limit=${limit}${repoPath ? `&repo_path=${encodeURIComponent(repoPath)}` : ""}`),
  getReview: (id: string) => api.get(`/code-review/reviews/${id}`),
  addRepo: (path: string, name?: string) => api.post("/code-review/repos", { path, name }),
  getRepos: () => api.get("/code-review/repos"),
};

export const researchAPI = {
  start: (topic: string, depth = "standard", deadline?: string) =>
    api.post("/research/start", { topic, depth, deadline }),
  getReports: (status?: string, limit = 20) =>
    api.get(`/research/reports?limit=${limit}${status ? `&status=${status}` : ""}`),
  getReport: (id: string) => api.get(`/research/reports/${id}`),
  getMarkdown: (id: string) => api.get(`/research/reports/${id}/markdown`),
  cancel: (id: string) => api.post(`/research/reports/${id}/cancel`),
};

export const skillsAPI = {
  list: (tag?: string) => api.get(`/skills${tag ? `?tag=${tag}` : ""}`),
  getStats: () => api.get("/skills/stats"),
  match: (description: string) => api.get(`/skills/match?description=${encodeURIComponent(description)}`),
  get: (id: string) => api.get(`/skills/${id}`),
  extract: (taskDescription: string, steps: any[], result: any) =>
    api.post("/skills/extract", { task_description: taskDescription, steps, result }),
  execute: (id: string, params: Record<string, any>) => api.post(`/skills/${id}/execute`, { params }),
  delete: (id: string) => api.delete(`/skills/${id}`),
};

export const federatedAPI = {
  register: (name: string, port = 8000) => api.post("/federated/register", { name, port }),
  addPeer: (name: string, host: string, port: number) => api.post("/federated/peers", { name, host, port }),
  getPeers: () => api.get("/federated/peers"),
  discover: () => api.post("/federated/discover"),
  startRound: (adapterName?: string) => api.post("/federated/rounds/start", { adapter_name: adapterName }),
  contributeRound: (roundId: string) => api.post(`/federated/rounds/${roundId}/contribute`),
  receiveDelta: (roundId: string, delta: any, epsilonSpent: number, peerId: string) =>
    api.post(`/federated/rounds/${roundId}/receive`, { delta, epsilon_spent: epsilonSpent, peer_id: peerId }),
  aggregateRound: (roundId: string) => api.post(`/federated/rounds/${roundId}/aggregate`),
  getRounds: () => api.get("/federated/rounds"),
  getRound: (roundId: string) => api.get(`/federated/rounds/${roundId}`),
  getStats: () => api.get("/federated/stats"),
};

export default api;
