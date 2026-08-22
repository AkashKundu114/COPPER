import React from "react";
import {
  LayoutDashboard,
  MessageSquare,
  Calendar,
  CheckSquare,
  FolderKanban,
  Brain,
  Bot,
  Activity,
  BarChart3,
  Sparkles,
  ShieldCheck,
  Utensils,
  Settings,
} from "lucide-react";

export type NavSection =
  | "dashboard"
  | "chat"
  | "today"
  | "tasks"
  | "projects"
  | "memory"
  | "agents"
  | "activity"
  | "insights"
  | "benchmarks"
  | "self-improvement"
  | "security"
  | "food"
  | "settings";

interface SidebarProps {
  activeSection: NavSection;
  onSelectSection: (section: NavSection) => void;
}

const NAV_ITEMS: { id: NavSection; label: string; icon: React.ElementType }[] = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "chat", label: "Conversation", icon: MessageSquare },
  { id: "today", label: "Today / Schedule", icon: Calendar },
  { id: "tasks", label: "Tasks", icon: CheckSquare },
  { id: "projects", label: "Projects", icon: FolderKanban },
  { id: "memory", label: "Memory Center", icon: Brain },
  { id: "agents", label: "Agent Registry", icon: Bot },
  { id: "activity", label: "Agent Activity", icon: Activity },
  { id: "insights", label: "Insights", icon: BarChart3 },
  { id: "benchmarks", label: "Benchmarks & Metrics", icon: Activity },
  { id: "self-improvement", label: "Self-Improvement", icon: Sparkles },
  { id: "security", label: "Data Firewall", icon: ShieldCheck },
  { id: "food", label: "Food & Meals", icon: Utensils },
  { id: "settings", label: "Settings", icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeSection, onSelectSection }) => {
  return (
    <aside className="w-64 h-screen bg-bg flex flex-col justify-between p-4 z-30 select-none">
      <div>
        <div className="drag-region flex items-center gap-3 px-3 py-4 mb-4">
          <div className="w-8 h-8 rounded-lg bg-accent text-bg shadow-neon flex items-center justify-center font-bold text-sm">
            C
          </div>
          <div>
            <h1 className="font-semibold text-[15px] tracking-tight glow-text text-accent">C.O.P.P.E.R.</h1>
            <p className="text-[11px] text-text-muted">Personal AI OS</p>
          </div>
        </div>

        <nav className="no-drag space-y-0.5 overflow-y-auto max-h-[calc(100vh-160px)] custom-scrollbar pr-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectSection(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-bg-raised text-accent shadow-hud border border-neon"
                    : "text-text-muted hover:text-accent hover:bg-bg-panel hover:shadow-hud"
                }`}
              >
                <Icon className={`w-[18px] h-[18px] ${isActive ? "text-accent" : "text-text-muted"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-3 rounded-lg bg-bg-panel border border-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
          <span className="text-xs font-medium text-text">100% Offline</span>
        </div>
      </div>
    </aside>
  );
};
