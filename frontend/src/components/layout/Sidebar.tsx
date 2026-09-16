import React from "react";
import {
  LayoutDashboard,
  Radio,
  MessageSquare,
  Bot,
  Brain,
  BarChart3,
  Sparkles,
  Settings,
  Shield,
  Calendar,
  CheckSquare,
  Layers,
  Activity,
  TrendingUp,
  UtensilsCrossed,
  Users,
  Mail,
  Workflow,
  BookOpen,
} from "lucide-react";
import { soundFX } from "../../lib/soundFX";

export type NavSection =
  | "dashboard"
  | "companion"
  | "chat"
  | "today"
  | "tasks"
  | "projects"
  | "meetings"
  | "email"
  | "research"
  | "automations"
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

interface NavGroup {
  category: string;
  items: { id: NavSection; label: string; icon: React.ElementType }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    category: "WORKSPACE",
    items: [
      { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
      { id: "chat", label: "Pair-Programmer", icon: MessageSquare },
      { id: "companion", label: "Voice Companion", icon: Radio },
      { id: "projects", label: "Repositories", icon: Layers },
      { id: "tasks", label: "Sprint Backlog", icon: CheckSquare },
      { id: "research", label: "Research & Docs", icon: BookOpen },
      { id: "automations", label: "Automations", icon: Workflow },
    ],
  },
  {
    category: "OPERATIONS",
    items: [
      { id: "today", label: "Daily Standup", icon: Calendar },
      { id: "meetings", label: "Meetings & Audio", icon: Users },
      { id: "email", label: "Alerts & Feeds", icon: Mail },
      { id: "food", label: "Wellness", icon: UtensilsCrossed },
    ],
  },
  {
    category: "TECHNICAL TELEMETRY",
    items: [
      { id: "memory", label: "Memory Graph", icon: Brain },
      { id: "agents", label: "Agent Fleet", icon: Bot },
      { id: "benchmarks", label: "Benchmarks", icon: BarChart3 },
      { id: "security", label: "Zero-Trust Security", icon: Shield },
      { id: "activity", label: "Activity Log", icon: Activity },
      { id: "insights", label: "System Insights", icon: TrendingUp },
      { id: "self-improvement", label: "Self-Improvement", icon: Sparkles },
      { id: "settings", label: "Settings", icon: Settings },
    ],
  },
];

export const Sidebar: React.FC<SidebarProps> = ({
  activeSection,
  onSelectSection,
}) => {
  return (
    <aside
      aria-label="Main Navigation"
      className="w-60 h-screen bg-[#14060B]/95 backdrop-blur-2xl border-r border-[#F6E6EA]/[0.08] flex flex-col justify-between p-3 z-30 select-none shadow-[16px_0_48px_rgba(10,3,6,0.55)] font-mono flex-shrink-0"
    >
      <div className="flex-1 flex flex-col min-h-0">
        {/* Brand & Classification Header */}
        <div className="drag-region px-3 py-3 mb-2 border-b border-[#F6E6EA]/[0.08] flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blush-100 via-accent to-burgundy-700 text-burgundy-950 flex items-center justify-center font-display font-black text-sm shadow-md flex-shrink-0" aria-hidden="true">
              C
            </div>
            <div className="overflow-hidden">
              <div className="flex items-center gap-1.5">
                <h1 className="font-display font-bold text-[14px] tracking-tight text-white truncate">
                  C.O.P.P.E.R.
                </h1>
                <span className="w-1.5 h-1.5 rounded-full bg-verdigris flex-shrink-0" aria-hidden="true" />
              </div>
              <p className="text-[8.5px] text-zinc-400 font-mono tracking-[0.14em] uppercase truncate font-semibold">
                AI DEV WORKSTATION
              </p>
            </div>
          </div>

          <div className="mt-2.5 px-2 py-1 rounded-lg bg-white/[0.03] border border-white/[0.06] flex items-center justify-between text-[9px] text-zinc-400 font-mono">
            <span className="text-verdigris font-semibold">AIR-GAPPED</span>
            <span className="text-zinc-300">30 AGENTS</span>
          </div>
        </div>

        {/* Navigation Sections */}
        <nav aria-label="Application Sections" className="no-drag space-y-3 overflow-y-auto flex-1 custom-scrollbar pr-1 min-h-0">
          {NAV_GROUPS.map((group) => (
            <div key={group.category} className="space-y-0.5">
              <div className="px-2.5 py-1 text-[8.5px] font-mono font-semibold tracking-[0.14em] text-zinc-500 uppercase">
                <span>{group.category}</span>
              </div>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeSection === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      soundFX.play("tab");
                      onSelectSection(item.id);
                    }}
                    aria-current={isActive ? "page" : undefined}
                    aria-label={`${item.label} section${isActive ? ", current page" : ""}`}
                    className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-[12px] font-medium transition-all duration-150 group cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blush-100 ${
                      isActive
                        ? "bg-blush-100/12 text-white border-l-2 border-blush-100 font-semibold"
                        : "text-zinc-400 border-l-2 border-transparent hover:text-white hover:bg-white/[0.04]"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <Icon
                        aria-hidden="true"
                        className={`w-3.5 h-3.5 flex-shrink-0 transition-colors ${
                          isActive
                            ? "text-blush-100"
                            : "text-zinc-500 group-hover:text-zinc-300"
                        }`}
                      />
                      <span className="tracking-tight truncate">{item.label}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Bottom Telemetry & Air-Gap Status Panel */}
      <div className="p-2.5 rounded-xl bg-[#220D15]/80 border border-blush-100/[0.10] space-y-1.5 font-mono text-[9px] flex-shrink-0 mt-2 shadow-[inset_0_1px_0_rgba(246,230,234,0.08)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-verdigris shadow-[0_0_8px_rgba(95,168,143,0.7)] animate-pulse flex-shrink-0" />
            <span className="font-bold text-white tracking-wider">
              100% OFFLINE
            </span>
          </div>
          <span className="text-blush-300/60">0.05ms</span>
        </div>

        <div className="w-full bg-[#12060A] rounded-full h-1 overflow-hidden border border-blush-100/10">
          <div className="bg-gradient-to-r from-accent via-blush-300 to-blush-100 h-full w-[80%]" />
        </div>

        <div className="flex justify-between text-[9px] text-zinc-400">
          <span>VRAM: 6.4/8.0 GB</span>
          <span className="text-verdigris font-semibold">PASS</span>
        </div>
      </div>
    </aside>
  );
};
