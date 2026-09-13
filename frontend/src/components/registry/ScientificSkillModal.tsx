import React, { useState } from "react";
import { X, Copy, Check, BookOpen, Compass, FileText } from "lucide-react";
import type { ScientificSkill } from "../../services/api";

interface ScientificSkillModalProps {
  skill: ScientificSkill | null;
  onClose: () => void;
  onAttachToResearch?: (skill: ScientificSkill) => void;
}

export const ScientificSkillModal: React.FC<ScientificSkillModalProps> = ({
  skill,
  onClose,
  onAttachToResearch,
}) => {
  const [copied, setCopied] = useState(false);

  if (!skill) return null;

  const handleCopyInstructions = () => {
    const text = skill.instructions || skill.instruction_preview || skill.description;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl border bg-emerald-950/40 border-emerald-500/40 text-emerald-400">
              <BookOpen size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-tight font-sans">
                  {skill.name}
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold bg-emerald-950/50 text-emerald-300 border border-emerald-800/40">
                  {skill.category}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                Path: {skill.path || "builtin/skills"}
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

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs">
          {/* Discipline Mandate */}
          <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 space-y-2">
            <div className="flex items-center gap-2 text-slate-400 uppercase text-[10px] font-semibold tracking-wider font-mono">
              <Compass size={12} className="text-emerald-400" />
              <span>Scientific Domain Scope</span>
            </div>
            <p className="text-slate-200 leading-relaxed font-sans text-sm">
              {skill.description}
            </p>
          </div>

          {/* Protocols & Instructions */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 font-mono uppercase text-[10px] font-semibold tracking-wider flex items-center gap-1.5">
                <FileText size={12} className="text-cyan-400" />
                Operational Execution Guidelines
              </span>
              <button
                onClick={handleCopyInstructions}
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
                    <span>Copy Instructions</span>
                  </>
                )}
              </button>
            </div>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap select-text">
              {skill.instructions || skill.instruction_preview || "Scientific skill loaded and ready for query execution."}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/50 flex items-center justify-between gap-3">
          <div className="text-[11px] text-slate-500 font-mono">
            Scientific Protocol Engine: 1 of 165 Verified Disciplines
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition-all"
            >
              Close
            </button>
            {onAttachToResearch && (
              <button
                onClick={() => {
                  onAttachToResearch(skill);
                  onClose();
                }}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-lg shadow-emerald-600/20"
              >
                <BookOpen size={14} />
                <span>Attach to Research</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
