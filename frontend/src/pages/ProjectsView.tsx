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

const PROJECTS: ProjectItem[] = [];

export const ProjectsView: React.FC = () => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">Project Center</h1>
        <p className="text-xs text-gray-400 font-mono">Overview of active projects & health status indicators</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {PROJECTS.length === 0 ? (
          <div className="col-span-2 p-8 text-center text-xs text-gray-500 font-mono bg-[#14141a] rounded-xl border border-white/5">
            No active projects. Start a new project to track its health and milestones here.
          </div>
        ) : (
          PROJECTS.map((proj) => (
            <div key={proj.id} className="p-5 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2 font-bold text-sm text-white">
                  <FolderKanban size={16} className="text-sky-500" />
                  {proj.name}
                </div>
                {proj.health === "healthy" && <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950 text-emerald-500 border border-emerald-900">Healthy</span>}
                {proj.health === "at_risk" && <span className="px-2 py-0.5 rounded text-[10px] bg-amber-950 text-amber-500 border border-amber-900">At Risk</span>}
                {proj.health === "blocked" && <span className="px-2 py-0.5 rounded text-[10px] bg-rose-950 text-rose-500 border border-rose-900">Blocked</span>}
              </div>
              <p className="text-[11px] text-gray-400 font-mono leading-relaxed">{proj.reason}</p>
              <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[10px] font-mono">
                <span className="text-gray-500">Progress</span>
                <span className="text-white">{proj.completedTasks} / {proj.totalTasks} Tasks</span>
              </div>
              <div className="h-1.5 w-full bg-black rounded-full overflow-hidden">
                <div className="h-full bg-sky-500" style={{ width: `${(proj.completedTasks / proj.totalTasks) * 100}%` }} />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
