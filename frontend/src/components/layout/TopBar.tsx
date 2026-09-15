import React, { useState, useEffect } from "react";
import { Server, Search, User, Eye, Crosshair, Clipboard } from "lucide-react";
import type { ProfileResponse } from "../../lib/api";
import { useSensorMode, type SensorMode } from "../../context/SensorModeContext";
import { CognitiveStatusBadge } from "../ambient/CognitiveStatusBadge";

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
  dashboard: "Operations Center",
  companion: "Companion HUD // VAD",
  chat: "Multi-Agent Conversation",
  agents: "Agent Registry & Swarm",
  memory: "Memory Center & Atlas",
  benchmarks: "System Benchmarks",
  "self-improvement": "Self-Improvement & LoRA",
  security: "Security Center & Audit",
  today: "Today & Schedule",
  tasks: "Tasks & Objective Queue",
  projects: "Projects & Workspaces",
  meetings: "Meeting Intelligence & Local Audio",
  email: "Email Delegation & Drafts",
  research: "Autonomous Deep Research Hub",
  automations: "Visual Automation & Workflow Builder",
  activity: "Activity Stream & Logs",
  insights: "System Insights & Trends",
  food: "Nutrition & Bio Tracker",
  settings: "System Diagnostics & Settings",
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
  const { mode, setMode } = useSensorMode();
  const [timeUtc, setTimeUtc] = useState("");
  const [timeLocal, setTimeLocal] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeUtc(now.toISOString().slice(11, 19) + "Z");
      setTimeLocal(now.toLocaleTimeString([], { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const sensorButtons: { id: SensorMode; label: string }[] = [
    { id: "eo", label: "EO" },
    { id: "flir", label: "FLIR" },
    { id: "nvg", label: "NVG" },
    { id: "crt", label: "CRT" },
  ];

  const displayTitle =
    SECTION_TITLES[sectionTitle] || sectionTitle.replace(/-/g, " ");

  return (
    <header
      role="banner"
      aria-label="Top Bar Controls and Status"
      className="drag-region h-16 bg-[#16080D]/80 backdrop-blur-2xl border-b border-[#F6E6EA]/[0.10] flex items-center justify-between px-4 md:px-6 z-20 select-none shadow-[0_6px_28px_rgba(10,3,6,0.35)]"
    >
      {/* Left: Section Title & Coordinates Ticker */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-blush-100 animate-pulse shadow-[0_0_10px_rgba(246,230,234,0.9)]" aria-hidden="true" />
          <h2 className="font-display text-xs md:text-sm font-bold text-white tracking-wide uppercase whitespace-nowrap">
            {displayTitle}
          </h2>
        </div>

        <div className="hidden 2xl:flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-[#1A0A0F]/80 border border-blush-100/20 font-mono text-[10px] text-blush-200 whitespace-nowrap flex-shrink-0 shadow-sm" aria-label="GPS Coordinates 37 degrees 46 minutes North, 122 degrees 25 minutes West, Altitude 420 Kilometers">
          <Crosshair size={10} className="text-blush-100 animate-spin" aria-hidden="true" />
          <span>37°46'N 122°25'W</span>
          <span className="text-blush-300/40" aria-hidden="true">|</span>
          <span className="text-zinc-400">420KM</span>
        </div>
      </div>

      {/* Center: Command Bar + Sensor Look Pills */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          onClick={onOpenCommandPalette}
          aria-label="Open command palette (Ctrl+K)"
          className="no-drag flex items-center gap-2 px-3 py-2 rounded-xl bg-blush-100/[0.045] border border-blush-100/[0.12] text-[11px] text-zinc-300 hover:text-white hover:border-blush-100/40 hover:bg-blush-100/[0.08] transition-all w-36 sm:w-48 md:w-56 justify-between group shadow-sm flex-shrink-0 cursor-pointer focus-visible:ring-2 focus-visible:ring-blush-100"
        >
          <div className="flex items-center gap-1.5 overflow-hidden">
            <Search size={12} className="text-blush-200 group-hover:scale-110 transition-transform flex-shrink-0" aria-hidden="true" />
            <span className="font-mono text-[10px] tracking-tight truncate">COMMAND PALETTE...</span>
          </div>
          <kbd className="px-1.5 py-0.5 rounded-md bg-[#1A0A0F] text-[9px] font-mono text-blush-100 border border-blush-100/30 flex-shrink-0 font-bold">
            Ctrl+K
          </kbd>
        </button>

        {/* God's Eye Sensor Look Mode Switcher */}
        <div
          role="radiogroup"
          aria-label="Sensor display mode"
          className="no-drag flex items-center p-0.5 rounded-xl bg-blush-100/[0.04] border border-blush-100/[0.10] font-mono text-[10px] flex-shrink-0"
        >
          <span className="hidden sm:flex px-1 text-zinc-400 text-[9px] items-center gap-0.5" aria-hidden="true">
            <Eye size={10} className="text-blush-200" />
          </span>
          {sensorButtons.map((btn) => (
            <button
              key={btn.id}
              role="radio"
              aria-checked={mode === btn.id}
              aria-label={`Sensor mode: ${btn.label}`}
              onClick={() => setMode(btn.id)}
              className={`px-1.5 py-0.5 rounded-lg text-[10px] transition-all font-bold whitespace-nowrap cursor-pointer focus-visible:ring-1 focus-visible:ring-blush-100 ${
                mode === btn.id
                  ? "bg-blush-100 text-burgundy-950 shadow-[0_2px_10px_rgba(246,230,234,0.35)]"
                  : "text-zinc-300 hover:text-white hover:bg-blush-100/[0.06]"
              }`}
              title={`Switch sensor look: ${btn.label}`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Right: Tactical Clocks, DEFCON status & Air-Gap telemetry */}
      <div className="flex items-center gap-2 flex-shrink-0 pr-24">
        {/* Tactical Clock */}
        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-[#1A0A0F]/80 border border-blush-100/15 font-mono text-[10px] whitespace-nowrap flex-shrink-0 shadow-sm" aria-label={`UTC time: ${timeUtc}, Local time: ${timeLocal}`}>
          <span className="text-zinc-400">UTC</span>
          <span className="text-blush-100 font-bold">{timeUtc}</span>
          <span className="text-blush-300/30" aria-hidden="true">|</span>
          <span className="text-zinc-400">LOC</span>
          <span className="text-accent font-bold">{timeLocal}</span>
        </div>

        {/* Real-Time Ambient Cognitive Load */}
        <CognitiveStatusBadge />

        {/* DEFCON / Threat Status Badge */}
        <div className="hidden lg:flex items-center gap-1 px-2.5 py-0.5 rounded-lg bg-verdigris/12 border border-verdigris/35 text-verdigris text-[10px] font-bold font-mono whitespace-nowrap flex-shrink-0 shadow-sm" role="status" aria-label="System status: DEFCON 5, all systems nominal">
          <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" aria-hidden="true" />
          <span>DEFCON 5 // OK</span>
        </div>

        <div className="hidden sm:flex items-center gap-1 px-2 py-0.5 rounded-lg bg-[#1A0A0F]/80 border border-blush-100/25 text-blush-100 text-[10px] font-medium font-mono whitespace-nowrap flex-shrink-0">
          <Server size={11} className="text-blush-100" aria-hidden="true" />
          <span>LOCAL</span>
        </div>

        {onToggleClipboard && (
          <button
            onClick={onToggleClipboard}
            aria-label="Toggle Smart Clipboard history drawer"
            aria-expanded={isClipboardOpen}
            className={`no-drag flex items-center gap-1.5 px-3 py-2 rounded-xl border text-[11px] font-mono whitespace-nowrap flex-shrink-0 cursor-pointer transition-all ${
              isClipboardOpen
                ? "bg-accent-500/20 text-accent-400 border-accent-500/50 shadow-sm shadow-accent-500/20"
                : "bg-blush-100/[0.045] border-blush-100/[0.12] hover:border-accent-500/50 hover:bg-blush-100/[0.08] text-zinc-300 hover:text-white"
            }`}
            title="Smart Clipboard Intelligence"
          >
            <Clipboard size={12} className={isClipboardOpen ? "text-accent-400" : "text-zinc-400"} />
            <span className="hidden xl:inline font-semibold">CLIPBOARD</span>
          </button>
        )}

        <button
          onClick={onToggleDrawer}
          aria-label="Toggle user profile and agent details drawer"
          aria-expanded={drawerOpen}
          className="no-drag flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blush-100/[0.045] border border-blush-100/[0.12] hover:border-blush-100/40 hover:bg-blush-100/[0.08] text-[11px] text-zinc-300 hover:text-white transition-all font-mono whitespace-nowrap flex-shrink-0 cursor-pointer focus-visible:ring-2 focus-visible:ring-blush-100"
        >
          <User size={12} className="text-accent" aria-hidden="true" />
          <span className="font-semibold text-white">
            {profile?.relationship_tier || "OPERATOR"}
          </span>
        </button>
      </div>
    </header>
  );
};
