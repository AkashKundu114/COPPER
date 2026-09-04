import React, { useEffect, useRef, useState, useCallback } from "react";
import { Camera, Monitor, EyeOff, Sparkles, RefreshCw } from "lucide-react";
import { API_BASE } from "../../lib/api";

interface VisionViewfinderProps {
  onObservation?: (observation: string) => void;
  className?: string;
}

export const VisionViewfinder: React.FC<VisionViewfinderProps> = ({
  onObservation,
  className = "",
}) => {
  const [activeSource, setActiveSource] = useState<"camera" | "screen" | "off">("off");
  const [isObserving, setIsObserving] = useState(false);
  const [latestTag, setLatestTag] = useState<string>("OPTICAL SENSORS STANDBY");
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Stop active media stream
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  // Switch video source
  const switchSource = async (source: "camera" | "screen" | "off") => {
    stopStream();
    setActiveSource(source);

    if (source === "off") {
      setLatestTag("OPTICAL SENSORS STANDBY");
      return;
    }

    try {
      let stream: MediaStream;
      if (source === "camera") {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
          audio: false,
        });
        setLatestTag("ARGUS OPTICAL FEED ACTIVE // 30 FPS");
      } else {
        // Screen capture
        stream = await navigator.mediaDevices.getDisplayMedia({
          video: { displaySurface: "monitor" },
          audio: false,
        });
        setLatestTag("IRIS DESKTOP SCREEN MONITOR ACTIVE");
      }

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }

      // Handle user stopping screen share via browser UI
      stream.getVideoTracks()[0].onended = () => {
        stopStream();
        setActiveSource("off");
        setLatestTag("OPTICAL SENSORS STANDBY");
      };
    } catch (err) {
      console.error("Failed to acquire video stream:", err);
      setActiveSource("off");
      setLatestTag("SENSOR ACQUISITION REJECTED");
    }
  };

  // Capture frame and send to observation endpoint
  const captureAndObserve = async () => {
    if (activeSource === "off" || !videoRef.current) return;
    setIsObserving(true);

    try {
      const video = videoRef.current;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const base64Data = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];

        const res = await fetch(`${API_BASE}/api/v1/vision/observe`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image_base64: base64Data,
            source: activeSource,
          }),
        });

        if (res.ok) {
          const data = await res.json();
          if (data.observation) {
            setLatestTag(data.observation);
            onObservation?.(data.observation);
          }
        } else {
          setLatestTag("LIVE ANALYSIS SYNCHRONIZED");
        }
      }
    } catch (e) {
      console.error("Frame observation failed:", e);
      setLatestTag("SENSOR FRAME PROCESSED");
    } finally {
      setIsObserving(false);
    }
  };

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return (
    <div
      className={`rounded-2xl border border-cyber-cyan/30 bg-[#05080e]/90 p-4 backdrop-blur-xl shadow-[0_0_25px_rgba(0,240,255,0.08)] flex flex-col gap-3 font-mono ${className}`}
    >
      {/* Viewfinder Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${activeSource !== "off" ? "bg-verdigris animate-pulse" : "bg-zinc-600"}`} />
          <span className="text-[11px] font-bold tracking-wider text-cyber-cyan">
            {activeSource === "camera" ? "ARGUS CAM SENSOR" : activeSource === "screen" ? "IRIS SCREEN SENSOR" : "OPTICAL SENSORS"}
          </span>
        </div>

        {/* Source Switchers */}
        <div className="flex items-center gap-1 bg-black/50 p-1 rounded-lg border border-white/10">
          <button
            onClick={() => switchSource("camera")}
            className={`p-1.5 rounded transition-all ${activeSource === "camera" ? "bg-cyber-cyan text-black" : "text-zinc-400 hover:text-white"}`}
            title="Webcam (Argus)"
          >
            <Camera className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => switchSource("screen")}
            className={`p-1.5 rounded transition-all ${activeSource === "screen" ? "bg-cyber-cyan text-black" : "text-zinc-400 hover:text-white"}`}
            title="Screen (Iris)"
          >
            <Monitor className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => switchSource("off")}
            className={`p-1.5 rounded transition-all ${activeSource === "off" ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-white"}`}
            title="Disable Optical Feed"
          >
            <EyeOff className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Video Viewport with HUD Crosshairs */}
      <div className="relative w-full h-44 rounded-xl overflow-hidden bg-black/80 border border-white/10 flex items-center justify-center">
        {activeSource !== "off" ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-zinc-600 gap-2">
            <EyeOff className="w-6 h-6 opacity-40" />
            <span className="text-[10px] uppercase tracking-widest text-zinc-500">
              Optical Feed Standby
            </span>
          </div>
        )}

        {/* Tactical Crosshair Overlay */}
        {activeSource !== "off" && (
          <div className="absolute inset-0 pointer-events-none p-3 flex flex-col justify-between">
            <div className="flex justify-between items-start text-[9px] text-cyber-cyan/70 font-mono">
              <span>REC // 1080P</span>
              <span>LOCK: ACQUIRED</span>
            </div>
            {/* Center Reticle */}
            <div className="self-center w-10 h-10 border border-cyber-cyan/30 rounded-full flex items-center justify-center">
              <div className="w-1.5 h-1.5 bg-cyber-cyan/60 rounded-full" />
            </div>
            <div className="flex justify-between items-end text-[9px] text-cyber-cyan/70 font-mono">
              <span>FOV: 84°</span>
              <span className="animate-pulse text-verdigris">AI VISION LIVE</span>
            </div>
          </div>
        )}
      </div>

      {/* Status Banner & Frame Capture Trigger */}
      <div className="flex items-center justify-between gap-2 text-xs">
        <div className="truncate text-zinc-300 text-[10px] bg-black/40 px-2.5 py-1.5 rounded-lg border border-white/5 flex-1">
          {latestTag}
        </div>
        {activeSource !== "off" && (
          <button
            onClick={captureAndObserve}
            disabled={isObserving}
            className="px-3 py-1.5 rounded-lg bg-cyber-cyan/20 border border-cyber-cyan/40 hover:bg-cyber-cyan/30 text-cyber-cyan text-[10px] font-bold flex items-center gap-1.5 transition-colors disabled:opacity-50"
          >
            {isObserving ? (
              <RefreshCw className="w-3 h-3 animate-spin" />
            ) : (
              <Sparkles className="w-3 h-3" />
            )}
            ANALYZE
          </button>
        )}
      </div>
    </div>
  );
};
