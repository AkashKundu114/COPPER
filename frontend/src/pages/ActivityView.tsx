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
} from "lucide-react";
import { API_BASE } from "../lib/api";
import {
  TaskGraphVisualizer,
  type TaskGraphData,
} from "../components/chat/TaskGraphVisualizer";

interface ActivityLog {
  id: string;
  timestamp: string;
  category: "Tools" | "NEXUS" | "Routing" | "Guardian" | "Firewall" | "Inference" | "Memory";
  title: string;
  detail: string;
  status: "success" | "warning" | "blocked" | "running";
  io?: {
    arguments?: Record<string, any>;
    output?: any;
    duration_ms?: number;
    guardian_level?: number;
  };
  taskGraph?: TaskGraphData;
}

const INITIAL_LOGS: ActivityLog[] = [
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
    timestamp: "6m ago",
    category: "Routing",
    title: "Autonomous Intent Dispatched",
    detail: "Classified intent -> Routed to AXIS (Forge AI Engineer).",
    status: "success",
  },
];

export const ActivityView: React.FC = () => {
  const [logs, setLogs] = useState<ActivityLog[]>(INITIAL_LOGS);
  const [filter, setFilter] = useState<string>("all");
  const [expandedLogs, setExpandedLogs] = useState<Record<string, boolean>>({ "tool-1": true });
  const [isSimulating, setIsSimulating] = useState(false);

  useEffect(() => {
    // Fetch live traces from backend if available
    fetch(`${API_BASE}/api/v1/orchestration/traces?limit=10`)
      .then((r) => r.json())
      .then((traces) => {
        if (Array.isArray(traces) && traces.length > 0) {
          const fetchedLogs: ActivityLog[] = traces.map((tr) => ({
            id: tr.dag_id || `trace-${Date.now()}`,
            timestamp: "Recent",
            category: "NEXUS",
            title: `Multi-Agent DAG: ${tr.goal?.slice(0, 60)}...`,
            detail: `Executed ${tr.tasks?.length || 0} specialist sub-tasks across ContextBus.`,
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
      case "tools":
        return <Wrench size={14} className="text-cyan-400" />;
      case "nexus":
        return <Network size={14} className="text-purple-400" />;
      case "guardian":
        return <ShieldAlert size={14} className="text-amber-400" />;
      case "inference":
        return <Cpu size={14} className="text-emerald-400" />;
      default:
        return <Terminal size={14} className="text-accent-400" />;
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
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
            NEXUS DAG decomposition, Redis context bus dispatches, and local tool telemetry
          </p>
        </div>

        <div className="flex items-center gap-2">
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
            "nexus",
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
            {cat === "nexus" ? "NEXUS Multi-Agent DAG" : cat}
          </button>
        ))}
      </div>

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
