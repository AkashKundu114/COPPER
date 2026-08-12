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
  { id: "self-improvement", label: "Self-Improvement", icon: Sparkles },
  { id: "security", label: "Security Center", icon: ShieldCheck },
  { id: "food", label: "Food & Meals", icon: Utensils },
  { id: "settings", label: "Settings", icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeSection, onSelectSection }) => {
  return (
    <aside className="w-64 h-screen bg-[#0d0d11]/90 backdrop-blur-xl border-r border-[#b87333]/20 flex flex-col justify-between p-4 text-gray-200 z-30 select-none">
      {/* Brand Header */}
      <div>
        <div className="flex items-center gap-3 px-3 py-4 border-b border-[#b87333]/20 mb-4">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#ff5722] via-[#b87333] to-[#4a3b32] flex items-center justify-center font-bold text-white shadow-lg shadow-[#ff5722]/20 border border-[#ff5722]/40">
            C
          </div>
          <div>
            <h1 className="font-bold tracking-wider text-base text-white font-mono">C.O.P.P.E.R.</h1>
            <p className="text-[10px] text-[#b87333] font-medium tracking-tight">AI Operating System</p>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="space-y-1 overflow-y-auto max-h-[calc(100vh-180px)] custom-scrollbar pr-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectSection(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-[#b87333]/20 text-[#ff5722] border border-[#ff5722]/40 shadow-sm shadow-[#ff5722]/10"
                    : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-[#ff5722]" : "text-gray-400"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer System Mode */}
      <div className="p-3 rounded-lg bg-[#14141a] border border-white/5 text-[11px] text-gray-400 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-mono text-emerald-400 font-medium">100% Offline</span>
        </div>
        <span className="text-[10px] text-gray-500">v1.0.0</span>
      </div>
    </aside>
  );
};
