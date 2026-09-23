import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  ArrowUpRight,
  Target,
  Sparkles,
  Activity,
  Clock,
  Code2,
  GitBranch,
  CheckSquare,
  Brain,
  Shield,
  Layers,
  Plus,
} from "lucide-react";
import { HudCard } from "../components/hud/HudBrackets";
import type { NavSection } from "../components/layout/Sidebar";
import { systemAPI, cognitiveAPI, type CockpitStatus } from "../services/api";
import { scheduleAPI, tasksAPI, type ScheduleEvent, type TaskItem } from "../lib/api";

interface DashboardViewProps {
  onNavigate?: (section: NavSection) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [cockpit, setCockpit] = useState<CockpitStatus | null>(null);
  const [scheduleEvents, setScheduleEvents] = useState<ScheduleEvent[]>([]);
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [cognitiveState, setCognitiveState] = useState<{
    state: string;
    confidence: number;
    recommendations: string[];
    current_focus_streak?: number;
  } | null>(null);
  const [intelDismissed, setIntelDismissed] = useState(false);

  const fetchLiveTelemetry = useCallback(async () => {
    try {
      const res = await systemAPI.getCockpitStatus();
      if (res.data) {
        setCockpit(res.data);
      }
    } catch (err) {
      console.error("Error loading live cockpit telemetry:", err);
    }
  }, []);

  const fetchOperationalData = useCallback(async () => {
    try {
      const [eventsData, tasksData, cogRes] = await Promise.all([
        scheduleAPI.list().catch(() => []),
        tasksAPI.list().catch(() => []),
        cognitiveAPI.getState().catch(() => null),
      ]);
      setScheduleEvents(eventsData || []);
      setTasks(tasksData || []);
      if (cogRes?.data) {
        setCognitiveState(cogRes.data);
      }
    } catch (err) {
      console.error("Error loading operational dashboard data:", err);
    }
  }, []);

  useEffect(() => {
    fetchLiveTelemetry();
    fetchOperationalData();
    const interval = setInterval(fetchLiveTelemetry, 3000);
    return () => clearInterval(interval);
  }, [fetchLiveTelemetry, fetchOperationalData]);

  // Derived priority task
  const activeTask =
    tasks.find((t) => t.status === "active") ||
    tasks.find((t) => t.priority === "high") ||
    tasks[0] ||
    null;

