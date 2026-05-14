import { useLocation } from "react-router-dom";
import { Wifi, WifiOff } from "lucide-react";
import { useSettingsStore } from "@/store/settingsStore";

const PAGE_TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/chat": "Chat",
  "/memory": "Memory",
  "/reminders": "Reminders",
  "/automation": "Automation",
  "/settings": "Settings",
};

export function Navbar() {
  const { pathname } = useLocation();
  const { provider } = useSettingsStore();
  const title = PAGE_TITLES[pathname] || "COPPER";

  return (
    <header className="h-12 flex items-center justify-between px-4 border-b border-white/5 bg-dark-800/50 backdrop-blur-sm">
      <h1 className="text-sm font-semibold text-gray-300">{title}</h1>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
          <span className="capitalize">{provider}</span>
        </div>
        <div className="text-xs text-gray-600 font-mono">
          {new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </div>
      </div>
    </header>
  );
}
