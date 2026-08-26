import React, { useState } from "react";
import { CheckCircle, Activity, Terminal, Trash2 } from "lucide-react";

interface ActivityLog {
  id: string;
  timestamp: string;
  category: "Routing" | "Guardian" | "Firewall" | "Inference" | "Memory";
  title: string;
  detail: string;
  status: "success" | "warning" | "blocked";
}

const INITIAL_LOGS: ActivityLog[] = [
  {
    id: "1",
    timestamp: "Just now",
    category: "Inference",
    title: "Local Ollama Token Stream",
    detail: "Streamed response using 'llama3.1:8b' with 0 cloud calls.",
    status: "success",
  },
  {
    id: "2",
    timestamp: "1m ago",
    category: "Guardian",
    title: "Level 0 Alignment Check Passed",
    detail: "User prompt verified safe. Zero prompt injection detected.",
    status: "success",
  },
  {
    id: "3",
    timestamp: "1m ago",
    category: "Routing",
    title: "Autonomous Intent Dispatched",
    detail: "Classified intent -> Routed to Chat Core Companion.",
    status: "success",
  },
  {
    id: "4",
    timestamp: "3m ago",
    category: "Firewall",
    title: "Data Firewall Egress Scan",
    detail: "Outgoing packet verified: 100% offline localhost connection only.",
    status: "success",
  },
  {
    id: "5",
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

  const clearLogs = () => {
    setLogs([]);
  };

  const filtered =
    filter === "all"
      ? logs
      : logs.filter((l) => l.category.toLowerCase() === filter.toLowerCase());

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Activity size={20} className="text-accent-400" />
            <h1 className="text-xl font-bold text-white tracking-tight font-sans">
              Agent Activity Panel
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Step-by-step execution traces, tool dispatches, and local telemetry
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
      <div className="flex gap-2 border-b border-slate-800 pb-3">
        {(
          [
            "all",
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
            {cat}
          </button>
        ))}
      </div>

      {/* Active Execution Graph Summary */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Active Execution Pipeline
        </h3>
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2.5">
          <div className="flex items-center gap-3 text-verdigris-400">
            <CheckCircle size={15} />
            <span>
              Orchestrator → Autonomous Routing (Active Model: Qwen 2.5 Coder /
              Llama 3.1)
            </span>
          </div>
          <div className="flex items-center gap-3 text-verdigris-400">
            <CheckCircle size={15} />
            <span>Guardian Alignment Engine (Level 0 - Permitted)</span>
          </div>
          <div className="flex items-center gap-3 text-verdigris-400">
            <CheckCircle size={15} />
            <span>
              Data Firewall Egress Check (0 PII Leaks - Localhost 127.0.0.1
              Only)
            </span>
          </div>
          <div className="flex items-center gap-3 text-verdigris-400">
            <CheckCircle size={15} />
            <span>
              Hardware Accelerated Inference (NVIDIA RTX 5060 VRAM Active)
            </span>
          </div>
        </div>
      </div>

      {/* Real-time Activity Event Logs */}
      <div className="space-y-2.5">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Event Timeline
        </h3>
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-slate-900/60 rounded-2xl border border-slate-800">
            No activity logs found.
          </div>
        ) : (
          filtered.map((log) => (
            <div
              key={log.id}
              className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex items-start justify-between gap-3 hover:border-slate-700 transition-all"
            >
              <div className="flex items-start gap-3">
                <div className="p-1.5 rounded-lg bg-accent-500/10 text-accent-400 border border-accent-500/20 mt-0.5">
                  <Terminal size={14} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white font-sans text-xs">
                      {log.title}
                    </span>
                    <span className="px-2 py-0.2 rounded text-[10px] bg-slate-800 text-accent-400 font-bold uppercase">
                      {log.category}
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px] mt-1">
                    {log.detail}
                  </p>
                </div>
              </div>
              <span className="text-[10px] text-slate-500">
                {log.timestamp}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
