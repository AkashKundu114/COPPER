import React, { useState, useEffect } from "react";
import {
  Plus,
  Tag,
  CheckCircle2,
  Circle,
  Trash2,
  X,
  Clock,
} from "lucide-react";

export type TaskStatus = "inbox" | "planned" | "active" | "completed";

export interface TaskItem {
  id: string;
  title: string;
  project: string;
  priority: "high" | "medium" | "low";
  duration: string;
  status: TaskStatus;
  createdAt: number;
}

const STORAGE_KEY = "copper_tasks_data";

export const TasksView: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [activeFilter, setActiveFilter] = useState<TaskStatus | "all">("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [project, setProject] = useState("General");
  const [priority, setPriority] = useState<"high" | "medium" | "low">("medium");
  const [duration, setDuration] = useState("30m");
  const [status, setStatus] = useState<TaskStatus>("inbox");

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
    } catch (e) {
      console.error(e);
    }
  }, [tasks]);

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const newTask: TaskItem = {
      id: `task-${Date.now()}`,
      title: title.trim(),
      project: project.trim() || "General",
      priority,
      duration: duration.trim() || "30m",
      status,
      createdAt: Date.now(),
    };

    setTasks((prev) => [newTask, ...prev]);
    setTitle("");
    setIsModalOpen(false);
  };

  const toggleTaskStatus = (id: string) => {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === id
          ? { ...t, status: t.status === "completed" ? "active" : "completed" }
          : t,
      ),
    );
  };

  const deleteTask = (id: string) => {
    setTasks((prev) => prev.filter((t) => t.id !== id));
  };

  const filteredTasks =
    activeFilter === "all"
      ? tasks
      : tasks.filter((t) => t.status === activeFilter);

  const statuses: TaskStatus[] = ["inbox", "planned", "active", "completed"];

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Task Manager
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            Organize tasks, workflows, and milestones
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-accent-500/20"
        >
          <Plus size={15} strokeWidth={2.5} />
          <span>New Task</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveFilter("all")}
          className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
            activeFilter === "all"
              ? "bg-accent-500/20 text-accent-400 border border-accent-500/40"
              : "text-slate-400 hover:text-white"
          }`}
        >
          All ({tasks.length})
        </button>
        {statuses.map((st) => (
          <button
            key={st}
            onClick={() => setActiveFilter(st)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono capitalize transition-all ${
              activeFilter === st
                ? "bg-accent-500/20 text-accent-400 border border-accent-500/40"
                : "text-slate-400 hover:text-white"
            }`}
          >
            {st} ({tasks.filter((t) => t.status === st).length})
          </button>
        ))}
      </div>

      {/* Tasks List */}
      {filteredTasks.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <p className="text-sm font-semibold text-slate-300">
            No tasks in this view
          </p>
          <p className="text-xs text-slate-500 font-mono">
            Click "+ New Task" above to add your first task.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              className={`p-4 rounded-xl border transition-all flex flex-col justify-between gap-3 ${
                task.status === "completed"
                  ? "bg-slate-950/40 border-slate-900 opacity-60"
                  : "bg-slate-900/80 border-slate-800 hover:border-slate-700 shadow-sm"
              }`}
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => toggleTaskStatus(task.id)}
                  className="mt-0.5 text-slate-400 hover:text-accent-400 transition-colors flex-shrink-0"
                >
                  {task.status === "completed" ? (
                    <CheckCircle2 size={18} className="text-verdigris-400" />
                  ) : (
                    <Circle size={18} />
                  )}
                </button>
                <div className="flex-1 space-y-1">
                  <p
                    className={`text-sm font-medium text-white ${task.status === "completed" ? "line-through text-slate-400" : ""}`}
                  >
                    {task.title}
                  </p>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono text-slate-400">
                    <span className="flex items-center gap-1 text-accent-400">
                      <Tag size={11} /> {task.project}
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock size={11} /> {task.duration}
                    </span>
                    <span>•</span>
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] font-semibold uppercase ${
                        task.priority === "high"
                          ? "bg-danger-950 text-danger-400 border border-danger-800/40"
                          : task.priority === "medium"
                            ? "bg-molten-950 text-molten-400 border border-molten-800/40"
                            : "bg-slate-800 text-slate-300"
                      }`}
                    >
                      {task.priority}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => deleteTask(task.id)}
                  className="p-1 text-slate-500 hover:text-danger-400 transition-colors rounded-lg hover:bg-slate-800"
                  title="Delete task"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Task Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">Create New Task</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-3.5">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Task Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Implement user auth flow..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Project
                  </label>
                  <input
                    type="text"
                    value={project}
                    onChange={(e) => setProject(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Estimated Duration
                  </label>
                  <input
                    type="text"
                    value={duration}
                    onChange={(e) => setDuration(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Priority
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Initial Status
                  </label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  >
                    <option value="inbox">Inbox</option>
                    <option value="planned">Planned</option>
                    <option value="active">Active</option>
                  </select>
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
                  Create Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
