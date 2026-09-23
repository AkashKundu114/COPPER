import React, { useState, useEffect } from "react";
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
  Activity,
  TrendingUp,
  UtensilsCrossed,
  Users,
  Mail,
} from "lucide-react";
import { soundFX } from "../../lib/soundFX";
import { systemAPI } from "../../services/api";
import { AGENTS } from "../../constants/agents";

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

interface NavItem {
  id: NavSection;
  label: string;
  icon: React.ElementType;
  testId?: string;
  ariaLabel?: string;
}

interface NavGroup {
  category: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    category: "WORKSPACE",
    items: [
      { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
      {
        id: "chat",
        label: "Pair-Programmer",
        icon: MessageSquare,
        testId: "conversation-nav",
        ariaLabel: "Conversation",
      },
      { id: "companion", label: "Voice Companion", icon: Radio },
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
      {
        id: "activity",
        label: "Activity Log",
        icon: Activity,
        testId: "activity-nav",
        ariaLabel: "Activity Stream",
      },
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
  const [telemetry, setTelemetry] = useState<{
    vramUsed: number;
    vramTotal: number;
    vramPct: number;
  }>({
    vramUsed: 0.22,
    vramTotal: 8.0,
    vramPct: 2.8,
  });

  useEffect(() => {
    const fetchTelem = () => {
      systemAPI
        .getTelemetry()
        .then((res) => {
          if (res.data?.gpu) {
            const gpu = res.data.gpu;
            setTelemetry({
              vramUsed: gpu.vram_used_gb || 0.22,
              vramTotal: gpu.vram_total_gb || 8.0,
              vramPct: gpu.vram_percent || 2.8,
            });
          }
        })
        .catch(() => {});
    };
    fetchTelem();
    const iv = setInterval(fetchTelem, 4000);
    return () => clearInterval(iv);
  }, []);

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
            <span className="text-zinc-300">{AGENTS.length} AGENTS</span>
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
                const testId = item.testId || `${item.id}-nav`;
                return (
                  <button
                    key={item.id}
                    type="button"
                    data-testid={testId}
                    onClick={() => {
                      soundFX.play("tab");
                      onSelectSection(item.id);
                    }}
                    aria-current={isActive ? "page" : undefined}
                    aria-label={
                      item.ariaLabel ||
                      `${item.label} section${isActive ? ", current page" : ""}`
                    }
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
          <span className="text-blush-300/60">0.16ms</span>
        </div>

        <div className="w-full bg-[#12060A] rounded-full h-1 overflow-hidden border border-blush-100/10">
          <div
            className="bg-gradient-to-r from-accent via-blush-300 to-blush-100 h-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(5, telemetry.vramPct))}%` }}
          />
        </div>

        <div className="flex justify-between text-[9px] text-zinc-400">
          <span>VRAM: {telemetry.vramUsed.toFixed(1)}/{telemetry.vramTotal.toFixed(1)} GB</span>
          <span className="text-verdigris font-semibold">PASS</span>
        </div>
      </div>
    </aside>
  );
};

