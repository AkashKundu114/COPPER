import React from "react";
import { Plus, Tag } from "lucide-react";

export type TaskStatus = "inbox" | "planned" | "active" | "blocked" | "completed" | "archived";

interface TaskItem {
  id: string;
  title: string;
  project: string;
  priority: "high" | "medium" | "low";
  duration: string;
  status: TaskStatus;
}

const INITIAL_TASKS: TaskItem[] = [
  { id: "1", title: "Map Ollama local models in pre-trained router", project: "COPPER Core", priority: "high", duration: "90 min", status: "active" },
  { id: "2", title: "Run Alembic DB migration on memory_v2 schema", project: "Database Engine", priority: "high", duration: "45 min", status: "planned" },
  { id: "3", title: "Validate Tauri desktop bundle on Windows x64", project: "Tauri Shell", priority: "medium", duration: "60 min", status: "inbox" },
  { id: "4", title: "Fix SVG label rotation math in NeuralBrain component", project: "UI System", priority: "medium", duration: "30 min", status: "completed" },
  { id: "5", title: "Setup PII redaction rules for Zero-Trust Firewall", project: "Data Firewall", priority: "high", duration: "60 min", status: "blocked" },
];

export const TasksView: React.FC = () => {
  const statuses: TaskStatus[] = ["inbox", "planned", "active", "blocked", "completed", "archived"];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Task Manager</h1>
          <p className="text-xs text-gray-400 font-mono">Organized by Inbox, Planned, Active, Blocked, Completed, Archived</p>
        </div>
        <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#ff5722] hover:bg-[#ff5722]/80 text-black font-bold text-xs transition-all shadow-md">
          <Plus size={14} />
          <span>New Task</span>
        </button>
      </div>

      {}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {statuses.slice(0, 3).map((status) => (
          <div key={status} className="p-4 rounded-xl bg-[#14141a] border border-white/10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-white capitalize font-mono">{status}</span>
              <span className="px-2 py-0.5 rounded bg-black/50 text-[10px] text-gray-400 font-mono">
                {INITIAL_TASKS.filter((t) => t.status === status).length}
              </span>
            </div>
            <div className="space-y-2">
              {INITIAL_TASKS
                .filter((t) => t.status === status)
                .map((task) => (
                  <div key={task.id} className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-2 text-xs hover:border-[#b87333]/50 transition-all">
                    <p className="font-semibold text-white">{task.title}</p>
                    <div className="flex items-center justify-between text-[10px] font-mono text-gray-400">
                      <span className="flex items-center gap-1"><Tag size={10} className="text-[#ff5722]" /> {task.project}</span>
                      <span>{task.duration}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
