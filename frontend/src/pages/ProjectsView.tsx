import React, { useState, useEffect } from "react";
import {
  FolderKanban,
  Plus,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  X,
} from "lucide-react";
import { workspaceAPI } from "../lib/api";

export interface ProjectItem {
  id: string;
  name: string;
  health: "healthy" | "at_risk" | "blocked" | "completed";
  reason: string;
  completedTasks: number;
  totalTasks: number;
}

export const ProjectsView: React.FC = () => {
  const [projects, setProjects] = useState<ProjectItem[]>([]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [reason, setReason] = useState("");
  const [health, setHealth] = useState<ProjectItem["health"]>("healthy");
  const [totalTasks, setTotalTasks] = useState(5);
  const [completedTasks] = useState(0);

  useEffect(() => {
    workspaceAPI.list<ProjectItem>("project").then(setProjects).catch(console.error);
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    const payload = {
      name: name.trim(),
      reason: reason.trim() || "Project milestone tracking active.",
      health,
      completedTasks: Number(completedTasks) || 0,
      totalTasks: Math.max(1, Number(totalTasks) || 1),
    };

    const newProject = await workspaceAPI.create<ProjectItem>("project", payload);
    setProjects((prev) => [newProject, ...prev]);
    setName("");
    setReason("");
    setIsModalOpen(false);
  };

  const incrementTask = async (project: ProjectItem) => {
    const completedTasks = Math.min(project.totalTasks, project.completedTasks + 1);
    const health = completedTasks === project.totalTasks ? "completed" : project.health;
    const updated = await workspaceAPI.update<ProjectItem>("project", project.id, { completedTasks, health });
    setProjects((prev) => prev.map((p) => p.id === project.id ? updated : p));
  };

  const deleteProject = async (id: string) => {
    await workspaceAPI.remove("project", id);
    setProjects((prev) => prev.filter((p) => p.id !== id));
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Project Center
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            Overview of active projects, task completion, and health indicators
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-accent-500/20"
        >
          <Plus size={15} strokeWidth={2.5} />
          <span>New Project</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {projects.length === 0 ? (
          <div className="col-span-2 p-12 text-center text-xs text-slate-500 font-mono bg-slate-900/60 rounded-2xl border border-slate-800 space-y-2">
            <p className="font-semibold text-slate-300">
              No active projects yet.
            </p>
            <p>Click "+ New Project" to organize your high-level milestones.</p>
          </div>
        ) : (
          projects.map((proj) => {
            const pct = Math.round(
              (proj.completedTasks / Math.max(1, proj.totalTasks)) * 100,
            );
            return (
              <div
                key={proj.id}
                className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 shadow-sm hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2 font-bold text-sm text-white">
                      <FolderKanban size={17} className="text-accent-400" />
                      <span>{proj.name}</span>
                    </div>
                    {proj.health === "healthy" && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] bg-verdigris-950 text-verdigris-400 border border-verdigris-800/40 font-mono font-semibold flex items-center gap-1">
                        <CheckCircle2 size={11} /> Healthy
                      </span>
                    )}
                    {proj.health === "at_risk" && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] bg-molten-950 text-molten-400 border border-molten-800/40 font-mono font-semibold flex items-center gap-1">
                        <AlertTriangle size={11} /> At Risk
                      </span>
                    )}
                    {proj.health === "blocked" && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] bg-danger-950 text-danger-400 border border-danger-800/40 font-mono font-semibold flex items-center gap-1">
                        <ShieldAlert size={11} /> Blocked
                      </span>
                    )}
                    {proj.health === "completed" && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] bg-purple-950 text-purple-400 border border-purple-800/40 font-mono font-semibold flex items-center gap-1">
                        <CheckCircle2 size={11} /> Complete
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 font-mono leading-relaxed">
                    {proj.reason}
                  </p>
                </div>

                <div className="space-y-2 pt-2 border-t border-slate-800/60">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="text-slate-400">
                      Progress: <strong className="text-white">{pct}%</strong>
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-400">
                        {proj.completedTasks} / {proj.totalTasks} Tasks
                      </span>
                      <button
                        onClick={() => incrementTask(proj)}
                        disabled={proj.completedTasks >= proj.totalTasks}
                        className="px-2 py-0.5 rounded bg-accent-500/20 hover:bg-accent-500/30 text-accent-400 border border-accent-500/40 text-[10px] disabled:opacity-30"
                      >
                        +1 Task
                      </button>
                    </div>
                  </div>
                  <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        pct === 100 ? "bg-verdigris-400" : "bg-accent-500"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="flex justify-end pt-1">
                    <button
                      onClick={() => deleteProject(proj.id)}
                      className="text-slate-500 hover:text-danger-400 p-1 rounded transition-colors text-[11px] flex items-center gap-1 font-mono"
                    >
                      <Trash2 size={12} /> Delete
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* New Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">
                Create New Project
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-3.5">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Project Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Vision AI Integration..."
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                />
              </div>

              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Description / Goal
                </label>
                <textarea
                  placeholder="e.g. Local OCR and multimodal screen interpretation."
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500 resize-none h-16"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Health Status
                  </label>
                  <select
                    value={health}
                    onChange={(e) => setHealth(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  >
                    <option value="healthy">Healthy</option>
                    <option value="at_risk">At Risk</option>
                    <option value="blocked">Blocked</option>
                    <option value="completed">Completed</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Total Target Tasks
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={totalTasks}
                    onChange={(e) => setTotalTasks(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 rounded-xl hover:bg-slate-800 text-slate-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold shadow-md"
                >
                  Save Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
