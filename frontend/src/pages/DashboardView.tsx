import React from "react";
import {
  Calendar,
  ArrowUpRight,
  Target,
  Sparkles,
  Activity,
  Clock,
} from "lucide-react";

export const DashboardView: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none pb-12">
      {}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-[#141b2d] via-[#1a1512] to-[#090d16] border border-[#f97316]/30 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-[#f97316]/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                SYSTEM OPTIMAL
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#f97316]/20 text-[#f97316] border border-[#f97316]/40 font-bold">
                100% OFFLINE ZERO-EGRESS
              </span>
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Welcome back, Akash.
            </h1>
            <p className="text-xs text-gray-400 font-mono mt-0.5">
              C.O.P.P.E.R. v1.0.0 Active • All 26 Local Models Loaded • 0
              Security Threats
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <div className="p-2.5 rounded-xl bg-black/40 border border-white/10 text-right">
              <span className="text-gray-400 block text-[10px]">
                Active Router Speed
              </span>
              <span className="text-[#f97316] font-bold">0.052 ms</span>
            </div>
            <div className="p-2.5 rounded-xl bg-black/40 border border-white/10 text-right">
              <span className="text-gray-400 block text-[10px]">
                Throughput
              </span>
              <span className="text-cyan-400 font-bold">~18,950 QPS</span>
            </div>
          </div>
        </div>
      </div>

      {}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {}
        <div className="p-5 rounded-2xl bg-bg-panel border border-border shadow-hud space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center gap-1.5 font-bold text-white">
              <Calendar className="w-4 h-4 text-[#f97316]" /> Schedule Timeline
            </span>
            <span className="font-mono text-[10px] text-gray-400">Today</span>
          </div>
          <div className="space-y-2">
            <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs flex justify-between items-center">
              <div>
                <p className="font-bold text-white">Database Schema Sync</p>
                <p className="text-[10px] text-gray-400 font-mono flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3 text-cyan-400" /> 10:00 AM - 11:30
                  AM
                </p>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-500/30 font-bold">
                Active
              </span>
            </div>
            <div className="p-3 rounded-xl bg-black/40 border border-white/5 text-xs flex justify-between items-center opacity-70">
              <div>
                <p className="font-bold text-white">Guardian Safety Audit</p>
                <p className="text-[10px] text-gray-400 font-mono flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3 text-gray-500" /> 02:00 PM - 03:30
                  PM
                </p>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-gray-800 text-gray-400">
                Upcoming
              </span>
            </div>
          </div>
        </div>

        {}
        <div className="p-5 rounded-2xl bg-bg-panel border border-border shadow-hud space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center gap-1.5 font-bold text-white">
              <Target className="w-4 h-4 text-[#f97316]" /> Core Sprint
              Milestone
            </span>
            <span className="font-mono text-[10px] text-[#f97316] font-bold">
              High Priority
            </span>
          </div>
          <div className="p-3.5 rounded-xl bg-[#f97316]/10 border border-[#f97316]/30 space-y-1.5">
            <p className="text-xs font-bold text-white">
              Local AI Multi-Agent Mesh
            </p>
            <p className="text-[11px] text-gray-300">
              AXIS Coding Agent & DeepSeek-R1 reasoning engine connected to
              SQLite & ChromaDB.
            </p>
            <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-[#f97316]">
              <span>Deadline: 6:00 PM</span>
              <span className="flex items-center gap-1 cursor-pointer hover:underline font-bold">
                View Project <ArrowUpRight className="w-3 h-3" />
              </span>
            </div>
          </div>
        </div>

        {}
        <div className="p-5 rounded-2xl bg-bg-panel border border-border shadow-hud space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center gap-1.5 font-bold text-white">
              <Sparkles className="w-4 h-4 text-cyan-400" /> Proactive Guardian
              Advice
            </span>
            <span className="font-mono text-[10px] text-cyan-400 font-bold">
              Evidence: 94%
            </span>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed italic bg-black/30 p-3 rounded-xl border border-white/5">
            "Your peak cognitive velocity is scheduled for 10 AM - 12 PM. 3
            planned deep focus tasks remain queued."
          </p>
          <div className="flex gap-2 pt-1">
            <button className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#f97316] to-[#ea580c] hover:from-[#fb923c] hover:to-[#f97316] text-white font-bold text-xs transition-all shadow-md font-mono">
              Accept Schedule
            </button>
            <button className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 text-xs border border-white/10 transition-all font-mono">
              Dismiss
            </button>
          </div>
        </div>
      </div>

      {}
      <div className="p-6 rounded-2xl bg-bg-panel border border-border space-y-4 shadow-hud">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono font-bold text-gray-400 uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#f97316]" /> Live System
            Telemetry & Resource Monitor
          </h3>
          <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400" /> All 213
            Pytest Tests Passing
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
          <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[10px] text-gray-400 uppercase">
              Routing Precision
            </span>
            <p className="text-xl font-bold text-white">100.0%</p>
            <span className="text-[10px] text-[#f97316]">0.052ms Avg</span>
          </div>

          <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[10px] text-gray-400 uppercase">
              Guardian Threat Shield
            </span>
            <p className="text-xl font-bold text-emerald-400">100.0%</p>
            <span className="text-[10px] text-emerald-400">0 Breaches</span>
          </div>

          <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[10px] text-gray-400 uppercase">
              RTX 5060 VRAM
            </span>
            <p className="text-xl font-bold text-purple-400">6.4 / 8.0 GB</p>
            <span className="text-[10px] text-emerald-400">1.6 GB Free</span>
          </div>

          <div className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[10px] text-gray-400 uppercase">
              Active Models
            </span>
            <p className="text-xl font-bold text-cyan-400">26 Artifacts</p>
            <span className="text-[10px] text-gray-400">39.50 GB Offline</span>
          </div>
        </div>
      </div>
    </div>
  );
};
