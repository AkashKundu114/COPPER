import React, { useState } from "react";
import {
  Brain,
  Search,
  Code2,
  Terminal,
  FileText,
  Clock,
  Eye,
  Palette,
  ShieldAlert,
  ShieldCheck,
  Activity,
  Layers,
  Globe,
  Lock,
  FolderTree,
  Calendar,
  Table2,
  ScrollText,
  Scan,
  MousePointerClick,
  AppWindow,
  ScanText,
  Layout,
  Film,
  DownloadCloud,
  Ghost,
  BookMarked,
  Radio,
  RadioTower,
  Clapperboard,
  AlertCircle,
  Share2,
  Mic,
  Volume2,
  Mail,
  Languages,
  SlidersHorizontal,
  ListTodo,
  KeyRound,
  Boxes,
  FileCode2,
  Bug,
  GitMerge,
  Zap,
  BarChart3,
  Binary,
  RefreshCw,
  Target,
  Sparkles,
  Compass,
  ArrowRight,
  BookOpen,
  Network,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronRight,
  MessageSquare,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export interface TaskGraphNode {
  id: string;
  agent: string;
  title?: string;
  instruction: string;
  depends_on: string[];
  output_key?: string;
  status: "pending" | "running" | "done" | "failed";
  output?: any;
  error?: string | null;
  execution_time_ms?: number;
}

export interface InterAgentMessageItem {
  id: string;
  dag_id?: string;
  sender: string;
  recipient: string;
  message_type: string;
  content: string;
  timestamp?: number;
  payload?: Record<string, any>;
}

export interface TaskGraphArtifact {
  name: string;
  url: string;
  agent?: string;
  task_id?: string;
}

export interface TaskGraphData {
  dag_id?: string;
  goal: string;
  total_tasks?: number;
  tasks: TaskGraphNode[];
  status?: "running" | "done" | "failed";
  total_duration_ms?: number;
  final_response?: string;
  inter_agent_messages?: InterAgentMessageItem[];
  artifacts?: TaskGraphArtifact[];
  active_step?: string;
}

interface Props {
  graph: TaskGraphData;
  isCompact?: boolean;
  className?: string;
}

const AGENT_THEMES: Record<
  string,
  { name: string; icon: any; color: string; border: string; bg: string; text: string }
> = {
  // Core Reasoning
  CHRONOS: { name: "CHRONOS", icon: Compass, color: "#10b981", border: "border-emerald-500/40", bg: "bg-emerald-950/25", text: "text-emerald-400" },
  REMINDER: { name: "CHRONOS", icon: Clock, color: "#10b981", border: "border-emerald-500/40", bg: "bg-emerald-950/25", text: "text-emerald-400" },
  MNEMONIC: { name: "MNEMONIC", icon: Brain, color: "#14b8a6", border: "border-teal-500/40", bg: "bg-teal-950/25", text: "text-teal-400" },
  AEGIS: { name: "AEGIS", icon: ShieldAlert, color: "#f59e0b", border: "border-amber-500/40", bg: "bg-amber-950/25", text: "text-amber-400" },
  SYNAPSE: { name: "SYNAPSE", icon: Network, color: "#22c55e", border: "border-green-500/40", bg: "bg-green-950/25", text: "text-green-400" },
  LUMEN: { name: "LUMEN", icon: Sparkles, color: "#fbbf24", border: "border-yellow-500/40", bg: "bg-yellow-950/25", text: "text-yellow-400" },
  OMNI: { name: "OMNI", icon: Search, color: "#f97316", border: "border-orange-500/40", bg: "bg-orange-950/25", text: "text-orange-400" },
  RESEARCH: { name: "OMNI", icon: Search, color: "#f97316", border: "border-orange-500/40", bg: "bg-orange-950/25", text: "text-orange-400" },

  // Code Engineering
  AXIS: { name: "AXIS", icon: Code2, color: "#06b6d4", border: "border-cyan-500/40", bg: "bg-cyan-950/25", text: "text-cyan-400" },
  CODING: { name: "AXIS", icon: Code2, color: "#06b6d4", border: "border-cyan-500/40", bg: "bg-cyan-950/25", text: "text-cyan-400" },
  CYPHER: { name: "CYPHER", icon: FileCode2, color: "#0ea5e9", border: "border-sky-500/40", bg: "bg-sky-950/25", text: "text-sky-400" },
  CRUCIBLE: { name: "CRUCIBLE", icon: Bug, color: "#ef4444", border: "border-red-500/40", bg: "bg-red-950/25", text: "text-red-400" },
  FORGE: { name: "FORGE", icon: Terminal, color: "#3b82f6", border: "border-blue-500/40", bg: "bg-blue-950/25", text: "text-blue-400" },
  AUTOMATION: { name: "FORGE", icon: Terminal, color: "#3b82f6", border: "border-blue-500/40", bg: "bg-blue-950/25", text: "text-blue-400" },
  SANDBOX: { name: "FORGE", icon: Terminal, color: "#3b82f6", border: "border-blue-500/40", bg: "bg-blue-950/25", text: "text-blue-400" },
  NEXUS: { name: "NEXUS", icon: GitMerge, color: "#8b5cf6", border: "border-violet-500/40", bg: "bg-violet-950/25", text: "text-violet-400" },
  ARGUS: { name: "ARGUS", icon: ShieldCheck, color: "#e11d48", border: "border-rose-500/40", bg: "bg-rose-950/25", text: "text-rose-400" },
  APEX: { name: "APEX", icon: Zap, color: "#10b981", border: "border-emerald-500/40", bg: "bg-emerald-950/25", text: "text-emerald-400" },
  QUANTA: { name: "QUANTA", icon: BarChart3, color: "#6366f1", border: "border-indigo-500/40", bg: "bg-indigo-950/25", text: "text-indigo-400" },
  TENSOR: { name: "TENSOR", icon: Binary, color: "#ec4899", border: "border-pink-500/40", bg: "bg-pink-950/25", text: "text-pink-400" },
  GOLIATH: { name: "GOLIATH", icon: Boxes, color: "#64748b", border: "border-slate-700/60", bg: "bg-slate-900/60", text: "text-slate-300" },
  PIVOT: { name: "PIVOT", icon: RefreshCw, color: "#22c55e", border: "border-green-500/40", bg: "bg-green-950/25", text: "text-green-400" },

  // OS & Desktop Automation
  ATLAS: { name: "ATLAS", icon: FolderTree, color: "#0ea5e9", border: "border-sky-500/40", bg: "bg-sky-950/25", text: "text-sky-400" },
  KINETIC: { name: "KINETIC", icon: Calendar, color: "#f59e0b", border: "border-amber-500/40", bg: "bg-amber-950/25", text: "text-amber-400" },
  PULSE: { name: "PULSE", icon: Activity, color: "#10b981", border: "border-emerald-500/40", bg: "bg-emerald-950/25", text: "text-emerald-400" },
  ZENITH: { name: "ZENITH", icon: Target, color: "#8b5cf6", border: "border-violet-500/40", bg: "bg-violet-950/25", text: "text-violet-400" },
  LEDGER: { name: "LEDGER", icon: Table2, color: "#eab308", border: "border-yellow-500/40", bg: "bg-yellow-950/25", text: "text-yellow-400" },
  VAULT: { name: "VAULT", icon: Lock, color: "#ef4444", border: "border-red-500/40", bg: "bg-red-950/25", text: "text-red-400" },
  ECHO: { name: "ECHO", icon: ScrollText, color: "#64748b", border: "border-slate-700/60", bg: "bg-slate-900/60", text: "text-slate-300" },
  WARDEN: { name: "WARDEN", icon: ShieldAlert, color: "#dc2626", border: "border-red-600/40", bg: "bg-red-950/25", text: "text-red-400" },
  PROXY: { name: "PROXY", icon: Globe, color: "#06b6d4", border: "border-cyan-500/40", bg: "bg-cyan-950/25", text: "text-cyan-400" },

  // Vision & Screen RPA
  HAWK: { name: "HAWK", icon: Scan, color: "#ec4899", border: "border-pink-500/40", bg: "bg-pink-950/25", text: "text-pink-400" },
  TALON: { name: "TALON", icon: MousePointerClick, color: "#f43f5e", border: "border-rose-500/40", bg: "bg-rose-950/25", text: "text-rose-400" },
  PORTAL: { name: "PORTAL", icon: AppWindow, color: "#a855f7", border: "border-purple-500/40", bg: "bg-purple-950/25", text: "text-purple-400" },
  IRIS: { name: "IRIS", icon: ScanText, color: "#d946ef", border: "border-fuchsia-500/40", bg: "bg-fuchsia-950/25", text: "text-fuchsia-400" },
  VISION: { name: "IRIS", icon: ScanText, color: "#d946ef", border: "border-fuchsia-500/40", bg: "bg-fuchsia-950/25", text: "text-fuchsia-400" },
  CANVAS: { name: "CANVAS", icon: Layout, color: "#3b82f6", border: "border-blue-500/40", bg: "bg-blue-950/25", text: "text-blue-400" },
  PRISM: { name: "PRISM", icon: Layers, color: "#8b5cf6", border: "border-violet-500/40", bg: "bg-violet-950/25", text: "text-violet-400" },
  RENDER: { name: "RENDER", icon: Film, color: "#f97316", border: "border-orange-500/40", bg: "bg-orange-950/25", text: "text-orange-400" },
  SPECTRE: { name: "SPECTRE", icon: Eye, color: "#14b8a6", border: "border-teal-500/40", bg: "bg-teal-950/25", text: "text-teal-400" },
  PICASSO: { name: "PICASSO", icon: Palette, color: "#fbbf24", border: "border-yellow-500/40", bg: "bg-yellow-950/25", text: "text-yellow-400" },
  IMAGE: { name: "PICASSO", icon: Palette, color: "#fbbf24", border: "border-yellow-500/40", bg: "bg-yellow-950/25", text: "text-yellow-400" },

  // Web & Streaming
  RAPTOR: { name: "RAPTOR", icon: DownloadCloud, color: "#22c55e", border: "border-green-500/40", bg: "bg-green-950/25", text: "text-green-400" },
  PHANTOM: { name: "PHANTOM", icon: Ghost, color: "#6366f1", border: "border-indigo-500/40", bg: "bg-indigo-950/25", text: "text-indigo-400" },
  VANGUARD: { name: "VANGUARD", icon: BookMarked, color: "#0ea5e9", border: "border-sky-500/40", bg: "bg-sky-950/25", text: "text-sky-400" },
  AETHER: { name: "AETHER", icon: Radio, color: "#a855f7", border: "border-purple-500/40", bg: "bg-purple-950/25", text: "text-purple-400" },
  BEACON: { name: "BEACON", icon: RadioTower, color: "#10b981", border: "border-emerald-500/40", bg: "bg-emerald-950/25", text: "text-emerald-400" },
  DIRECTOR: { name: "DIRECTOR", icon: Clapperboard, color: "#f43f5e", border: "border-rose-500/40", bg: "bg-rose-950/25", text: "text-rose-400" },
  GLITCH: { name: "GLITCH", icon: AlertCircle, color: "#f59e0b", border: "border-amber-500/40", bg: "bg-amber-950/25", text: "text-amber-400" },
  SPIDER: { name: "SPIDER", icon: Share2, color: "#06b6d4", border: "border-cyan-500/40", bg: "bg-cyan-950/25", text: "text-cyan-400" },

  // Audio & Language & Documents
  SONAR: { name: "SONAR", icon: Mic, color: "#06b6d4", border: "border-cyan-500/40", bg: "bg-cyan-950/25", text: "text-cyan-400" },
  ORACLE: { name: "ORACLE", icon: Volume2, color: "#8b5cf6", border: "border-violet-500/40", bg: "bg-violet-950/25", text: "text-violet-400" },
  HERMES: { name: "HERMES", icon: Mail, color: "#3b82f6", border: "border-blue-500/40", bg: "bg-blue-950/25", text: "text-blue-400" },
  AEON: { name: "AEON", icon: Clock, color: "#f59e0b", border: "border-amber-500/40", bg: "bg-amber-950/25", text: "text-amber-400" },
  POLYGLOT: { name: "POLYGLOT", icon: Languages, color: "#10b981", border: "border-emerald-500/40", bg: "bg-emerald-950/25", text: "text-emerald-400" },
  SIREN: { name: "SIREN", icon: SlidersHorizontal, color: "#ec4899", border: "border-pink-500/40", bg: "bg-pink-950/25", text: "text-pink-400" },
  VORTEX: { name: "VORTEX", icon: ListTodo, color: "#14b8a6", border: "border-teal-500/40", bg: "bg-teal-950/25", text: "text-teal-400" },
  ENIGMA: { name: "ENIGMA", icon: KeyRound, color: "#ef4444", border: "border-red-500/40", bg: "bg-red-950/25", text: "text-red-400" },
  KINESIS: { name: "KINESIS", icon: FileText, color: "#a855f7", border: "border-purple-500/40", bg: "bg-purple-950/25", text: "text-purple-400" },
  DOCUMENT: { name: "KINESIS", icon: FileText, color: "#a855f7", border: "border-purple-500/40", bg: "bg-purple-950/25", text: "text-purple-400" },

  // Master Orchestration & Synthesis
  CHAT: { name: "NEXUS", icon: Sparkles, color: "#10b981", border: "border-emerald-500/40", bg: "bg-emerald-950/25", text: "text-emerald-400" },
  SYNTHESIZER: { name: "SYNTHESIS", icon: Sparkles, color: "#10b981", border: "border-emerald-500/40", bg: "bg-emerald-950/25", text: "text-emerald-400" },
};

export function TaskGraphVisualizer({ graph, className = "" }: Props) {
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({});
  const [showMessages, setShowMessages] = useState<boolean>(false);

  const tasks = graph.tasks || [];
  const messages = graph.inter_agent_messages || [];
  const artifacts = graph.artifacts || [];

  const completedCount = tasks.filter((t) => t.status === "done").length;
  const runningCount = tasks.filter((t) => t.status === "running").length;
  const failedCount = tasks.filter((t) => t.status === "failed").length;

  const isComplete = tasks.length > 0 && completedCount + failedCount === tasks.length;
  const isRunning = runningCount > 0 || (!isComplete && tasks.length > 0);

  const toggleNodeExpand = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setExpandedNodes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getAgentTheme = (agent: string) => {
    const key = agent.toUpperCase().trim();
    for (const [k, v] of Object.entries(AGENT_THEMES)) {
      if (k === key || key.includes(k)) return v;
    }
    return {
      name: agent,
      icon: Zap,
      color: "#94a3b8",
      border: "border-slate-700",
      bg: "bg-slate-900/40",
      text: "text-slate-300",
    };
  };

  // Group tasks into topological layers
  const layers: TaskGraphNode[][] = [];
  const assigned = new Set<string>();

  let remaining = [...tasks];
  let depth = 0;

  while (remaining.length > 0 && depth < 10) {
    const currentLayer = remaining.filter((t) =>
      t.depends_on.every((d) => assigned.has(d)),
    );

    if (currentLayer.length === 0) {
      // Break cycle or unresolvable dependencies
      layers.push(remaining);
      break;
    }

    layers.push(currentLayer);
    currentLayer.forEach((t) => assigned.add(t.id));
    remaining = remaining.filter((t) => !assigned.has(t.id));
    depth++;
  }

  return (
    <div
      className={`rounded-2xl border border-purple-900/40 bg-slate-950/80 backdrop-blur-xl shadow-2xl p-4 text-xs font-mono text-slate-200 overflow-hidden ${className}`}
    >
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3.5 border-b border-purple-950/60">
        <div className="flex items-center gap-2.5">
          <div
            className={`p-2 rounded-xl border ${
              isRunning
                ? "bg-purple-950/60 border-purple-500/50 text-purple-400 animate-pulse"
                : failedCount > 0
                ? "bg-danger-950/60 border-danger-500/50 text-danger-400"
                : "bg-emerald-950/60 border-emerald-500/50 text-emerald-400"
            }`}
          >
            <Network size={16} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-white font-sans text-sm tracking-tight">
                NEXUS Multi-Agent DAG
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  isRunning
                    ? "bg-purple-950 text-purple-400 border border-purple-800/50 animate-pulse"
                    : failedCount > 0
                    ? "bg-danger-950 text-danger-400 border border-danger-800/50"
                    : "bg-emerald-950 text-emerald-400 border border-emerald-800/50"
                }`}
              >
                {isRunning ? "Executing DAG" : failedCount > 0 ? "Failed" : "Synthesized"}
              </span>
              {graph.total_duration_ms ? (
                <span className="text-[10px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded-md border border-slate-800">
                  {graph.total_duration_ms}ms
                </span>
              ) : null}
            </div>
            <p className="text-[11px] text-slate-400 font-sans mt-0.5 line-clamp-1 max-w-xl">
              {graph.goal || "Multi-Agent Collaborative Workflow"}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={() => setShowMessages(!showMessages)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-[11px] transition-all ${
                showMessages
                  ? "bg-purple-950/80 border-purple-500/50 text-purple-300"
                  : "bg-slate-900/80 hover:bg-slate-800 border-slate-800 text-slate-400 hover:text-white"
              }`}
              title="Toggle Inter-Agent Redis Context Bus Stream"
            >
              <MessageSquare size={12} />
              <span>Bus ({messages.length})</span>
            </button>
          )}

          <div className="text-[11px] text-slate-400 bg-slate-900/90 border border-slate-800 px-2.5 py-1.5 rounded-xl flex items-center gap-1.5">
            <Layers size={12} className="text-purple-400" />
            <span>
              {completedCount}/{tasks.length} Done
            </span>
          </div>
        </div>
      </div>

      {/* Interactive Topological DAG Hierarchy */}
      <div className="py-4 space-y-4">
        {layers.map((layer, layerIdx) => (
          <div key={layerIdx} className="space-y-2">
            {layers.length > 1 && (
              <div className="flex items-center gap-2 px-1">
                <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                  {layerIdx === 0 ? "Phase 1: Initial Dispatch" : `Phase ${layerIdx + 1}: Dependent Layer`}
                </span>
                <div className="flex-1 h-[1px] bg-slate-800/60" />
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {layer.map((task) => {
                const theme = getAgentTheme(task.agent);
                const Icon = theme.icon;
                const isExpanded = !!expandedNodes[task.id];
                const isActive = graph.active_step === task.id || task.status === "running";

                return (
                  <motion.div
                    key={task.id}
                    layout
                    onClick={() => toggleNodeExpand(task.id)}
                    className={`rounded-xl border p-3 cursor-pointer transition-all ${
                      isActive
                        ? "bg-purple-950/30 border-purple-500/70 shadow-lg shadow-purple-950/50"
                        : task.status === "done"
                        ? "bg-slate-900/70 border-slate-800 hover:border-slate-700"
                        : task.status === "failed"
                        ? "bg-danger-950/20 border-danger-800/60 hover:border-danger-700"
                        : "bg-slate-950/40 border-slate-900 opacity-60"
                    }`}
                  >
                    {/* Node Header */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={`p-1.5 rounded-lg border ${theme.bg} ${theme.border} ${theme.text}`}
                        >
                          <Icon size={13} />
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-bold text-white font-sans text-xs">
                              {task.id}
                            </span>
                            <span
                              className={`px-1.5 py-0.2 rounded text-[9.5px] font-bold uppercase ${theme.bg} ${theme.text}`}
                            >
                              {task.agent}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Status Icon & Latency */}
                      <div className="flex items-center gap-1.5">
                        {task.status === "running" ? (
                          <div className="flex items-center gap-1 text-[10px] text-purple-400">
                            <Loader2 size={12} className="animate-spin" />
                            <span className="hidden sm:inline">Active</span>
                          </div>
                        ) : task.status === "done" ? (
                          <div className="flex items-center gap-1 text-[10px] text-emerald-400">
                            <CheckCircle2 size={12} />
                            {task.execution_time_ms ? (
                              <span className="text-[9.5px] text-slate-400 font-mono">
                                {task.execution_time_ms}ms
                              </span>
                            ) : null}
                          </div>
                        ) : task.status === "failed" ? (
                          <AlertTriangle size={13} className="text-danger-400" />
                        ) : (
                          <Clock size={12} className="text-slate-500" />
                        )}

                        <div className="text-slate-500 hover:text-slate-300 ml-1">
                          {isExpanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                        </div>
                      </div>
                    </div>

                    {/* Task Title & Instruction */}
                    <div className="mt-2 text-[11px]">
                      <p className="font-medium text-slate-200 line-clamp-1 font-sans">
                        {task.title || task.instruction}
                      </p>
                    </div>

                    {/* Dependencies indicator */}
                    {task.depends_on.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center gap-1 text-[10px] text-slate-400">
                        <ArrowRight size={10} className="text-purple-400" />
                        <span>depends on:</span>
                        <div className="flex items-center gap-1">
                          {task.depends_on.map((dep) => (
                            <span
                              key={dep}
                              className="px-1.5 py-0.2 rounded bg-purple-950/80 text-purple-300 border border-purple-800/40 font-bold"
                            >
                              {dep}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Expanded Drawer */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.15 }}
                          className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-2 text-[11px]"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div>
                            <div className="text-[9.5px] uppercase font-bold text-slate-400 mb-1">
                              Instruction:
                            </div>
                            <p className="text-slate-300 bg-black/40 p-2 rounded-lg leading-relaxed border border-slate-800">
                              {task.instruction}
                            </p>
                          </div>

                          {task.output && (
                            <div>
                              <div className="text-[9.5px] uppercase font-bold text-emerald-400 mb-1">
                                Output Observation:
                              </div>
                              <pre className="p-2 rounded-lg bg-black/60 border border-emerald-900/30 text-emerald-300 text-[10.5px] max-h-36 overflow-y-auto custom-scrollbar whitespace-pre-wrap">
                                {typeof task.output === "object"
                                  ? JSON.stringify(task.output, null, 2)
                                  : String(task.output)}
                              </pre>
                            </div>
                          )}

                          {task.error && (
                            <div>
                              <div className="text-[9.5px] uppercase font-bold text-danger-400 mb-1">
                                Error:
                              </div>
                              <pre className="p-2 rounded-lg bg-danger-950/40 border border-danger-800/40 text-danger-300 text-[10.5px]">
                                {task.error}
                              </pre>
                            </div>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Generated Artifacts Bar */}
      {artifacts.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2">
          <span className="text-[10.5px] font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1">
            <BookOpen size={12} />
            <span>Generated Artifacts:</span>
          </span>
          {artifacts.map((art, idx) => (
            <a
              key={idx}
              href={art.url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-purple-950/80 hover:bg-purple-900 border border-purple-700/50 text-purple-300 hover:text-white transition-colors text-[11px]"
            >
              <FileText size={11} />
              <span className="font-semibold">{art.name}</span>
            </a>
          ))}
        </div>
      )}

      {/* Inter-Agent Shared Context Bus Log Drawer */}
      <AnimatePresence>
        {showMessages && messages.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 pt-3 border-t border-purple-950/80 space-y-2"
          >
            <div className="flex items-center justify-between text-[10px] text-slate-400 uppercase font-bold tracking-wider">
              <span>Inter-Agent Redis Pub/Sub Messages</span>
              <span className="text-purple-400">{messages.length} Dispatches</span>
            </div>

            <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
              {messages.map((msg, i) => (
                <div
                  key={msg.id || i}
                  className="p-2 rounded-lg bg-black/40 border border-slate-800 flex items-start gap-2 text-[10.5px]"
                >
                  <div className="flex items-center gap-1 font-bold flex-shrink-0">
                    <span className="text-amber-400">{msg.sender}</span>
                    <ArrowRight size={10} className="text-slate-500" />
                    <span className="text-cyan-400">{msg.recipient}</span>
                  </div>
                  <div className="flex-1 text-slate-300 break-words">{msg.content}</div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
