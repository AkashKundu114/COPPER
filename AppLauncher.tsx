import { useState } from "react";
import { motion } from "framer-motion";
import { Grid, ExternalLink, Terminal, Globe, Code, Folder } from "lucide-react";
import { automationAPI } from "@/services/api";

const QUICK_APPS = [
  { name: "Terminal", icon: Terminal, app: "terminal", color: "text-green-400" },
  { name: "Browser", icon: Globe, app: "browser", color: "text-blue-400" },
  { name: "Editor", icon: Code, app: "editor", color: "text-purple-400" },
  { name: "Files", icon: Folder, app: "file_manager", color: "text-yellow-400" },
];

export function AppLauncher() {
  const [launching, setLaunching] = useState<string | null>(null);
  const [custom, setCustom] = useState("");

  const launch = async (app: string) => {
    setLaunching(app);
    await automationAPI.launchApp(app);
    setTimeout(() => setLaunching(null), 1500);
  };

  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-4">
        <Grid size={16} className="text-copper-400" />
        <span className="text-sm font-medium text-gray-400">App Launcher</span>
      </div>

      <div className="grid grid-cols-4 gap-2 mb-4">
        {QUICK_APPS.map(({ name, icon: Icon, app, color }) => (
          <motion.button
            key={app}
            whileTap={{ scale: 0.92 }}
            onClick={() => launch(app)}
            disabled={launching === app}
            className="flex flex-col items-center gap-1.5 p-3 rounded-xl bg-dark-700 hover:bg-dark-600 transition-colors disabled:opacity-60"
          >
            <Icon size={20} className={color} />
            <span className="text-xs text-gray-400">{name}</span>
          </motion.button>
        ))}
      </div>

      <div className="flex gap-2">
        <input
          value={custom}
          onChange={(e) => setCustom(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && custom && launch(custom)}
          placeholder="App name or path..."
          className="flex-1 input-copper text-sm py-1.5"
        />
        <button
          onClick={() => custom && launch(custom)}
          className="px-3 py-1.5 rounded-lg bg-copper-600/20 hover:bg-copper-600/40 text-copper-400 text-sm transition-colors"
        >
          <ExternalLink size={16} />
        </button>
      </div>
    </div>
  );
}
