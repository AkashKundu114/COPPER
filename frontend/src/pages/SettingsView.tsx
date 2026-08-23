import React, { useState, useEffect } from "react";
import { Power, Volume2, HardDrive, CheckCircle2, Play } from "lucide-react";
import { API_BASE } from "../lib/api";

export const SettingsView: React.FC = () => {
  const [backendRunning, setBackendRunning] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState("en_US-amy-medium");
  const [isPlayingVoice, setIsPlayingVoice] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    try {
      if ((window as any).require) {
        const { ipcRenderer } = (window as any).require("electron");
        ipcRenderer.invoke("get-backend-status").then(setBackendRunning);
      } else {
        // In browser dev mode, check port 8000 via fetch
        fetch(`${API_BASE}/api/v1/system/telemetry`)
          .then((res) => setBackendRunning(res.ok))
          .catch(() => setBackendRunning(false));
      }
    } catch {
      setBackendRunning(false);
    }
  }, []);

  const toggleBackend = async () => {
    try {
      if ((window as any).require) {
        const { ipcRenderer } = (window as any).require("electron");
        if (backendRunning) {
          await ipcRenderer.invoke("stop-backend");
          setBackendRunning(false);
          setToast("Python Backend Server stopped.");
        } else {
          await ipcRenderer.invoke("start-backend");
          setBackendRunning(true);
          setToast("Python Backend Server started.");
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const testVoiceSample = async () => {
    setIsPlayingVoice(true);
    setToast("Synthesizing female voice sample with Piper ONNX...");
    try {
      const res = await fetch(`${API_BASE}/api/v1/voice/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: "Hello! I am C.O.P.P.E.R., your local offline AI operating system.",
          voice: selectedVoice
        })
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => setIsPlayingVoice(false);
        audio.play();
      } else {
        setIsPlayingVoice(false);
      }
    } catch (e) {
      console.error(e);
      setIsPlayingVoice(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight font-sans">System Settings</h1>
          <p className="text-xs text-slate-400 mt-1">Local endpoints, female voice synthesis, model storage paths, and runtime toggles</p>
        </div>
      </div>

      {toast && (
        <div className="p-3.5 rounded-xl bg-sky-950/60 border border-sky-500/40 text-sky-300 flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span>{toast}</span>
          </div>
          <button onClick={() => setToast(null)} className="text-sky-400 hover:text-white text-[11px]">
            Dismiss
          </button>
        </div>
      )}

      <div className="space-y-4">
        {/* Backend Toggle */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between shadow-sm">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-white font-bold font-sans text-sm">
              <Power size={17} className={backendRunning ? "text-sky-400" : "text-slate-500"} />
              <span>Python Backend Server (FastAPI + Uvicorn)</span>
            </div>
            <p className="text-[11px] text-slate-400">Controls the standalone backend runtime on port 8000 with WatchFiles live-reload.</p>
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

        {/* Voice Preference */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 text-white font-bold font-sans text-sm">
                <Volume2 size={17} className="text-emerald-400" />
                <span>Text-To-Speech (TTS) Voice Engine</span>
              </div>
              <p className="text-[11px] text-slate-400">High-fidelity local neural voice synthesis powered by Piper ONNX.</p>
            </div>
            <button
              onClick={testVoiceSample}
              disabled={isPlayingVoice}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 font-bold transition-all disabled:opacity-40"
            >
              <Play size={13} />
              <span>{isPlayingVoice ? "Playing Voice..." : "Test Voice"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: "en_US-amy-medium", name: "Amy (Female - Default)", tag: "Natural & Clear" },
              { id: "en_US-lessac-medium", name: "Lessac (Female)", tag: "Warm & Expressive" },
              { id: "en_US-danny-low", name: "Danny (Male)", tag: "Deep & Calm" }
            ].map((v) => (
              <button
                key={v.id}
                onClick={() => {
                  setSelectedVoice(v.id);
                  setToast(`Default voice set to ${v.name}`);
                }}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  selectedVoice === v.id
                    ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/50 shadow-sm"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                <p className="font-bold text-white font-sans text-xs">{v.name}</p>
                <p className="text-[10px] text-slate-500 mt-1">{v.tag}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Model Storage Directory */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 shadow-sm">
          <div className="flex items-center gap-2 text-white font-bold font-sans text-sm">
            <HardDrive size={17} className="text-sky-400" />
            <span>Local Weights & Storage Paths</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 text-[10px] uppercase font-bold">Ollama Model Blobs</span>
              <p className="text-white text-xs font-mono mt-0.5">D:\blobs</p>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 text-[10px] uppercase font-bold">Local App & Vectors</span>
              <p className="text-white text-xs font-mono mt-0.5">D:\C.O.P.P.E.R</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
