import React, { useState, useEffect } from "react";
import { Server, Terminal, Power } from "lucide-react";

export const SettingsView: React.FC = () => {
  const [devMode, setDevMode] = useState(true);
  const [backendRunning, setBackendRunning] = useState(false);

  useEffect(() => {
    try {
      if ((window as any).require) {
        const { ipcRenderer } = (window as any).require("electron");
        ipcRenderer.invoke("get-backend-status").then(setBackendRunning);
      }
    } catch (e) {
      console.warn("Not in Electron environment");
    }
  }, []);

  const toggleBackend = async () => {
    try {
      if ((window as any).require) {
        const { ipcRenderer } = (window as any).require("electron");
        if (backendRunning) {
          await ipcRenderer.invoke("stop-backend");
          setBackendRunning(false);
        } else {
          await ipcRenderer.invoke("start-backend");
          setBackendRunning(true);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">System Settings</h1>
        <p className="text-xs text-slate-400 font-mono">Preferences, local LLM endpoints, privacy firewall, and developer options</p>
      </div>

      <div className="space-y-4">
        {}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between font-mono text-xs">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-white font-bold">
              <Power size={16} className={backendRunning ? "text-sky-500" : "text-slate-500"} /> Python Backend Server
            </div>
            <p className="text-[11px] text-slate-400">Controls the standalone backend process for chat and orchestration.</p>
          </div>
          <button
            onClick={toggleBackend}
            className={`w-12 h-6 rounded-full p-1 transition-colors ${
              backendRunning ? "bg-sky-500" : "bg-slate-700"
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-white transition-transform ${
                backendRunning ? "translate-x-6" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3 font-mono text-xs">
          <div className="flex items-center gap-2 text-white font-bold">
            <Server size={16} className="text-teal-500" /> Local Ollama Model Server
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-slate-400 text-[10px] block mb-1">Ollama Base URL</label>
              <input
                type="text"
                defaultValue="http://localhost:11434"
                className="w-full px-3 py-1.5 rounded bg-slate-950 border border-slate-800 text-white font-mono"
              />
            </div>
            <div>
              <label className="text-slate-400 text-[10px] block mb-1">Default Model Pool</label>
              <select className="w-full px-3 py-1.5 rounded bg-slate-950 border border-slate-800 text-white font-mono">
                <option>llama3.1:8b (General Reasoning)</option>
                <option>qwen2.5-coder:7b (Code Synthesis)</option>
                <option>mistral:7b-instruct (Fast Chat)</option>
              </select>
            </div>
          </div>
        </div>

        {}
        <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between font-mono text-xs">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-white font-bold">
              <Terminal size={16} className="text-sky-500" /> Developer Mode
            </div>
            <p className="text-[11px] text-slate-400">Expose raw JSON state, prompt logs, and step execution timing.</p>
          </div>
          <button
            onClick={() => setDevMode(!devMode)}
            className={`w-12 h-6 rounded-full p-1 transition-colors ${
              devMode ? "bg-sky-500" : "bg-slate-700"
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-white transition-transform ${
                devMode ? "translate-x-6" : "translate-x-0"
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  );
};
