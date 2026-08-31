import React, { useState } from "react";
import {
  CheckCircle,
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
} from "lucide-react";

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
}

const INITIAL_LOGS: ActivityLog[] = [
  {
    id: "1",
    timestamp: "Just now",
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
    id: "2",
    timestamp: "1m ago",
    category: "NEXUS",
    title: "Multi-Agent DAG Collaboration Planned",
    detail: "Decomposed complex request into 3 parallel sub-tasks [OMNI, AXIS, KINESIS].",
    status: "success",
    io: {
      arguments: {
        goal: "Research local algorithms, test implementation, and author summary PDF",
        tasks: [
          { id: "T1", agent: "OMNI", instruction: "Research vector indexing algorithms" },
          { id: "T2", agent: "AXIS", instruction: "Implement HNSW benchmark script", depends_on: ["T1"] },
          { id: "T3", agent: "KINESIS", instruction: "Generate summary PDF documentation", depends_on: ["T2"] },
        ],
      },
      output: "All 3 sub-tasks synthesized successfully into final response.",
      duration_ms: 1840.5,
    },
  },
  {
    id: "3",
    timestamp: "2m ago",
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
    id: "4",
    timestamp: "3m ago",
    category: "Guardian",
    title: "Level 3 Safety Evaluation Passed",
    detail: "Command evaluated through safety gates. Zero dangerous triggers detected.",
    status: "success",
  },
  {
    id: "5",
    timestamp: "4m ago",
    category: "Routing",
    title: "Autonomous Intent Dispatched",
    detail: "Classified intent -> Routed to AXIS (Forge AI Engineer).",
    status: "success",
  },
  {
    id: "6",
    timestamp: "5m ago",
    category: "Firewall",
    title: "Data Firewall Egress Scan",
    detail: "Outgoing packet verified: 100% offline localhost connection only.",
    status: "success",
  },
  {
    id: "7",
    timestamp: "10m ago",
    category: "Memory",
    title: "Epistemic State Synchronization",
    detail: "Updated working profile facts in local vector store.",
    status: "success",
  },
];

export const ActivityView: React.FC = () => {
  const [logs, setLogs] = useState<ActivityLog[]>(INITIAL_LOGS);
  const [filter, setFilter] = useState<string>("all");
  const [expandedLogs, setExpandedLogs] = useState<Record<string, boolean>>({ "1": true, "2": true });

  const clearLogs = () => {
    setLogs([]);
  };

  const toggleExpand = (id: string) => {
    setExpandedLogs((prev) => ({ ...prev, [id]: !prev[id] }));
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
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Activity size={20} className="text-accent-400" />
            <h1 className="text-xl font-bold text-white tracking-tight font-sans">
              Agent Activity & Tool Trace Panel
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Step-by-step tool dispatches, NEXUS multi-agent DAGs, and local safety telemetry
          </p>
        </div>
        <button
          onClick={clearLogs}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <Trash2 size={13} />
          <span>Clear Logs</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {(
          [
            "all",
            "tools",
            "nexus",
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
                ? "bg-accent-500/20 text-accent-400 border border-accent-500/40 font-bold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {cat === "nexus" ? "NEXUS DAG" : cat}
          </button>
        ))}
      </div>

      {/* Active Execution Pipeline Card */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
          <span>Active Subsystem Pipelines</span>
          <span className="text-[10px] text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-2 py-0.5 rounded-full font-mono">
            Structured Function Calling & NEXUS Ready
          </span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 font-bold font-sans text-xs">
              <Wrench size={14} />
              <span>Tool Execution Framework</span>
            </div>
            <p className="text-[11px] text-slate-400">
              9 Builtin Concrete Tools (File, Shell, Sandbox, Web, Memory, Chronos) gated by Guardian Engine.
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-purple-400 font-bold font-sans text-xs">
              <Network size={14} />
              <span>NEXUS Multi-Agent DAG Planner</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Topological DAG executor running independent sub-agents in parallel with DeepSeek-R1 synthesis.
            </p>
          </div>
        </div>
      </div>

      {/* Real-time Activity Event Logs */}
      <div className="space-y-3">
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

            return (
              <div
                key={log.id}
                className="rounded-xl bg-slate-900/70 border border-slate-800 overflow-hidden hover:border-slate-700 transition-all"
              >
                <div
                  onClick={() => hasIO && toggleExpand(log.id)}
                  className={`p-4 flex items-start justify-between gap-3 ${
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
                            log.category === "Tools"
                              ? "bg-cyan-950/60 text-cyan-400 border border-cyan-800/40"
                              : log.category === "NEXUS"
                              ? "bg-purple-950/60 text-purple-400 border border-purple-800/40"
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
                        {log.io?.guardian_level !== undefined && log.io.guardian_level > 0 && (
                          <span className="text-[10px] text-amber-400 bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-800/30">
                            Guardian L{log.io.guardian_level}
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

                {/* Expandable I/O Drawer */}
                {hasIO && isExpanded && (
                  <div className="p-4 bg-slate-950/90 border-t border-slate-800/80 space-y-3">
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
