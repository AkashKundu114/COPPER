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
import { HolographicCore, type CompanionCoreState } from "../components/hud/HolographicCore";
import { VisionViewfinder } from "../components/hud/VisionViewfinder";
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
  const [audioLevel, setAudioLevel] = useState(0);
  const [showVision, setShowVision] = useState(false);
  const [muted, setMuted] = useState(false);

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

  // Determine current holographic core state
  let coreState: CompanionCoreState = "idle";
  if (speaking) coreState = "speaking";
  else if (thinking) coreState = "thinking";
  else if (isRecording) coreState = "listening";

  // Toggle Hands-Free Continuous Voice Mode
  const toggleHandsFree = () => {
    const nextVal = !handsFree;
    setHandsFree(nextVal);
    localStorage.setItem("copper_continuous_voice", String(nextVal));
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
      setIsRecording(false);
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
          const normalizedLevel = Math.min(1.0, avg / 60);
          setAudioLevel(normalizedLevel);

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
                    const res = await fetch(`${API_BASE}/api/v1/voice/transcribe`, {
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
            const res = await fetch(`${API_BASE}/api/v1/voice/transcribe`, {
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
    <div className="relative w-full h-full flex flex-col items-center justify-between p-6 select-none overflow-hidden font-mono bg-[#03060a]">
      {/* Background Radial Glow */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-[600px] h-[600px] bg-cyber-cyan/5 rounded-full blur-[140px]" />
      </div>

      {/* Top Tactical Status Bar */}
      <div className="w-full max-w-6xl flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-black/60 px-3 py-1.5 rounded-xl border border-cyber-cyan/30 backdrop-blur-md">
            <span className={`w-2 h-2 rounded-full ${connected ? "bg-verdigris animate-pulse" : "bg-red-500"}`} />
            <span className="text-xs font-bold tracking-wider text-white">
              COPPER EMBODIED COMPANION // v1.0
            </span>
          </div>
          <button
            onClick={toggleHandsFree}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
              handsFree
                ? "bg-verdigris/15 border-verdigris text-verdigris shadow-[0_0_15px_rgba(0,255,170,0.2)]"
                : "bg-black/60 border-white/10 text-zinc-400 hover:text-white"
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            {handsFree ? "HANDS-FREE DUPLEX [ON]" : "HANDS-FREE [OFF]"}
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowVision(!showVision)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all ${
              showVision
                ? "bg-cyber-cyan/20 border-cyber-cyan text-cyber-cyan"
                : "bg-black/60 border-white/10 text-zinc-400 hover:text-white"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            {showVision ? "EYES ACTIVE" : "ENABLE EYES"}
          </button>
          <button
            onClick={() => {
              setMuted(!muted);
              onSend(muted ? "unmute voice" : "mute voice");
            }}
            className={`p-2 rounded-xl border transition-all ${
              muted ? "bg-red-500/20 border-red-500 text-red-400" : "bg-black/60 border-white/10 text-zinc-400 hover:text-white"
            }`}
            title={muted ? "Unmute Voice" : "Mute Voice"}
          >
            {muted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Main Center Stage: 3D Holographic Core & Vision Viewfinder */}
      <div className="flex-1 w-full max-w-6xl flex items-center justify-center relative my-4">
        {/* Holographic Core Centered */}
        <div className="relative flex flex-col items-center justify-center">
          <HolographicCore
            state={coreState}
            audioLevel={audioLevel}
            size={420}
            className="transition-transform duration-300 hover:scale-105"
            onInteractivityClick={() => {
              if (speaking) stopAudio();
              else handleManualPushToTalk();
            }}
          />
          <span className="text-[11px] font-bold text-zinc-500 tracking-[0.25em] uppercase mt-2">
            {speaking ? "COPPER SPEAKING" : thinking ? "SYNAPSE PROCESSING" : isRecording ? "LISTENING // DUPLEX" : "STANDBY // AKASH"}
          </span>
        </div>

        {/* Ambient Vision Dock (Right Drawer overlay) */}
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
                  // Feed observation into chat
                  onSend(`[SYSTEM_OBSERVATION]: ${obs}`);
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Recent Conversational Dialogue Overlays */}
      <div className="w-full max-w-3xl flex flex-col gap-2.5 mb-4 z-10">
        <AnimatePresence>
          {recentLines.map((line) => {
            const isUser = line.agent === "YOU" || line.agent === "user";
            return (
              <motion.div
                key={line.id}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96 }}
                className={`flex ${isUser ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] px-4 py-2.5 rounded-2xl backdrop-blur-md text-sm border shadow-lg ${
                    isUser
                      ? "bg-white/10 border-white/15 text-white rounded-br-sm"
                      : "bg-[#050b14]/90 border-cyber-cyan/30 text-cyber-cyan rounded-bl-sm shadow-[0_0_20px_rgba(0,240,255,0.08)]"
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
      <div className="w-full max-w-4xl flex items-center justify-between gap-4 z-10 bg-black/60 p-3 rounded-2xl border border-white/10 backdrop-blur-xl">
        {/* Quick Directives */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onSend("use a smaller model")}
            className="px-2.5 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-cyber-cyan/40 text-[10px] text-zinc-300 hover:text-white flex items-center gap-1 transition-all"
          >
            <Cpu className="w-3 h-3 text-cyber-cyan" />
            1B MINI
          </button>
          <button
            onClick={() => onSend("clear vram")}
            className="px-2.5 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:border-red-500/40 text-[10px] text-zinc-300 hover:text-white flex items-center gap-1 transition-all"
          >
            <Trash2 className="w-3 h-3 text-red-400" />
            PURGE VRAM
          </button>
        </div>

        {/* Center Mic / Interrupt Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleManualPushToTalk}
            className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
              isRecording
                ? "bg-red-500 shadow-[0_0_25px_rgba(239,68,68,0.6)] scale-110"
                : "bg-cyber-cyan text-black hover:bg-cyber-cyan/80 shadow-[0_0_20px_rgba(0,240,255,0.4)]"
            }`}
          >
            {isRecording ? <Square className="w-6 h-6 fill-white text-white" /> : <Mic className="w-6 h-6" />}
          </button>

          {speaking && (
            <button
              onClick={stopAudio}
              className="px-4 py-2 rounded-xl bg-red-500/20 border border-red-500/40 hover:bg-red-500/30 text-red-400 text-xs font-bold uppercase tracking-wider transition-all"
            >
              BARGE-IN
            </button>
          )}
        </div>

        {/* Clean Dialogue button */}
        <button
          onClick={clearChat}
          className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-zinc-400 hover:text-white text-[10px] transition-all"
        >
          CLEAR LOG
        </button>
      </div>
    </div>
  );
};
