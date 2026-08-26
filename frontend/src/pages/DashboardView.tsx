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
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-text select-none pb-12">
      {}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-bg-panel via-bg-raised to-bg border border-accent/30 shadow-lg relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-accent/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-verdigris-950 text-verdigris-400 border border-verdigris-500/30 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-verdigris-400 animate-pulse" />
                SYSTEM OPTIMAL
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-accent/20 text-accent border border-accent/40 font-bold">
                100% OFFLINE ZERO-EGRESS
              </span>
            </div>
            <h1 className="text-2xl font-display font-bold text-text tracking-tight">
              Welcome back, Akash.
            </h1>
            <p className="text-xs text-text-muted font-mono mt-0.5">
              C.O.P.P.E.R. v1.0.0 Active • All 26 Local Models Loaded • 0
              Security Threats
            </p>
          </div>

          <div className="flex items-center gap-2 font-mono text-xs">
            <div className="p-2.5 rounded-xl bg-bg/60 border border-border text-right">
              <span className="text-text-muted block text-[10px]">
                Active Router Speed
              </span>
              <span className="text-accent font-bold">0.052 ms</span>
            </div>
            <div className="p-2.5 rounded-xl bg-bg/60 border border-border text-right">
              <span className="text-text-muted block text-[10px]">
                Throughput
              </span>
              <span className="text-accent-300 font-bold">~18,950 QPS</span>
            </div>
          </div>
        </div>
      </div>

      {}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {}
        <div className="p-5 rounded-2xl bg-bg-panel border border-border shadow-hud space-y-3">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span className="flex items-center gap-1.5 font-bold text-text">
              <Calendar className="w-4 h-4 text-accent" /> Schedule Timeline
            </span>
            <span className="font-mono text-[10px] text-text-muted">Today</span>
          </div>
          <div className="space-y-2">
            <div className="p-3 rounded-xl bg-bg/60 border border-border text-xs flex justify-between items-center">
              <div>
                <p className="font-bold text-text">Database Schema Sync</p>
                <p className="text-[10px] text-text-muted font-mono flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3 text-accent-300" /> 10:00 AM - 11:30
                  AM
                </p>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-verdigris-950 text-verdigris-400 border border-verdigris-500/30 font-bold">
                Active
              </span>
            </div>
            <div className="p-3 rounded-xl bg-bg/60 border border-border text-xs flex justify-between items-center opacity-70">
              <div>
                <p className="font-bold text-text">Guardian Safety Audit</p>
                <p className="text-[10px] text-text-muted font-mono flex items-center gap-1 mt-0.5">
                  <Clock className="w-3 h-3 text-text-muted" /> 02:00 PM - 03:30
                  PM
                </p>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-bg-raised text-text-muted">
                Upcoming
              </span>
            </div>
          </div>
        </div>

        {}
        <div className="p-5 rounded-2xl bg-bg-panel border border-border shadow-hud space-y-3">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span className="flex items-center gap-1.5 font-bold text-text">
              <Target className="w-4 h-4 text-accent" /> Core Sprint
              Milestone
            </span>
            <span className="font-mono text-[10px] text-accent font-bold">
              High Priority
            </span>
          </div>
          <div className="p-3.5 rounded-xl bg-accent/10 border border-accent/30 space-y-1.5">
            <p className="text-xs font-bold text-text">
              Local AI Multi-Agent Mesh
            </p>
            <p className="text-[11px] text-text-muted">
              AXIS Coding Agent & DeepSeek-R1 reasoning engine connected to
              SQLite & ChromaDB.
            </p>
            <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-accent">
              <span>Deadline: 6:00 PM</span>
              <span className="flex items-center gap-1 cursor-pointer hover:underline font-bold">
                View Project <ArrowUpRight className="w-3 h-3" />
              </span>
            </div>
          </div>
        </div>

        {}
        <div className="p-5 rounded-2xl bg-bg-panel border border-border shadow-hud space-y-3">
          <div className="flex items-center justify-between text-xs text-text-muted">
            <span className="flex items-center gap-1.5 font-bold text-text">
              <Sparkles className="w-4 h-4 text-accent-300" /> Proactive Guardian
              Advice
            </span>
            <span className="font-mono text-[10px] text-accent-300 font-bold">
              Evidence: 94%
            </span>
          </div>
          <p className="text-xs text-text-muted leading-relaxed italic bg-bg/50 p-3 rounded-xl border border-border">
            "Your peak cognitive velocity is scheduled for 10 AM - 12 PM. 3
            planned deep focus tasks remain queued."
          </p>
          <div className="flex gap-2 pt-1">
            <button className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-accent to-accent-600 hover:from-accent-400 hover:to-accent text-bg font-bold text-xs transition-all shadow-sm font-mono">
              Accept Schedule
            </button>
            <button className="px-3 py-1.5 rounded-lg bg-bg-raised hover:bg-border text-text-muted text-xs border border-border transition-all font-mono">
              Dismiss
            </button>
          </div>
        </div>
      </div>

      {}
      <div className="p-6 rounded-2xl bg-bg-panel border border-border space-y-4 shadow-hud">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono font-bold text-text-muted uppercase tracking-wider flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent" /> Live System
            Telemetry & Resource Monitor
          </h3>
          <span className="text-[11px] font-mono text-verdigris-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-verdigris-400" /> All 213
            Pytest Tests Passing
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
          <div className="p-3.5 rounded-xl bg-bg/60 border border-border space-y-1">
            <span className="text-[10px] text-text-muted uppercase">
              Routing Precision
            </span>
            <p className="text-xl font-bold text-text">100.0%</p>
            <span className="text-[10px] text-accent">0.052ms Avg</span>
          </div>

          <div className="p-3.5 rounded-xl bg-bg/60 border border-border space-y-1">
            <span className="text-[10px] text-text-muted uppercase">
              Guardian Threat Shield
            </span>
            <p className="text-xl font-bold text-verdigris-400">100.0%</p>
            <span className="text-[10px] text-verdigris-400">0 Breaches</span>
          </div>

          <div className="p-3.5 rounded-xl bg-bg/60 border border-border space-y-1">
            <span className="text-[10px] text-text-muted uppercase">
              RTX 5060 VRAM
            </span>
            <p className="text-xl font-bold text-accent-300">6.4 / 8.0 GB</p>
            <span className="text-[10px] text-verdigris-400">1.6 GB Free</span>
          </div>

          <div className="p-3.5 rounded-xl bg-bg/60 border border-border space-y-1">
            <span className="text-[10px] text-text-muted uppercase">
              Active Models
            </span>
            <p className="text-xl font-bold text-accent-300">26 Artifacts</p>
            <span className="text-[10px] text-text-muted">39.50 GB Offline</span>
          </div>
        </div>
      </div>
    </div>
  );
};
