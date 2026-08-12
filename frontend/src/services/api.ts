import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || "Request failed";
    console.error("[API Error]", msg);
    return Promise.reject(new Error(msg));
  }
);

// Chat
export const chatAPI = {
  sendMessage: (message: string, sessionId?: string, provider = "ollama") =>
    api.post("/chat/message", { message, session_id: sessionId, provider }),

  getHistory: (sessionId: string) => api.get(`/chat/history/${sessionId}`),

  clearHistory: (sessionId: string) => api.delete(`/chat/history/${sessionId}`),

  streamUrl: (message: string, sessionId: string) =>
    `${BASE_URL}/chat/stream?message=${encodeURIComponent(message)}&session_id=${sessionId}`,
};

// Voice
export const voiceAPI = {
  transcribe: (audioBlob: Blob, language?: string) => {
    const fd = new FormData();
    fd.append("audio", audioBlob, "recording.wav");
    if (language) fd.append("language", language);
    return api.post("/voice/transcribe", fd, { headers: { "Content-Type": "multipart/form-data" } });
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

// Memory
export const memoryAPI = {
  search: (query: string, limit = 10) => api.post("/memory/search", { query, limit }),
  add: (key: string, content: string, source = "manual") =>
    api.post("/memory/add", { key, content, source }),
  getAll: (skip = 0, limit = 50) => api.get(`/memory/all?skip=${skip}&limit=${limit}`),
  delete: (id: number) => api.delete(`/memory/${id}`),
  getStats: () => api.get("/memory/stats"),
};

// Reminders
export const remindersAPI = {
  create: (data: object) => api.post("/reminders/", data),
  parseFromText: (text: string) => api.post("/reminders/parse", { text }),
  list: (completed = false) => api.get(`/reminders/?completed=${completed}`),
  complete: (id: number) => api.patch(`/reminders/${id}/complete`),
  delete: (id: number) => api.delete(`/reminders/${id}`),
};

// Automation
export const automationAPI = {
  getStats: () => api.get("/automation/system/stats"),
  getProcesses: () => api.get("/automation/system/processes"),
  runCommand: (command: string) => api.post("/automation/system/command", { command }),
  launchApp: (app_name: string) => api.post("/automation/app/launch", { app_name }),
  openUrl: (url: string) => api.post("/automation/app/url", { url }),
  browseDirectory: (path: string) => api.get(`/automation/files/browse?path=${encodeURIComponent(path)}`),
  organizeFiles: (source: string, destination: string) =>
    api.post("/automation/files/organize", { source, destination }),
};

// Vision
export const visionAPI = {
  analyzeImage: (imageBlob: Blob, prompt?: string) => {
    const fd = new FormData();
    fd.append("image", imageBlob);
    if (prompt) fd.append("prompt", prompt);
    return api.post("/vision/analyze", fd, { headers: { "Content-Type": "multipart/form-data" } });
  },
  captureScreen: () => api.get("/vision/screen/capture", { responseType: "blob" }),
  analyzeScreen: (prompt?: string) =>
    api.get(`/vision/screen/analyze${prompt ? `?prompt=${encodeURIComponent(prompt)}` : ""}`),
};

// Guardian — disagreement verdicts surfaced from chat responses (pass 2/3 backend).
// A verdict rides along on ChatResponse.guardian_verdict; these calls are for the
// explicit user actions taken in the challenge modal.
export const guardianAPI = {
  acknowledge: (sessionId: string, decision: "follow" | "proceed" | "discuss") =>
    api.post("/guardian/acknowledge", { session_id: sessionId, decision }),
  confirmSafetyAction: (sessionId: string, confirmationText: string) =>
    api.post("/guardian/confirm", { session_id: sessionId, confirmation_text: confirmationText }),
};

// Agent Registry — Master UI Prompt §13-14
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

// Security / Audit — Master UI Prompt §20-21
export const auditAPI = {
  list: (category?: string, limit = 100) =>
    api.get(`/audit/${category ? `?category=${category}&limit=${limit}` : `?limit=${limit}`}`),
  exportData: () => api.get("/audit/export", { responseType: "blob" }),
  deleteAllData: (confirm: boolean) => api.post("/audit/delete-all", { confirm }),
};

export default api;
