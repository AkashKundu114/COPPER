import { motion } from "framer-motion";

interface Props {
  isActive: boolean;
  bars?: number;
}

export function VoiceVisualizer({ isActive, bars = 7 }: Props) {
  return (
    <div className="flex items-center justify-center gap-1 h-10">
      {Array.from({ length: bars }).map((_, i) => (
        <motion.div
          key={i}
          className="w-1 rounded-full bg-copper-500"
          animate={
            isActive
              ? { scaleY: [0.3, 1, 0.3], opacity: [0.5, 1, 0.5] }
              : { scaleY: 0.2, opacity: 0.3 }
          }
          transition={
            isActive
              ? { duration: 0.8 + Math.random() * 0.4, repeat: Infinity, delay: i * 0.08, ease: "easeInOut" }
              : { duration: 0.3 }
          }
          style={{ height: 32 }}
        />
      ))}
    </div>
  );
}
