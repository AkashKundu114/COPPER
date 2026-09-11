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
  Loader2,
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

const INITIAL_LOGS: ActivityLog[] = [
  {
    id: "otel-sample-1",
    timestamp: "Just now",
    category: "Tracing",
    title: "Distributed Trace: websocket.request",
    detail: "OpenTelemetry request traced across WebSocket -> Router -> Guardian -> Agent -> LLM -> Response (412.5ms)",
    status: "success",
    distributedTrace: {
      trace_id: "4bf92f3577b34da6a3ce929d0e0e4736",
      root_name: "copper.websocket.request",
      timestamp: Date.now() - 30000,
      duration_ms: 412.5,
      status: "success",
      spans_count: 6,
      root_attributes: {
        "copper.session_id": "sess-live-trace",
        "copper.message": "Analyze system performance and explain trace telemetry",
        "copper.mode": "auto",
        "copper.provider": "ollama",
      },
      grafana_url: "http://localhost:3000/explore?left=%5B%7B%22datasource%22%3A%22Tempo%22%2C%22queries%22%3A%5B%7B%22query%22%3A%224bf92f3577b34da6a3ce929d0e0e4736%22%7D%5D%7D%5D",
      spans: [
        {
          span_id: "00f067aa0ba902b7",
          name: "copper.websocket.request",
          parent_id: null,
          start_time_ms: 0,
          end_time_ms: 412.5,
          duration_ms: 412.5,
          offset_ms: 0,
          status: "UNSET",
          attributes: { "copper.session_id": "sess-live-trace", "copper.client": "websocket" },
        },
        {
          span_id: "5fb397be34d23b0f",
          name: "copper.router",
          parent_id: "00f067aa0ba902b7",
          start_time_ms: 2.1,
          end_time_ms: 4.8,
          duration_ms: 2.7,
          offset_ms: 2.1,
          status: "UNSET",
          attributes: {
            "router.selected_agent": "coding",
            "router.confidence": 0.98,
            "router.stage": "fast_pattern_scoring",
            "router.agent_codename": "AXIS",
          },
        },
        {
          span_id: "38924bce89ef23aa",
          name: "copper.guardian",
          parent_id: "00f067aa0ba902b7",
          start_time_ms: 5.2,
          end_time_ms: 7.1,
          duration_ms: 1.9,
          offset_ms: 5.2,
          status: "UNSET",
          attributes: {
            "guardian.action": "Analyze system performance and explain trace telemetry",
            "guardian.is_consequential": false,
            "guardian.verdict_level": "ALLOW",
            "guardian.reasoning": "Benign analytical query cleared",
          },
        },
        {
          span_id: "90ab245d8ef012cb",
          name: "copper.agent",
          parent_id: "00f067aa0ba902b7",
          start_time_ms: 8.0,
          end_time_ms: 405.0,
          duration_ms: 397.0,
          offset_ms: 8.0,
          status: "UNSET",
          attributes: {
            "agent.type": "coding",
            "agent.name": "AXIS",
            "agent.mode": "auto",
            "agent.target_model": "qwen2.5-coder-abliterated:7b",
          },
        },
        {
          span_id: "c092ab345ef67812",
          name: "copper.llm",
          parent_id: "90ab245d8ef012cb",
          start_time_ms: 12.0,
          end_time_ms: 402.0,
          duration_ms: 390.0,
          offset_ms: 12.0,
          status: "UNSET",
          attributes: {
            "llm.model": "qwen2.5-coder-abliterated:7b",
            "llm.provider": "ollama",
            "llm.prompt_tokens": 54,
            "llm.completion_tokens": 142,
            "llm.total_tokens": 196,
            "llm.tokens_per_sec": 44.2,
            "llm.ttft_ms": 145.2,
            "llm.latency_ms": 390.0,
          },
        },
        {
          span_id: "1234567890abcdef",
          name: "copper.response",
          parent_id: "00f067aa0ba902b7",
          start_time_ms: 405.2,
          end_time_ms: 412.5,
          duration_ms: 7.3,
          offset_ms: 405.2,
          status: "UNSET",
          attributes: {
            "response.length": 580,
            "response.total_time_ms": 412.5,
            "response.tokens_per_sec": 44.2,
          },
        },
      ],
    },
  },
  {
    id: "nexus-example-1",
    timestamp: "Just now",
    category: "NEXUS",
    title: "Multi-Agent DAG Collaboration: CSV Analysis & PDF Synthesis",
    detail: "Decomposed complex sales analytics request into 4 specialist tasks [OMNI, AXIS, FORGE, KINESIS].",
    status: "success",
    taskGraph: {
      dag_id: "dag_sales_demo",
      goal: "Analyze sales CSV data, write Python visualization script, execute in sandbox, and generate PDF report",
      status: "done",
      total_duration_ms: 1840.5,
      tasks: [
        {
          id: "T1",
          agent: "OMNI",
          title: "Analyze CSV Data & Extract Key Insights",
          instruction: "Analyze sales metrics, identify 28% quarterly revenue growth and top electronics category.",
          depends_on: [],
          status: "done",
          execution_time_ms: 320.4,
          output: "OMNI Data Analysis: Identified $1.42M Q3 revenue (+28% QoQ). Top category: Enterprise Cloud (+42%).",
        },
        {
          id: "T2",
          agent: "AXIS",
          title: "Author Matplotlib Visualization Script",
          instruction: "Write a matplotlib Python script based on {T1.output} to plot revenue curves.",
          depends_on: ["T1"],
          status: "done",
          execution_time_ms: 410.2,
          output: "```python\nimport matplotlib.pyplot as plt\nmonths = ['Jul', 'Aug', 'Sep']\nrev = [1.1, 1.25, 1.42]\nplt.plot(months, rev, marker='o')\nplt.title('Q3 Sales Growth')\nplt.savefig('sales_trends.png')\n```",
        },
        {
          id: "T2.1",
          agent: "FORGE",
          title: "Execute Script in Sandbox & Capture Chart",
          instruction: "Execute {T2.output} inside isolated Forge Sandbox and save sales_trends.png.",
          depends_on: ["T2"],
          status: "done",
          execution_time_ms: 185.0,
          output: "Forge Sandbox Execution: Status 0 (Success). Generated image artifact: 'sales_trends.png' (640x480).",
        },
        {
          id: "T3",
          agent: "KINESIS",
          title: "Generate Downloadable PDF Executive Report",
          instruction: "Synthesize insights {T1.output} and charts {T2.1.output} into a formal PDF report.",
          depends_on: ["T1", "T2.1"],
          status: "done",
          execution_time_ms: 580.6,
          output: "Document Artifact Created Successfully\n- Filename: Q3_Executive_Sales_Report.pdf\n- Format: PDF (1.2 MB)\n- Download URL: [Q3_Executive_Sales_Report.pdf](/api/v1/documents/download/sales_report.pdf)",
        },
      ],
      inter_agent_messages: [
        {
          id: "msg-1",
          sender: "OMNI",
          recipient: "AXIS",
          message_type: "data_transfer",
          content: "Transferred extracted Q3 revenue metrics ($1.42M, +28%) for plot script generation.",
        },
        {
          id: "msg-2",
          sender: "AXIS",
          recipient: "FORGE",
          message_type: "task_handoff",
          content: "Matplotlib visualization script compiled. Dispatched to Forge Sandbox.",
        },
        {
          id: "msg-3",
          sender: "FORGE",
          recipient: "KINESIS",
          message_type: "data_transfer",
          content: "Sandbox executed successfully. Saved 'sales_trends.png' for PDF report insertion.",
        },
        {
          id: "msg-4",
          sender: "BUS",
          recipient: "CHAT",
          message_type: "task_handoff",
          content: "All 4 sub-tasks completed. Dispatched to CHAT for final executive synthesis.",
        },
      ],
      artifacts: [
        {
          name: "Q3_Executive_Sales_Report.pdf",
          url: "/api/v1/documents/download/sales_report.pdf",
          agent: "KINESIS",
          task_id: "T3",
        },
      ],
    },
  },
  {
    id: "tool-1",
    timestamp: "2m ago",
    category: "Tools",
    title: "Tool Invoked: python_execute",
    detail: "Executed Python script in isolated Forge Sandbox environment.",
    status: "success",
    io: {
      arguments: {
        code: "import math\nprint(f'Pi calculation: {math.pi * 2}')",
        timeout: 10,
      },
      output: {
        status: "success",
        stdout: "Pi calculation: 6.283185307179586\n",
        stderr: "",
        exit_code: 0,
      },
      duration_ms: 12.4,
      guardian_level: 2,
    },
  },
  {
    id: "tool-2",
    timestamp: "4m ago",
    category: "Tools",
    title: "Tool Invoked: file_read",
    detail: "Safely read local configuration file 'backend/app/core/config.py'.",
    status: "success",
    io: {
      arguments: { path: "backend/app/core/config.py" },
      output: { status: "success", size_bytes: 3420, message: "File read complete." },
      duration_ms: 3.1,
      guardian_level: 0,
    },
  },
  {
    id: "guard-1",
    timestamp: "5m ago",
    category: "Guardian",
    title: "Level 3 Safety Evaluation Passed",
    detail: "Command evaluated through safety gates. Zero dangerous triggers detected.",
    status: "success",
  },
  {
    id: "route-1",
    timestamp: "Just now",
    category: "Routing",
    title: "Autonomous Intent Dispatched: AXIS",
    detail: "Routed to AXIS (confidence: 97%) because 'write a python script' matched CODING keywords",
    status: "success",
    routingExplanation: {
      id: "prism-sample-1",
      prompt: "Write a python script to sort an array using quicksort",
      agent: "coding",
      agent_codename: "AXIS",
      agent_display: "AXIS (Coding Engineer)",
      decision_summary: "Routed to AXIS (confidence: 97%) because 'write a python script' matched CODING keywords",
      confidence: 0.97,
      confidence_pct: 97,
      latency_ms: 0.048,
      route_stage: "fast_pattern_scoring",
      scores: { coding: 5.0, automation: 1.0, research: 0.5, document: 0.0 },
      score_breakdown: [
        { agent: "coding", agent_name: "AXIS (Coding Engineer)", codename: "AXIS", score: 5.0, percentage: 76.9, is_winner: true },
        { agent: "automation", agent_name: "FORGE (OS & Sandbox Automation)", codename: "FORGE", score: 1.0, percentage: 15.4, is_winner: false },
        { agent: "research", agent_name: "OMNI (Research & Analysis)", codename: "OMNI", score: 0.5, percentage: 7.7, is_winner: false },
      ],
      matched_keywords: ["\\b(write|debug|create)\\s+.*(script|code)\\b", "\\b(python|quicksort)\\b"],
      matched_terms: [
        { term: "Write a python script", start: 0, end: 21, agent: "coding" },
        { term: "quicksort", start: 45, end: 54, agent: "coding" },
      ],
      suppressed_rules: [
        {
          agent: "document",
          agent_name: "KINESIS (Document Architect)",
          codename: "KINESIS",
          pattern: "^(write a script to)\\b",
          matched_text: "Write a script to",
          penalty: 8.0,
          reason: "Negative rule 'Write a script to' suppressed document agent in favor of coding (-8.0 score)",
        },
      ],
      stage_progression: [
        { stage_id: "learned_memory_cache", stage_number: 0, name: "Learned Memory Cache", status: "passed", decision: "Cache miss -> Proceeded to Stage 1" },
        { stage_id: "fast_smalltalk_filter", stage_number: 1, name: "Fast Smalltalk Filter", status: "passed", decision: "No greeting detected -> Proceeded to Stage 2" },
        { stage_id: "fast_pattern_scoring", stage_number: 2, name: "Weighted Pattern & Suppression", status: "matched", decision: "Specialist rules fired -> Selected AXIS (Coding Engineer) with winning score 5.0" },
        { stage_id: "consequential_safety", stage_number: 3, name: "Consequential Action Safety Gate", status: "evaluated", decision: "Benign operation verified -> Execution cleared" },
        { stage_id: "fallback_resolution", stage_number: 4, name: "Micro-Router / Fallback", status: "bypassed", decision: "Bypassed (Resolved deterministically in earlier stages)" },
      ],
      is_consequential: false,
      cascade_risk: 0.16,
      sub_tasks: [],
      confidence_calibration: {
        raw_confidence: 0.97,
        calibrated_confidence: 0.96,
        calibrated_pct: 96,
        certainty_tier: "HIGH_CERTAINTY",
        certainty_description: "Optimal single-agent determinism",
        routing_entropy: 0.28,
        runner_up_margin: 4.0,
        is_consequential: false,
        cascade_risk: 0.16,
      },
    },
  },
];

