import React from "react";
import { Calendar, ArrowUpRight, Target, Sparkles } from "lucide-react";

export const DashboardView: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      {}
      <div className="p-6 rounded-xl bg-gradient-to-r from-[#14141a] via-[#1a1614] to-[#0d0d11] border border-[#b87333]/30 shadow-xl space-y-2">
        <h1 className="text-2xl font-bold text-white tracking-tight">Good morning, Alex.</h1>
        <p className="text-sm text-[#ff5722] font-mono">You have 4 important tasks scheduled today.</p>
      </div>

      {}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {}
        <div className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center gap-1.5 font-medium text-white">
              <Calendar size={14} className="text-[#ff5722]" /> Schedule Overview
            </span>
            <span className="font-mono text-[10px] text-gray-500">Today</span>
          </div>
          <div className="space-y-2">
            <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 text-xs flex justify-between items-center">
              <div>
                <p className="font-semibold text-white">Database Optimization</p>
                <p className="text-[10px] text-gray-400 font-mono">10:00 AM - 11:30 AM</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-500/30">Active</span>
            </div>
            <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 text-xs flex justify-between items-center opacity-70">
              <div>
                <p className="font-semibold text-white">Guardian Alignment Audit</p>
                <p className="text-[10px] text-gray-400 font-mono">02:00 PM - 03:30 PM</p>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-gray-800 text-gray-400">Upcoming</span>
            </div>
          </div>
        </div>

        {}
        <div className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center gap-1.5 font-medium text-white">
              <Target size={14} className="text-[#ff5722]" /> Priority Commitment
            </span>
            <span className="font-mono text-[10px] text-amber-400 font-semibold">High</span>
          </div>
          <div className="p-3 rounded-lg bg-[#b87333]/10 border border-[#b87333]/30 space-y-1">
            <p className="text-xs font-bold text-white">Deploy Pre-Trained Model Router</p>
            <p className="text-[11px] text-gray-300">Map Ollama Llama 3.1 & Qwen 2.5 Coder pools.</p>
            <div className="pt-2 flex items-center justify-between text-[10px] font-mono text-[#ff5722]">
              <span>Deadline: 6:00 PM</span>
              <span className="flex items-center gap-1 cursor-pointer hover:underline">View Project <ArrowUpRight size={10} /></span>
            </div>
          </div>
        </div>

        {}
        <div className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span className="flex items-center gap-1.5 font-medium text-white">
              <Sparkles size={14} className="text-[#ff5722]" /> COPPER Recommendation
            </span>
            <span className="font-mono text-[10px] text-emerald-400">Evidence 86%</span>
          </div>
          <p className="text-xs text-gray-300 italic">
            "Your peak deep-work focus window is between 10 AM - 12 PM. 3 planned focus tasks remain."
          </p>
          <div className="pt-1 flex gap-2">
            <button className="px-2.5 py-1 rounded bg-[#ff5722] hover:bg-[#ff5722]/80 text-black font-bold text-[11px] transition-all">
              Apply Schedule
            </button>
            <button className="px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-gray-300 text-[11px] border border-white/10 transition-all">
              Dismiss
            </button>
          </div>
        </div>
      </div>

      {}
      <div className="p-5 rounded-xl bg-[#14141a] border border-white/10 space-y-4">
        <h3 className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">Productivity Metrics (Neutral Overview)</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 rounded-lg bg-black/40 border border-white/5">
            <span className="text-[10px] text-gray-500 font-mono uppercase">Tasks Remaining</span>
            <p className="text-xl font-bold text-white mt-1">3 Tasks</p>
          </div>
          <div className="p-3 rounded-lg bg-black/40 border border-white/5">
            <span className="text-[10px] text-gray-500 font-mono uppercase">Focus Time Today</span>
            <p className="text-xl font-bold text-emerald-400 mt-1">2h 45m</p>
          </div>
          <div className="p-3 rounded-lg bg-black/40 border border-white/5">
            <span className="text-[10px] text-gray-500 font-mono uppercase">Schedule Adherence</span>
            <p className="text-xl font-bold text-amber-400 mt-1">88%</p>
          </div>
          <div className="p-3 rounded-lg bg-black/40 border border-white/5">
            <span className="text-[10px] text-gray-500 font-mono uppercase">Guardian Pass</span>
            <p className="text-xl font-bold text-blue-400 mt-1">Level 0 (Pass)</p>
          </div>
        </div>
      </div>
    </div>
  );
};
