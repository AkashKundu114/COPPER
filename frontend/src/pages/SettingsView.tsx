import React, { useState, useEffect } from "react";
import {
  Power,
  Volume2,
  HardDrive,
  CheckCircle2,
  Play,
  Mic,
  Sparkles,
  ShieldCheck,
  Cpu,
  DownloadCloud,
  RotateCcw,
} from "lucide-react";
import { API_BASE } from "../lib/api";
import { personalityAPI } from "../services/api";
import { Button } from "../components/ui/Button";

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
        const ipc =
          (window as any).copperAPI ||
          (window as any).ipcRenderer ||
          ((window as any).require
            ? (window as any).require("electron")?.ipcRenderer
            : null);
        if (ipc) {
          const running = await ipc.invoke("get-backend-status");
          if (active) setBackendRunning(running);
        } else {
          const res = await fetch(`${API_BASE}/system/telemetry`);
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
      const ipc =
        (window as any).copperAPI ||
        (window as any).ipcRenderer ||
        ((window as any).require
          ? (window as any).require("electron")?.ipcRenderer
          : null);
      if (ipc) {
        if (backendRunning) {
          await ipc.invoke("stop-backend");
          setBackendRunning(false);
          setToast("Python Backend Server stopped.");
        } else {
          await ipc.invoke("start-backend");
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
    setToast("Synthesizing voice sample with Piper ONNX...");
    try {
      const res = await fetch(`${API_BASE}/voice/speak`, {
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
    <div className="p-6 space-y-5 max-w-5xl mx-auto text-text select-none font-sans text-xs pb-16">
      <div>
        <h1 className="text-xl font-bold text-text tracking-tight">
          System Settings
        </h1>
        <p className="text-xs text-text-secondary mt-1">
          Local endpoints, voice synthesis, personality adaptation, and GPU authorization
        </p>
      </div>

      {toast && (
        <div className="p-3 rounded-lg bg-surface-elevated border border-copper/30 text-copper flex items-center justify-between animate-fade-in shadow-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={15} />
            <span className="text-xs font-medium">{toast}</span>
          </div>
          <button
            onClick={() => setToast(null)}
            className="text-text-secondary hover:text-text text-2xs cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="space-y-4">
        {/* Backend Toggle */}
        <div className="surface-card p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-text font-semibold text-sm">
              <Power
                size={16}
                className={backendRunning ? "text-success" : "text-text-tertiary"}
              />
              <span>Python Backend Server (FastAPI + Uvicorn)</span>
            </div>
            <p className="text-2xs text-text-secondary">
              Controls the standalone backend runtime on port 8000 with WatchFiles live-reload.
            </p>
          </div>
          <button
            onClick={toggleBackend}
            className={`w-11 h-6 rounded-full p-0.5 transition-colors cursor-pointer ${
              backendRunning ? "bg-copper" : "bg-surface-active"
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white transition-transform ${
                backendRunning ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {/* Continuous Voice Toggle */}
        <div className="surface-card p-4 rounded-xl border border-border flex items-center justify-between">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-text font-semibold text-sm">
              <Mic
                size={16}
                className={continuousVoice ? "text-copper" : "text-text-tertiary"}
              />
              <span>Hands-Free Mode (Continuous Voice)</span>
            </div>
            <p className="text-2xs text-text-secondary">
              Companion listens continuously via VAD without requiring a push-to-talk click.
            </p>
          </div>
          <button
            onClick={() => {
              const newVal = !continuousVoice;
              setContinuousVoice(newVal);
              localStorage.setItem("copper_continuous_voice", String(newVal));
              setToast(newVal ? "Hands-Free Mode Enabled" : "Hands-Free Mode Disabled");
            }}
            className={`w-11 h-6 rounded-full p-0.5 transition-colors cursor-pointer ${
              continuousVoice ? "bg-copper" : "bg-surface-active"
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white transition-transform ${
                continuousVoice ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
        </div>

        {/* Voice Preference */}
        <div className="surface-card p-4 rounded-xl border border-border space-y-3.5">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2 text-text font-semibold text-sm">
                <Volume2 size={16} className="text-copper" />
                <span>Text-To-Speech (TTS) Voice Engine</span>
              </div>
              <p className="text-2xs text-text-secondary">
                High-fidelity local neural voice synthesis powered by Piper ONNX.
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={testVoiceSample}
              disabled={isPlayingVoice}
            >
              <Play size={12} className="mr-1" />
              <span>{isPlayingVoice ? "Playing..." : "Test Voice"}</span>
            </Button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {[
              {
                id: "en-US-AvaNeural",
                name: "Ava (Neural)",
                tag: "Ultra Realistic & Fluent",
              },
              {
                id: "en-US-JennyNeural",
                name: "Jenny (Neural)",
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
                className={`p-3 rounded-lg border text-left transition-all cursor-pointer ${
                  selectedVoice === v.id
                    ? "bg-copper-subtle text-text border-copper/50"
                    : "bg-surface-base border-border-subtle text-text-secondary hover:text-text hover:bg-surface-hover"
                }`}
              >
                <p className="font-semibold text-text text-xs">{v.name}</p>
                <p className="text-2xs text-text-tertiary mt-0.5">{v.tag}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Model Storage Directory */}
        <div className="surface-card p-4 rounded-xl border border-border space-y-3">
          <div className="flex items-center gap-2 text-text font-semibold text-sm">
            <HardDrive size={16} className="text-copper" />
            <span>Local Weights & Storage Paths</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-surface-base border border-border-subtle">
              <span className="text-text-tertiary text-2xs uppercase font-mono font-medium">
                Ollama Model Blobs
              </span>
              <p className="text-text text-xs font-mono mt-0.5">D:\blobs</p>
            </div>
            <div className="p-3 rounded-lg bg-surface-base border border-border-subtle">
              <span className="text-text-tertiary text-2xs uppercase font-mono font-medium">
                Local App & Vectors
              </span>
              <p className="text-text text-xs font-mono mt-0.5">D:\C.O.P.P.E.R</p>
            </div>
          </div>
        </div>

        {/* Personality Adaptation */}
        <div className="surface-card p-4 rounded-xl border border-border space-y-3.5 text-xs">
          <div className="flex items-center gap-2 text-text font-semibold text-sm">
            <Sparkles size={16} className="text-copper" />
            <span>AI Personality & Adaptation</span>
          </div>
          <p className="text-text-secondary text-2xs">
            Tune C.O.P.P.E.R's conversational mannerisms, technical depth, formality, and behavioral patterns.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Warmth Slider */}
            <div className="p-3 rounded-lg bg-surface-base border border-border-subtle space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-secondary font-medium">Warmth & Empathy</span>
                <span className="text-copper font-mono font-semibold">{Math.round(personality.warmth * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={personality.warmth}
                onChange={(e) => handleUpdatePersonality("warmth", parseFloat(e.target.value))}
                className="w-full accent-copper cursor-pointer"
              />
              <span className="text-2xs text-text-tertiary block">Analytical ← → Empathetic</span>
            </div>

            {/* Formality Slider */}
            <div className="p-3 rounded-lg bg-surface-base border border-border-subtle space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-secondary font-medium">Formality Level</span>
                <span className="text-copper font-mono font-semibold">{Math.round(personality.formality * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={personality.formality}
                onChange={(e) => handleUpdatePersonality("formality", parseFloat(e.target.value))}
                className="w-full accent-copper cursor-pointer"
              />
              <span className="text-2xs text-text-tertiary block">Casual Chat ← → Executive Briefing</span>
            </div>

            {/* Verbosity Slider */}
            <div className="p-3 rounded-lg bg-surface-base border border-border-subtle space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-secondary font-medium">Verbosity & Detail</span>
                <span className="text-copper font-mono font-semibold">{Math.round(personality.verbosity * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={personality.verbosity}
                onChange={(e) => handleUpdatePersonality("verbosity", parseFloat(e.target.value))}
                className="w-full accent-copper cursor-pointer"
              />
              <span className="text-2xs text-text-tertiary block">Terse Bullets ← → Comprehensive Explanations</span>
            </div>

            {/* Humor Slider */}
            <div className="p-3 rounded-lg bg-surface-base border border-border-subtle space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-text-secondary font-medium">Humor & Wit</span>
                <span className="text-copper font-mono font-semibold">{Math.round(personality.humor * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={personality.humor}
                onChange={(e) => handleUpdatePersonality("humor", parseFloat(e.target.value))}
                className="w-full accent-copper cursor-pointer"
              />
              <span className="text-2xs text-text-tertiary block">Strictly Serious ← → Playful Wit</span>
            </div>
          </div>

          {/* Behavior Toggles */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <div className="p-3 rounded-lg bg-surface-base border border-border-subtle flex items-center justify-between">
              <div>
                <p className="font-medium text-text text-xs">Code-First Responses</p>
                <p className="text-text-tertiary text-2xs">Provide solution code immediately before prose</p>
              </div>
              <button
                onClick={() => handleUpdatePersonality("code_first", !personality.code_first)}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors cursor-pointer ${
                  personality.code_first ? "bg-copper" : "bg-surface-active"
                }`}
              >
                <div
                  className={`w-4 h-4 rounded-full bg-white transition-transform ${
                    personality.code_first ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-surface-base border border-border-subtle flex items-center justify-between">
              <div>
                <p className="font-medium text-text text-xs">Expressive Formatting & Emojis</p>
                <p className="text-text-tertiary text-2xs">Use contextual symbols and icons in output</p>
              </div>
              <button
                onClick={() => handleUpdatePersonality("use_emojis", !personality.use_emojis)}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors cursor-pointer ${
                  personality.use_emojis ? "bg-copper" : "bg-surface-active"
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

        {/* GPU Hardware Authorization & Model Setup */}
        <div className="surface-card p-4 rounded-xl border border-border space-y-3.5">
          <div className="flex items-center gap-2.5 border-b border-border pb-3">
            <div className="p-1.5 bg-copper-subtle text-copper rounded-lg">
              <ShieldCheck size={18} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text">GPU Authorization & Local Model Setup</h2>
              <p className="text-2xs text-text-secondary">Manage offline hardware fingerprinting and one-click model downloads</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-3.5 rounded-lg bg-surface-base border border-border-subtle space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-text">
                <Cpu size={14} className="text-copper" />
                <span>GPU Runtime & License Status</span>
              </div>
              <p className="text-2xs text-text-secondary leading-relaxed">
                Bound to host hardware fingerprint. Compatible with NVIDIA RTX dedicated GPU and shared master access codes.
              </p>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  fetch("/api/activation/status")
                    .then((r) => r.json())
                    .then((d) =>
                      alert(
                        `Status: ${d.activated ? "Authorized" : "Not Activated"}\nMode: ${d.mode}\nGPU: ${d.gpu_info?.name || "Detected"}`
                      )
                    )
                    .catch(() => alert("Activation check failed"));
                }}
              >
                Inspect GPU Fingerprint
              </Button>
            </div>

            <div className="p-3.5 rounded-lg bg-surface-base border border-border-subtle space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-text">
                <DownloadCloud size={14} className="text-info" />
                <span>One-Click Dependency & Model Installer</span>
              </div>
              <p className="text-2xs text-text-secondary leading-relaxed">
                Re-launch the onboarding setup wizard to adjust model presets, select active agents, or pull missing weights.
              </p>
              <Button
                variant="primary"
                size="sm"
                onClick={async () => {
                  await fetch("/api/setup/state", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ completed: false, current_step: 1 }),
                  });
                  window.location.reload();
                }}
              >
                <RotateCcw size={13} className="mr-1" /> Re-run Setup Wizard
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
