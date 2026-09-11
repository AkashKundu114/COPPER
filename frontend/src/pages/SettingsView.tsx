import React, { useState, useEffect } from "react";
import { Power, Volume2, HardDrive, CheckCircle2, Play, Mic, Sparkles } from "lucide-react";
import { API_BASE } from "../lib/api";
import { personalityAPI } from "../services/api";

export const SettingsView: React.FC = () => {
  const [backendRunning, setBackendRunning] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState(
    () => localStorage.getItem("copper_selected_voice") || "en-US-AvaNeural"
  );
  const [isPlayingVoice, setIsPlayingVoice] = useState(false);
  const [continuousVoice, setContinuousVoice] = useState(
    () => localStorage.getItem("copper_continuous_voice") === "true"
  );
  const [toast, setToast] = useState<string | null>(null);

  // Personality & Communication Style Adaptation State
  const [personality, setPersonality] = useState({
    warmth: 0.7,
    formality: 0.4,
    verbosity: 0.5,
    humor: 0.3,
    use_emojis: true,
    code_first: true,
  });

  useEffect(() => {
    personalityAPI
      .getConfig()
      .then((res: any) => {
        if (res.data) setPersonality(res.data);
      })
      .catch(() => {});
  }, []);

  const handleUpdatePersonality = async (key: string, value: any) => {
    const updated = { ...personality, [key]: value };
    setPersonality(updated);
    try {
      await personalityAPI.updateConfig(updated);
      setToast(`Personality parameter '${key}' updated.`);
    } catch {
      setToast("Failed to save personality setting.");
    }
  };

  useEffect(() => {
    let active = true;
    const checkStatus = async () => {
      try {
        if ((window as any).require) {
          const { ipcRenderer } = (window as any).require("electron");
          const running = await ipcRenderer.invoke("get-backend-status");
          if (active) setBackendRunning(running);
        } else {
          const res = await fetch(`${API_BASE}/api/v1/system/telemetry`);
          if (active) setBackendRunning(res.ok);
        }
      } catch {
        if (active) setBackendRunning(false);
      }
    };
    checkStatus();
    return () => {
      active = false;
    };
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
          voice: selectedVoice,
        }),
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
    <div className="modern-page p-6 space-y-6 max-w-6xl mx-auto text-slate-200 select-none font-mono text-xs">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight font-sans">
            System Settings
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Local endpoints, female voice synthesis, model storage paths, and
            runtime toggles
          </p>
        </div>
      </div>

      {toast && (
        <div className="p-3.5 rounded-xl bg-accent-950/60 border border-accent-500/40 text-accent-300 flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} />
            <span>{toast}</span>
          </div>
          <button
            onClick={() => setToast(null)}
            className="text-accent-400 hover:text-white text-[11px]"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="space-y-4">
        {/* Backend Toggle */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between shadow-sm">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-white font-bold font-sans text-sm">
              <Power
                size={17}
                className={backendRunning ? "text-accent-400" : "text-slate-500"}
              />
              <span>Python Backend Server (FastAPI + Uvicorn)</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Controls the standalone backend runtime on port 8000 with
              WatchFiles live-reload.
            </p>
          </div>
          <button
            onClick={toggleBackend}
            className={`w-12 h-6 rounded-full p-1 transition-colors ${
              backendRunning ? "bg-accent-500" : "bg-slate-700"
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-white transition-transform ${
                backendRunning ? "translate-x-6" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {/* Continuous Voice Toggle */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center justify-between shadow-sm">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-white font-bold font-sans text-sm">
              <Mic size={17} className={continuousVoice ? "text-purple-400" : "text-slate-500"} />
              <span>E.V.E. Hands-Free Mode (Continuous Voice)</span>
            </div>
            <p className="text-[11px] text-slate-400">
              Voice assistant listens continuously without needing to press the mic button. Interrupt E.V.E. by speaking.
            </p>
          </div>
          <button
            onClick={() => {
              const newVal = !continuousVoice;
              setContinuousVoice(newVal);
              localStorage.setItem("copper_continuous_voice", String(newVal));
              setToast(newVal ? "Hands-Free Mode Enabled" : "Hands-Free Mode Disabled");
            }}
            className={`w-12 h-6 rounded-full p-1 transition-colors ${
              continuousVoice ? "bg-purple-500" : "bg-slate-700"
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full bg-white transition-transform ${
                continuousVoice ? "translate-x-6" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {/* Voice Preference */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 text-white font-bold font-sans text-sm">
                <Volume2 size={17} className="text-verdigris-400" />
                <span>Text-To-Speech (TTS) Voice Engine</span>
              </div>
              <p className="text-[11px] text-slate-400">
                High-fidelity local neural voice synthesis powered by Piper
                ONNX.
              </p>
            </div>
            <button
              onClick={testVoiceSample}
              disabled={isPlayingVoice}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-verdigris-500/20 hover:bg-verdigris-500/30 text-verdigris-400 border border-verdigris-500/40 font-bold transition-all disabled:opacity-40"
            >
              <Play size={13} />
              <span>{isPlayingVoice ? "Playing Voice..." : "Test Voice"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              {
                id: "en-US-AvaNeural",
                name: "Ava (Neural Female)",
                tag: "Ultra Realistic & Fluent",
              },
              {
                id: "en-US-JennyNeural",
                name: "Jenny (Neural Female)",
                tag: "Warm & Expressive",
              },
              {
                id: "zira",
                name: "Zira (Windows Native)",
                tag: "100% Offline Native",
              },
              {
                id: "david",
                name: "David (Windows Native)",
                tag: "100% Offline Native Male",
              },
            ].map((v) => (
              <button
                key={v.id}
                onClick={() => {
                  setSelectedVoice(v.id);
                  localStorage.setItem("copper_selected_voice", v.id);
                  setToast(`Voice set to ${v.name}`);
                }}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  selectedVoice === v.id
                    ? "bg-verdigris-500/15 text-verdigris-400 border-verdigris-500/50 shadow-sm"
                    : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                <p className="font-bold text-white font-sans text-xs">
                  {v.name}
                </p>
                <p className="text-[10px] text-slate-500 mt-1">{v.tag}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Model Storage Directory */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3 shadow-sm">
          <div className="flex items-center gap-2 text-white font-bold font-sans text-sm">
            <HardDrive size={17} className="text-accent-400" />
            <span>Local Weights & Storage Paths</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 text-[10px] uppercase font-bold">
                Ollama Model Blobs
              </span>
              <p className="text-white text-xs font-mono mt-0.5">D:\blobs</p>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 text-[10px] uppercase font-bold">
                Local App & Vectors
              </span>
              <p className="text-white text-xs font-mono mt-0.5">
                D:\C.O.P.P.E.R
              </p>
            </div>
          </div>
        </div>
        {/* Personality & Communication Style Adaptation (Tier 4 Companion Intelligence) */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 shadow-sm font-mono text-xs">
          <div className="flex items-center gap-2 text-white font-bold font-sans text-sm">
            <Sparkles size={17} className="text-purple-400" />
            <span>AI Personality & Communication Style Adaptation</span>
          </div>
          <p className="text-slate-400 text-[11px]">
            Tune C.O.P.P.E.R's conversational mannerisms, technical depth, formality, and behavioral patterns.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Warmth Slider */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">Warmth & Empathy</span>
                <span className="text-accent-400 font-bold">{Math.round(personality.warmth * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={personality.warmth}
                onChange={(e) => handleUpdatePersonality("warmth", parseFloat(e.target.value))}
                className="w-full accent-accent-500 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500 block">Analytical ← → Empathetic</span>
            </div>

            {/* Formality Slider */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">Formality Level</span>
                <span className="text-purple-400 font-bold">{Math.round(personality.formality * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={personality.formality}
                onChange={(e) => handleUpdatePersonality("formality", parseFloat(e.target.value))}
                className="w-full accent-purple-500 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500 block">Casual Chat ← → Executive Briefing</span>
            </div>

            {/* Verbosity Slider */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">Verbosity & Detail</span>
                <span className="text-cyber-cyan font-bold">{Math.round(personality.verbosity * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={personality.verbosity}
                onChange={(e) => handleUpdatePersonality("verbosity", parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500 block">Terse Bullets ← → Comprehensive Explanations</span>
            </div>

            {/* Humor Slider */}
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-300 font-bold">Humor & Wit</span>
                <span className="text-verdigris font-bold">{Math.round(personality.humor * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={personality.humor}
                onChange={(e) => handleUpdatePersonality("humor", parseFloat(e.target.value))}
                className="w-full accent-emerald-500 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500 block">Strictly Serious ← → Playful Wit</span>
            </div>
          </div>

          {/* Behavior Toggles */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <p className="font-bold text-white text-xs">Code-First Responses</p>
                <p className="text-slate-400 text-[10px]">Provide solution code immediately before prose</p>
              </div>
              <button
                onClick={() => handleUpdatePersonality("code_first", !personality.code_first)}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors ${
                  personality.code_first ? "bg-verdigris" : "bg-slate-700"
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform ${
                    personality.code_first ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <p className="font-bold text-white text-xs">Expressive Formatting & Emojis</p>
                <p className="text-slate-400 text-[10px]">Use contextual symbols and icons in output</p>
              </div>
              <button
                onClick={() => handleUpdatePersonality("use_emojis", !personality.use_emojis)}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors ${
                  personality.use_emojis ? "bg-verdigris" : "bg-slate-700"
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform ${
                    personality.use_emojis ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
