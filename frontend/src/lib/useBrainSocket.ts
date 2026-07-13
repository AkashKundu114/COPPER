import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "./api";

export type BrainEvent =
  | { type: "copper_thinking" }
  | { type: "route_decision"; agent: string; tier: string; color: string }
  | { type: "edge_pulse"; from: string; to: string }
  | { type: "agent_active"; agent: string }
  | { type: "agent_speaking"; agent: string; text: string }
  | { type: "memory_update"; profile_delta: { key: string; value: string }[]; agent: string; familiarity: number; tier: string; glow?: number }
  | { type: "done" };

export interface ChatLine {
  id: string;
  agent: string;
  text: string;
  timestamp: number;
}

interface BrainState {
  connected: boolean;
  thinking: boolean;
  activeAgent: string | null;
  activeEdge: { from: string; to: string } | null;
  pulseSeq: number;
  lines: ChatLine[];
  send: (message: string) => void;
  lastMemoryUpdate: BrainEvent | null;
}

const WS_URL = API_BASE.replace(/^http/, "ws") + "/api/chat/ws";

export function useBrainSocket(onProfileChange?: () => void): BrainState {
  const [connected, setConnected] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [activeEdge, setActiveEdge] = useState<{ from: string; to: string } | null>(null);
  const [pulseSeq, setPulseSeq] = useState(0);
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [lastMemoryUpdate, setLastMemoryUpdate] = useState<BrainEvent | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

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
          break;
        case "memory_update":
          setLastMemoryUpdate(event);
          onProfileChange?.();
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
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((message: string) => {
    setLines((prev) => [...prev, { id: `${Date.now()}-user`, agent: "YOU", text: message, timestamp: Date.now() }]);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message }));
    }
  }, []);

  return { connected, thinking, activeAgent, activeEdge, pulseSeq, lines, send, lastMemoryUpdate };
}
