import { motion } from "framer-motion";
import { Settings, Cpu, Volume2, Eye, Palette } from "lucide-react";
import { useSettingsStore } from "@/store/settingsStore";

function Section({ title, icon: Icon, children }: any) {
  return (
    <div className="glass rounded-xl p-4 space-y-4">
      <div className="flex items-center gap-2 pb-2 border-b border-white/5">
        <Icon size={16} className="text-copper-400" />
        <span className="text-sm font-semibold text-gray-300">{title}</span>
      </div>
      {children}
    </div>
  );
}

function Toggle({ label, value, onChange, description }: any) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-300">{label}</p>
        {description && <p className="text-xs text-gray-600 mt-0.5">{description}</p>}
      </div>
      <button onClick={() => onChange(!value)}
        className={`relative w-10 h-5 rounded-full transition-colors ${value ? "bg-copper-600" : "bg-dark-600"}`}>
        <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${value ? "translate-x-5" : ""}`} />
      </button>
    </div>
  );
}

function Select({ label, value, options, onChange }: any) {
  return (
    <div className="flex items-center justify-between gap-4">
      <label className="text-sm text-gray-300 flex-shrink-0">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="bg-dark-700 border border-copper-600/30 text-white text-sm rounded-lg px-3 py-1.5 outline-none focus:border-copper-500/60">
        {options.map((o: any) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

export default function SettingsPage() {
  const s = useSettingsStore();

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-4 space-y-4 h-full overflow-y-auto">
      <div className="flex items-center gap-2">
        <Settings size={20} className="text-copper-400" />
        <h2 className="font-semibold text-white">Settings</h2>
      </div>

      <Section title="AI Provider" icon={Cpu}>
        <Select label="Default Provider"
          value={s.provider}
          onChange={(v: any) => s.update({ provider: v })}
          options={[{ value: "ollama", label: "Ollama (Local)" }, { value: "openai", label: "OpenAI (Cloud)" }]}
        />
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Ollama Model</label>
          <input value={s.ollamaModel} onChange={(e) => s.update({ ollamaModel: e.target.value })}
            className="w-full input-copper text-sm" />
        </div>
        <div>
          <label className="text-xs text-gray-500 mb-1 block">OpenAI Model</label>
          <input value={s.openaiModel} onChange={(e) => s.update({ openaiModel: e.target.value })}
            className="w-full input-copper text-sm" />
        </div>
      </Section>

      <Section title="Voice & Audio" icon={Volume2}>
        <Toggle label="Text-to-Speech" value={s.enableTTS} onChange={(v: boolean) => s.update({ enableTTS: v })}
          description="Read AI responses aloud" />
        <Toggle label="Wake Word Detection" value={s.enableWakeWord}
          onChange={(v: boolean) => s.update({ enableWakeWord: v })}
          description={`Say "${s.wakeWord}" to activate`} />
        <Select label="TTS Voice"
          value={s.ttsVoice}
          onChange={(v: string) => s.update({ ttsVoice: v })}
          options={["alloy","echo","fable","onyx","nova","shimmer"].map((v) => ({ value: v, label: v.charAt(0).toUpperCase() + v.slice(1) }))}
        />
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Wake Word</label>
          <input value={s.wakeWord} onChange={(e) => s.update({ wakeWord: e.target.value })}
            className="w-full input-copper text-sm" />
        </div>
      </Section>

      <Section title="Appearance" icon={Palette}>
        <Toggle label="Scanline Effect" value={s.enableScanline}
          onChange={(v: boolean) => s.update({ enableScanline: v })}
          description="Retro CRT scanline animation" />
        <Toggle label="Particle Effects" value={s.enableParticles}
          onChange={(v: boolean) => s.update({ enableParticles: v })}
          description="Floating ambient particles" />
      </Section>

      <button onClick={s.reset}
        className="w-full py-2 rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 text-sm transition-colors">
        Reset to Defaults
      </button>

      <p className="text-center text-xs text-gray-700 pb-2">COPPER v1.0.0 · MIT License</p>
    </motion.div>
  );
}