export const ActivityView: React.FC = () => {
  const [logs, setLogs] = useState<ActivityLog[]>(INITIAL_LOGS);
  const [filter, setFilter] = useState<string>("all");
  const [expandedLogs, setExpandedLogs] = useState<Record<string, boolean>>({ "tool-1": true, "route-1": true });
  const [isSimulating, setIsSimulating] = useState(false);
  const [showBenchmarkAnalytics, setShowBenchmarkAnalytics] = useState(false);

  useEffect(() => {
    // Fetch live traces from backend if available
    fetch(`${API_BASE}/api/v1/orchestration/traces?limit=10`)
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
    fetch(`${API_BASE}/api/v1/routing/history?limit=20`)
      .then((r) => r.json())
      .then((data) => {
        if (data && Array.isArray(data.history) && data.history.length > 0) {
          const fetchedRouting: ActivityLog[] = data.history.map((h: any) => ({
            id: h.id || `route-${Date.now()}-${Math.random()}`,
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
      const res = await fetch(`${API_BASE}/api/v1/orchestration/plan`, {
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
              execution_time_ms: Math.floor(Math.random() * 300) + 100,
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
          <div className="flex items-center gap-2">
            <Activity size={20} className="text-purple-400" />
            <h1 className="text-xl font-bold text-white tracking-tight font-sans">
              Agent Activity & Multi-Agent Execution Trace Panel
            </h1>
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
              <Loader2 size={13} className="animate-spin text-purple-400" />
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
            {cat === "tracing"
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
