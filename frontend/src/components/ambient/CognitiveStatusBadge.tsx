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
      label: "HIGH LOAD",
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
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-xl border text-[10px] font-mono font-bold tracking-wider transition-all shadow-sm cursor-pointer hover:opacity-90 ${current.color}`}
        title={`Cognitive Load: ${current.label} (${Math.round(profile.confidence * 100)}% conf). Click to inspect.`}
      >
        <IconComponent size={12} className="animate-pulse" />
        <span>{current.label}</span>
        {profile.state === "deep_focus" && (
          <span className="flex items-center gap-0.5 text-[9px] text-purple-300 font-normal">
            <ShieldAlert size={9} />
            Muted
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-10 w-72 p-3.5 rounded-2xl bg-slate-950/95 backdrop-blur-xl border border-slate-800 shadow-2xl z-50 font-mono text-xs space-y-3 animate-fade-in">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <IconComponent size={14} className="text-white" />
              <span className="font-bold text-white text-xs font-sans">Cognitive Load State</span>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-slate-500 hover:text-white text-[10px]"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/60">
              <span className="text-slate-400 block">Switch Rate</span>
              <span className="text-white font-bold">{profile.window_switch_rate.toFixed(1)}/min</span>
            </div>
            <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800/60">
              <span className="text-slate-400 block">Focus Streak</span>
              <span className="text-accent-400 font-bold">{profile.current_focus_streak.toFixed(1)} mins</span>
            </div>
          </div>

          {profile.recommendations && profile.recommendations.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">
                Autonomous Recommendations
              </span>
              <div className="space-y-1">
                {profile.recommendations.map((rec, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-[10px] text-slate-300">
                    <span className="text-accent-400 mt-0.5">•</span>
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
