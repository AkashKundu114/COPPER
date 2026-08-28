import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "../lib/api";
import type { ProactiveAlert } from "../components/alerts/SpiderSenseToast";

export type BrainEvent =
  | { type: "copper_thinking" }
  | { type: "route_decision"; agent: string; tier: string; color: string }
  | { type: "edge_pulse"; from: string; to: string }
  | { type: "agent_active"; agent: string }
  | { type: "agent_speaking"; agent: string; text: string }
  | {
      type: "memory_update";
      profile_delta: { key: string; value: string }[];
      agent: string;
      familiarity: number;
      tier: string;
      glow?: number;
      correction_acknowledged?: boolean;
      self_memory_id?: string;
      self_memory_summary?: string;
    }
  | { type: "done" }
  | { type: "audio_playback"; audio_base64: string }
  | {
      type: "proactive_intervention";
      alert_id: string;
      severity: "info" | "warning" | "critical" | "reflection";
      category: string;
      title: string;
      message: string;
      mode: string;
      suggested_actions: string[];
    };

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
  send: (message: string, mode?: string) => void;
  sendSystemAction: (action: string, payload: Record<string, any>) => void;
  lastMemoryUpdate: BrainEvent | null;
  alerts: ProactiveAlert[];
  dismissAlert: (alertId: string) => void;
  stopAudio: () => void;
  lastCorrectionAck: { id: string; summary: string; timestamp: number } | null;
}

function estimateSpeakingDuration(text: string): number {
  return Math.min(5000, Math.max(900, text.length * 45));
}

const WS_URL = API_BASE.replace(/^http/, "ws") + "/api/v1/chat/ws/default";

export function useBrainSocket(onProfileChange?: () => void): BrainState {
  const [connected, setConnected] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [activeEdge, setActiveEdge] = useState<{
    from: string;
    to: string;
  } | null>(null);
  const [pulseSeq, setPulseSeq] = useState(0);
  const [lines, setLines] = useState<ChatLine[]>([]);
  const [lastMemoryUpdate, setLastMemoryUpdate] = useState<BrainEvent | null>(
    null,
  );
  const [speaking, setSpeaking] = useState(false);
  const [speakingAgent, setSpeakingAgent] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );
  const speakingTimer = useRef<ReturnType<typeof setTimeout> | undefined>(
    undefined,
  );
  const [alerts, setAlerts] = useState<ProactiveAlert[]>([]);
  const [lastCorrectionAck, setLastCorrectionAck] = useState<{ id: string; summary: string; timestamp: number } | null>(null);

  const audioQueue = useRef<string[]>([]);
  const isPlayingAudio = useRef<boolean>(false);
  const currentAudio = useRef<HTMLAudioElement | null>(null);

  const playNextAudio = useCallback(() => {
    if (audioQueue.current.length === 0) {
      isPlayingAudio.current = false;
      setSpeaking(false);
      return;
    }

    isPlayingAudio.current = true;
    setSpeaking(true);
    const base64 = audioQueue.current.shift()!;

    try {
      const audio = new Audio("data:audio/wav;base64," + base64);
      currentAudio.current = audio;

      audio.onended = () => {
        playNextAudio();
      };

      audio.onerror = (e) => {
        console.error("Audio playback error", e);
        playNextAudio();
      };

      audio.play().catch((e) => {
        console.error("Failed to play audio", e);
        playNextAudio();
      });
    } catch (e) {
      console.error("Failed to initialize audio", e);
      playNextAudio();
    }
  }, []);

  const stopAudio = useCallback(() => {
    if (currentAudio.current) {
      currentAudio.current.pause();
      currentAudio.current = null;
    }
    audioQueue.current = [];
    isPlayingAudio.current = false;
    setSpeaking(false);
  }, []);

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
          if (!isPlayingAudio.current) {
            setSpeaking(false);
            clearTimeout(speakingTimer.current);
          }
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
          setLines((prev) => {
            const last = prev[prev.length - 1];
            // If the last line is from the same agent and is a stream, append to it
            if (
              last &&
              last.agent === event.agent &&
              last.id.startsWith("stream-")
            ) {
              return [
                ...prev.slice(0, -1),
                { ...last, text: last.text + event.text },
              ];
            }
            // Otherwise, start a new stream bubble
            return [
              ...prev,
              {
                id: `stream-${Date.now()}`,
                agent: event.agent,
                text: event.text,
                timestamp: Date.now(),
              },
            ];
          });
          setSpeakingAgent(event.agent);

          if (!isPlayingAudio.current) {
            setSpeaking(true);
            clearTimeout(speakingTimer.current);
            speakingTimer.current = setTimeout(() => {
              if (!isPlayingAudio.current) setSpeaking(false);
            }, estimateSpeakingDuration(event.text));
          }
          break;
        case "memory_update":
          setLastMemoryUpdate(event);
          if (event.correction_acknowledged && event.self_memory_id && event.self_memory_summary) {
            setLastCorrectionAck({
              id: event.self_memory_id,
              summary: event.self_memory_summary,
              timestamp: Date.now()
            });
          }
          onProfileChange?.();
          break;
        case "proactive_intervention":
          setAlerts((prev) => {
            if (prev.some((a) => a.alert_id === event.alert_id)) return prev;
            return [
              ...prev,
              {
                alert_id: event.alert_id,
                severity: event.severity,
                category: event.category,
                title: event.title,
                message: event.message,
                mode: event.mode,
                suggested_actions: event.suggested_actions,
              },
            ];
          });
          break;
        case "audio_playback":
          audioQueue.current.push(event.audio_base64);
          if (!isPlayingAudio.current) {
            clearTimeout(speakingTimer.current);
            playNextAudio();
          }
          break;
        case "done":
          setThinking(false);
          setActiveEdge(null);
          setTimeout(() => setActiveAgent(null), 1200);
          break;
      }
    };
  }, [onProfileChange, playNextAudio]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      clearTimeout(speakingTimer.current);
      if (currentAudio.current) {
        currentAudio.current.pause();
        currentAudio.current = null;
      }
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((message: string, mode: string = "auto") => {
    setLines((prev) => [
      ...prev,
      {
        id: `${Date.now()}-user`,
        agent: "YOU",
        text: message,
        timestamp: Date.now(),
      },
    ]);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message, mode }));
    }
  }, []);

  const dismissAlert = useCallback((alertId: string) => {
    setAlerts((prev) => prev.filter((a) => a.alert_id !== alertId));
  }, []);

  const sendSystemAction = useCallback(
    (action: string, payload: Record<string, any>) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action, ...payload }));
      }
    },
    [],
  );

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
    stopAudio,
    lastCorrectionAck,
  };
}
