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
  | { type: "done"; metrics?: MessageMetrics }
  | { type: "message_metrics"; metrics: MessageMetrics }
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
    }
  | {
      type: "tool_call_start";
      agent: string;
      tool: string;
      arguments: Record<string, any>;
      timestamp?: number;
    }
  | {
      type: "tool_call_end";
      tool: string;
      success: boolean;
      output: any;
      duration_ms: number;
    }
  | {
      type: "task_graph_start";
      dag_id?: string;
      goal: string;
      total_tasks: number;
      tasks: any[];
    }
  | {
      type: "task_graph_step_start";
      dag_id?: string;
      id: string;
      agent: string;
      title?: string;
      instruction: string;
      depends_on?: string[];
    }
  | {
      type: "task_graph_step_end";
      dag_id?: string;
      id: string;
      agent: string;
      status: string;
      output?: any;
      error?: string;
      execution_time_ms?: number;
    }
  | {
      type: "task_graph_complete";
      dag_id?: string;
      goal: string;
      final_response: string;
      tasks: any[];
      success: boolean;
      total_duration_ms?: number;
      inter_agent_messages?: any[];
      artifacts?: any[];
    }
  | {
      type: "inter_agent_message";
      id: string;
      dag_id: string;
      sender: string;
      recipient: string;
      message_type: string;
      content: string;
      timestamp?: number;
      payload?: Record<string, any>;
    }
  | {
      type: "computer_use_step";
      step: number;
      max_steps: number;
      action: string;
      action_details?: Record<string, any>;
      thought?: string;
      screenshot_b64?: string;
      status?: "running" | "completed" | "blocked" | "error";
      summary?: string;
      window_title?: string;
      coordinates?: { x: number; y: number } | null;
    };

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

export interface ComputerUseStep {
  step: number;
  max_steps: number;
  action: string;
  action_details?: Record<string, any>;
  thought?: string;
  screenshot_b64?: string;
  status: "running" | "completed" | "blocked" | "error";
  summary?: string;
  window_title?: string;
  coordinates?: { x: number; y: number } | null;
  timestamp?: number;
}

export interface ChatLine {
  id: string;
  agent: string;
  text: string;
  timestamp: number;
  taskGraph?: ActiveTaskGraphTrace | null;
  computerUseSteps?: ComputerUseStep[];
  metrics?: MessageMetrics | null;
}

export interface ActiveToolTrace {
  tool: string;
  agent: string;
  arguments: Record<string, any>;
  status: "running" | "done" | "error";
  output?: any;
  duration_ms?: number;
}

