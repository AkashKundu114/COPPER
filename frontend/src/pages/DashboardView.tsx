import React, { useState } from "react";
import { motion } from "framer-motion";
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
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{ visible: { transition: { staggerChildren: 0.07 } } }}
      className="modern-page p-5 md:p-7 space-y-6 max-w-7xl mx-auto text-text select-none pb-16 font-mono"
    >
      {/* Top Classified Mission Banner */}
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} className="p-6 md:p-7 rounded-3xl bg-[linear-gradient(135deg,rgba(21,31,47,0.88),rgba(7,11,19,0.9))] border border-white/[0.11] shadow-[0_20px_48px_rgba(0,0,0,0.28),inset_0_1px_0_rgba(255,255,255,0.06)] relative overflow-hidden backdrop-blur-2xl">
        <div className="absolute -top-24 right-0 w-[28rem] h-[28rem] bg-cyber-cyan/[0.10] rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 left-1/3 w-72 h-72 bg-accent/[0.07] rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-verdigris/12 text-verdigris border border-verdigris/30 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" />
                DEFCON 5 // SYSTEM OPTIMAL
              </span>
              <span className="px-2.5 py-1 rounded-full text-[10px] bg-cyber-cyan/12 text-cyber-cyan border border-cyber-cyan/30 font-bold">
                PRIVATE AI WORKSPACE
              </span>
              <span className="px-2.5 py-1 rounded-full text-[10px] bg-accent/15 text-accent border border-accent/30 font-bold">
                100% AIR-GAPPED LOCALHOST
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white tracking-[-0.035em]">
              Your intelligence, in motion.
            </h1>
            <p className="text-xs text-zinc-400 mt-1">
              Operator: <span className="text-white font-bold">Akash</span> • C.O.P.P.E.R. v1.0.0 • 26 local models ready • zero egress
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <div className="p-3 rounded-2xl bg-black/25 border border-white/[0.08] text-right shadow-inner">
              <span className="text-zinc-500 block text-[9px] uppercase tracking-wider">
                Intent Velocity
              </span>
              <span className="text-cyber-cyan font-bold text-sm">0.105 ms</span>
            </div>
            <div className="p-3 rounded-2xl bg-black/25 border border-white/[0.08] text-right shadow-inner">
              <span className="text-zinc-500 block text-[9px] uppercase tracking-wider">
                Mesh Throughput
              </span>
              <span className="text-accent font-bold text-sm">~9,856 QPS</span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Centerpiece: God's Eye 3D Holographic Globe & Orbital Satellite Reconnaissance */}
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} className="w-full">
        <TacticalGlobe />
      </motion.div>

      {/* 3 Tactical Mission HUD Cards */}
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} className="grid grid-cols-1 md:grid-cols-3 gap-5">
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
              className="lift-on-hover px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyber-cyan to-accent text-black font-bold text-xs shadow-[0_8px_20px_rgba(0,240,255,0.22)] hover:brightness-110 cursor-pointer"
              >
                EXECUTE PLAN
              </button>
              <button
                onClick={() => setIntelDismissed(true)}
              className="lift-on-hover px-3.5 py-2 rounded-xl bg-white/[0.045] hover:bg-white/[0.09] text-zinc-300 text-xs border border-white/[0.1] cursor-pointer"
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
      </motion.div>

      {/* Live Hardware & Telemetry Matrix */}
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }}>
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
          <div className="lift-on-hover p-3.5 rounded-2xl bg-black/25 border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
              Router Precision
            </span>
            <p className="text-xl font-bold text-white">100.0%</p>
            <span className="text-[10px] text-cyber-cyan">0.052ms Avg Latency</span>
          </div>

          <div className="lift-on-hover p-3.5 rounded-2xl bg-black/25 border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
              Threat Shield
            </span>
            <p className="text-xl font-bold text-verdigris">100.0%</p>
            <span className="text-[10px] text-verdigris">0 Security Breaches</span>
          </div>

          <div className="lift-on-hover p-3.5 rounded-2xl bg-black/25 border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
              RTX 5060 VRAM
            </span>
            <p className="text-xl font-bold text-accent">6.4 / 8.0 GB</p>
            <span className="text-[10px] text-verdigris">1.6 GB Headroom</span>
          </div>

          <div className="lift-on-hover p-3.5 rounded-2xl bg-black/25 border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
              Neural Mesh Models
            </span>
            <p className="text-xl font-bold text-cyber-cyan">26 Loaded</p>
            <span className="text-[10px] text-zinc-400">39.50 GB Offline Weight</span>
          </div>
        </div>
      </HudCard>
      </motion.div>
    </motion.div>
  );
};
