import { motion } from "framer-motion";
import { CpuWidget } from "@/components/dashboard/CpuWidget";
import { MemoryWidget } from "@/components/dashboard/MemoryWidget";
import { FocusTimer } from "@/components/dashboard/FocusTimer";
import { ReminderWidget } from "@/components/dashboard/ReminderWidget";
import { WeatherWidget } from "@/components/dashboard/WeatherWidget";
import { AppLauncher } from "@/components/system/AppLauncher";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
};
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export default function Dashboard() {
  return (
    <motion.div variants={container} initial="hidden" animate="show"
      className="p-4 grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 auto-rows-min">

      {/* Header banner */}
      <motion.div variants={item} className="col-span-full glass rounded-xl p-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold glow-text">Good {getGreeting()},</h2>
          <p className="text-sm text-gray-500">COPPER is online and ready to assist.</p>
        </div>
        <div className="text-3xl">🤖</div>
      </motion.div>

      <motion.div variants={item}><CpuWidget /></motion.div>
      <motion.div variants={item}><MemoryWidget /></motion.div>
      <motion.div variants={item}><WeatherWidget /></motion.div>
      <motion.div variants={item}><FocusTimer /></motion.div>
      <motion.div variants={item}><ReminderWidget /></motion.div>
      <motion.div variants={item} className="sm:col-span-2 xl:col-span-1"><AppLauncher /></motion.div>
    </motion.div>
  );
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return "Morning";
  if (h < 18) return "Afternoon";
  return "Evening";
}
