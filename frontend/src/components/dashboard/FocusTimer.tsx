import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Play, Pause, RotateCcw, Timer } from "lucide-react";

const PRESETS = [
  { label: "Focus", minutes: 25 },
  { label: "Short break", minutes: 5 },
  { label: "Long break", minutes: 15 },
];

export function FocusTimer() {
  const [total, setTotal] = useState(25 * 60);
  const [remaining, setRemaining] = useState(25 * 60);
  const [running, setRunning] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (running) {
      intervalRef.current = setInterval(() => {
        setRemaining((r) => {
          if (r <= 1) { setRunning(false); return 0; }
          return r - 1;
        });
      }, 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [running]);

  const reset = (mins?: number) => {
    setRunning(false);
    const secs = (mins ?? total / 60) * 60;
    setTotal(secs);
    setRemaining(secs);
  };

  const m = String(Math.floor(remaining / 60)).padStart(2, "0");
  const s = String(remaining % 60).padStart(2, "0");
  const progress = 1 - remaining / total;

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
      className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-4">
        <Timer size={16} className="text-purple-400" />
        <span className="text-sm font-medium text-gray-400">Focus Timer</span>
      </div>

      {/* Presets */}
      <div className="flex gap-1.5 mb-4">
        {PRESETS.map((p) => (
          <button key={p.label} onClick={() => reset(p.minutes)}
            className="flex-1 text-xs py-1 rounded-lg bg-dark-600 hover:bg-dark-500 text-gray-400 hover:text-white transition-colors">
            {p.label}
          </button>
        ))}
      </div>

      {/* Clock */}
      <div className="flex flex-col items-center gap-3">
        <div className="relative w-24 h-24">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="44" fill="none" stroke="#1a1a28" strokeWidth="8" />
            <circle cx="50" cy="50" r="44" fill="none" stroke="#a855f7" strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${progress * 276.5} 276.5`}
              style={{ transition: "stroke-dasharray 0.5s ease" }} />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl font-mono font-bold text-white">{m}:{s}</span>
          </div>
        </div>

        <div className="flex gap-2">
          <button onClick={() => setRunning((r) => !r)}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 text-sm transition-colors">
            {running ? <Pause size={14} /> : <Play size={14} />}
            {running ? "Pause" : "Start"}
          </button>
          <button onClick={() => reset()}
            className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-white/10 transition-colors">
            <RotateCcw size={14} />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
