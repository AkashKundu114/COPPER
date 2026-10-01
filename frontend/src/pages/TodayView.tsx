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
import { scheduleAPI, type ScheduleEvent } from "../lib/api";
import { DailyBriefingCard } from "../components/ambient/DailyBriefingCard";
import { ActivityDashboardWidget } from "../components/ambient/ActivityDashboardWidget";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

export const TodayView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"day" | "week" | "month">("day");
  const [events, setEvents] = useState<ScheduleEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [time, setTime] = useState("10:00 AM");
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState<ScheduleEvent["category"]>("Focus");

  const loadEvents = async () => {
    try {
      const data = await scheduleAPI.list();
      setEvents(data || []);
    } catch (err) {
      console.error("Failed to load schedule events from backend:", err);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
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

    try {
      const newEvent = await scheduleAPI.create(payload);
      setEvents((prev) => [...prev, newEvent]);
      setTitle("");
      setIsModalOpen(false);
    } catch (err) {
      console.error("Failed to create schedule event:", err);
    }
  };

  const toggleEvent = async (event: ScheduleEvent) => {
    try {
      const updated = await scheduleAPI.update(event.id, { completed: !event.completed });
      setEvents((prev) => prev.map((e) => (e.id === event.id ? updated : e)));
    } catch (err) {
      console.error("Failed to toggle schedule event:", err);
    }
  };

  const deleteEvent = async (id: string) => {
    try {
      await scheduleAPI.delete(id);
      setEvents((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      console.error("Failed to delete schedule event:", err);
    }
  };

  const todayDate = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="p-6 space-y-5 max-w-5xl mx-auto text-text select-none font-sans pb-16">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text tracking-tight">
            Today
          </h1>
          <p className="text-xs text-text-secondary mt-0.5">{todayDate} • Live Standup Schedule</p>
        </div>
        <div className="flex items-center gap-2.5">
          <div className="flex gap-1 p-1 bg-surface-base rounded-lg border border-border-subtle text-xs">
            {(["day", "week", "month"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1 rounded-md capitalize transition-colors cursor-pointer text-xs ${
                  activeTab === tab
                    ? "bg-copper text-text-inverse font-medium shadow-sm"
                    : "text-text-secondary hover:text-text hover:bg-surface-hover"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsModalOpen(true)}
          >
            <Plus size={14} className="mr-1" />
            <span>Add Event</span>
          </Button>
        </div>
      </div>

      {/* Autonomous Ambient Briefing Card */}
      <DailyBriefingCard />

      {/* Live Focus Widget */}
      <ActivityDashboardWidget />

      {/* Schedule Recommendation Banner */}
      <div className="surface-card p-3.5 rounded-xl border border-border flex items-center justify-between text-xs">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-copper-subtle text-copper">
            <Sparkles size={15} />
          </div>
          <div>
            <p className="font-semibold text-text">
              Schedule Optimizer
            </p>
            <p className="text-text-secondary text-2xs">
              {events.filter((e) => !e.completed).length} pending events scheduled for today.
            </p>
          </div>
        </div>
        <Badge variant="success">On Track</Badge>
      </div>

      {/* Timeline Section */}
      <div className="surface-card p-4 rounded-xl border border-border space-y-3.5">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-text uppercase tracking-wider">
            {activeTab === "day"
              ? "Today's Timeline"
              : activeTab === "week"
                ? "This Week's Plan"
                : "Monthly Calendar Agenda"}
          </h3>
          <span className="text-2xs font-mono text-text-tertiary">
            {events.length} Items
          </span>
        </div>

        {loading ? (
          <div className="p-10 text-center text-xs text-text-tertiary font-mono">
            Loading events...
          </div>
        ) : events.length === 0 ? (
          <div className="p-10 text-center text-xs text-text-tertiary font-mono">
            No events scheduled. Click "+ Add Event" to plan your day.
          </div>
        ) : (
          <div className="space-y-2">
            {events.map((event) => (
              <div
                key={event.id}
                className={`p-3 rounded-lg border flex items-center justify-between transition-colors ${
                  event.completed
                    ? "bg-surface-base/50 border-border-subtle opacity-50"
                    : "bg-surface-base border-border-subtle hover:border-border shadow-sm"
                }`}
              >
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => toggleEvent(event)}
                    className="text-text-tertiary hover:text-copper transition-colors cursor-pointer"
                  >
                    {event.completed ? (
                      <CheckCircle2 size={17} className="text-success" />
                    ) : (
                      <Circle size={17} />
                    )}
                  </button>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-medium text-copper flex items-center gap-1">
                        <Clock size={11} /> {event.time}
                      </span>
                      <Badge
                        variant={
                          event.category === "Focus"
                            ? "copper"
                            : event.category === "Meeting"
                            ? "info"
                            : event.category === "Review"
                            ? "warning"
                            : "default"
                        }
                      >
                        {event.category}
                      </Badge>
                    </div>
                    <p
                      className={`text-xs font-medium text-text mt-0.5 ${
                        event.completed ? "line-through text-text-tertiary" : ""
                      }`}
                    >
                      {event.title}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => deleteEvent(event.id)}
                  className="p-1 text-text-tertiary hover:text-danger rounded-md hover:bg-surface-hover transition-colors cursor-pointer"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-sm animate-fade-in font-sans text-xs">
          <div className="w-full max-w-md surface-card border border-border rounded-xl p-5 shadow-elevation-modal space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <h3 className="font-semibold text-sm text-text">
                Add Schedule Event
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-text-secondary hover:text-text cursor-pointer"
              >
                <X size={15} />
              </button>
            </div>

            <form onSubmit={handleCreateEvent} className="space-y-3">
              <div>
                <label className="text-2xs text-text-secondary font-medium block mb-1">
                  Event / Task Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Deep Work Session..."
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-base border border-border-subtle text-text placeholder:text-text-tertiary outline-none focus:border-copper text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-2xs text-text-secondary font-medium block mb-1">
                    Time
                  </label>
                  <input
                    type="text"
                    value={time}
                    onChange={(e) => setTime(e.target.value)}
                    placeholder="e.g. 10:30 AM"
                    className="w-full px-3 py-2 rounded-lg bg-surface-base border border-border-subtle text-text placeholder:text-text-tertiary outline-none focus:border-copper text-xs"
                  />
                </div>
                <div>
                  <label className="text-2xs text-text-secondary font-medium block mb-1">
                    Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-lg bg-surface-base border border-border-subtle text-text outline-none focus:border-copper text-xs cursor-pointer"
                  >
                    <option value="Focus">Focus</option>
                    <option value="Meeting">Meeting</option>
                    <option value="Review">Review</option>
                    <option value="Break">Break</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-border">
                <Button
                  variant="ghost"
                  size="sm"
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                >
                  Save Event
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
