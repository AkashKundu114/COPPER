import React from "react";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  MessageSquare,
} from "lucide-react";

export interface GuardianChallengePayload {
  level: number;
  reasoning: string;
  evidence: string[];
  confidence: string;
  recommendation: string;
}

interface GuardianChallengeModalProps {
  payload: GuardianChallengePayload | null;
  onProceedAnyway: () => void;
  onFollowRecommendation: () => void;
  onDiscuss: () => void;
}

export const GuardianChallengeModal: React.FC<GuardianChallengeModalProps> = ({
  payload,
  onProceedAnyway,
  onFollowRecommendation,
  onDiscuss,
}) => {
  if (!payload) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 select-none">
      <div className="copper-trace w-full max-w-lg bg-bg-panel border-2 border-molten/50 rounded-xl p-6 shadow-xl space-y-4">
        {}
        <div className="flex items-center gap-3 border-b border-molten/20 pb-4">
          <div className="w-10 h-10 rounded-lg bg-molten/15 border border-molten/40 flex items-center justify-center text-molten">
            <ShieldAlert size={24} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-molten uppercase tracking-wider font-mono">
              COPPER Recommends Against This
            </h3>
            <p className="text-xs text-text-muted">
              Guardian Level 2 Conflict Challenge
            </p>
          </div>
        </div>

        {}
        <div className="space-y-2 text-xs text-text-muted leading-relaxed">
          <p className="font-medium text-text">{payload.reasoning}</p>

          {payload.evidence && payload.evidence.length > 0 && (
            <div className="space-y-1 bg-bg/60 p-3 rounded-lg border border-border font-mono text-[11px]">
              <span className="text-text-muted font-semibold block mb-1">
                Evidence:
              </span>
              {payload.evidence.map((ev, i) => (
                <div key={i} className="flex items-center gap-2 text-text-muted">
                  <span className="text-molten">•</span>
                  <span>{ev}</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between text-[11px] font-mono pt-1 text-text-muted">
            <span>
              Confidence:{" "}
              <strong className="text-molten">{payload.confidence}</strong>
            </span>
          </div>

          <div className="p-3 bg-molten/10 border border-molten/30 rounded-lg text-molten-200">
            <strong className="block text-[11px] uppercase tracking-wide text-molten mb-0.5">
              Recommendation:
            </strong>
            {payload.recommendation}
          </div>
        </div>

        {}
        <div className="grid grid-cols-3 gap-2 pt-2">
          <button
            onClick={onFollowRecommendation}
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-molten hover:bg-molten-400 text-bg text-xs font-bold transition-all shadow-sm"
          >
            <CheckCircle2 size={14} />
            <span>Follow Rec</span>
          </button>

          <button
            onClick={onDiscuss}
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-bg-raised hover:bg-border text-text text-xs font-medium transition-all border border-border"
          >
            <MessageSquare size={14} />
            <span>Discuss</span>
          </button>

          <button
            onClick={onProceedAnyway}
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-danger/15 hover:bg-danger/25 text-danger-300 text-xs font-medium transition-all border border-danger/40"
          >
            <XCircle size={14} />
            <span>Proceed Anyway</span>
          </button>
        </div>
      </div>
    </div>
  );
};
