import React, { useState } from "react";
import { Server, Terminal } from "lucide-react";

export const SettingsView: React.FC = () => {
  const [devMode, setDevMode] = useState(true);

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-gray-200 select-none">
      <div>
        <h1 className="text-xl font-bold text-white tracking-tight">System Settings</h1>
        <p className="text-xs text-gray-400 font-mono">Preferences, local LLM endpoints, privacy firewall, and developer options</p>
      </div>

      <div className="space-y-4">
        {}
        <div className="p-5 rounded-xl bg-[#14141a] border border-white/10 space-y-3 font-mono text-xs">
          <div className="flex items-center gap-2 text-white font-bold">
            <Server size={16} className="text-[#ff5722]" /> Local Ollama Model Server
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-gray-400 text-[10px] block mb-1">Ollama Base URL</label>
              <input
                type="text"
                defaultValue="http://localhost:11434"
                className="w-full px-3 py-1.5 rounded bg-black/50 border border-white/10 text-white font-mono"
              />
            </div>
            <div>
              <label className="text-gray-400 text-[10px] block mb-1">Default Model Pool</label>
              <select className="w-full px-3 py-1.5 rounded bg-black/50 border border-white/10 text-white font-mono">
                <option>llama3.1:8b (General Reasoning)</option>
                <option>qwen2.5-coder:7b (Code Synthesis)</option>
                <option>mistral:7b-instruct (Fast Chat)</option>
              </select>
            </div>
          </div>
        </div>

        {}
        <div className="p-5 rounded-xl bg-[#14141a] border border-white/10 flex items-center justify-between font-mono text-xs">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-white font-bold">
              <Terminal size={16} className="text-[#ff5722]" /> Developer Mode
            </div>
            <p className="text-[11px] text-gray-400">Expose raw JSON state, prompt logs, and step execution timing.</p>
          </div>
          <button
            onClick={() => setDevMode(!devMode)}
            className={`w-12 h-6 rounded-full p-1 transition-colors ${
              devMode ? "bg-[#ff5722]" : "bg-gray-700"
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
