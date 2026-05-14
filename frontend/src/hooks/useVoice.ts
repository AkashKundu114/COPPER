import { useCallback } from "react";
import { useVoiceStore } from "@/store/voiceStore";
import { voiceAPI } from "@/services/api";
import { recorder, playAudioUrl } from "@/services/voiceService";
import { useSettingsStore } from "@/store/settingsStore";

export function useVoice() {
  const store = useVoiceStore();
  const { enableTTS, ttsVoice } = useSettingsStore();

  const startRecording = useCallback(async () => {
    try {
      store.setError(null);
      await recorder.start();
      store.setRecording(true);
    } catch (e: any) {
      store.setError(e.message || "Microphone access denied");
    }
  }, []);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    if (!recorder.isRecording) return null;
    store.setRecording(false);
    store.setProcessing(true);
    try {
      const blob = await recorder.stop();
      return blob;
    } catch (e: any) {
      store.setError(e.message);
      return null;
    } finally {
      store.setProcessing(false);
    }
  }, []);

  const transcribe = useCallback(async (blob: Blob): Promise<string> => {
    store.setProcessing(true);
    try {
      const { data } = await voiceAPI.transcribe(blob);
      store.setTranscript(data.transcript);
      return data.transcript;
    } catch (e: any) {
      store.setError(e.message);
      return "";
    } finally {
      store.setProcessing(false);
    }
  }, []);

  const speak = useCallback(
    async (text: string) => {
      if (!enableTTS) return;
      store.setSpeaking(true);
      try {
        const url = await voiceAPI.synthesize(text, ttsVoice);
        await playAudioUrl(url);
      } catch (e: any) {
        console.error("TTS error:", e);
      } finally {
        store.setSpeaking(false);
      }
    },
    [enableTTS, ttsVoice]
  );

  return {
    ...store,
    startRecording,
    stopRecording,
    transcribe,
    speak,
  };
}
