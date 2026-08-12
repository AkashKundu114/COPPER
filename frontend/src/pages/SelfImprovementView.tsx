import React from "react";

export const SelfImprovementView: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Self-Improvement & Benchmark Dashboard</h1>
        <p className="text-xs text-gray-400 font-mono">Evaluated experience learning, candidate model metrics, and rollback controls</p>
      </div>

      <div className="p-5 rounded-xl bg-[#14141a] border border-white/10 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-white font-mono">Pre-Trained Candidate Pool Evaluation</h3>
            <p className="text-xs text-gray-400">Comparing Llama 3.1 8B vs Qwen 2.5 Coder 7B baseline</p>
          </div>
          <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 text-xs font-mono font-bold border border-emerald-500/30">Candidate Ready</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono text-xs">
          <div className="p-3 rounded-lg bg-black/40 border border-white/5">
            <span className="text-gray-500 text-[10px]">Task Success</span>
            <p className="text-lg font-bold text-emerald-400 mt-1">+3.2%</p>
          </div>
          <div className="p-3 rounded-lg bg-black/40 border border-white/5">
            <span className="text-gray-500 text-[10px]">Schedule Realism</span>
            <p className="text-lg font-bold text-emerald-400 mt-1">+5.1%</p>
          </div>
          <div className="p-3 rounded-lg bg-black/40 border border-white/5">
            <span className="text-gray-500 text-[10px]">Latency Reduction</span>
            <p className="text-lg font-bold text-emerald-400 mt-1">-7.8%</p>
          </div>
          <div className="p-3 rounded-lg bg-black/40 border border-white/5">
            <span className="text-gray-500 text-[10px]">Safety Regression</span>
            <p className="text-lg font-bold text-blue-400 mt-1">None</p>
          </div>
        </div>

        <div className="flex gap-3 pt-2 font-mono text-xs">
          <button className="px-4 py-2 rounded-lg bg-[#ff5722] hover:bg-[#ff5722]/80 text-black font-bold transition-all">
            Run Benchmark Suite
          </button>
          <button className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 transition-all">
            Rollback to Checkpoint
          </button>
        </div>
      </div>
    </div>
  );
};
