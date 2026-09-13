import React, { useState } from "react";
import { X, Copy, Check, Sparkles, Shield, Terminal, UserCheck } from "lucide-react";
import type { AgencyPersona } from "../../services/api";

interface PersonaDossierModalProps {
  persona: AgencyPersona | null;
  onClose: () => void;
  onActivate?: (persona: AgencyPersona) => void;
}

export const PersonaDossierModal: React.FC<PersonaDossierModalProps> = ({
  persona,
  onClose,
  onActivate,
}) => {
  const [copied, setCopied] = useState(false);

  if (!persona) return null;

  const handleCopyPrompt = () => {
    const promptText = persona.system_prompt || persona.description;
    navigator.clipboard.writeText(promptText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getDivisionColor = (division: string) => {
    switch (division.toLowerCase()) {
      case "engineering":
        return { text: "text-cyan-400", border: "border-cyan-500/40", bg: "bg-cyan-950/40" };
      case "security":
        return { text: "text-rose-400", border: "border-rose-500/40", bg: "bg-rose-950/40" };
      case "gis":
        return { text: "text-emerald-400", border: "border-emerald-500/40", bg: "bg-emerald-950/40" };
      case "finance":
        return { text: "text-amber-400", border: "border-amber-500/40", bg: "bg-amber-950/40" };
      case "design":
        return { text: "text-fuchsia-400", border: "border-fuchsia-500/40", bg: "bg-fuchsia-950/40" };
      case "academic":
        return { text: "text-violet-400", border: "border-violet-500/40", bg: "bg-violet-950/40" };
      case "marketing":
        return { text: "text-orange-400", border: "border-orange-500/40", bg: "bg-orange-950/40" };
      case "operations":
        return { text: "text-sky-400", border: "border-sky-500/40", bg: "bg-sky-950/40" };
      case "health":
        return { text: "text-teal-400", border: "border-teal-500/40", bg: "bg-teal-950/40" };
      default:
        return { text: "text-indigo-400", border: "border-indigo-500/40", bg: "bg-indigo-950/40" };
    }
  };

  const colors = getDivisionColor(persona.division);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-xl border ${colors.bg} ${colors.border} ${colors.text}`}>
              <Sparkles size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-tight font-sans">
                  {persona.name}
                </h2>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold ${colors.bg} ${colors.text} border ${colors.border}`}
                >
                  {persona.division_label || persona.division}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                ID: {persona.id}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs">
          {/* Mission & Role */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-slate-400 uppercase text-[10px] font-semibold tracking-wider font-mono">
              <Shield size={12} className="text-cyan-400" />
              <span>Specialist Mandate & Role</span>
            </div>
            <p className="text-slate-200 leading-relaxed font-sans text-sm">
              {persona.description || persona.role}
            </p>
          </div>

          {/* Persona Vibe & Tone */}
          {persona.vibe && (
            <div className="bg-slate-950/40 p-3 rounded-xl border border-slate-800/60 flex items-center justify-between">
              <span className="text-slate-400 font-mono text-[11px]">Operational Persona & Vibe:</span>
              <span className="text-cyan-300 font-mono font-medium text-[11px] bg-cyan-950/50 px-2.5 py-1 rounded-lg border border-cyan-800/40">
                "{persona.vibe}"
              </span>
            </div>
          )}

          {/* Directive / System Prompt Directive */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 font-mono uppercase text-[10px] font-semibold tracking-wider flex items-center gap-1.5">
                <Terminal size={12} className="text-amber-400" />
                Autonomous System Prompt Directive
              </span>
              <button
                onClick={handleCopyPrompt}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] transition-all font-mono"
              >
                {copied ? (
                  <>
                    <Check size={12} className="text-emerald-400" />
                    <span className="text-emerald-400 font-bold">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={12} />
                    <span>Copy Directive</span>
                  </>
                )}
              </button>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap select-text">
              {persona.system_prompt || persona.system_prompt_preview || persona.description}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/50 flex items-center justify-between gap-3">
          <div className="text-[11px] text-slate-500 font-mono">
            Autonomous Specialist Fleet: 1 of 264 Verified Personas
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition-all"
            >
              Close
            </button>
            {onActivate && (
              <button
                onClick={() => {
                  onActivate(persona);
                  onClose();
                }}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition-all shadow-lg shadow-cyan-600/20"
              >
                <UserCheck size={14} />
                <span>Inject into Chat</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