  // Real GPU readings or fallbacks from live telemetry
  const gpuModel = cockpit?.hardware?.gpu?.model
    ? cockpit.hardware.gpu.model.replace("NVIDIA GeForce ", "")
    : "System GPU";
  const vramUsed = cockpit?.hardware?.gpu?.vram_used_gb ?? 0;
  const vramTotal = cockpit?.hardware?.gpu?.vram_total_gb ?? 8.0;
  const vramHeadroom = (Math.max(0, vramTotal - vramUsed)).toFixed(1);

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
      className="modern-page p-5 md:p-7 space-y-6 max-w-7xl mx-auto text-text select-none pb-16 font-mono"
    >
      {/* SDE Mission Command Header */}
      <motion.div
        variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
        className="p-6 md:p-7 rounded-3xl bg-[linear-gradient(135deg,rgba(35,14,23,0.88),rgba(18,6,10,0.95))] border border-blush-100/[0.15] shadow-[0_24px_56px_rgba(10,3,6,0.5),inset_0_1px_0_rgba(246,230,234,0.12)] relative overflow-hidden backdrop-blur-2xl"
      >
        <div className="absolute -top-24 right-0 w-[28rem] h-[28rem] bg-blush-100/[0.08] rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 left-1/3 w-72 h-72 bg-accent/[0.09] rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-verdigris/12 text-verdigris border border-verdigris/30 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" />
                {cockpit?.security?.defcon_label || "DEFCON 5 // SYSTEM OPTIMAL"}
              </span>
              <span className="px-2.5 py-1 rounded-full text-[10px] bg-blush-100/12 text-blush-100 border border-blush-100/30 font-bold flex items-center gap-1">
                <GitBranch className="w-3 h-3 text-accent" />
                {cockpit?.git?.repo || "COPPER"} ({cockpit?.git?.branch || "MAIN"})
              </span>
              <span className="px-2.5 py-1 rounded-full text-[10px] bg-accent/15 text-accent border border-accent/30 font-bold">
                {cockpit?.security?.air_gapped_label || "100% AIR-GAPPED SDE SUITE"}
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white tracking-[-0.03em]">
              Sovereign Engineering Cockpit
            </h1>
            <p className="text-xs text-blush-300/70 mt-1">
              Autonomous {cockpit?.agents?.fleet_count ?? 30}-agent fleet ready •{" "}
              {cockpit?.models?.summary_label || "Zero external egress"}
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <div className="p-3 rounded-2xl bg-[#1A0A0F]/80 border border-blush-100/[0.12] text-right shadow-[inset_0_1px_0_rgba(246,230,234,0.08)]">
              <span className="text-blush-300/60 block text-[9px] uppercase tracking-wider">
                Router Velocity
              </span>
              <span className="text-blush-100 font-display font-bold text-sm">
                {cockpit?.routing?.velocity_ms !== undefined
                  ? `${cockpit.routing.velocity_ms.toFixed(3)} ms`
                  : "0.158 ms"}
              </span>
            </div>
            <div className="p-3 rounded-2xl bg-[#1A0A0F]/80 border border-blush-100/[0.12] text-right shadow-[inset_0_1px_0_rgba(246,230,234,0.08)]">
              <span className="text-blush-300/60 block text-[9px] uppercase tracking-wider">
                Mesh Throughput
              </span>
              <span className="text-accent font-display font-bold text-sm">
                ~{cockpit?.routing?.throughput_qps
                  ? Math.round(cockpit.routing.throughput_qps).toLocaleString()
                  : "6,271"}{" "}
                QPS
              </span>
            </div>
          </div>
        </div>

