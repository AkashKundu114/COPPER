import React, { useEffect, useState } from "react";
import { Brain, Zap, Coffee, AlertTriangle, ShieldAlert } from "lucide-react";
import { cognitiveAPI } from "../../services/api";

interface CognitiveProfile {
  state: "deep_focus" | "normal_flow" | "context_switching" | "stressed" | "idle";
  confidence: number;
  window_switch_rate: number;
  avg_session_duration: number;
  current_focus_streak: number;
  recommendations: string[];
}

export const CognitiveStatusBadge: React.FC = () => {
  const [profile, setProfile] = useState<CognitiveProfile | null>(null);

  const fetchStatus = () => {
    cognitiveAPI
      .getState()
      .then((res: any) => {
        if (res.data) {
          setProfile(res.data);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);


  if (!profile) return null;

  const stateConfig = {
    deep_focus: {
      label: "DEEP FOCUS",
      color: "text-purple-400 bg-purple-950/60 border-purple-800/40 shadow-purple-900/30",
      icon: Zap,
    },
    normal_flow: {
      label: "FLOW",
      color: "text-verdigris bg-verdigris/10 border-verdigris/30",
      icon: Brain,
    },
    context_switching: {
      label: "SWITCHING",
      color: "text-amber-400 bg-amber-950/60 border-amber-800/40",
      icon: Coffee,
    },
    stressed: {
      label: "HIGG LOAD",
      color: "text-danger-400 bg-danger-950/60 border-danger-800/40",
      icon: AlertTriangle,
    },
    idle: {
      label: "IDLE",
      color: "text-zinc-400 bg-zinc-900/60 border-zinc-800",
      icon: Brain,
    },
  };

  const current = stateConfig[profile.state] || stateConfig.normal_flow;
  const IconComponent = current.icon;

  return (
    <div
      className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-xl border text-[10px] font-mono font-bold tracking-wider transition-all shadow-sm ${current.color}`}
      title={`Cognitive Load: ${current.label} (${Math.round(profile.confidence * 100)}% conf). Switches/min: ${profile.window_switch_rate.toFixed(1)}. Focus Streak: ${profile.current_focus_streak.toFixed(1)}m.`}
    >
      <IconComponent size={12} className="animate-pulse" />
      <span>{current.label}</span>
      {profile.state === "deep_focus" && (
        <span className="flex items-center gap-0.5 text-[9px] text-purple-300 font-normal">
          <ShieldAlert size={9} />
          Muted
        </span>
      )}
    </div>
  );
};
