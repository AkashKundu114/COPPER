import { NavLink } from "react-router-dom";
import { motion } from "framer-motion";
import {
  LayoutDashboard, MessageSquare, Brain, Bell, Settings,
  Cpu, Eye, Zap,
} from "lucide-react";

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/chat", icon: MessageSquare, label: "Chat" },
  { to: "/memory", icon: Brain, label: "Memory" },
  { to: "/reminders", icon: Bell, label: "Reminders" },
  { to: "/automation", icon: Zap, label: "Automation" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  return (
    <motion.aside
      initial={{ x: -60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-16 lg:w-56 h-full flex flex-col bg-dark-800 border-r border-white/5"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-white/5">
        <div className="w-8 h-8 rounded-lg bg-copper-600 flex items-center justify-center flex-shrink-0">
          <Cpu size={16} className="text-white" />
        </div>
        <span className="hidden lg:block font-bold text-copper-400 tracking-wider text-lg">COPPER</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group ${
                isActive
                  ? "bg-copper-600/20 text-copper-400 border border-copper-600/30"
                  : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
              }`
            }
          >
            <Icon size={18} className="flex-shrink-0" />
            <span className="hidden lg:block text-sm font-medium">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Status */}
      <div className="px-3 py-4 border-t border-white/5">
        <div className="hidden lg:flex items-center gap-2 text-xs text-gray-600">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
          <span>System Online</span>
        </div>
      </div>
    </motion.aside>
  );
}
