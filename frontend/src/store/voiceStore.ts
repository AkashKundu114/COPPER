import { create } from "zustand";

interface VoiceStore {
  isRecording: boolean;
  isProcessing: boolean;
  isSpeaking: boolean;
  transcript: string;
  error: string | null;
  volume: number;

  setRecording: (v: boolean) => void;
  setProcessing: (v: boolean) => void;
  setSpeaking: (v: boolean) => void;
  setTranscript: (t: string) => void;
  setError: (e: string | null) => void;
  setVolume: (v: number) => void;
  reset: () => void;
}

export const useVoiceStore = create<VoiceStore>((set) => ({
  isRecording: false,
  isProcessing: false,
  isSpeaking: false,
  transcript: "",
  error: null,
  volume: 0,

  setRecording: (v) => set({ isRecording: v }),
  setProcessing: (v) => set({ isProcessing: v }),
  setSpeaking: (v) => set({ isSpeaking: v }),
  setTranscript: (t) => set({ transcript: t }),
  setError: (e) => set({ error: e }),
  setVolume: (v) => set({ volume: v }),
  reset: () => set({ isRecording: false, isProcessing: false, isSpeaking: false, transcript: "", error: null }),
}));
