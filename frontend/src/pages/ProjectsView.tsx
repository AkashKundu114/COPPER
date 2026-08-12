import React from "react";
import { FolderKanban } from "lucide-react";

interface ProjectItem {
  id: string;
  name: string;
  health: "healthy" | "at_risk" | "blocked";
  reason: string;
  completedTasks: number;
  totalTasks: number;
}

const PROJECTS: ProjectItem[] = [
  { id: "1", name: "C.O.P.P.E.R. Core Architecture", health: "healthy", reason: "All 100% offline local components validated.", completedTasks: 18, totalTasks: 20 },
  { id: "2", name: "Pre-Trained Model Pool Egress", health: "healthy", reason: "Ollama Llama 3.1 & Qwen 2.5 models loaded.", completedTasks: 12, totalTasks: 12 },
  { id: "3", name: "Data Firewall PII Scanner", health: "at_risk", reason: "Regex rules require validation on complex nested JSON payloads.", completedTasks: 8, totalTasks: 12 },
  { id: "4", name: "Multi-Device P2P Memory Sync", health: "blocked", reason: "Waiting on WebRTC encrypted transport milestone.", completedTasks: 2, totalTasks: 10 },
];

export const ProjectsView: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Project Center</h1>
        <p className="text-xs text-gray-400 font-mono">Overview of active projects & health status indicators</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PROJECTS.map((proj) => (
          <div key={proj.id} className="p-5 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FolderKanban size={16} className="text-[#ff5722]" />
                <h3 className="text-sm font-bold text-white">{proj.name}</h3>
              </div>
              <span
                className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                  proj.health === "healthy"
                    ? "bg-emerald-950 text-emerald-400 border border-emerald-500/30"
                    : proj.health === "at_risk"
                    ? "bg-amber-950 text-amber-400 border border-amber-500/30"
                    : "bg-red-950 text-red-400 border border-red-500/30"
                }`}
              >
                {proj.health.replace("_", " ")}
              </span>
            </div>

            <p className="text-xs text-gray-400 leading-relaxed">{proj.reason}</p>

            <div className="space-y-1 font-mono text-[11px]">
              <div className="flex justify-between text-gray-400">
                <span>Task Completion</span>
                <span>{proj.completedTasks} / {proj.totalTasks} Tasks</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-black/50 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-[#b87333] to-[#ff5722]"
                  style={{ width: `${(proj.completedTasks / proj.totalTasks) * 100}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
