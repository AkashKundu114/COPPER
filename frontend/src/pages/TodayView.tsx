import React, { useState, useEffect } from "react";
import {
  Clock,
  Plus,
  Trash2,
  CheckCircle2,
  Circle,
  X,
  Sparkles,
} from "lucide-react";
import { workspaceAPI } from "../lib/api";

interface ScheduleEvent {
  id: string;
  time: string;
  title: string;
  category: "Focus" | "Meeting" | "Break" | "Review";
  completed: boolean;
}

export const TodayView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"day" | "week" | "month">("day");
  const [events, setEvents] = useState<ScheduleEvent[]>([]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [time, setTime] = useState("10:00 AM");
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState<ScheduleEvent["category"]>("Focus");

  useEffect(() => {
    workspaceAPI.list<ScheduleEvent>("event").then(setEvents).catch(console.error);
  }, []);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const payload = {
      time: time.trim() || "12:00 PM",
      title: title.trim(),
      category,
      completed: false,
    };

    const newEvent = await workspaceAPI.create<ScheduleEvent>("event", payload);
    setEvents((prev) => [...prev, newEvent]);
    setTitle("");
    setIsModalOpen(false);
  };

  const toggleEvent = async (event: ScheduleEvent) => {
    const updated = await workspaceAPI.update<ScheduleEvent>("event", event.id, { completed: !event.completed });
    setEvents((prev) => prev.map((e) => e.id === event.id ? updated : e));
  };

  const deleteEvent = async (id: string) => {
    await workspaceAPI.remove("event", id);
    setEvents((prev) => prev.filter((e) => e.id !== id));
  };

  const todayDate = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Schedule & Today Overview
          </h1>
          <p className="text-xs text-slate-400 font-mono">{todayDate}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 p-1 bg-slate-900 rounded-xl border border-slate-800 text-xs font-mono">
            {(["day", "week", "month"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 rounded-lg capitalize transition-all ${
                  activeTab === tab
                    ? "bg-accent-500/20 text-accent-400 border border-accent-500/40"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-accent-500 hover:bg-accent-400 text-slate-950 font-bold text-xs transition-all shadow-md shadow-accent-500/20"
          >
            <Plus size={14} strokeWidth={2.5} />
            <span>Add Event</span>
          </button>
        </div>
      </div>

      {/* AI Proactive Recommendation Banner */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs font-mono">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-accent-500/10 text-accent-400 border border-accent-500/20">
            <Sparkles size={16} />
          </div>
          <div>
            <p className="font-semibold text-white">
              Smart Schedule Optimizer Active
            </p>
            <p className="text-slate-400 text-[11px]">
              {events.filter((e) => !e.completed).length} pending events
              scheduled for today. Optimal focus window: 11:00 AM – 1:00 PM.
            </p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-verdigris-950 text-verdigris-400 text-[10px] font-bold border border-verdigris-800/40">
          On Track
        </span>
      </div>

      {/* Timeline Section */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider">
            {activeTab === "day"
              ? "Today's Timeline"
              : activeTab === "week"
                ? "This Week's Plan"
                : "Monthly Calendar Agenda"}
          </h3>
          <span className="text-[11px] font-mono text-slate-500">
            {events.length} Items
          </span>
        </div>

        {events.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 font-mono">
            No events scheduled. Click "+ Add Event" to plan your day.
          </div>
        ) : (
          <div className="space-y-2.5">
            {events.map((event) => (
              <div
                key={event.id}
                className={`p-3.5 rounded-xl border flex items-center justify-between transition-all ${
                  event.completed
                    ? "bg-slate-950/40 border-slate-900 opacity-50"
                    : "bg-slate-950/80 border-slate-800/80 hover:border-slate-700 shadow-sm"
                }`}
              >
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => toggleEvent(event)}
                    className="text-slate-400 hover:text-accent-400 transition-colors"
                  >
                    {event.completed ? (
                      <CheckCircle2 size={18} className="text-verdigris-400" />
                    ) : (
                      <Circle size={18} />
                    )}
                  </button>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-accent-400 flex items-center gap-1">
                        <Clock size={11} /> {event.time}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                          event.category === "Focus"
                            ? "bg-purple-950 text-purple-400 border border-purple-800/40"
                            : event.category === "Meeting"
                              ? "bg-blue-950 text-blue-400 border border-blue-800/40"
                              : event.category === "Review"
                                ? "bg-molten-950 text-molten-400 border border-molten-800/40"
                                : "bg-slate-800 text-slate-300"
                        }`}
                      >
                        {event.category}
                      </span>
                    </div>
                    <p
                      className={`text-sm font-medium text-white mt-0.5 ${event.completed ? "line-through text-slate-400" : ""}`}
                    >
                      {event.title}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => deleteEvent(event.id)}
                  className="p-1.5 text-slate-500 hover:text-danger-400 rounded-lg hover:bg-slate-800 transition-colors"
                  title="Delete event"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Event Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in font-mono text-xs">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="font-bold text-sm text-white">
                Add Schedule Event
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateEvent} className="space-y-3.5">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">
                  Event / Milestone Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Deep Work Session..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Time
                  </label>
                  <input
                    type="text"
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    placeholder="e.g. 10:30 AM"
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white outline-none focus:border-accent-500"
                  >
                    <option value="Focus">Focus</option>
                    <option value="Meeting">Meeting</option>
                    <option value="Review">Review</option>
                    <option value="Break">Break</option>
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
                  Save Event
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
