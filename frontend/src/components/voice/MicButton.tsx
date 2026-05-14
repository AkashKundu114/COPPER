import { Mic, MicOff } from "lucide-react";
import { motion } from "framer-motion";

interface Props {
  isRecording: boolean;
  disabled?: boolean;
  onClick: () => void;
  size?: number;
}

export function MicButton({ isRecording, disabled, onClick, size = 18 }: Props) {
  return (
    <motion.button
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
      disabled={disabled}
      className={`p-2 rounded-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed
        ${isRecording
          ? "bg-red-500/20 text-red-400 animate-pulse"
          : "text-gray-500 hover:text-copper-400 hover:bg-copper-400/10"
        }`}
    >
      {isRecording ? <MicOff size={size} /> : <Mic size={size} />}
    </motion.button>
  );
}
