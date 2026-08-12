import React from "react";
import { ShieldAlert, CheckCircle2, XCircle, MessageSquare } from "lucide-react";

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
      <div className="w-full max-w-lg bg-[#0d0d11] border-2 border-amber-500/60 rounded-xl p-6 shadow-2xl space-y-4">
        {}
        <div className="flex items-center gap-3 border-b border-amber-500/20 pb-4">
          <div className="w-10 h-10 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
            <ShieldAlert size={24} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider font-mono">
              COPPER Recommends Against This
            </h3>
            <p className="text-xs text-gray-400">Guardian Level 2 Conflict Challenge</p>
          </div>
        </div>

        {}
        <div className="space-y-2 text-xs text-gray-300 leading-relaxed">
          <p className="font-medium text-white">{payload.reasoning}</p>
          
          {payload.evidence && payload.evidence.length > 0 && (
            <div className="space-y-1 bg-white/5 p-3 rounded-lg border border-white/5 font-mono text-[11px]">
              <span className="text-gray-400 font-semibold block mb-1">Evidence:</span>
              {payload.evidence.map((ev, i) => (
                <div key={i} className="flex items-center gap-2 text-gray-300">
                  <span className="text-amber-400">•</span>
                  <span>{ev}</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between text-[11px] font-mono pt-1 text-gray-400">
            <span>Confidence: <strong className="text-amber-400">{payload.confidence}</strong></span>
          </div>

          <div className="p-3 bg-amber-950/30 border border-amber-500/30 rounded-lg text-amber-200">
            <strong className="block text-[11px] uppercase tracking-wide text-amber-400 mb-0.5">Recommendation:</strong>
            {payload.recommendation}
          </div>
        </div>

        {}
        <div className="grid grid-cols-3 gap-2 pt-2">
          <button
            onClick={onFollowRecommendation}
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-black text-xs font-bold transition-all shadow-md"
          >
            <CheckCircle2 size={14} />
            <span>Follow Rec</span>
          </button>

          <button
            onClick={onDiscuss}
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-medium transition-all border border-white/10"
          >
            <MessageSquare size={14} />
            <span>Discuss</span>
          </button>

          <button
            onClick={onProceedAnyway}
            className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-red-950/60 hover:bg-red-900/80 text-red-300 text-xs font-medium transition-all border border-red-500/40"
          >
            <XCircle size={14} />
            <span>Proceed Anyway</span>
          </button>
        </div>
      </div>
    </div>
  );
};
