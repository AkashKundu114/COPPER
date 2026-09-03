import React, { useState } from "react";
import {
  Calendar,
  ArrowUpRight,
  Target,
  Sparkles,
  Activity,
  Clock,
} from "lucide-react";
import { TacticalGlobe } from "../components/hud/TacticalGlobe";
import { HudCard } from "../components/hud/HudBrackets";
import type { NavSection } from "../components/layout/Sidebar";

interface DashboardViewProps {
  onNavigate?: (section: NavSection) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [intelDismissed, setIntelDismissed] = useState(false);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto text-text select-none pb-16 font-mono">
      {/* Top Classified Mission Banner */}
      <div className="p-6 rounded-2xl bg-[#05080e]/90 border border-cyber-cyan/30 shadow-[0_0_25px_rgba(0,240,255,0.12)] relative overflow-hidden backdrop-blur-xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyber-cyan/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-verdigris/15 text-verdigris border border-verdigris/40 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" />
                DEFCON 5 // SYSTEM OPTIMAL
              </span>
              <span className="px-2.5 py-0.5 rounded text-[10px] bg-cyber-cyan/15 text-cyber-cyan border border-cyber-cyan/40 font-bold">
                GOD'S EYE TACTICAL SURVEILLANCE
              </span>
              <span className="px-2.5 py-0.5 rounded text-[10px] bg-accent/20 text-accent border border-accent/40 font-bold">
                100% AIR-GAPPED LOCALHOST
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-display font-bold text-white tracking-tight">
              Tactical Operations Center
            </h1>
            <p className="text-xs text-zinc-400 mt-1">
              Operator: <span className="text-white font-bold">Akash</span> • Core: C.O.P.P.E.R. v1.0.0 • 26 Neural Model Artifacts Loaded • Zero Egress
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <div className="p-2.5 rounded-xl bg-black/60 border border-cyber-cyan/20 text-right">
              <span className="text-zinc-500 block text-[9px] uppercase tracking-wider">
                Intent Velocity
              </span>
              <span className="text-cyber-cyan font-bold text-sm">0.052 ms</span>
            </div>
            <div className="p-2.5 rounded-xl bg-black/60 border border-cyber-cyan/20 text-right">
              <span className="text-zinc-500 block text-[9px] uppercase tracking-wider">
                Mesh Throughput
              </span>
              <span className="text-accent font-bold text-sm">~18,950 QPS</span>
            </div>
          </div>
        </div>
      </div>

      {/* Centerpiece: God's Eye 3D Holographic Globe & Orbital Satellite Reconnaissance */}
      <div className="w-full">
        <TacticalGlobe />
      </div>

      {/* 3 Tactical Mission HUD Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Mission Timeline */}
        <HudCard tag="TIMELINE" subtag="DAILY-OPS">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
            <span className="flex items-center gap-2 font-bold text-white tracking-tight">
              <Calendar className="w-4 h-4 text-cyber-cyan" /> Mission Schedule
            </span>
            <span className="text-[10px] text-cyber-cyan">ACTIVE DAY</span>
          </div>
          <div className="space-y-2">
            <div className="p-3 rounded-xl bg-black/50 border border-white/10 text-xs flex justify-between items-center">
              <div>
                <p className="font-bold text-white">Database Schema Sync</p>
                <p className="text-[10px] text-zinc-400 font-mono flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3 text-cyber-cyan" /> 10:00 AM - 11:30 AM
                </p>
              </div>
              <span className="px-2 py-0.5 rounded text-[9px] bg-verdigris/15 text-verdigris border border-verdigris/30 font-bold">
                ACTIVE
              </span>
            </div>
            <div className="p-3 rounded-xl bg-black/50 border border-white/10 text-xs flex justify-between items-center opacity-65">
              <div>
                <p className="font-bold text-white">Guardian Safety Audit</p>
                <p className="text-[10px] text-zinc-400 font-mono flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3 text-zinc-500" /> 02:00 PM - 03:30 PM
                </p>
              </div>
              <span className="px-2 py-0.5 rounded text-[9px] bg-zinc-800 text-zinc-400">
                QUEUED
              </span>
            </div>
          </div>
        </HudCard>

