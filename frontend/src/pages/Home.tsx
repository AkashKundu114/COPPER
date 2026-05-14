import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Cpu } from "lucide-react";

export default function Home() {
  const navigate = useNavigate();
  useEffect(() => {
    const t = setTimeout(() => navigate("/dashboard"), 2000);
    return () => clearTimeout(t);
  }, [navigate]);

  return (
    <div className="h-full flex flex-col items-center justify-center bg-grid-dark bg-grid">
      <motion.div
        initial={{ scale: 0.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", damping: 15 }}
        className="flex flex-col items-center gap-6"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
          className="w-20 h-20 rounded-2xl bg-copper-600 flex items-center justify-center"
          style={{ boxShadow: "0 0 60px rgba(255,124,31,0.5)" }}
        >
          <Cpu size={40} className="text-white" />
        </motion.div>
        <div className="text-center">
          <h1 className="text-4xl font-bold glow-text">COPPER</h1>
          <p className="text-gray-500 text-sm mt-2">Centralized Omnifunctional Personal Productivity and Execution Routine</p>
        </div>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}>
          <div className="flex gap-1">
            {["Initializing", "AI", "Engine"].map((word, i) => (
              <motion.span key={word} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                transition={{ delay: 1 + i * 0.2 }} className="text-xs text-gray-600">
                {word}{i < 2 ? " ·" : ""}
              </motion.span>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
