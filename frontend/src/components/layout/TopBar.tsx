import React, { useState, useEffect } from "react";
import { Search, User, Clipboard, GitBranch, Volume2, VolumeX } from "lucide-react";
import type { ProfileResponse } from "../../lib/api";
import { CognitiveStatusBadge } from "../ambient/CognitiveStatusBadge";
import { soundFX } from "../../lib/soundFX";
import { systemAPI } from "../../services/api";

interface TopBarProps {
  sectionTitle: string;
  profile: ProfileResponse | null;
  drawerOpen: boolean;
  onToggleDrawer: () => void;
  onOpenCommandPalette: () => void;
  onToggleClipboard?: () => void;
  isClipboardOpen?: boolean;
}

const SECTION_TITLES: Record<string, string> = {
  dashboard: "Mission Cockpit",
  companion: "Voice Companion",
  chat: "Pair Programmer",
  agents: "Agent Fleet",
  memory: "Memory Graph",
  benchmarks: "Routing & Benchmarks",
  "self-improvement": "Self-Improvement",
  security: "Security Center",
  today: "Daily Standup",
  tasks: "Sprint Backlog",
  projects: "Workspaces",
  meetings: "Architecture Notes",
  email: "Alerts & Feeds",
  research: "Documentation",
  automations: "Automations",
  activity: "System Activity",
  insights: "Analytics",
  food: "Wellness",
  settings: "Settings",
};

