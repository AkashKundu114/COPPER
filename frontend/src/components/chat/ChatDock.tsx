import { useState, useRef } from "react";
import { Paperclip, ArrowUp, Mic, MicOff } from "lucide-react";
import { API_BASE } from "../../lib/api";

interface Props {
  connected: boolean;
  thinking: boolean;
  onSend: (message: string) => void;
}

export function ChatDock({ connected, thinking, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const submit = () => {
    const msg = draft.trim();
    if (!msg || thinking) return;
    onSend(msg);
    setDraft("");
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        
        const formData = new FormData();
        formData.append("file", audioBlob, "voice.webm");

        try {
          const res = await fetch(`${API_BASE}/api/v1/voice/transcribe`, {
            method: "POST",
            body: formData,
          });
          const data = await res.json();
          if (data.text) {
            onSend(data.text);
          }
        } catch (e) {
          console.error("Voice transcription error", e);
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch (e) {
      console.error("Mic access denied", e);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className={`w-full flex items-end gap-2 bg-bg-panel border rounded-2xl px-3 py-2.5 shadow-sm transition-all duration-300 ${thinking ? 'border-accent shadow-neon animate-pulse-glow' : 'border-border focus-within:border-accent hover:shadow-hud'}`}>
      <button 
        className="p-2 text-accent hover:text-accent-hover rounded-full transition-colors flex-shrink-0"
        title="Attach file (coming soon)"
      >
        <Paperclip size={18} />
      </button>

      <textarea
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder={thinking ? "C.O.P.P.E.R. is thinking..." : isRecording ? "Listening..." : "Message C.O.P.P.E.R..."}
        className="flex-1 bg-transparent outline-none text-[15px] text-text placeholder:text-text-muted resize-none max-h-32 min-h-[24px] py-1.5 custom-scrollbar"
        rows={draft.split("\n").length > 1 ? Math.min(draft.split("\n").length, 5) : 1}
        disabled={isRecording}
      />

      <button
        onClick={toggleRecording}
        className={`p-2 ml-1 rounded-full transition-all flex-shrink-0 ${isRecording ? 'bg-red-500/20 text-red-500 animate-pulse' : 'text-accent hover:bg-accent/10 hover:text-accent-hover'}`}
        title={isRecording ? "Stop recording" : "Voice input"}
      >
        {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
      </button>

      <button
        onClick={submit}
        disabled={!draft.trim() || thinking || isRecording}
        className="p-2 ml-1 rounded-full bg-accent text-bg hover:bg-accent-hover hover:shadow-neon disabled:opacity-30 disabled:hover:bg-accent disabled:shadow-none transition-all flex-shrink-0"
        title={connected ? "Send message" : "Reconnecting..."}
      >
        <ArrowUp size={18} strokeWidth={3} />
      </button>
    </div>
  );
}
