import React, { useState } from "react";
import { AlertCircle } from "lucide-react";

export const TodayView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"day" | "week" | "month">("day");

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Schedule & Today Overview</h1>
          <p className="text-xs text-gray-400 font-mono">Day, Week, and Month planning views</p>
        </div>
        <div className="flex gap-1 p-1 bg-[#14141a] rounded-lg border border-white/10 text-xs font-mono">
          {(["day", "week", "month"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 rounded capitalize transition-all ${
                activeTab === tab ? "bg-[#b87333]/30 text-[#ff5722] border border-[#ff5722]/40" : "text-gray-400 hover:text-white"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* COPPER Schedule Recommendation Alert */}
      <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/40 text-xs space-y-2">
        <div className="flex items-center gap-2 text-amber-400 font-semibold font-mono">
          <AlertCircle size={16} />
          <span>COPPER Recommendation</span>
        </div>
        <p className="text-gray-300">
          "DSA practice is running 45 minutes past schedule. Move DSA from 18:00 to 19:00 to avoid fatigue conflict with evening refactoring?"
        </p>
        <div className="flex gap-2 pt-1 font-mono">
          <button className="px-3 py-1 bg-amber-500 hover:bg-amber-400 text-black font-bold rounded text-[11px]">Apply Change</button>
          <button className="px-3 py-1 bg-white/5 hover:bg-white/10 text-gray-300 rounded border border-white/10 text-[11px]">Modify</button>
          <button className="px-3 py-1 bg-white/5 hover:bg-white/10 text-gray-400 rounded text-[11px]">Ignore</button>
        </div>
      </div>

      {/* Schedule Timeline */}
      <div className="p-5 rounded-xl bg-[#14141a] border border-white/10 space-y-4">
        <h3 className="text-xs font-mono font-semibold text-gray-400 uppercase tracking-wider">Today's Timeline</h3>
        <div className="space-y-3 font-mono text-xs">
          <div className="flex gap-4 items-center p-3 rounded-lg bg-black/40 border-l-4 border-l-emerald-500 border border-white/5">
            <span className="w-24 text-gray-400 text-[11px]">09:00 - 10:30 AM</span>
            <div className="flex-1">
              <p className="font-bold text-white">Focus Session 1: Pre-Trained LLM Router</p>
              <p className="text-[10px] text-gray-400">Map Ollama llama3.1 & qwen2.5 models</p>
            </div>
            <span className="text-emerald-400 text-[10px] bg-emerald-950 px-2 py-0.5 rounded border border-emerald-500/30">Completed</span>
          </div>

          <div className="flex gap-4 items-center p-3 rounded-lg bg-[#b87333]/10 border-l-4 border-l-[#ff5722] border border-[#ff5722]/30">
            <span className="w-24 text-[#ff5722] text-[11px] font-bold">11:00 - 12:30 PM</span>
            <div className="flex-1">
              <p className="font-bold text-white">PostgreSQL & Epistemic Schema Migration</p>
              <p className="text-[10px] text-gray-300">Run Alembic migrations on memory_v2</p>
            </div>
            <span className="text-[#ff5722] text-[10px] bg-[#ff5722]/20 px-2 py-0.5 rounded border border-[#ff5722]/40 animate-pulse">In Progress</span>
          </div>

          <div className="flex gap-4 items-center p-3 rounded-lg bg-black/40 border-l-4 border-l-gray-700 border border-white/5 opacity-70">
            <span className="w-24 text-gray-500 text-[11px]">03:00 - 04:30 PM</span>
            <div className="flex-1">
              <p className="font-bold text-white">Tauri Desktop Shell Build Test</p>
              <p className="text-[10px] text-gray-500">Validate native OS permissions</p>
            </div>
            <span className="text-gray-400 text-[10px] bg-gray-800 px-2 py-0.5 rounded">Upcoming</span>
          </div>
        </div>
      </div>
    </div>
  );
};
