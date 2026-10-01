import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Mic,
  Square,
  Cpu,
  Volume2,
  VolumeX,
  Radio,
  Eye,
  Trash2,
} from "lucide-react";
import { ThinkingOrb as OfficialThinkingOrb, type OrbState } from "thinking-orbs";
import { VisionViewfinder } from "../components/hud/VisionViewfinder";
import { soundFX } from "../lib/soundFX";
import { type ChatLine } from "../hooks/useBrainSocket";
import { API_BASE } from "../lib/api";

interface CompanionHUDViewProps {
  lines: ChatLine[];
  thinking: boolean;
  speaking: boolean;
  connected: boolean;
  onSend: (msg: string) => void;
  stopAudio: () => void;
  clearChat?: () => void;
}

export const CompanionHUDView: React.FC<CompanionHUDViewProps> = ({
  lines,
  thinking,
  speaking,
  connected,
  onSend,
  stopAudio,
  clearChat,
}) => {
  const [handsFree, setHandsFree] = useState<boolean>(() => {
    return localStorage.getItem("copper_continuous_voice") === "true";
  });
  const [isRecording, setIsRecording] = useState(false);
  const [showVision, setShowVision] = useState(false);
  const [muted, setMuted] = useState(() => soundFX.isMuted());

  // Audio & VAD Refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const silenceTimerRef = useRef<number>(0);
  const isRecordingRef = useRef(false);
  const speakingRef = useRef(speaking);
  const onSendRef = useRef(onSend);
  const stopAudioRef = useRef(stopAudio);

  useEffect(() => {
    speakingRef.current = speaking;
    onSendRef.current = onSend;
    stopAudioRef.current = stopAudio;
  }, [speaking, onSend, stopAudio]);

  // Determine official ThinkingOrb state reacting to live duplex voice companion activity
  let autoDotsState: OrbState = "breathing";
  if (speaking) autoDotsState = "weaving";
  else if (thinking) autoDotsState = "solving";
  else if (isRecording) autoDotsState = "listening";
  else if (handsFree) autoDotsState = "connecting";

  // Toggle Hands-Free Continuous Voice Mode
  const toggleHandsFree = () => {
    const nextVal = !handsFree;
    setHandsFree(nextVal);
    localStorage.setItem("copper_continuous_voice", String(nextVal));
    if (!nextVal) {
      setIsRecording(false);
      isRecordingRef.current = false;
    }
  };

  // Setup Continuous Web Audio VAD
  useEffect(() => {
    if (!handsFree) {
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(() => {});
        audioContextRef.current = null;
      }
      if (micStreamRef.current) {
        micStreamRef.current.getTracks().forEach((t) => t.stop());
        micStreamRef.current = null;
      }
      isRecordingRef.current = false;
      return;
    }

    let animationFrameId: number;
    let localStream: MediaStream;
    let localCtx: AudioContext;
    let localAnalyser: AnalyserNode;

    const startVAD = async () => {
      try {
        localStream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        });
        micStreamRef.current = localStream;

        localCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        audioContextRef.current = localCtx;

        localAnalyser = localCtx.createAnalyser();
        localAnalyser.fftSize = 256;
        analyserRef.current = localAnalyser;

        const micSource = localCtx.createMediaStreamSource(localStream);
        micSource.connect(localAnalyser);

        const bufferLength = localAnalyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const checkAudio = () => {
          localAnalyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          const avg = sum / bufferLength;

          // Threshold for human speech
          if (avg > 14) {
            if (!isRecordingRef.current) {
              // BARGE-IN: If COPPER is speaking, immediately cut audio!
              if (speakingRef.current) {
                stopAudioRef.current();
              }

              isRecordingRef.current = true;
              setIsRecording(true);
              chunksRef.current = [];

              try {
                const rec = new MediaRecorder(localStream);
                mediaRecorderRef.current = rec;
                rec.ondataavailable = (e) => {
                  if (e.data.size > 0) chunksRef.current.push(e.data);
                };
                rec.onstop = async () => {
                  const blob = new Blob(chunksRef.current, { type: "audio/webm" });
                  const formData = new FormData();
                  formData.append("file", blob, "voice.webm");

                  try {
                    const res = await fetch(`${API_BASE}/voice/transcribe`, {
                      method: "POST",
                      body: formData,
                    });
                    const data = await res.json();
                    if (data.text && data.text.trim().length > 0) {
                      onSendRef.current(data.text);
                    }
                  } catch (err) {
                    console.error("Continuous VAD transcription error:", err);
                  }
                };
                rec.start();
              } catch (e) {
                console.error("MediaRecorder start failed:", e);
              }
            }
            silenceTimerRef.current = performance.now();
          } else {
            // Silence detection
            if (isRecordingRef.current) {
              if (performance.now() - silenceTimerRef.current > 1300) {
                // 1.3 seconds of silence after speaking: finalize speech chunk
                isRecordingRef.current = false;
                setIsRecording(false);
                if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
                  mediaRecorderRef.current.stop();
                }
              }
            }
          }

          animationFrameId = requestAnimationFrame(checkAudio);
        };

        checkAudio();
      } catch (err) {
        console.error("Failed to initialize hands-free VAD:", err);
      }
    };

    startVAD();

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      if (localStream) localStream.getTracks().forEach((t) => t.stop());
      if (localCtx) localCtx.close().catch(() => {});
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
    };
  }, [handsFree]);

  // Push-to-talk fallback when hands-free is off
  const handleManualPushToTalk = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
      isRecordingRef.current = false;
    } else {
      if (speaking) stopAudio();
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const rec = new MediaRecorder(stream);
        mediaRecorderRef.current = rec;
        chunksRef.current = [];
        rec.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };
        rec.onstop = async () => {
          stream.getTracks().forEach((t) => t.stop());
          const blob = new Blob(chunksRef.current, { type: "audio/webm" });
          const formData = new FormData();
          formData.append("file", blob, "voice.webm");
          try {
            const res = await fetch(`${API_BASE}/voice/transcribe`, {
              method: "POST",
              body: formData,
            });
            const data = await res.json();
            if (data.text && data.text.trim().length > 0) {
              onSend(data.text);
            }
          } catch (e) {
            console.error("Transcribe failed:", e);
          }
        };
        rec.start();
        setIsRecording(true);
        isRecordingRef.current = true;
      } catch (e) {
        console.error("Mic access denied:", e);
      }
    }
  };

  const recentLines = lines.slice(-4);

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-between p-6 select-none overflow-hidden font-sans bg-canvas text-text">
      {/* Subtle Ambient Glow */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-[500px] h-[500px] bg-copper-subtle rounded-full blur-[140px] opacity-40" />
      </div>

      {/* Top Status Bar */}
      <div className="w-full max-w-5xl flex items-center justify-between z-10">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-2 bg-surface-elevated px-3 py-1.5 rounded-lg border border-border shadow-sm">
            <span className={`w-2 h-2 rounded-full ${connected ? "bg-success" : "bg-danger"}`} />
            <span className="font-sans text-xs font-semibold tracking-wide text-text">
              COPPER COMPANION
            </span>
          </div>
          <button
            onClick={toggleHandsFree}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
              handsFree
                ? "bg-success-dim border-success/30 text-success"
                : "bg-surface-elevated border-border-subtle text-text-secondary hover:text-text hover:bg-surface-hover"
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            {handsFree ? "HANDS-FREE [ON]" : "HANDS-FREE [OFF]"}
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              soundFX.play("toggle");
              setShowVision(!showVision);
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer ${
              showVision
                ? "bg-copper-subtle border-copper/30 text-copper"
                : "bg-surface-elevated border-border-subtle text-text-secondary hover:text-text hover:bg-surface-hover"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            {showVision ? "EYES ACTIVE" : "ENABLE EYES"}
          </button>
          <button
            onClick={() => {
              const nextMuted = soundFX.toggleMute();
              setMuted(nextMuted);
              onSend(nextMuted ? "mute voice" : "unmute voice");
            }}
            className={`p-2 rounded-lg border transition-all cursor-pointer ${
              muted
                ? "bg-danger-dim border-danger/30 text-danger"
                : "bg-surface-elevated border-border-subtle text-text-secondary hover:text-text hover:bg-surface-hover"
            }`}
            title={muted ? "Unmute Voice" : "Mute Voice"}
          >
            {muted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Main Center Stage: Thinking Orb Visualizer */}
      <div className="flex-1 w-full max-w-5xl flex items-center justify-center relative my-2">
        <div className="relative flex items-center justify-center select-none py-10">
          <div
            className="scale-[3.2] cursor-pointer transition-transform duration-200 hover:scale-[3.35] active:scale-[3.05] flex items-center justify-center p-2"
            onClick={() => {
              soundFX.play("click");
              if (speaking) stopAudio();
              else handleManualPushToTalk();
            }}
            title="Click to interact with Companion"
          >
            <OfficialThinkingOrb
              state={autoDotsState}
              size={64}
              theme="dark"
              speed={1.0}
            />
          </div>
        </div>

        {/* Ambient Vision Dock */}
        <AnimatePresence>
          {showVision && (
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              className="absolute right-0 top-1/2 -translate-y-1/2 w-80 z-20"
            >
              <VisionViewfinder
                onObservation={(obs) => {
                  onSend(`[SYSTEM_OBSERVATION]: ${obs}`);
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Recent Conversational Dialogue Overlays */}
      <div className="w-full max-w-2xl flex flex-col gap-2.5 mb-3 z-10">
        <AnimatePresence>
          {recentLines.map((line) => {
            const isUser = line.agent === "YOU" || line.agent === "user";
            return (
              <motion.div
                key={line.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96 }}
                className={`flex ${isUser ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] px-4 py-2 rounded-2xl text-sm border shadow-sm ${
                    isUser
                      ? "bg-copper-subtle border-copper/20 text-text rounded-br-sm"
                      : "surface-glass text-text border-border-subtle rounded-bl-sm"
                  }`}
                >
                  <p className="leading-relaxed font-sans">{line.text}</p>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Bottom Control Deck */}
      <div className="w-full max-w-3xl flex items-center justify-between gap-4 z-10 surface-glass p-2.5 px-4 rounded-xl border border-border">
        {/* Quick Directives */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              soundFX.play("click");
              onSend("use a smaller model");
            }}
            className="px-2.5 py-1.5 rounded-md bg-surface-base hover:bg-surface-hover border border-border-subtle text-2xs text-text-secondary hover:text-text flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Cpu className="w-3.5 h-3.5 text-copper" />
            1B MINI
          </button>
          <button
            onClick={() => {
              soundFX.play("click");
              onSend("clear vram");
            }}
            className="px-2.5 py-1.5 rounded-md bg-surface-base hover:bg-surface-hover border border-border-subtle hover:border-danger/30 text-2xs text-text-secondary hover:text-danger flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5 text-danger" />
            PURGE VRAM
          </button>
        </div>

        {/* Center Mic / Interrupt Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleManualPushToTalk}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-200 cursor-pointer ${
              isRecording
                ? "bg-danger text-white shadow-lg scale-105"
                : "bg-copper hover:bg-copper-bright text-text-inverse shadow-md active:scale-95"
            }`}
          >
            {isRecording ? <Square className="w-5 h-5 fill-current" /> : <Mic className="w-5 h-5 stroke-[2.2]" />}
          </button>

          {speaking && (
            <button
              onClick={() => {
                soundFX.play("click");
                stopAudio();
              }}
              className="px-3 py-1.5 rounded-lg bg-danger-dim border border-danger/30 text-danger text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer"
            >
              BARGE-IN
            </button>
          )}
        </div>

        {/* Clear Log button */}
        <button
          onClick={() => {
            soundFX.play("click");
            clearChat?.();
          }}
          className="px-2.5 py-1.5 rounded-md bg-surface-base hover:bg-surface-hover border border-border-subtle text-text-secondary hover:text-text text-2xs transition-colors cursor-pointer"
        >
          CLEAR LOG
        </button>
      </div>
    </div>
  );
};