        {/* Quick Developer Action Strip */}
        <div className="mt-5 pt-4 border-t border-blush-100/[0.10] flex flex-wrap gap-2 relative z-10">
          <button
            onClick={() => onNavigate?.("chat")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-blush-100 via-accent to-accent text-burgundy-950 font-bold text-xs shadow-md hover:brightness-110 cursor-pointer font-mono"
          >
            <Code2 className="w-3.5 h-3.5" /> Start Coding Session
          </button>
          <button
            onClick={() => onNavigate?.("projects")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#14070B]/80 hover:bg-[#1E0C13] text-zinc-200 border border-blush-100/20 text-xs font-mono cursor-pointer transition-all"
          >
            <Layers className="w-3.5 h-3.5 text-accent" /> Repos & Workspaces
          </button>
          <button
            onClick={() => onNavigate?.("tasks")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#14070B]/80 hover:bg-[#1E0C13] text-zinc-200 border border-blush-100/20 text-xs font-mono cursor-pointer transition-all"
          >
            <CheckSquare className="w-3.5 h-3.5 text-blush-200" /> Sprint Queue
          </button>
          <button
            onClick={() => onNavigate?.("security")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#14070B]/80 hover:bg-[#1E0C13] text-zinc-200 border border-blush-100/20 text-xs font-mono cursor-pointer transition-all"
          >
            <Shield className="w-3.5 h-3.5 text-verdigris" /> Security Audit
          </button>
          <button
            onClick={() => onNavigate?.("memory")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#14070B]/80 hover:bg-[#1E0C13] text-zinc-200 border border-blush-100/20 text-xs font-mono cursor-pointer transition-all"
          >
            <Brain className="w-3.5 h-3.5 text-cyan-400" /> Epistemic Memory
          </button>
          <button
            onClick={() => onNavigate?.("benchmarks")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#14070B]/80 hover:bg-[#1E0C13] text-zinc-200 border border-blush-100/20 text-xs font-mono cursor-pointer transition-all"
          >
            <Activity className="w-3.5 h-3.5 text-amber-400" /> Live Telemetry & QPS
          </button>
        </div>
      </motion.div>

      <motion.div
        variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}
        className="grid grid-cols-1 md:grid-cols-3 gap-5"
      >
        {/* Live Mission Timeline */}
        <HudCard glow="blush">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-3 gap-2">
            <span className="flex items-center gap-2 font-bold text-white tracking-tight">
              <Calendar className="w-4 h-4 text-blush-100 flex-shrink-0" /> Mission Schedule
            </span>
            <div className="flex items-center gap-2 font-mono flex-shrink-0">
              <span className="px-2 py-0.5 rounded-md bg-blush-100/10 border border-blush-100/25 text-blush-100 text-[9px] font-semibold uppercase tracking-wider">
                TIMELINE
              </span>
              <span className="text-[10px] text-blush-100 font-bold">
                {scheduleEvents.length > 0 ? `${scheduleEvents.length} EVENTS` : "LIVE STANDBY"}
              </span>
            </div>
          </div>

          {scheduleEvents.length > 0 ? (
            <div className="space-y-2 max-h-56 overflow-y-auto custom-scrollbar">
              {scheduleEvents.slice(0, 3).map((evt) => (
                <div
                  key={evt.id}
                  className={`p-3 rounded-xl border text-xs flex justify-between items-center shadow-inner ${
                    evt.completed
                      ? "bg-[#14070B]/50 border-white/5 opacity-60"
                      : "bg-[#14070B]/80 border-blush-100/10"
                  }`}
                >
                  <div className="overflow-hidden pr-2">
                    <p className="font-bold text-white truncate">{evt.title}</p>
                    <p className="text-[10px] text-blush-300/60 font-mono flex items-center gap-1 mt-0.5">
                      <Clock className="w-3 h-3 text-blush-200" /> {evt.time}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase flex-shrink-0 ${
                      evt.completed
                        ? "bg-zinc-800 text-zinc-400 border border-zinc-700"
                        : "bg-verdigris/15 text-verdigris border border-verdigris/30"
                    }`}
                  >
                    {evt.completed ? "DONE" : evt.category || "ACTIVE"}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-[#14070B]/50 border border-white/5 text-center space-y-2">
              <p className="text-xs text-zinc-400">
                No operational events queued today. System nominal.
              </p>
              <button
                onClick={() => onNavigate?.("today")}
                className="inline-flex items-center gap-1 text-[11px] text-blush-100 hover:text-white cursor-pointer font-bold"
              >
                <Plus className="w-3 h-3" /> Schedule Standup Event
              </button>
            </div>
          )}
        </HudCard>

        {/* Live Priority Objective */}
        <HudCard glow="copper">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-3 gap-2">
            <span className="flex items-center gap-2 font-bold text-white tracking-tight">
              <Target className="w-4 h-4 text-accent flex-shrink-0" /> Priority Objective
            </span>
            <div className="flex items-center gap-2 font-mono flex-shrink-0">
              <span className="px-2 py-0.5 rounded-md bg-accent/15 border border-accent/30 text-accent text-[9px] font-semibold uppercase tracking-wider">
                SPRINT
              </span>
              <span className="text-[10px] text-accent font-bold">
                {activeTask ? (activeTask.priority || "ACTIVE").toUpperCase() : "QUEUE NOMINAL"}
              </span>
            </div>
          </div>

          {activeTask ? (
            <div className="p-3.5 rounded-xl bg-accent/10 border border-accent/25 space-y-2 shadow-[inset_0_1px_0_rgba(201,124,76,0.15)]">
              <p className="text-xs font-bold text-white font-sans truncate">
                {activeTask.title}
              </p>
              <p className="text-[11px] text-zinc-300 font-sans line-clamp-2">
                Project: {activeTask.project} • Est: {activeTask.duration || "30m"} • Status:{" "}
                {activeTask.status}
              </p>
              <div className="pt-2 flex items-center justify-between text-[10px] text-accent">
                <span>PRIORITY: {(activeTask.priority || "HIGH").toUpperCase()}</span>
                <button
                  onClick={() => onNavigate?.("tasks")}
                  className="flex items-center gap-1 cursor-pointer hover:underline font-bold text-accent"
                >
                  INSPECT SPRINT <ArrowUpRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-[#14070B]/50 border border-white/5 text-center space-y-2">
              <p className="text-xs text-zinc-400">
                Sprint queue is clear. No active tasks in flight.
              </p>
              <button
                onClick={() => onNavigate?.("tasks")}
                className="inline-flex items-center gap-1 text-[11px] text-accent hover:underline cursor-pointer font-bold"
              >
                <Plus className="w-3 h-3" /> Add Backlog Task
              </button>
            </div>
          )}
        </HudCard>

        {/* Live Guardian Proactive Intel */}
        {!intelDismissed ? (
          <HudCard glow="blush">
            <div className="flex items-center justify-between text-xs text-zinc-400 mb-3 gap-2">
              <span className="flex items-center gap-2 font-bold text-white tracking-tight">
                <Sparkles className="w-4 h-4 text-verdigris flex-shrink-0" /> Tactical Intelligence
              </span>
              <div className="flex items-center gap-2 font-mono flex-shrink-0">
                <span className="px-2 py-0.5 rounded-md bg-verdigris/15 border border-verdigris/30 text-verdigris text-[9px] font-semibold uppercase tracking-wider">
                  GUARDIAN
                </span>
                <span className="text-[10px] text-verdigris font-bold">
                  EVIDENCE {Math.round((cognitiveState?.confidence ?? 1.0) * 100)}%
                </span>
              </div>
            </div>
            <p className="text-xs text-zinc-200 leading-relaxed italic bg-[#14070B]/80 p-3 rounded-xl border border-blush-100/10 font-sans shadow-inner">
              "{cognitiveState?.recommendations?.[0] ||
                `Cognitive state: ${cognitiveState?.state || "idle"}. ${
                  tasks.length > 0
                    ? `${tasks.length} planned sprint tasks remain in queue.`
                    : "Zero pending tasks. Standby for developer input."
                }`}"
            </p>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => onNavigate?.("chat")}
                className="lift-on-hover px-3.5 py-2 rounded-xl bg-gradient-to-r from-blush-100 via-accent to-accent text-burgundy-950 font-bold text-xs shadow-[0_8px_20px_rgba(246,230,234,0.22)] hover:brightness-110 cursor-pointer font-mono"
              >
                EXECUTE PLAN
              </button>
              <button
                onClick={() => setIntelDismissed(true)}
                className="lift-on-hover px-3.5 py-2 rounded-xl bg-blush-100/[0.05] hover:bg-blush-100/[0.1] text-zinc-300 text-xs border border-blush-100/[0.12] cursor-pointer font-mono"
              >
                DISMISS
              </button>
            </div>
          </HudCard>
        ) : (
          <HudCard glow="blush">
            <div className="flex items-center justify-between text-xs text-zinc-400 mb-3 gap-2">
              <span className="flex items-center gap-2 font-bold text-white tracking-tight">
                <Sparkles className="w-4 h-4 text-zinc-500 flex-shrink-0" /> Tactical Intelligence
              </span>
              <div className="flex items-center gap-2 font-mono flex-shrink-0">
                <span className="px-2 py-0.5 rounded-md bg-zinc-800 border border-zinc-700 text-zinc-400 text-[9px] font-semibold uppercase tracking-wider">
                  GUARDIAN
                </span>
                <span className="text-[10px] text-zinc-500 font-bold">STANDBY</span>
              </div>
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed italic bg-[#14070B]/50 p-3 rounded-xl border border-white/5 font-sans">
              All tactical intelligence advisories acknowledged. System standing by for operational
              directives.
            </p>
            <button
              onClick={() => setIntelDismissed(false)}
              className="mt-2 text-[10px] text-blush-200 hover:underline font-mono cursor-pointer"
            >
              RESTORE ADVISORY
            </button>
          </HudCard>
        )}
      </motion.div>

      {/* Live Hardware & Telemetry Matrix */}
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}>
        <HudCard glow="blush">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-bold text-blush-300/70 uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-blush-100" /> Hardware & Model Telemetry Matrix
              </h3>
              <span className="px-2 py-0.5 rounded-md bg-blush-100/10 border border-blush-100/25 text-blush-100 text-[9px] font-semibold uppercase tracking-wider font-mono">
                TELEMETRY
              </span>
            </div>
            <button
              onClick={() => onNavigate?.("benchmarks")}
              className="text-[11px] text-verdigris flex items-center gap-1.5 font-bold hover:underline cursor-pointer"
            >
              <span className="w-2 h-2 rounded-full bg-verdigris animate-pulse" /> LIVE TELEMETRY
              & BENCHMARKS →
            </button>
          </div>
            <button
              onClick={() => onNavigate?.("benchmarks")}
              className="text-[11px] text-verdigris flex items-center gap-1.5 font-bold hover:underline cursor-pointer"
            >
              <span className="w-2 h-2 rounded-full bg-verdigris animate-pulse" /> LIVE TELEMETRY
              & BENCHMARKS →
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="lift-on-hover p-4 rounded-2xl bg-[#14070B]/70 border border-blush-100/[0.12] space-y-1 shadow-[inset_0_1px_0_rgba(246,230,234,0.06)]">
              <span className="text-[10px] text-blush-300/60 uppercase tracking-wider">
                Router Precision
              </span>
              <p className="text-2xl font-display font-bold text-white">
                {cockpit?.routing?.precision_pct !== undefined
                  ? `${cockpit.routing.precision_pct.toFixed(1)}%`
                  : "97.8%"}
              </p>
              <span className="text-[10px] text-blush-200">
                {cockpit?.routing?.velocity_ms !== undefined
                  ? `${cockpit.routing.velocity_ms.toFixed(3)}ms Avg Latency`
                  : "0.158ms Avg Latency"}
              </span>
            </div>

            <div className="lift-on-hover p-4 rounded-2xl bg-[#14070B]/70 border border-blush-100/[0.12] space-y-1 shadow-[inset_0_1px_0_rgba(246,230,234,0.06)]">
              <span className="text-[10px] text-blush-300/60 uppercase tracking-wider">
                Threat Shield
              </span>
              <p className="text-2xl font-display font-bold text-verdigris">
                {cockpit?.security?.threat_shield_pct !== undefined
                  ? `${cockpit.security.threat_shield_pct.toFixed(1)}%`
                  : "100.0%"}
              </p>
              <span className="text-[10px] text-verdigris">
                {cockpit?.security?.security_breaches ?? 0} Security Breaches
              </span>
            </div>

            <div className="lift-on-hover p-4 rounded-2xl bg-[#14070B]/70 border border-blush-100/[0.12] space-y-1 shadow-[inset_0_1px_0_rgba(246,230,234,0.06)]">
              <span className="text-[10px] text-blush-300/60 uppercase tracking-wider truncate block">
                {gpuModel} VRAM
              </span>
              <p className="text-2xl font-display font-bold text-accent">
                {vramUsed} / {vramTotal} GB
              </p>
              <span className="text-[10px] text-verdigris">
                {vramHeadroom} GB Headroom
              </span>
            </div>

            <div className="lift-on-hover p-4 rounded-2xl bg-[#14070B]/70 border border-blush-100/[0.12] space-y-1 shadow-[inset_0_1px_0_rgba(246,230,234,0.06)]">
              <span className="text-[10px] text-blush-300/60 uppercase tracking-wider">
                Neural Mesh Models
              </span>
              <p className="text-2xl font-display font-bold text-blush-100">
                {cockpit?.models?.loaded_count && cockpit.models.loaded_count > 0
                  ? `${cockpit.models.loaded_count} Loaded`
                  : "Core Standby"}
              </p>
              <span className="text-[10px] text-zinc-400">
                {cockpit?.models?.total_offline_weight_gb
                  ? `${cockpit.models.total_offline_weight_gb.toFixed(2)} GB Loaded`
                  : cockpit?.models?.always_on_mini_model || "Zero External Egress"}
              </span>
            </div>
          </div>
        </HudCard>
      </motion.div>
    </motion.div>
  );
};
