import { useState } from "react";
import { motion } from "framer-motion";
import { Zap, Terminal, FolderOpen, Monitor, Play } from "lucide-react";
import { automationAPI } from "@/services/api";

type Tab = "terminal" | "files" | "system";

export default function Automation() {
  const [tab, setTab] = useState<Tab>("terminal");
  const [cmd, setCmd] = useState("");
  const [output, setOutput] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [dirPath, setDirPath] = useState("~");
  const [files, setFiles] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);

  const runCommand = async () => {
    if (!cmd.trim()) return;
    setRunning(true);
    try {
      const { data } = await automationAPI.runCommand(cmd);
      setOutput(data);
    } catch (e: any) {
      setOutput({ stdout: "", stderr: e.message, success: false });
    } finally { setRunning(false); }
  };

  const browseDir = async () => {
    const { data } = await automationAPI.browseDirectory(dirPath);
    setFiles(data);
  };

  const loadStats = async () => {
    const { data } = await automationAPI.getStats();
    setStats(data);
  };

  const TABS: { id: Tab; icon: any; label: string }[] = [
    { id: "terminal", icon: Terminal, label: "Terminal" },
    { id: "files", icon: FolderOpen, label: "Files" },
    { id: "system", icon: Monitor, label: "System" },
  ];

  return (
    <div className="p-4 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center gap-2">
        <Zap size={20} className="text-yellow-400" />
        <h2 className="font-semibold text-white">Automation</h2>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 glass rounded-xl">
        {TABS.map(({ id, icon: Icon, label }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm transition-all
              ${tab === id ? "bg-copper-600/30 text-copper-300" : "text-gray-500 hover:text-gray-300"}`}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* Terminal */}
      {tab === "terminal" && (
        <div className="space-y-3">
          <div className="flex gap-2">
            <input value={cmd} onChange={(e) => setCmd(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runCommand()}
              placeholder="Enter shell command..."
              className="flex-1 input-copper text-sm font-mono" />
            <button onClick={runCommand} disabled={running || !cmd.trim()}
              className="px-4 py-2 rounded-lg bg-green-600/20 hover:bg-green-600/40 text-green-400 transition-colors disabled:opacity-40">
              <Play size={16} />
            </button>
          </div>
          {output && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              className="glass rounded-xl p-4 font-mono text-sm space-y-2">
              <div className={`text-xs px-2 py-1 rounded inline-block ${output.success ? "bg-green-600/20 text-green-400" : "bg-red-600/20 text-red-400"}`}>
                exit {output.returncode}
              </div>
              {output.stdout && <pre className="text-gray-300 whitespace-pre-wrap break-all">{output.stdout}</pre>}
              {output.stderr && <pre className="text-red-400 whitespace-pre-wrap break-all">{output.stderr}</pre>}
            </motion.div>
          )}
        </div>
      )}

      {/* Files */}
      {tab === "files" && (
        <div className="space-y-3">
          <div className="flex gap-2">
            <input value={dirPath} onChange={(e) => setDirPath(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && browseDir()}
              placeholder="Directory path" className="flex-1 input-copper text-sm font-mono" />
            <button onClick={browseDir}
              className="px-4 py-2 rounded-lg bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 transition-colors">
              Browse
            </button>
          </div>
          <div className="space-y-1">
            {files.map((f, i) => (
              <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className="flex items-center gap-3 px-3 py-2 rounded-lg glass hover:bg-white/5 transition-colors">
                <span className="text-lg">{f.is_dir ? "📁" : "📄"}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200 truncate">{f.name}</p>
                  {!f.is_dir && <p className="text-xs text-gray-600">{f.size_bytes} B</p>}
                </div>
              </motion.div>
            ))}
            {files.length === 0 && <p className="text-xs text-gray-600 text-center py-6">No files loaded</p>}
          </div>
        </div>
      )}

      {/* System */}
      {tab === "system" && (
        <div className="space-y-3">
          <button onClick={loadStats}
            className="btn-ghost text-sm w-full">Load System Info</button>
          {stats && (
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "CPU", value: `${stats.cpu_percent?.toFixed(1)}%`, color: "text-copper-400" },
                { label: "Memory", value: `${stats.memory_percent?.toFixed(1)}%`, color: "text-cyan-400" },
                { label: "Disk", value: `${stats.disk_percent?.toFixed(1)}%`, color: "text-yellow-400" },
                { label: "OS", value: stats.os, color: "text-purple-400" },
              ].map(({ label, value, color }) => (
                <div key={label} className="glass rounded-xl p-3">
                  <p className="text-xs text-gray-500 mb-1">{label}</p>
                  <p className={`text-lg font-bold ${color}`}>{value}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
