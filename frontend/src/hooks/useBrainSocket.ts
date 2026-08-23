import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "../lib/api";
import type { ProactiveAlert } from "../components/alerts/SpiderSenseToast";

export type BrainEvent =
  | { type: "copper_thinking" }
  | { type: "route_decision"; agent: string; tier: string; color: string }
  | { type: "edge_pulse"; from: string; to: string }
  | { type: "agent_active"; agent: string }
  | { type: "agent_speaking"; agent: string; text: string }
  | { type: "memory_update"; profile_delta: { key: string; value: string }[]; agent: string; familiarity: number; tier: string; glow?: number }
  | { type: "done" }
  | { type: "proactive_intervention"; alert_id: string; severity: "info" | "warning" | "critical"; category: string; title: string; message: string; mode: string; suggested_actions: string[] };

export interface ChatLine {
  id: string;
  agent: string;
  text: string;
  timestamp: number;
}

export type BrainLine = ChatLine;

interface BrainState {
  connected: boolean;
  thinking: boolean;
  activeAgent: string | null;
  activeEdge: { from: string; to: string } | null;
  pulseSeq: number;
  speaking: boolean;
  speakingAgent: string | null;
  lines: ChatLine[];
  send: (message: string) => void;
  sendSystemAction: (action: string, payload: Record<string, any>) => void;
  lastMemoryUpdate: BrainEvent | null;
  alerts: ProactiveAlert[];
  dismissAlert: (alertId: string) => void;
}

function estimateSpeakingDuration(text: string): number {
  return Math.min(5000, Math.max(900, text.length * 45));
}

const WS_URL = API_BASE.replace(/^http/, "ws") + "/api/v1/chat/ws/default";

export function useBrainSocket(onProfileChange?: () => void): BrainState {
  const [connected, setConnected] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [activeEdge, setActiveEdge] = useState<{ from: string; to: string } | null>(null);
  const [pulseSeq, setPulseSeq] = useState(0);
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [lastMemoryUpdate, setLastMemoryUpdate] = useState<BrainEvent | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const [speakingAgent, setSpeakingAgent] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const speakingTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([]);

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      reconnectTimer.current = setTimeout(connect, 2000);
    };
    ws.onerror = () => ws.close();

    ws.onmessage = (evt) => {
      const event: BrainEvent = JSON.parse(evt.data);
      switch (event.type) {
        case "copper_thinking":
          setThinking(true);
          setActiveAgent(null);
          setActiveEdge(null);
          setSpeaking(false);
          clearTimeout(speakingTimer.current);
          break;
        case "route_decision":
          break;
        case "edge_pulse":
          setActiveEdge({ from: event.from, to: event.to });
          setPulseSeq((n) => n + 1);
          break;
        case "agent_active":
          setActiveAgent(event.agent);
          break;
        case "agent_speaking":
          setLines((prev) => [
            ...prev,
            { id: `${Date.now()}-${Math.random()}`, agent: event.agent, text: event.text, timestamp: Date.now() },
          ]);
          setSpeakingAgent(event.agent);
          setSpeaking(true);
          clearTimeout(speakingTimer.current);
          speakingTimer.current = setTimeout(() => setSpeaking(false), estimateSpeakingDuration(event.text));
          break;
        case "memory_update":
          setLastMemoryUpdate(event);
          onProfileChange?.();
          break;
        case "proactive_intervention":
          setAlerts((prev) => {
            if (prev.some((a) => a.alert_id === event.alert_id)) return prev;
            return [...prev, { alert_id: event.alert_id, severity: event.severity, category: event.category, title: event.title, message: event.message, mode: event.mode, suggested_actions: event.suggested_actions }];
          });
          break;
        case "done":
          setThinking(false);
          setActiveEdge(null);
          setTimeout(() => setActiveAgent(null), 1200);
          break;
      }
    };
  }, [onProfileChange]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      clearTimeout(speakingTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((message: string) => {
    setLines((prev) => [...prev, { id: `${Date.now()}-user`, agent: "YOU", text: message, timestamp: Date.now() }]);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message }));
    }
  }, []);

  const dismissAlert = useCallback((alertId: string) => {
    setAlerts((prev) => prev.filter((a) => a.alert_id !== alertId));
  }, []);

  const sendSystemAction = useCallback((action: string, payload: Record<string, any>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...payload }));
    }
  }, []);

  return {
    connected,
    thinking,
    activeAgent,
    activeEdge,
    pulseSeq,
    speaking,
    speakingAgent,
    lines,
    send,
    sendSystemAction,
    lastMemoryUpdate,
    alerts,
    dismissAlert,
  };
}