export interface ActiveTaskGraphTrace {
  dag_id?: string;
  goal: string;
  total_tasks: number;
  tasks: any[];
  active_step?: string;
  status?: "running" | "done" | "failed";
  total_duration_ms?: number;
  inter_agent_messages?: any[];
  artifacts?: any[];
  final_response?: string;
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
  activeTool: ActiveToolTrace | null;
  activeTaskGraph: ActiveTaskGraphTrace | null;
  activeComputerUse: ComputerUseStep[] | null;
  clearChat: () => void;
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
  const [activeTool, setActiveTool] = useState<ActiveToolTrace | null>(null);
  const [activeTaskGraph, setActiveTaskGraph] = useState<ActiveTaskGraphTrace | null>(null);
  const [activeComputerUse, setActiveComputerUse] = useState<ComputerUseStep[] | null>(null);

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
      const mimeType = base64.startsWith("UklGR") ? "audio/wav" : "audio/mpeg";
      const audio = new Audio(`data:${mimeType};base64,` + base64);
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
        case "tool_call_start":
          setActiveTool({
            tool: event.tool,
            agent: event.agent,
            arguments: event.arguments,
            status: "running",
          });
          break;
        case "tool_call_end":
          setActiveTool((prev) =>
            prev
              ? {
                  ...prev,
                  status: event.success ? "done" : "error",
                  output: event.output,
                  duration_ms: event.duration_ms,
                }
              : null,
          );
          setTimeout(() => setActiveTool(null), 3000);
          break;
        case "task_graph_start":
          setActiveTaskGraph({
            dag_id: event.dag_id,
            goal: event.goal,
            total_tasks: event.total_tasks,
            tasks: event.tasks,
            status: "running",
            inter_agent_messages: [],
            artifacts: [],
          });
          break;
        case "task_graph_step_start":
          setActiveTaskGraph((prev) =>
            prev
              ? {
                  ...prev,
                  active_step: event.id,
                  tasks: prev.tasks.map((t) =>
                    t.id === event.id ? { ...t, status: "running", title: event.title || t.title } : t,
                  ),
                }
              : null,
          );
          break;
        case "task_graph_step_end":
          setActiveTaskGraph((prev) =>
            prev
              ? {
                  ...prev,
                  tasks: prev.tasks.map((t) =>
                    t.id === event.id
                      ? {
                          ...t,
                          status: event.status,
                          output: event.output,
                          error: event.error,
                          execution_time_ms: event.execution_time_ms,
                        }
                      : t,
                  ),
                }
              : null,
          );
          break;
        case "inter_agent_message":
          setActiveTaskGraph((prev) =>
            prev
              ? {
                  ...prev,
                  inter_agent_messages: [
                    ...(prev.inter_agent_messages || []),
                    {
                      id: event.id,
                      dag_id: event.dag_id,
                      sender: event.sender,
                      recipient: event.recipient,
                      message_type: event.message_type,
                      content: event.content,
                      timestamp: event.timestamp || Date.now(),
                      payload: event.payload,
                    },
                  ],
                }
              : null,
          );
          break;
        case "task_graph_complete":
          setActiveTaskGraph((prev) => {
            const completedTrace: ActiveTaskGraphTrace = {
              dag_id: event.dag_id,
              goal: event.goal,
              total_tasks: event.tasks?.length || prev?.total_tasks || 0,
              tasks: event.tasks || prev?.tasks || [],
              status: event.success ? "done" : "failed",
              total_duration_ms: event.total_duration_ms,
              inter_agent_messages: event.inter_agent_messages || prev?.inter_agent_messages || [],
              artifacts: event.artifacts || prev?.artifacts || [],
              final_response: event.final_response,
            };

            // Also attach completed taskGraph to the current assistant message in feed
            setLines((curLines) => {
              const lastIdx = curLines.reduce(
                (acc, l, idx) => (l.agent !== "YOU" && l.agent !== "user" ? idx : acc),
                -1,
              );
              if (lastIdx >= 0) {
                const updated = [...curLines];
                updated[lastIdx] = {
                  ...updated[lastIdx],
                  taskGraph: completedTrace,
                };
                return updated;
              }
              return curLines;
            });

            return completedTrace;
          });
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
        case "message_metrics":
          if (event.metrics) {
            setLines((curLines) => {
              const lastIdx = curLines.reduce(
                (acc, l, idx) => (l.agent !== "YOU" && l.agent !== "user" ? idx : acc),
                -1,
              );
              if (lastIdx >= 0) {
                const updated = [...curLines];
                updated[lastIdx] = {
                  ...updated[lastIdx],
                  metrics: event.metrics,
                };
                return updated;
              }
              return curLines;
            });
          }
          break;
        case "computer_use_step": {
          const stepData: ComputerUseStep = {
            step: event.step,
            max_steps: event.max_steps,
            action: event.action,
            action_details: event.action_details,
            thought: event.thought,
            screenshot_b64: event.screenshot_b64,
            status: event.status || "running",
            summary: event.summary,
            window_title: event.window_title,
            coordinates: event.coordinates,
            timestamp: Date.now(),
          };

          setActiveComputerUse((prev) => {
            const list = prev ? [...prev] : [];
            const existingIdx = list.findIndex((s) => s.step === event.step);
            if (existingIdx >= 0) {
              list[existingIdx] = stepData;
            } else {
              list.push(stepData);
            }
            return list;
          });

          // Also attach live steps to the last assistant message in lines
          setLines((curLines) => {
            const lastIdx = curLines.reduce(
              (acc, l, idx) => (l.agent !== "YOU" && l.agent !== "user" ? idx : acc),
              -1,
            );
            if (lastIdx >= 0) {
              const updated = [...curLines];
              const prevSteps = updated[lastIdx].computerUseSteps || [];
              const sIdx = prevSteps.findIndex((s) => s.step === event.step);
              const newSteps = [...prevSteps];
              if (sIdx >= 0) {
                newSteps[sIdx] = stepData;
              } else {
                newSteps.push(stepData);
              }
              updated[lastIdx] = {
                ...updated[lastIdx],
                computerUseSteps: newSteps,
              };
              return updated;
            }
            return curLines;
          });

          if (event.status === "completed" || event.status === "blocked") {
            setTimeout(() => setActiveComputerUse(null), 4000);
          }
          break;
        }
        case "done":
          setThinking(false);
          setActiveEdge(null);
          if (event.metrics) {
            setLines((curLines) => {
              const lastIdx = curLines.reduce(
                (acc, l, idx) => (l.agent !== "YOU" && l.agent !== "user" ? idx : acc),
                -1,
              );
              if (lastIdx >= 0) {
                const updated = [...curLines];
                updated[lastIdx] = {
                  ...updated[lastIdx],
                  metrics: event.metrics,
                };
                return updated;
              }
              return curLines;
            });
          }
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
      const voice = localStorage.getItem("copper_selected_voice") || "en-US-AvaNeural";
      wsRef.current.send(JSON.stringify({ message, mode, voice }));
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

  const clearChat = useCallback(() => {
    setLines([]);
    fetch(`${API_BASE}/api/v1/chat/history/default`, { method: "DELETE" }).catch(() => {});
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
    stopAudio,
    lastCorrectionAck,
    activeTool,
    activeTaskGraph,
    activeComputerUse,
    clearChat,
  };
}