        {/* Tactical Objective */}
        <HudCard tag="SPRINT" subtag="OBJ-01">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
            <span className="flex items-center gap-2 font-bold text-white tracking-tight">
              <Target className="w-4 h-4 text-accent" /> Priority Objective
            </span>
            <span className="text-[10px] text-accent font-bold">HIGH PRIORITY</span>
          </div>
          <div className="p-3.5 rounded-xl bg-accent/10 border border-accent/30 space-y-2">
            <p className="text-xs font-bold text-white font-sans">
              Local AI Multi-Agent Mesh
            </p>
            <p className="text-[11px] text-zinc-300 font-sans leading-relaxed">
              Qwen2.5-Coder coding agent & DeepSeek-R1 reasoning engine synchronized with SQLite & ChromaDB vector store.
            </p>
            <div className="pt-2 flex items-center justify-between text-[10px] text-accent">
              <span>TARGET: 18:00 HRS</span>
              <button
                onClick={() => onNavigate?.("agents")}
                className="flex items-center gap-1 cursor-pointer hover:underline font-bold text-accent"
              >
                INSPECT OBJECTIVE <ArrowUpRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        </HudCard>

        {/* Guardian Proactive Intel */}
        {!intelDismissed ? (
          <HudCard tag="GUARDIAN" subtag="EPISTEMIC-94%">
            <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
              <span className="flex items-center gap-2 font-bold text-white tracking-tight">
                <Sparkles className="w-4 h-4 text-verdigris" /> Tactical Intelligence
              </span>
              <span className="text-[10px] text-verdigris font-bold">EVIDENCE 94%</span>
            </div>
            <p className="text-xs text-zinc-300 leading-relaxed italic bg-black/50 p-3 rounded-xl border border-white/10 font-sans">
              "Your peak cognitive velocity is scheduled for 10 AM - 12 PM. 3 planned deep focus tasks remain queued."
            </p>
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => onNavigate?.("chat")}
                className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyber-cyan to-accent text-black font-bold text-xs transition-all shadow-[0_0_12px_rgba(0,240,255,0.4)] hover:brightness-110 cursor-pointer"
              >
                EXECUTE PLAN
              </button>
              <button
                onClick={() => setIntelDismissed(true)}
                className="px-3 py-1.5 rounded-lg bg-black/60 hover:bg-zinc-800 text-zinc-400 text-xs border border-white/10 transition-all cursor-pointer"
              >
                DISMISS
              </button>
            </div>
          </HudCard>
        ) : (
          <HudCard tag="GUARDIAN" subtag="STANDBY">
            <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
              <span className="flex items-center gap-2 font-bold text-white tracking-tight">
                <Sparkles className="w-4 h-4 text-zinc-500" /> Tactical Intelligence
              </span>
              <span className="text-[10px] text-zinc-500">STANDBY</span>
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed italic bg-black/30 p-3 rounded-xl border border-white/5 font-sans">
              All tactical intelligence advisories acknowledged. System standing by for operational directives.
            </p>
            <button
              onClick={() => setIntelDismissed(false)}
              className="mt-2 text-[10px] text-cyber-cyan hover:underline font-mono cursor-pointer"
            >
              RESTORE ADVISORY
            </button>
          </HudCard>
        )}
      </div>

      {/* Live Hardware & Telemetry Matrix */}
      <HudCard tag="TELEMETRY" subtag="ALL-SENSORS-OK">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyber-cyan" /> Hardware & Model Telemetry Matrix
          </h3>
          <button
            onClick={() => onNavigate?.("benchmarks")}
            className="text-[11px] text-verdigris flex items-center gap-1.5 font-bold hover:underline cursor-pointer"
          >
            <span className="w-2 h-2 rounded-full bg-verdigris animate-pulse" /> LIVE TELEMETRY & BENCHMARKS →
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-xl bg-black/60 border border-cyber-cyan/20 space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
              Router Precision
            </span>
            <p className="text-xl font-bold text-white">100.0%</p>
            <span className="text-[10px] text-cyber-cyan">0.052ms Avg Latency</span>
          </div>

          <div className="p-3.5 rounded-xl bg-black/60 border border-cyber-cyan/20 space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
              Threat Shield
            </span>
            <p className="text-xl font-bold text-verdigris">100.0%</p>
            <span className="text-[10px] text-verdigris">0 Security Breaches</span>
          </div>

          <div className="p-3.5 rounded-xl bg-black/60 border border-cyber-cyan/20 space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
              RTX 5060 VRAM
            </span>
            <p className="text-xl font-bold text-accent">6.4 / 8.0 GB</p>
            <span className="text-[10px] text-verdigris">1.6 GB Headroom</span>
          </div>

          <div className="p-3.5 rounded-xl bg-black/60 border border-cyber-cyan/20 space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
              Neural Mesh Models
            </span>
            <p className="text-xl font-bold text-cyber-cyan">26 Loaded</p>
            <span className="text-[10px] text-zinc-400">39.50 GB Offline Weight</span>
          </div>
        </div>
      </HudCard>
    </div>
  );
};
