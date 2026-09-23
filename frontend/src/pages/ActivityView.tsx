import React, { useState, useEffect } from "react";
import {
  Activity,
  Terminal,
  Trash2,
  Wrench,
  Network,
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  Cpu,
  Clock,
  Sparkles,
  Zap,
  Compass,
  BarChart3,
  Radio,
} from "lucide-react";
import { API_BASE, type DistributedTrace, fetchDistributedTraces } from "../lib/api";
import {
  TaskGraphVisualizer,
  type TaskGraphData,
} from "../components/chat/TaskGraphVisualizer";
import { PassiveActivityTimeline } from "../components/ambient/PassiveActivityTimeline";
import { ThinkingOrb } from "thinking-orbs";
import {
  RoutingExplanationCard,
  type RoutingExplanationData,
} from "../components/routing/RoutingExplanationCard";
import { RoutingBenchmarkView } from "../components/routing/RoutingBenchmarkView";
import { TraceWaterfallVisualizer } from "../components/telemetry/TraceWaterfallVisualizer";

interface ActivityLog {
  id: string;
  timestamp: string;
  category: "Tools" | "NEXUS" | "Routing" | "Guardian" | "Firewall" | "Inference" | "Memory" | "Cache" | "Tracing";
  title: string;
  detail: string;
  status: "success" | "warning" | "blocked" | "running" | "error";
  io?: {
    arguments?: Record<string, any>;
    output?: any;
    duration_ms?: number;
    guardian_level?: number;
  };
  taskGraph?: TaskGraphData;
  routingExplanation?: RoutingExplanationData;
  distributedTrace?: DistributedTrace;
}
export const ActivityView: React.FC = () => {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [expandedLogs, setExpandedLogs] = useState<Record<string, boolean>>({});
  const [isSimulating, setIsSimulating] = useState(false);
  const [showBenchmarkAnalytics, setShowBenchmarkAnalytics] = useState(false);

  useEffect(() => {
    // Fetch live traces from backend if available
    fetch(`${API_BASE}/orchestration/traces?limit=10`)
      .then((r) => r.json())
      .then((traces) => {
        if (Array.isArray(traces) && traces.length > 0) {
          const fetchedLogs: ActivityLog[] = traces.map((tr) => ({
            id: tr.dag_id || `trace-${Date.now()}`,
            timestamp: "Recent",
            category: (tr.category as any) || "NEXUS",
            title: tr.goal?.startsWith("⚡") ? tr.goal : `Multi-Agent DAG: ${tr.goal?.slice(0, 60)}...`,
            detail: tr.tasks?.[0]?.output || `Executed ${tr.tasks?.length || 0} specialist sub-tasks across ContextBus.`,
            status: tr.success ? "success" : "warning",
            taskGraph: tr,
          }));
          setLogs((prev) => {
            const existingIds = new Set(prev.map((p) => p.id));
            const newTraces = fetchedLogs.filter((f) => !existingIds.has(f.id));
            return [...newTraces, ...prev];
          });
        }
      })
      .catch(() => {});

    // Fetch live PRISM routing history
    fetch(`${API_BASE}/routing/history?limit=20`)
      .then((r) => r.json())
      .then((data) => {
        if (data && Array.isArray(data.history) && data.history.length > 0) {
          const fetchedRouting: ActivityLog[] = data.history.map((h: any, idx: number) => ({
            id: h.id || `route-${Date.now()}-${idx}`,
            timestamp: "Recent",
            category: "Routing",
            title: `PRISM Intent Routed: ${h.agent_codename || h.agent?.toUpperCase()}`,
            detail: h.decision_summary,
            status: "success",
            routingExplanation: h,
          }));
          setLogs((prev) => {
            const existingIds = new Set(prev.map((p) => p.id));
            const newRouting = fetchedRouting.filter((f) => !existingIds.has(f.id));
            return [...newRouting, ...prev];
          });
        }
      })
      .catch(() => {});

    // Fetch live OpenTelemetry distributed traces
    fetchDistributedTraces(25)
      .then((data) => {
        if (data && Array.isArray(data.traces) && data.traces.length > 0) {
          const fetchedTraces: ActivityLog[] = data.traces.map((tr) => ({
            id: tr.trace_id,
            timestamp: tr.timestamp
              ? new Date(tr.timestamp * 1000).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                })
              : "Recent",
            category: "Tracing",
            title: `Distributed Trace: ${tr.root_name.replace("copper.", "")}`,
            detail: `Traced ${tr.spans_count} spans across execution pipeline (${tr.duration_ms.toFixed(1)}ms)`,
            status: tr.status === "error" ? "error" : "success",
            distributedTrace: tr,
          }));
          setLogs((prev) => {
            const existingIds = new Set(prev.map((p) => p.id));
            const newTraces = fetchedTraces.filter((f) => !existingIds.has(f.id));
            return [...newTraces, ...prev];
          });
        }
      })
      .catch(() => {});
  }, []);

  const clearLogs = () => {
    setLogs([]);
  };

  const toggleExpand = (id: string) => {
    setExpandedLogs((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const runExampleDAGSimulation = async () => {
    setIsSimulating(true);
    try {
      const res = await fetch(`${API_BASE}/orchestration/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message:
            "Analyze this CSV sales data, write a Python script to visualize trends, and create a PDF report with the findings",
        }),
      });
      const data = await res.json();
      if (data && data.tasks) {
        const newTrace: ActivityLog = {
          id: `dag-${Date.now()}`,
          timestamp: "Just now",
          category: "NEXUS",
          title: "Multi-Agent DAG Collaboration: CSV Sales Pipeline",
          detail: `Decomposed into ${data.tasks.length} tasks with DeepSeek-R1 reasoning.`,
          status: "success",
          taskGraph: {
            dag_id: `dag_${Date.now()}`,
            goal: data.goal || "Analyze CSV sales data and synthesize PDF report",
            status: "done",
            total_duration_ms: 1250,
            tasks: data.tasks.map((t: any) => ({
              ...t,
              status: "done",
              execution_time_ms: t.duration_ms || 240,
              output: `Simulated specialist output from ${t.agent} for '${t.title || t.id}'.`,
            })),
            inter_agent_messages: [
              {
                id: "m1",
                sender: "OMNI",
                recipient: "AXIS",
                message_type: "data_transfer",
                content: "Transferred analyzed dataset for trend script generation.",
              },
              {
                id: "m2",
                sender: "AXIS",
                recipient: "FORGE",
                message_type: "task_handoff",
                content: "Passed matplotlib script to sandbox executor.",
              },
              {
                id: "m3",
                sender: "FORGE",
                recipient: "KINESIS",
                message_type: "data_transfer",
                content: "Captured chart output artifact for PDF document.",
              },
            ],
            artifacts: [
              {
                name: "Sales_Trends_Analysis.pdf",
                url: "#",
                agent: "KINESIS",
              },
            ],
          },
        };
        setLogs((prev) => [newTrace, ...prev]);
        setFilter("nexus");
      }
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setIsSimulating(false);
    }
  };

  const filtered =
    filter === "all"
      ? logs
      : logs.filter((l) => l.category.toLowerCase() === filter.toLowerCase());

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case "cache":
        return <Zap size={14} className="text-amber-400 fill-amber-400" />;
      case "tools":
        return <Wrench size={14} className="text-cyan-400" />;
      case "nexus":
        return <Network size={14} className="text-purple-400" />;
      case "guardian":
        return <ShieldAlert size={14} className="text-amber-400" />;
      case "routing":
        return <Compass size={14} className="text-purple-400" />;
      case "inference":
        return <Cpu size={14} className="text-emerald-400" />;
      case "tracing":
        return <Radio size={14} className="text-purple-400 animate-pulse" />;
      default:
        return <Terminal size={14} className="text-accent-400" />;
    }
  };

  return (
    <div className="modern-page p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap">
            <Activity size={20} className="text-purple-400" />
            <h1 className="text-xl font-bold text-white tracking-tight font-sans">
              Agent Activity Stream & Multi-Agent Execution Trace Panel
            </h1>
            <span className="text-[10px] text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-0.5 rounded-full font-mono">
              Live Execution & Governance Log
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            NEXUS DAG decomposition, PRISM explainable routing telemetry, and local tool execution traces
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBenchmarkAnalytics(!showBenchmarkAnalytics)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-sans font-semibold transition-all ${
              showBenchmarkAnalytics
                ? "bg-purple-600 text-white border-purple-500 shadow-lg shadow-purple-900/50"
                : "bg-slate-900 hover:bg-slate-800 border-slate-800 text-slate-300 hover:text-white"
            }`}
          >
            <BarChart3 size={13} />
            <span>PRISM Benchmarks</span>
          </button>

          <button
            onClick={runExampleDAGSimulation}
            disabled={isSimulating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-950/80 hover:bg-purple-900 border border-purple-600/50 text-purple-200 font-sans font-semibold text-xs shadow-lg shadow-purple-950/50 transition-all disabled:opacity-50"
          >
            {isSimulating ? (
              <ThinkingOrb state="connecting" size={20} theme="dark" />
            ) : (
              <Sparkles size={13} className="text-purple-400" />
            )}
            <span>Trigger Example Multi-Agent Flow</span>
          </button>

          <button
            onClick={clearLogs}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <Trash2 size={13} />
            <span>Clear Logs</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {(
          [
            "all",
            "ambient",
            "tracing",
            "nexus",
            "cache",
            "tools",
            "routing",
            "guardian",
            "inference",
            "firewall",
            "memory",
          ] as const
        ).map((cat) => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-3 py-1.5 rounded-lg capitalize transition-all ${
              filter === cat
                ? "bg-purple-500/20 text-purple-400 border border-purple-500/40 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {cat === "ambient"
              ? "🖥️ Passive Context & Sessions"
              : cat === "tracing"
              ? "📡 Distributed Traces (OTel)"
              : cat === "nexus"
              ? "NEXUS Multi-Agent DAG"
              : cat === "cache"
              ? "⚡ Instant Recall"
              : cat}
          </button>
        ))}
      </div>

      {/* PRISM Systematic Benchmark Analytics & Calibration Panel */}
      {showBenchmarkAnalytics && (
        <div className="transition-all animate-in fade-in duration-300">
          <RoutingBenchmarkView />
        </div>
      )}

      {/* Passive Context & Activity Timeline View (Phase 1 Ambient Intelligence) */}
      {filter === "ambient" && (
        <div className="space-y-4 animate-in fade-in duration-300">
          <PassiveActivityTimeline />
        </div>
      )}

      {/* Active Execution Pipeline Card */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
          <span>Active Collaboration Architecture</span>
          <span className="text-[10px] text-purple-400 bg-purple-950/40 border border-purple-800/40 px-2.5 py-0.5 rounded-full font-mono">
            DeepSeek-R1 DAG + Redis Pub/Sub Active
          </span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-purple-400 font-bold font-sans text-xs">
              <Network size={14} />
              <span>NEXUS Planner & DAG Orchestrator</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Decomposes high-level requests into atomic sub-tasks with dependency graphs, parallel execution tiers, and final response synthesis.
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 font-bold font-sans text-xs">
              <Terminal size={14} />
              <span>Redis Pub/Sub Shared Context Bus</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Distributed event broadcasting, inter-agent data passing, and real-time state sharing across specialist squads (OMNI, AXIS, FORGE, KINESIS).
            </p>
          </div>
        </div>
      </div>

      {/* Real-time Activity Event Logs */}
      <div className="space-y-4">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Execution Traces ({filtered.length})
        </h3>
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-slate-900/60 rounded-2xl border border-slate-800">
            No activity logs match the selected filter.
          </div>
        ) : (
          filtered.map((log) => {
            // Render OpenTelemetry distributed trace waterfall
            if (log.distributedTrace) {
              return (
                <div key={log.id} className="transition-all">
                  <TraceWaterfallVisualizer
                    trace={log.distributedTrace}
                    defaultExpanded={filter === "tracing" || !!expandedLogs[log.id]}
                  />
                </div>
              );
            }

            // Render PRISM explainable routing card with horizontal bar charts, keyword highlights, and stage progression
            if (log.routingExplanation) {
              return (
                <div key={log.id} className="transition-all">
                  <RoutingExplanationCard
                    data={log.routingExplanation}
                    initialExpanded={filter === "routing" || !!expandedLogs[log.id]}
                  />
                </div>
              );
            }

            const isExpanded = !!expandedLogs[log.id];
            const hasIO = !!log.io;
            const hasGraph = !!log.taskGraph;

            return (
              <div
                key={log.id}
                className="rounded-2xl bg-slate-900/70 border border-slate-800 overflow-hidden hover:border-slate-700 transition-all space-y-2 p-4"
              >
                <div
                  onClick={() => hasIO && toggleExpand(log.id)}
                  className={`flex items-start justify-between gap-3 ${
                    hasIO ? "cursor-pointer select-none" : ""
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 mt-0.5">
                      {getCategoryIcon(log.category)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white font-sans text-xs">
                          {log.title}
                        </span>
                        <span
                          className={`px-2 py-0.2 rounded text-[10px] font-bold uppercase ${
                            log.category === "NEXUS"
                              ? "bg-purple-950/60 text-purple-400 border border-purple-800/40"
                              : log.category === "Tools"
                              ? "bg-cyan-950/60 text-cyan-400 border border-cyan-800/40"
                              : "bg-slate-800 text-accent-400"
                          }`}
                        >
                          {log.category}
                        </span>
                        {log.io?.duration_ms && (
                          <span className="flex items-center gap-1 text-[10px] text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                            <Clock size={10} />
                            {log.io.duration_ms}ms
                          </span>
                        )}
                      </div>
                      <p className="text-slate-400 text-[11px] mt-1">
                        {log.detail}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-slate-500">
                      {log.timestamp}
                    </span>
                    {hasIO && (
                      <div className="text-slate-400 hover:text-white">
                        {isExpanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
                      </div>
                    )}
                  </div>
                </div>

                {/* If Log Contains Task Graph, Render Full Interactive Visualizer */}
                {hasGraph && log.taskGraph && (
                  <div className="mt-3">
                    <TaskGraphVisualizer graph={log.taskGraph} />
                  </div>
                )}

                {/* If Log Contains Distributed Trace, Render Waterfall Visualizer */}
                {log.distributedTrace && (
                  <div className="mt-3">
                    <TraceWaterfallVisualizer trace={log.distributedTrace} />
                  </div>
                )}

                {/* Expandable I/O Drawer for simple tools */}
                {hasIO && isExpanded && (
                  <div className="p-4 bg-slate-950/90 border border-slate-800/80 rounded-xl space-y-3 mt-2">
                    {log.io?.arguments && (
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                          Arguments (JSON Payload)
                        </div>
                        <pre className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-cyan-300 text-[11px] overflow-x-auto">
                          {JSON.stringify(log.io.arguments, null, 2)}
                        </pre>
                      </div>
                    )}

                    {log.io?.output && (
                      <div>
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                          Output Result / Observation
                        </div>
                        <pre className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-emerald-300 text-[11px] overflow-x-auto whitespace-pre-wrap">
                          {typeof log.io.output === "object"
                            ? JSON.stringify(log.io.output, null, 2)
                            : String(log.io.output)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
