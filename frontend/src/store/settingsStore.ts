import { create } from "zustand";
import { persist } from "zustand/middleware";

interface Settings {
  provider: "ollama" | "openai";
  ollamaModel: string;
  openaiModel: string;
  ttsVoice: string;
  enableTTS: boolean;
  enableWakeWord: boolean;
  wakeWord: string;
  theme: "dark" | "darker";
  enableScanline: boolean;
  enableParticles: boolean;
}

interface SettingsStore extends Settings {
  update: (partial: Partial<Settings>) => void;
  reset: () => void;
}

const defaults: Settings = {
  provider: "ollama",
  ollamaModel: "llama3",
  openaiModel: "gpt-4o",
  ttsVoice: "alloy",
  enableTTS: false,
  enableWakeWord: false,
  wakeWord: "copper",
  theme: "dark",
  enableScanline: true,
  enableParticles: true,
};

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      ...defaults,
      update: (partial) => set((s) => ({ ...s, ...partial })),
      reset: () => set(defaults),
    }),
    { name: "copper-settings" }
  )
);
