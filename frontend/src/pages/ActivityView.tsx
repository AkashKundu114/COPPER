import React from "react";
import { CheckCircle } from "lucide-react";

export const ActivityView: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Agent Activity Panel</h1>
        <p className="text-xs text-gray-400 font-mono">Step-by-step execution traces & tool run history</p>
      </div>

      <div className="p-5 rounded-xl bg-[#14141a] border border-white/10 space-y-4 font-mono text-xs">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Active Execution Graph</h3>
        <div className="p-4 rounded-lg bg-black/50 border border-white/5 space-y-3">
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle size={14} />
            <span>Orchestrator $\rightarrow$ Agent Routing (Target: Coding Agent `qwen2.5-coder:7b`)</span>
          </div>
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle size={14} />
            <span>Guardian Alignment Check (Level 0 - Execute)</span>
          </div>
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle size={14} />
            <span>Data Firewall Egress Scan (0 PII detected - Local Egress Only)</span>
          </div>
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle size={14} />
            <span>Executed Ollama Local Inference (`qwen2.5-coder:7b`, 4.4GB VRAM)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
