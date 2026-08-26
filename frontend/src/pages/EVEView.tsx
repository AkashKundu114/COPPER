import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence, type Variants } from "framer-motion";
import { Mic, Square, Loader2 } from "lucide-react";
import { type ChatLine } from "../hooks/useBrainSocket";
import { API_BASE } from "../lib/api";

interface Props {
  lines: ChatLine[];
  thinking: boolean;
  speaking: boolean;
  connected: boolean;
  onSend: (msg: string) => void;
  stopAudio: () => void;
}

export function EVEView({ lines, thinking, speaking, onSend, stopAudio }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  
  // Refs for VAD closures
  const speakingRef = useRef(speaking);
  const onSendRef = useRef(onSend);
  const stopAudioRef = useRef(stopAudio);

  useEffect(() => {
    speakingRef.current = speaking;
    onSendRef.current = onSend;
    stopAudioRef.current = stopAudio;
  }, [speaking, onSend, stopAudio]);

  useEffect(() => {
    const isContinuousMode = localStorage.getItem("copper_continuous_voice") === "true";
    if (!isContinuousMode) return;

    let audioContext: AudioContext;
    let analyser: AnalyserNode;
    let microphone: MediaStreamAudioSourceNode;
    let stream: MediaStream;
    let animationFrame: number;
    let isCurrentlyRecording = false;
    let silenceStart = 0;
    
    let recorder: MediaRecorder;
    let chunks: BlobPart[] = [];

    const initVAD = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ 
          audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } 
        });
        audioContext = new AudioContext();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 512;
        analyser.minDecibels = -70; // Sensible threshold
        
        microphone = audioContext.createMediaStreamSource(stream);
        microphone.connect(analyser);
        
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const checkVolume = () => {
          analyser.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
          }
          const average = sum / bufferLength;
          
          // Threshold logic
          if (average > 15) { // User is speaking
            if (!isCurrentlyRecording) {
              if (speakingRef.current) stopAudioRef.current(); // Interrupt E.V.E.
              
              isCurrentlyRecording = true;
              setIsRecording(true);
              recorder = new MediaRecorder(stream);
              chunks = [];
              
              recorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunks.push(e.data);
              };
              
              recorder.onstop = async () => {
                const audioBlob = new Blob(chunks, { type: "audio/webm" });
                const formData = new FormData();
                formData.append("file", audioBlob, "voice.webm");
                
                try {
                  const res = await fetch(`${API_BASE}/api/v1/voice/transcribe`, {
                    method: "POST",
                    body: formData,
                  });
                  const data = await res.json();
                  if (data.text && data.text.trim().length > 0) {
                    onSendRef.current(data.text);
                  }
                } catch (e) {
                  console.error("VAD STT error", e);
                }
              };
              recorder.start();
            }
            silenceStart = 0; // Reset silence timer
          } else {
            if (isCurrentlyRecording) {
              if (silenceStart === 0) silenceStart = performance.now();
              else if (performance.now() - silenceStart > 1500) { // 1.5s of silence = stop talking
                isCurrentlyRecording = false;
                setIsRecording(false);
                recorder.stop();
              }
            }
          }
          animationFrame = requestAnimationFrame(checkVolume);
        };
        
        checkVolume();
      } catch (e) {
        console.error("VAD init failed", e);
      }
    };
    
    initVAD();
    
    return () => {
      if (animationFrame) cancelAnimationFrame(animationFrame);
      if (stream) stream.getTracks().forEach(t => t.stop());
      if (audioContext) audioContext.close();
      if (isCurrentlyRecording && recorder) {
        recorder.stop();
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      if (speaking) stopAudio();
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
          if (data.text && data.text.trim().length > 0) {
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

  const blobVariants: Variants = {
    idle: {
      scale: [1, 1.05, 1],
      borderRadius: ["40% 60% 70% 30%", "50% 50% 30% 70%", "40% 60% 70% 30%"],
      rotate: [0, 90, 180, 270, 360],
      transition: { duration: 8, repeat: Infinity, ease: "linear" }
    },
    recording: {
      scale: [1, 1.1, 1],
      borderRadius: ["30% 70% 50% 50%", "60% 40% 40% 60%", "30% 70% 50% 50%"],
      rotate: [0, -90, -180, -270, -360],
      transition: { duration: 2, repeat: Infinity, ease: "linear" }
    },
    thinking: {
      scale: [1, 1.2, 0.9, 1.1, 1],
      borderRadius: ["20% 80% 20% 80%", "80% 20% 80% 20%", "20% 80% 20% 80%"],
      rotate: [0, 360],
      transition: { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
    },
    speaking: {
      scale: [1.1, 1.3, 1.1, 1.2, 1.1],
      borderRadius: ["40% 60% 30% 70%", "60% 40% 70% 30%", "40% 60% 30% 70%"],
      rotate: [0, 45, 90, 135, 180],
      transition: { duration: 0.5, repeat: Infinity, ease: "easeInOut" }
    }
  };

  const currentState = speaking ? "speaking" : thinking ? "thinking" : isRecording ? "recording" : "idle";

  const getBlobColor = () => {
    if (speaking) return "bg-accent-500 shadow-[0_0_60px_rgba(6,182,212,0.8)]";
    if (thinking) return "bg-orange-500 shadow-[0_0_40px_rgba(249,115,22,0.6)]";
    if (isRecording) return "bg-red-500 shadow-[0_0_40px_rgba(239,68,68,0.6)]";
    return "bg-accent/80 shadow-[0_0_30px_rgba(0,255,204,0.4)]";
  };

  const lastLines = lines.slice(-3);

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-8 overflow-hidden relative">
      <div className="flex-1 flex items-center justify-center relative w-full max-w-2xl">
        <div className="absolute inset-0 flex items-center justify-center opacity-20 pointer-events-none">
          <div className="w-96 h-96 bg-accent rounded-full blur-[120px]" />
        </div>
        
        <motion.div
          variants={blobVariants}
          animate={currentState}
          className={`w-64 h-64 mix-blend-screen transition-colors duration-500 ${getBlobColor()}`}
        />

        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none gap-2">
          <h2 className="text-3xl font-black tracking-[0.2em] text-white mix-blend-overlay opacity-80">E.V.E.</h2>
          <span className="text-xs uppercase tracking-widest font-bold text-white/50">{currentState}</span>
        </div>
      </div>

      <div className="w-full max-w-3xl h-48 flex flex-col justify-end gap-2 mb-8">
        <AnimatePresence>
          {lastLines.map((line) => {
            const isUser = line.agent === "User";
            return (
              <motion.div
                key={line.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={`w-full flex ${isUser ? "justify-end" : "justify-start"}`}
              >
                <div className={`max-w-[80%] p-4 rounded-2xl backdrop-blur-md border ${isUser ? "bg-white/10 border-white/10 text-text rounded-tr-sm" : "bg-accent/10 border-accent/20 text-accent rounded-tl-sm shadow-[0_0_15px_rgba(0,255,204,0.1)]"}`}>
                  <p className="text-lg leading-relaxed">{line.text}</p>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
        {thinking && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="w-full flex justify-start">
             <div className="p-4 rounded-2xl bg-accent/5 border border-accent/10 rounded-tl-sm flex items-center gap-3">
               <Loader2 className="w-5 h-5 text-accent animate-spin" />
               <span className="text-accent/70 font-medium">Processing...</span>
             </div>
          </motion.div>
        )}
      </div>

      <div className="flex items-center gap-6">
        <button onClick={toggleRecording} className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${isRecording ? "bg-red-500 hover:bg-red-600 shadow-[0_0_30px_rgba(239,68,68,0.5)] scale-110" : "bg-white/5 border-2 border-white/10 hover:border-accent hover:bg-accent/10"}`}>
          {isRecording ? <Square className="w-8 h-8 text-white fill-white" /> : <Mic className="w-8 h-8 text-white" />}
        </button>
        {speaking && (
          <button onClick={stopAudio} className="px-6 py-3 rounded-full bg-white/5 hover:bg-red-500/20 text-white hover:text-red-400 transition-colors border border-white/10 hover:border-red-500/30 text-sm font-medium tracking-wide uppercase">Interrupt</button>
        )}
      </div>
    </div>
  );
}
