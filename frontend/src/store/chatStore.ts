import { create } from "zustand";
import { chatAPI } from "@/services/api";

export type Role = "user" | "assistant" | "system";
export type AgentType = "chat" | "coding" | "automation" | "reminder" | "research" | "vision";

export interface Message {
  id: string;
  role: Role;
  content: string;
  agentType?: AgentType;
  timestamp: Date;
  isStreaming?: boolean;
}

interface ChatStore {
  messages: Message[];
  sessionId: string;
  isLoading: boolean;
  streamingId: string | null;
  provider: "ollama" | "openai";

  setProvider: (p: "ollama" | "openai") => void;
  setSessionId: (id: string) => void;
  addMessage: (role: Role, content: string, agentType?: AgentType) => string;
  appendChunk: (id: string, chunk: string) => void;
  finishStream: (id: string) => void;
  clearMessages: () => void;
  loadHistory: (sessionId: string) => Promise<void>;
}

let _msgId = 0;
const newId = () => `msg_${Date.now()}_${_msgId++}`;

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  sessionId: crypto.randomUUID(),
  isLoading: false,
  streamingId: null,
  provider: "ollama",

  setProvider: (p) => set({ provider: p }),
  setSessionId: (id) => set({ sessionId: id }),

  addMessage: (role, content, agentType) => {
    const id = newId();
    const msg: Message = {
      id,
      role,
      content,
      agentType,
      timestamp: new Date(),
      isStreaming: role === "assistant" && !content,
    };
    set((s) => ({ messages: [...s.messages, msg] }));
    if (role === "assistant" && !content) set({ streamingId: id });
    return id;
  },

  appendChunk: (id, chunk) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + chunk } : m
      ),
    })),

  finishStream: (id) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, isStreaming: false } : m
      ),
      streamingId: null,
      isLoading: false,
    })),

  clearMessages: () => set({ messages: [], streamingId: null }),

  loadHistory: async (sessionId) => {
    try {
      const { data } = await chatAPI.getHistory(sessionId);
      const messages: Message[] = data.map((h: any) => ({
        id: String(h.id),
        role: h.role as Role,
        content: h.content,
        agentType: h.agent_type,
        timestamp: new Date(h.created_at),
      }));
      set({ messages, sessionId });
    } catch (e) {
      console.error("Failed to load history:", e);
    }
  },
}));
