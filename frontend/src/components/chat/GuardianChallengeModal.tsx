import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { ShieldAlert, AlertTriangle } from "lucide-react";
import { guardianAPI } from "@/services/api";

export interface GuardianVerdict {
  level: number; // 2 = CHALLENGE, 3 = SAFETY
  level_name: string;
  reasoning?: string;
  evidence: string[];
  confidence?: string;
  recommendation?: string;
  requires_confirmation: boolean;
}

interface Props {
  verdict: GuardianVerdict | null;
  sessionId: string;
  onResolved: (decision: "follow" | "proceed" | "discuss") => void;
  onClose: () => void;
}

export function GuardianChallengeModal({ verdict, sessionId, onResolved, onClose }: Props) {
  const [confirmText, setConfirmText] = useState("");
  if (!verdict) return null;

  const isSafety = verdict.level === 3;

  const resolve = async (decision: "follow" | "proceed" | "discuss") => {
    await guardianAPI.acknowledge(sessionId, decision);
    onResolved(decision);
  };

  const confirmSafety = async () => {
    if (confirmText.trim().toLowerCase() !== "confirm") return;
    await guardianAPI.confirmSafetyAction(sessionId, confirmText);
    onResolved("proceed");
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
          className={`glass rounded-2xl w-full max-w-lg p-6 space-y-4 border-2 ${
            isSafety ? "border-red-500/50" : "border-amber-500/40"
          }`}
        >
          <div className="flex items-center gap-2">
            {isSafety ? (
              <AlertTriangle size={18} className="text-red-400" />
            ) : (
              <ShieldAlert size={18} className="text-amber-400" />
            )}
            <h3 className="font-semibold text-white text-sm tracking-wide">
              {isSafety ? "CONFIRMATION REQUIRED" : "COPPER RECOMMENDS AGAINST THIS"}
            </h3>
          </div>

          {verdict.reasoning && (
            <p className="text-sm text-gray-300 leading-relaxed">{verdict.reasoning}</p>
          )}

          {verdict.evidence.length > 0 && (
            <div className="text-xs text-gray-400 space-y-1">
              <p className="uppercase tracking-wide text-gray-600">Evidence</p>
              {verdict.evidence.map((e, i) => (
                <p key={i}>• {e}</p>
              ))}
            </div>
          )}

          {verdict.confidence && (
            <p className="text-xs text-gray-500">Confidence: {verdict.confidence}</p>
          )}

          {verdict.recommendation && (
            <p className="text-sm text-copper-400">Recommendation: {verdict.recommendation}</p>
          )}

          {isSafety ? (
            <div className="space-y-2 pt-2">
              <p className="text-xs text-gray-500">Type "confirm" to proceed anyway.</p>
              <input
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="confirm"
                className="w-full input-copper text-sm"
              />
              <div className="flex gap-2 pt-1">
                <button onClick={confirmSafety} disabled={confirmText.trim().toLowerCase() !== "confirm"}
                  className="flex-1 py-2 rounded-lg bg-red-600/80 hover:bg-red-600 text-white text-sm disabled:opacity-40">
                  Confirm & Proceed
                </button>
                <button onClick={onClose} className="flex-1 btn-ghost text-sm">Cancel</button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-2 pt-2">
              <button onClick={() => resolve("follow")} className="btn-copper text-sm w-full">
                Follow COPPER's recommendation
              </button>
              <button onClick={() => resolve("proceed")} className="btn-ghost text-sm w-full">
                Proceed anyway
              </button>
              <button onClick={() => resolve("discuss")} className="text-xs text-gray-500 hover:text-gray-300 text-center">
                Discuss further
              </button>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
