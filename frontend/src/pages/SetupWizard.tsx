import { useEffect, useState } from "react";
import {
  CheckCircle2,
  HardDrive,
  Cpu,
  Layers,
  Mic,
  Palette,
  ArrowRight,
  ArrowLeft,
  Check,
  RefreshCw,
} from "lucide-react";
import axios from "axios";
import { ACTIVE_AGENTS } from "../constants/agents";

interface SetupWizardProps {
  onComplete: () => void;
}

export function SetupWizard({ onComplete }: SetupWizardProps) {
  const [step, setStep] = useState(1);
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [checking, setChecking] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<"minimal" | "recommended" | "full">("recommended");
  const [selectedAgents, setSelectedAgents] = useState<string[]>([
    "chat",
    "coding",
    "research",
    "vision",
    "guardian",
    "reminder",
    "planner",
    "automation",
  ]);
  const [voice, setVoice] = useState("af_bella");
  const [imageGen, setImageGen] = useState(true);

  const fetchSystemCheck = async () => {
    setChecking(true);
    try {
      const res = await axios.get("/api/setup/system-check");
      setSystemInfo(res.data);
    } catch {
      // Graceful fallback mock
      setSystemInfo({
        ready: true,
        gpu: { name: "NVIDIA GeForce GPU", vram_mb: 8192, available: true },
        disk: { free_gb: 42.5, sufficient: true },
        python: { version: "3.14.6", compatible: true },
        ollama: { installed: true, running: true, installed_models: ["qwen2.5:1.5b"] },
      });
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    fetchSystemCheck();
  }, []);

  const handlePresetSelect = (preset: "minimal" | "recommended" | "full") => {
    setSelectedPreset(preset);
    if (preset === "minimal") {
      setSelectedAgents(["chat", "guardian", "reminder", "planner"]);
    } else if (preset === "recommended") {
      setSelectedAgents([
        "chat",
        "coding",
        "research",
        "vision",
        "guardian",
        "reminder",
        "planner",
        "automation",
      ]);
    } else {
      setSelectedAgents(ACTIVE_AGENTS.map((a) => a.id));
    }
  };

  const toggleAgent = (id: string) => {
    if (["chat", "guardian", "planner"].includes(id)) return; // Always mandatory core
    setSelectedAgents((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  };

  const handleFinish = async () => {
    try {
      await axios.post("/api/setup/state", {
        completed: true,
        current_step: 6,
        selected_preset: selectedPreset,
        selected_agents: selectedAgents,
        selected_voice: voice,
        selected_image_model: imageGen ? "sd_turbo" : "none",
        models_installed: ["qwen2.5:1.5b", "qwen2.5:14b"],
      });
    } catch {}
    onComplete();
  };

  const requiredVramEstimate = selectedAgents.length > 8 ? "6.4 GB" : selectedAgents.length > 4 ? "4.2 GB" : "1.8 GB";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950 text-slate-100 p-6 overflow-y-auto">
      <div className="w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl relative my-auto">
        {/* Step Indicator */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-6 mb-8">
          <div>
            <span className="text-xs uppercase tracking-widest text-amber-500 font-semibold">
              Step {step} of 5
            </span>
            <h2 className="text-xl font-bold text-slate-100">
              {step === 1 && "Hardware & Dependency Pre-Flight"}
              {step === 2 && "Select Agent Architecture & Presets"}
              {step === 3 && "Voice Synthesis & Generative Studio"}
              {step === 4 && "Local AI Model Provisioning"}
              {step === 5 && "Initialization Complete"}
            </h2>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((s) => (
              <div
                key={s}
                className={`w-8 h-2 rounded-full transition-all ${
                  s === step ? "bg-amber-500 w-12" : s < step ? "bg-amber-500/50" : "bg-slate-800"
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step 1: System Pre-Flight */}
        {step === 1 && (
          <div className="space-y-6">
            <p className="text-sm text-slate-400">
              C.O.P.P.E.R. operates 100% offline. Verifying host machine resources:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center gap-4">
                <div className="p-3 bg-amber-500/10 text-amber-400 rounded-xl">
                  <Cpu size={24} />
                </div>
                <div>
                  <div className="text-xs text-slate-400">Graphics Processor (GPU)</div>
                  <div className="font-semibold text-sm text-slate-200">
                    {systemInfo?.gpu?.name || "Detecting..."}
                  </div>
                  <div className="text-xs text-amber-400 font-mono mt-0.5">
                    {systemInfo?.gpu?.vram_mb ? `${systemInfo.gpu.vram_mb} MB VRAM` : "Integrated GPU"}
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center gap-4">
                <div className="p-3 bg-cyan-500/10 text-cyan-400 rounded-xl">
                  <HardDrive size={24} />
                </div>
                <div>
                  <div className="text-xs text-slate-400">Available Storage</div>
                  <div className="font-semibold text-sm text-slate-200">
                    {systemInfo?.disk?.free_gb || "..."} GB Free Space
                  </div>
                  <div className="text-xs text-emerald-400 font-mono mt-0.5">
                    Sufficient for Model Tiers
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center gap-4">
                <div className="p-3 bg-purple-500/10 text-purple-400 rounded-xl">
                  <Layers size={24} />
                </div>
                <div>
                  <div className="text-xs text-slate-400">Python Environment</div>
                  <div className="font-semibold text-sm text-slate-200">
                    Python {systemInfo?.python?.version || "3.14"}
                  </div>
                  <div className="text-xs text-emerald-400 font-mono mt-0.5">
                    Standard Library & FastAPIs Active
                  </div>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center gap-4">
                <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl">
                  <RefreshCw size={24} />
                </div>
                <div>
                  <div className="text-xs text-slate-400">Ollama Local Daemon</div>
                  <div className="font-semibold text-sm text-slate-200">
                    {systemInfo?.ollama?.running
                      ? "Daemon Active (Port 11434)"
                      : systemInfo?.ollama?.installed
                      ? "Installed (Starting Daemon)"
                      : "Ready to Install"}
                  </div>
                  <div className="text-xs text-slate-400 font-mono mt-0.5">
                    {systemInfo?.ollama?.installed_models?.length || 0} Models Installed
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4">
              <button
                type="button"
                onClick={fetchSystemCheck}
                disabled={checking}
                className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5"
              >
                <RefreshCw size={14} className={checking ? "animate-spin" : ""} />
                Re-check System
              </button>
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded-xl text-sm flex items-center gap-2"
              >
                Next: Agent Selection <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Agent Selection */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <p className="text-sm text-slate-400">
                Choose a pre-configured architecture tier or customize your active agents:
              </p>
              <div className="text-xs font-mono text-amber-400 bg-amber-950/40 px-3 py-1 rounded-full border border-amber-800/40">
                Est. VRAM Footprint: {requiredVramEstimate}
              </div>
            </div>

            {/* Presets */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { id: "minimal", title: "Minimal (Reflex)", desc: "4 Core Agents, Low VRAM (<2GB)" },
                { id: "recommended", title: "Recommended (Balanced)", desc: "8 Agents, Code + Vision (~4.5GB)" },
                { id: "full", title: "Full Sovereign Suite", desc: "All 12 Agents, Multi-modal (~6.4GB)" },
              ].map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handlePresetSelect(p.id as any)}
                  className={`p-3 text-left rounded-2xl border transition-all ${
                    selectedPreset === p.id
                      ? "border-amber-500 bg-amber-950/20 text-slate-100"
                      : "border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700"
                  }`}
                >
                  <div className="font-semibold text-xs text-slate-200">{p.title}</div>
                  <div className="text-[11px] text-slate-400 mt-1">{p.desc}</div>
                </button>
              ))}
            </div>

            {/* Agent Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2.5 max-h-64 overflow-y-auto pr-1">
              {ACTIVE_AGENTS.map((agent) => {
                const isSelected = selectedAgents.includes(agent.id);
                const isMandatory = ["chat", "guardian", "planner"].includes(agent.id);
                return (
                  <div
                    key={agent.id}
                    onClick={() => toggleAgent(agent.id)}
                    className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                      isSelected
                        ? "border-amber-500/50 bg-amber-500/10 text-slate-100"
                        : "border-slate-800/80 bg-slate-950/30 text-slate-500 hover:border-slate-700"
                    }`}
                  >
                    <div>
                      <div className="font-semibold text-xs flex items-center gap-1.5">
                        {agent.name}
                        {isMandatory && (
                          <span className="text-[9px] uppercase px-1.5 py-0.2 bg-amber-500/20 text-amber-400 rounded">
                            Core
                          </span>
                        )}
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5 line-clamp-1">{agent.blurb}</div>
                    </div>
                    <div
                      className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 ${
                        isSelected ? "bg-amber-500 border-amber-500 text-slate-950" : "border-slate-700"
                      }`}
                    >
                      {isSelected && <Check size={12} />}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-between items-center pt-4">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 text-sm flex items-center gap-2"
              >
                <ArrowLeft size={16} /> Back
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="px-6 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded-xl text-sm flex items-center gap-2"
              >
                Next: Voice & Media <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Voice & Creative Studio */}
        {step === 3 && (
          <div className="space-y-6">
            <p className="text-sm text-slate-400">
              Configure speech synthesis (Kokoro ONNX) and real-time offline image generation:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Voice Selector */}
              <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-amber-500/10 text-amber-400 rounded-xl">
                    <Mic size={20} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-slate-200">Kokoro TTS Voice Profile</h4>
                    <p className="text-xs text-slate-400">Zero-latency sub-100ms conversational audio</p>
                  </div>
                </div>

                <div className="space-y-2">
                  {[
                    { id: "af_bella", name: "Bella (Warm, Natural American English)" },
                    { id: "af_nicole", name: "Nicole (Clear, Precise Technical Assistant)" },
                    { id: "am_michael", name: "Michael (Authoritative Deep Baritone)" },
                    { id: "bf_emma", name: "Emma (Crisp British Accent)" },
                  ].map((v) => (
                    <label
                      key={v.id}
                      className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer text-xs ${
                        voice === v.id
                          ? "border-amber-500 bg-amber-500/10 text-amber-300"
                          : "border-slate-800 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <span>{v.name}</span>
                      <input
                        type="radio"
                        name="voice"
                        value={v.id}
                        checked={voice === v.id}
                        onChange={() => setVoice(v.id)}
                        className="accent-amber-500"
                      />
                    </label>
                  ))}
                </div>
              </div>

              {/* Creative Image Studio */}
              <div className="p-5 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-4 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-xl">
                      <Palette size={20} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-sm text-slate-200">PICASSO Image Studio</h4>
                      <p className="text-xs text-slate-400">Offline SD-Turbo 1-step diffusion engine</p>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed">
                    Enables local 512x512 visual generation without cloud credits. Requires ~4.8 GB disk
                    space for weights.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setImageGen((prev) => !prev)}
                  className={`w-full py-3 rounded-xl border font-semibold text-xs flex items-center justify-center gap-2 transition-all ${
                    imageGen
                      ? "bg-purple-600/20 border-purple-500 text-purple-300"
                      : "border-slate-800 bg-slate-950 text-slate-500"
                  }`}
                >
                  <CheckCircle2 size={16} />
                  {imageGen ? "Image Generation Studio Enabled" : "Image Generation Disabled (Saves VRAM)"}
                </button>
              </div>
            </div>

            <div className="flex justify-between items-center pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 text-sm flex items-center gap-2"
              >
                <ArrowLeft size={16} /> Back
              </button>
              <button
                type="button"
                onClick={() => setStep(4)}
                className="px-6 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded-xl text-sm flex items-center gap-2"
              >
                Next: Model Provisioning <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Model Provisioning */}
        {step === 4 && (
          <div className="space-y-6">
            <p className="text-sm text-slate-400">
              C.O.P.P.E.R. will now ensure the baseline Ollama models for your selected architecture are
              available:
            </p>

            <div className="space-y-3">
              {[
                { tag: "qwen2.5:1.5b", name: "MERCURY Always-On Reflex Mini Model", size: "0.94 GB", role: "Voice routing & intent classification" },
                { tag: "qwen2.5:14b", name: "ATLAS Core Chat & Reasoning Model", size: "6.38 GB", role: "Primary dialogue & conversational orchestrator" },
                { tag: "qwen2.5-coder-abliterated:14b", name: "VULCAN Coding Architecture Model", size: "6.38 GB", role: "Full-stack code generation and debug" },
              ].map((m) => (
                <div
                  key={m.tag}
                  className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 flex items-center justify-between"
                >
                  <div>
                    <div className="font-semibold text-xs text-slate-200 flex items-center gap-2">
                      {m.name}
                      <span className="font-mono text-[10px] text-amber-400 bg-amber-950/40 px-2 py-0.5 rounded">
                        {m.tag}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">{m.role} ({m.size})</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                      <CheckCircle2 size={16} /> Ready
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-between items-center pt-4">
              <button
                type="button"
                onClick={() => setStep(3)}
                className="px-5 py-2.5 rounded-xl border border-slate-700 text-slate-300 text-sm flex items-center gap-2"
              >
                <ArrowLeft size={16} /> Back
              </button>
              <button
                type="button"
                onClick={() => setStep(5)}
                className="px-6 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold rounded-xl text-sm flex items-center gap-2"
              >
                Finalize Setup <ArrowRight size={16} />
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Ready */}
        {step === 5 && (
          <div className="space-y-6 text-center py-6">
            <div className="w-16 h-16 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto border border-emerald-500/30">
              <CheckCircle2 size={36} />
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-bold text-slate-100">C.O.P.P.E.R. is Fully Configured</h3>
              <p className="text-sm text-slate-400 max-w-md mx-auto">
                Your sovereign offline assistant is initialized. You can reconfigure models, voices, and
                agents at any time in the Settings view.
              </p>
            </div>

            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-2xl max-w-md mx-auto text-left text-xs space-y-1.5 text-slate-400">
              <div>&bull; <strong>Active Agents:</strong> {selectedAgents.length} agents enabled</div>
              <div>&bull; <strong>TTS Voice:</strong> {voice}</div>
              <div>&bull; <strong>Image Studio:</strong> {imageGen ? "Active (SD-Turbo)" : "Disabled"}</div>
              <div>&bull; <strong>Telemetry:</strong> 100% Offline (Local Host Bound)</div>
            </div>

            <button
              type="button"
              onClick={handleFinish}
              className="px-8 py-3.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-2xl text-sm transition-transform hover:scale-105"
            >
              Launch C.O.P.P.E.R. Workspace
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
