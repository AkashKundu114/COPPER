import React, { useState, useEffect } from "react";
import { Server, Search, User, Eye, Crosshair } from "lucide-react";
import type { ProfileResponse } from "../../lib/api";
import { useSensorMode, type SensorMode } from "../../context/SensorModeContext";

interface TopBarProps {
  sectionTitle: string;
  profile: ProfileResponse | null;
  drawerOpen: boolean;
  onToggleDrawer: () => void;
  onOpenCommandPalette: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  sectionTitle,
  profile,
  onToggleDrawer,
  onOpenCommandPalette,
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

  return (
    <header className="drag-region h-14 bg-[#05080e]/90 backdrop-blur-xl border-b border-cyber-cyan/20 flex items-center justify-between px-6 z-20 select-none shadow-[0_4px_20px_rgba(0,0,0,0.5)]">
      {/* Left: Section Title & Coordinates Ticker */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-pulse" />
          <h2 className="font-display text-sm font-bold text-white tracking-tight uppercase">
            {sectionTitle}
          </h2>
        </div>

        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded bg-black/50 border border-cyber-cyan/20 font-mono text-[10px] text-cyber-cyan">
          <Crosshair size={11} className="text-cyber-cyan animate-spin" />
          <span>LAT 37°46'N LON 122°25'W</span>
          <span className="text-zinc-500">|</span>
          <span className="text-zinc-400">ALT 420KM</span>
        </div>
      </div>

      {/* Center: Command Bar + Sensor Look Pills */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenCommandPalette}
          className="no-drag flex items-center gap-2 px-3 py-1.5 rounded-lg bg-black/60 border border-cyber-cyan/30 text-[12px] text-zinc-400 hover:text-white hover:border-cyber-cyan/70 transition-all w-56 md:w-64 justify-between group shadow-sm"
        >
          <div className="flex items-center gap-2">
            <Search size={13} className="text-cyber-cyan group-hover:scale-110 transition-transform" />
            <span className="font-mono text-[11px]">COMMAND PALETTE...</span>
          </div>
          <kbd className="px-1.5 py-0.5 rounded bg-zinc-900 text-[10px] font-mono text-cyber-cyan border border-cyber-cyan/30">
            Ctrl+K
          </kbd>
        </button>

        {/* God's Eye Sensor Look Mode Switcher */}
        <div className="no-drag hidden sm:flex items-center p-0.5 rounded-lg bg-black/60 border border-cyber-cyan/30 font-mono text-[10px]">
          <span className="px-1.5 text-zinc-500 text-[9px] flex items-center gap-1">
            <Eye size={10} className="text-cyber-cyan" />
          </span>
          {sensorButtons.map((btn) => (
            <button
              key={btn.id}
              onClick={() => setMode(btn.id)}
              className={`px-2 py-0.5 rounded transition-all font-bold ${
                mode === btn.id
                  ? "bg-cyber-cyan text-black shadow-sm"
                  : "text-zinc-400 hover:text-white hover:bg-white/5"
              }`}
              title={`Switch sensor shader look to ${btn.label}`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Right: Tactical Clocks, DEFCON status & Air-Gap telemetry */}
      <div className="flex items-center gap-3 pr-32">
        {/* Tactical Clocks */}
        <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded bg-black/50 border border-white/10 font-mono text-[10px]">
          <span className="text-zinc-400">LOC</span>
          <span className="text-white font-bold">{timeLocal}</span>
          <span className="text-zinc-600">|</span>
          <span className="text-zinc-400">UTC</span>
          <span className="text-cyber-cyan font-bold">{timeUtc}</span>
        </div>

        {/* DEFCON / Threat Status Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded bg-verdigris/10 border border-verdigris/40 text-verdigris text-[10px] font-bold font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" />
          <span>DEFCON 5 // OK</span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-black/50 border border-cyber-cyan/30 text-cyber-cyan text-[11px] font-medium font-mono">
          <Server size={12} className="text-cyber-cyan" />
          <span>LOCAL</span>
        </div>

        <button
          onClick={onToggleDrawer}
          className="no-drag flex items-center gap-2 px-3 py-1 rounded-lg bg-black/60 border border-cyber-cyan/30 hover:border-cyber-cyan text-[12px] text-zinc-300 hover:text-white transition-all font-mono"
        >
          <User size={13} className="text-accent" />
          <span className="font-semibold text-white">
            {profile?.relationship_tier || "OPERATOR"}
          </span>
        </button>
      </div>
    </header>
  );
};
