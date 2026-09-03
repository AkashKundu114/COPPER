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

const NAV_ITEMS: { id: NavSection; label: string; icon: React.ElementType }[] =
  [
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

export const Sidebar: React.FC<SidebarProps> = ({
  activeSection,
  onSelectSection,
}) => {
  return (
    <aside className="w-64 h-screen bg-[#05080e]/95 backdrop-blur-2xl border-r border-cyber-cyan/20 flex flex-col justify-between p-3.5 z-30 select-none shadow-[16px_0_40px_rgba(0,0,0,0.5)] font-mono">
      <div>
        {/* Brand & Classification Header */}
        <div className="drag-region px-3 py-3 mb-3 border-b border-cyber-cyan/15">
          <div className="flex items-center gap-3">
            <div className="notch-corner w-9 h-9 bg-gradient-to-br from-cyber-cyan to-accent text-black flex items-center justify-center font-display font-black text-base shadow-[0_0_15px_rgba(0,240,255,0.4)]">
              C
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="font-display font-bold text-[15px] tracking-tight text-white">
                  C.O.P.P.E.R.
                </h1>
                <span className="w-1.5 h-1.5 rounded-full bg-cyber-cyan animate-ping" />
              </div>
              <p className="text-[9px] text-cyber-cyan font-mono tracking-wider uppercase">
                GOD'S EYE OPS // TIER-1
              </p>
            </div>
          </div>

          <div className="mt-2.5 px-2 py-1 rounded bg-black/60 border border-cyber-cyan/20 flex items-center justify-between text-[9px] text-zinc-400">
            <span className="text-verdigris font-bold">AIR-GAPPED</span>
            <span className="text-zinc-500">26 MODELS ACTIVE</span>
          </div>
        </div>

        {/* Navigation Sections */}
        <nav className="no-drag space-y-1 overflow-y-auto max-h-[calc(100vh-210px)] custom-scrollbar pr-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectSection(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-[12px] font-medium transition-all duration-200 group ${
                  isActive
                    ? "copper-trace bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/40 shadow-sm"
                    : "text-zinc-400 border border-transparent hover:text-white hover:bg-white/5"
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon
                    className={`w-[15px] h-[15px] flex-shrink-0 transition-colors ${
                      isActive
                        ? "text-cyber-cyan drop-shadow-[0_0_8px_rgba(0,240,255,0.5)]"
                        : "text-zinc-500 group-hover:text-zinc-300"
                    }`}
                  />
                  <span className="tracking-tight">{item.label}</span>
                </div>
                {isActive && (
                  <span className="text-[9px] text-cyber-cyan font-mono font-bold">
                    ▸
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Telemetry & Air-Gap Status Panel */}
      <div className="p-2.5 rounded-xl bg-black/60 border border-cyber-cyan/20 space-y-1.5 font-mono text-[10px]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-verdigris shadow-[0_0_8px_rgba(0,255,136,0.6)] animate-pulse" />
            <span className="font-bold text-white tracking-wider">
              100% OFFLINE
            </span>
          </div>
          <span className="text-zinc-500">0.05ms</span>
        </div>

        <div className="w-full bg-zinc-900 rounded-full h-1 overflow-hidden border border-white/5">
          <div className="bg-gradient-to-r from-cyber-cyan to-accent h-full w-[80%]" />
        </div>

        <div className="flex justify-between text-[9px] text-zinc-400">
          <span>VRAM: 6.4/8.0 GB</span>
          <span className="text-verdigris font-semibold">PASS</span>
        </div>
      </div>
    </aside>
  );
};