export const TopBar: React.FC<TopBarProps> = ({
  sectionTitle,
  profile,
  drawerOpen,
  onToggleDrawer,
  onOpenCommandPalette,
  onToggleClipboard,
  isClipboardOpen,
}) => {
  const [timeUtc, setTimeUtc] = useState("");
  const [timeLocal, setTimeLocal] = useState("");
  const [isElectron, setIsElectron] = useState(false);
  const [sfxMuted, setSfxMuted] = useState(() => soundFX.isMuted());
  const [gitStatus, setGitStatus] = useState({ branch: "main", repo: "COPPER" });

  useEffect(() => {
    systemAPI
      .getCockpitStatus()
      .then((res) => {
        if (res.data?.git) {
          setGitStatus({
            branch: res.data.git.branch || "main",
            repo: res.data.git.repo || "COPPER",
          });
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const isRunningInElectron =
      typeof window !== "undefined" &&
      (Boolean((window as any).ipcRenderer) ||
        Boolean((window as any).require) ||
        (typeof navigator !== "undefined" &&
          navigator.userAgent.toLowerCase().includes("electron")));
    setIsElectron(isRunningInElectron);

    const updateTime = () => {
      const now = new Date();
      setTimeUtc(now.toISOString().slice(11, 19) + "Z");
      setTimeLocal(now.toLocaleTimeString([], { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const displayTitle =
    SECTION_TITLES[sectionTitle] || sectionTitle.replace(/-/g, " ");

  return (
    <header
      role="banner"
      aria-label="Top Bar Controls and Status"
      className="drag-region h-14 bg-[#16080D]/90 backdrop-blur-xl border-b border-[#F6E6EA]/[0.08] flex items-center justify-between px-3 md:px-5 z-20 select-none shadow-[0_4px_20px_rgba(10,3,6,0.25)]"
    >
      {/* Left: Section Title & Repository context */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-accent ring-2 ring-accent/20" aria-hidden="true" />
          <h2 className="font-display text-xs md:text-sm font-semibold text-white tracking-wide uppercase whitespace-nowrap">
            {displayTitle}
          </h2>
        </div>

        <div className="hidden xl:flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-white/[0.03] border border-white/[0.08] font-mono text-[10px] text-zinc-400">
          <GitBranch size={11} className="text-accent" />
          <span className="text-zinc-200 font-medium">{gitStatus.branch}</span>
          <span className="text-zinc-600">/</span>
          <span className="text-zinc-300">{gitStatus.repo}</span>
          <span className="text-zinc-600">·</span>
          <span className="px-1.5 py-0.2 rounded bg-verdigris/15 text-verdigris text-[9px] font-bold">AIR-GAP</span>
        </div>
      </div>

      {/* Center: Command Palette Search */}
      <div className="flex items-center justify-center flex-1 max-w-xs md:max-w-sm px-2">
        <button
          onClick={() => {
            soundFX.play("click");
            onOpenCommandPalette();
          }}
          aria-label="Open command palette (Ctrl+K)"
          className="no-drag w-full flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.08] hover:border-white/20 text-[11px] text-zinc-400 hover:text-white transition-all group cursor-pointer focus-visible:ring-1 focus-visible:ring-accent shadow-sm"
        >
          <div className="flex items-center gap-2 overflow-hidden">
            <Search size={12} className="text-zinc-400 group-hover:text-accent transition-colors flex-shrink-0" aria-hidden="true" />
            <span className="text-[11px] tracking-tight truncate">Search or jump to...</span>
          </div>
          <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded bg-black/40 text-[9px] font-mono text-zinc-400 border border-white/10 flex-shrink-0 font-medium">
            Ctrl+K
          </kbd>
        </button>
      </div>

      {/* Right: Telemetry & Actions */}
      <div className={`flex items-center gap-2 flex-shrink-0 ${isElectron ? "pr-36" : "pr-2 sm:pr-4"}`}>
        {/* Tactical Local Clock with UTC in Tooltip */}
        <div
          className="hidden 2xl:flex items-center gap-1.5 px-2 py-0.5 rounded-lg bg-white/[0.03] border border-white/[0.08] font-mono text-[10px] whitespace-nowrap shadow-sm cursor-default"
          title={`Local: ${timeLocal} | UTC: ${timeUtc}`}
          aria-label={`Local time: ${timeLocal}, UTC time: ${timeUtc}`}
        >
          <span className="text-zinc-500">LOC</span>
          <span className="text-accent font-semibold">{timeLocal}</span>
        </div>

        {/* Real-Time Ambient Cognitive Load */}
        <CognitiveStatusBadge />

        {/* System Security / Status Badge */}
        <div
          className="hidden lg:flex items-center gap-1.5 px-2 py-1 rounded-lg bg-verdigris/10 border border-verdigris/25 text-verdigris text-[10px] font-bold font-mono whitespace-nowrap shadow-sm"
          role="status"
          aria-label="System status: DEFCON 5, all systems nominal"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" aria-hidden="true" />
          <span>DEFCON 5</span>
        </div>

        {/* Semantic Audio SFX Toggle (uisfx.com inspiration) */}
        <button
          onClick={() => {
            const next = soundFX.toggleMute();
            setSfxMuted(next);
          }}
          className={`no-drag p-1.5 rounded-lg border transition-all cursor-pointer ${
            sfxMuted
              ? "bg-white/[0.02] border-white/[0.06] text-zinc-500 hover:text-zinc-400"
              : "bg-white/[0.04] border-white/[0.12] text-zinc-300 hover:text-white hover:border-accent/40"
          }`}
          title={sfxMuted ? "Unmute UI Sound Effects" : "Mute UI Sound Effects"}
          aria-label={sfxMuted ? "Unmute UI Sound Effects" : "Mute UI Sound Effects"}
        >
          {sfxMuted ? <VolumeX size={13} /> : <Volume2 size={13} />}
        </button>

        {/* Smart Clipboard Trigger */}
        {onToggleClipboard && (
          <button
            onClick={() => {
              soundFX.play("click");
              onToggleClipboard();
            }}
            aria-label="Toggle Smart Clipboard history drawer"
            aria-expanded={isClipboardOpen}
            className={`no-drag flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[11px] font-mono whitespace-nowrap cursor-pointer transition-all ${
              isClipboardOpen
                ? "bg-accent/20 text-accent border-accent/40 shadow-sm"
                : "bg-white/[0.03] border-white/[0.08] hover:border-accent/40 hover:bg-white/[0.06] text-zinc-300 hover:text-white"
            }`}
            title="Smart Clipboard (History & Pointers)"
          >
            <Clipboard size={13} className={isClipboardOpen ? "text-accent" : "text-zinc-400"} />
            <span className="hidden xl:inline font-medium">CLIPBOARD</span>
          </button>
        )}

        {/* Operator Profile Trigger */}
        <button
          onClick={() => {
            soundFX.play("click");
            onToggleDrawer();
          }}
          aria-label="Toggle user profile and agent details drawer"
          aria-expanded={drawerOpen}
          className="no-drag flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.08] hover:border-blush-100/30 hover:bg-white/[0.06] text-[11px] text-zinc-300 hover:text-white transition-all font-mono whitespace-nowrap cursor-pointer focus-visible:ring-1 focus-visible:ring-accent"
        >
          <User size={13} className="text-accent" aria-hidden="true" />
          <span className="font-semibold text-white text-[11px]">
            {profile?.relationship_tier || "OPERATOR"}
          </span>
        </button>
      </div>
    </header>
  );
};
