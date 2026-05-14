import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader } from "lucide-react";

interface Props {
  isRecording: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  onToggle: () => void;
}

export function VoiceOrb({ isRecording, isProcessing, isSpeaking, onToggle }: Props) {
  const active = isRecording || isSpeaking;

  return (
    <div className="relative flex items-center justify-center">
      {/* Outer ring pulses */}
      <AnimatePresence>
        {active && (
          <>
            {[1, 2, 3].map((i) => (
              <motion.div
                key={i}
                className="absolute rounded-full border border-copper-500/30"
                initial={{ width: 64, height: 64, opacity: 0.8 }}
                animate={{ width: 64 + i * 30, height: 64 + i * 30, opacity: 0 }}
                transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.3, ease: "easeOut" }}
              />
            ))}
          </>
        )}
      </AnimatePresence>

      {/* Core button */}
      <motion.button
        whileTap={{ scale: 0.92 }}
        whileHover={{ scale: 1.05 }}
        onClick={onToggle}
        disabled={isProcessing}
        className={`relative z-10 w-16 h-16 rounded-full flex items-center justify-center transition-all
          ${isRecording
            ? "bg-red-600 shadow-[0_0_30px_rgba(239,68,68,0.5)]"
            : isSpeaking
            ? "bg-blue-600 shadow-[0_0_30px_rgba(59,130,246,0.5)]"
            : "bg-copper-600 shadow-[0_0_20px_rgba(255,124,31,0.4)] hover:shadow-[0_0_35px_rgba(255,124,31,0.6)]"
          }`}
      >
        <AnimatePresence mode="wait">
          {isProcessing ? (
            <motion.div key="loader" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Loader size={24} className="text-white animate-spin" />
            </motion.div>
          ) : isRecording ? (
            <motion.div key="stop" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
              <MicOff size={24} className="text-white" />
            </motion.div>
          ) : (
            <motion.div key="mic" initial={{ scale: 0 }} animate={{ scale: 1 }} exit={{ scale: 0 }}>
              <Mic size={24} className="text-white" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>
    </div>
  );
}
