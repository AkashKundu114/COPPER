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
      <motion.div variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} className="p-6 md:p-7 rounded-3xl bg-[linear-gradient(135deg,rgba(35,14,23,0.88),rgba(18,6,10,0.95))] border border-blush-100/[0.15] shadow-[0_24px_56px_rgba(10,3,6,0.5),inset_0_1px_0_rgba(246,230,234,0.12)] relative overflow-hidden backdrop-blur-2xl">
        <div className="absolute -top-24 right-0 w-[28rem] h-[28rem] bg-blush-100/[0.08] rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 left-1/3 w-72 h-72 bg-accent/[0.09] rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-verdigris/12 text-verdigris border border-verdigris/30 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" />
                DEFCON 5 // SYSTEM OPTIMAL
              </span>
              <span className="px-2.5 py-1 rounded-full text-[10px] bg-blush-100/12 text-blush-100 border border-blush-100/30 font-bold">
                PRIVATE AI WORKSPACE
              </span>
              <span className="px-2.5 py-1 rounded-full text-[10px] bg-accent/15 text-accent border border-accent/30 font-bold">
                100% AIR-GAPPED LOCALHOST
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-display font-bold text-white tracking-[-0.03em]">
              Your intelligence, in motion.
            </h1>
            <p className="text-xs text-blush-300/70 mt-1">
              Operator: <span className="text-white font-bold">Akash</span> • C.O.P.P.E.R. v1.0.0 • 26 local models ready • zero egress
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <div className="p-3 rounded-2xl bg-[#1A0A0F]/80 border border-blush-100/[0.12] text-right shadow-[inset_0_1px_0_rgba(246,230,234,0.08)]">
              <span className="text-blush-300/60 block text-[9px] uppercase tracking-wider">
                Intent Velocity
              </span>
              <span className="text-blush-100 font-display font-bold text-sm">0.105 ms</span>
            </div>
            <div className="p-3 rounded-2xl bg-[#1A0A0F]/80 border border-blush-100/[0.12] text-right shadow-[inset_0_1px_0_rgba(246,230,234,0.08)]">
              <span className="text-blush-300/60 block text-[9px] uppercase tracking-wider">
                Mesh Throughput
              </span>
              <span className="text-accent font-display font-bold text-sm">~9,856 QPS</span>
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
        <HudCard tag="TIMELINE" subtag="DAILY-OPS" glow="blush">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
            <span className="flex items-center gap-2 font-bold text-white tracking-tight">
              <Calendar className="w-4 h-4 text-blush-100" /> Mission Schedule
            </span>
            <span className="text-[10px] text-blush-100 font-bold">ACTIVE DAY</span>
          </div>
          <div className="space-y-2">
            <div className="p-3 rounded-xl bg-[#14070B]/80 border border-blush-100/10 text-xs flex justify-between items-center shadow-inner">
              <div>
                <p className="font-bold text-white">Database Schema Sync</p>
                <p className="text-[10px] text-blush-300/60 font-mono flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3 text-blush-200" /> 10:00 AM - 11:30 AM
                </p>
              </div>
              <span className="px-2 py-0.5 rounded text-[9px] bg-verdigris/15 text-verdigris border border-verdigris/30 font-bold">
                ACTIVE
              </span>
            </div>
            <div className="p-3 rounded-xl bg-[#14070B]/60 border border-blush-100/5 text-xs flex justify-between items-center opacity-65">
              <div>
                <p className="font-bold text-white">Guardian Safety Audit</p>
                <p className="text-[10px] text-zinc-400 font-mono flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3 text-zinc-500" /> 02:00 PM - 03:30 PM
                </p>
              </div>
              <span className="px-2 py-0.5 rounded text-[9px] bg-black/40 text-zinc-400 border border-white/5">
                QUEUED
              </span>
            </div>
          </div>
        </HudCard>

        {/* Tactical Objective */}
        <HudCard tag="SPRINT" subtag="OBJ-01" glow="copper">
          <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
            <span className="flex items-center gap-2 font-bold text-white tracking-tight">
              <Target className="w-4 h-4 text-accent" /> Priority Objective
            </span>
            <span className="text-[10px] text-accent font-bold">HIGH PRIORITY</span>
          </div>
          <div className="p-3.5 rounded-xl bg-accent/10 border border-accent/25 space-y-2 shadow-[inset_0_1px_0_rgba(201,124,76,0.15)]">
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
          <HudCard tag="GUARDIAN" subtag="EPISTEMIC-94%" glow="blush">
            <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
              <span className="flex items-center gap-2 font-bold text-white tracking-tight">
                <Sparkles className="w-4 h-4 text-verdigris" /> Tactical Intelligence
              </span>
              <span className="text-[10px] text-verdigris font-bold">EVIDENCE 94%</span>
            </div>
            <p className="text-xs text-zinc-200 leading-relaxed italic bg-[#14070B]/80 p-3 rounded-xl border border-blush-100/10 font-sans shadow-inner">
              "Your peak cognitive velocity is scheduled for 10 AM - 12 PM. 3 planned deep focus tasks remain queued."
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
          <HudCard tag="GUARDIAN" subtag="STANDBY" glow="blush">
            <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
              <span className="flex items-center gap-2 font-bold text-white tracking-tight">
                <Sparkles className="w-4 h-4 text-zinc-500" /> Tactical Intelligence
              </span>
              <span className="text-[10px] text-zinc-500">STANDBY</span>
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed italic bg-[#14070B]/50 p-3 rounded-xl border border-white/5 font-sans">
              All tactical intelligence advisories acknowledged. System standing by for operational directives.
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
      <HudCard tag="TELEMETRY" subtag="ALL-SENSORS-OK" glow="blush">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-blush-300/70 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-blush-100" /> Hardware & Model Telemetry Matrix
          </h3>
          <button
            onClick={() => onNavigate?.("benchmarks")}
            className="text-[11px] text-verdigris flex items-center gap-1.5 font-bold hover:underline cursor-pointer"
          >
            <span className="w-2 h-2 rounded-full bg-verdigris animate-pulse" /> LIVE TELEMETRY & BENCHMARKS →
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="lift-on-hover p-4 rounded-2xl bg-[#14070B]/70 border border-blush-100/[0.12] space-y-1 shadow-[inset_0_1px_0_rgba(246,230,234,0.06)]">
            <span className="text-[10px] text-blush-300/60 uppercase tracking-wider">
              Router Precision
            </span>
            <p className="text-2xl font-display font-bold text-white">100.0%</p>
            <span className="text-[10px] text-blush-200">0.052ms Avg Latency</span>
          </div>

          <div className="lift-on-hover p-4 rounded-2xl bg-[#14070B]/70 border border-blush-100/[0.12] space-y-1 shadow-[inset_0_1px_0_rgba(246,230,234,0.06)]">
            <span className="text-[10px] text-blush-300/60 uppercase tracking-wider">
              Threat Shield
            </span>
            <p className="text-2xl font-display font-bold text-verdigris">100.0%</p>
            <span className="text-[10px] text-verdigris">0 Security Breaches</span>
          </div>

          <div className="lift-on-hover p-4 rounded-2xl bg-[#14070B]/70 border border-blush-100/[0.12] space-y-1 shadow-[inset_0_1px_0_rgba(246,230,234,0.06)]">
            <span className="text-[10px] text-blush-300/60 uppercase tracking-wider">
              RTX 5060 VRAM
            </span>
            <p className="text-2xl font-display font-bold text-accent">6.4 / 8.0 GB</p>
            <span className="text-[10px] text-verdigris">1.6 GB Headroom</span>
          </div>

          <div className="lift-on-hover p-4 rounded-2xl bg-[#14070B]/70 border border-blush-100/[0.12] space-y-1 shadow-[inset_0_1px_0_rgba(246,230,234,0.06)]">
            <span className="text-[10px] text-blush-300/60 uppercase tracking-wider">
              Neural Mesh Models
            </span>
            <p className="text-2xl font-display font-bold text-blush-100">26 Loaded</p>
            <span className="text-[10px] text-zinc-400">39.50 GB Offline Weight</span>
          </div>
        </div>
      </HudCard>
      </motion.div>
    </motion.div>
  );
};
