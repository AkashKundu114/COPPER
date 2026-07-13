import { motion } from "framer-motion";
import { ClockWidget } from "./ClockWidget";
import { CalendarWidget } from "./CalendarWidget";
import { WeatherWidget } from "./WeatherWidget";
import { NetworkWidget } from "./NetworkWidget";

interface Props {
  connected: boolean;
  agentsMet: number;
  agentsTotal: number;
}

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};
const item = {
  hidden: { opacity: 0, x: -12 },
  show: { opacity: 1, x: 0 },
};

export function WidgetRail({ connected, agentsMet, agentsTotal }: Props) {
  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      animate="show"
      className="fixed top-20 left-6 z-20 flex flex-col gap-3 pointer-events-none"
    >
      <motion.div variants={item} className="pointer-events-auto"><ClockWidget /></motion.div>
      <motion.div variants={item} className="pointer-events-auto"><CalendarWidget /></motion.div>
      <motion.div variants={item} className="pointer-events-auto"><WeatherWidget /></motion.div>
      <motion.div variants={item} className="pointer-events-auto">
        <NetworkWidget connected={connected} agentsMet={agentsMet} agentsTotal={agentsTotal} />
      </motion.div>
    </motion.div>
  );
}
