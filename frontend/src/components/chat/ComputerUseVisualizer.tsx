import React, { useState, useRef } from "react";
import {
  Monitor,
  MousePointer,
  Keyboard,
  Compass,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Eye,
} from "lucide-react";

export interface ComputerUseStep {
  step: number;
  max_steps: number;
  action: string;
  action_details?: Record<string, any>;
  thought?: string;
  screenshot_b64?: string;
  status: "running" | "completed" | "blocked" | "error";
  summary?: string;
  window_title?: string;
  coordinates?: { x: number; y: number } | null;
  timestamp?: number;
}

interface ComputerUseVisualizerProps {
  steps: ComputerUseStep[];
  isLive?: boolean;
  className?: string;
}

export const ComputerUseVisualizer: React.FC<ComputerUseVisualizerProps> = ({
  steps,
  isLive = false,
  className = "",
}) => {
  const [selectedStepIndex, setSelectedStepIndex] = useState<number | null>(null);
  const [expanded, setExpanded] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const [naturalDim, setNaturalDim] = useState<{ w: number; h: number } | null>(null);

  if (!steps || steps.length === 0) return null;

  // View either the user-selected step or the latest step
  const currentIndex =
    selectedStepIndex !== null && selectedStepIndex >= 0 && selectedStepIndex < steps.length
      ? selectedStepIndex
      : steps.length - 1;

  const currentStep = steps[currentIndex];
  const isLastStep = currentIndex === steps.length - 1;

  const getActionIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case "click":
      case "double_click":
        return <MousePointer className="w-3.5 h-3.5 text-verdigris-400" />;
      case "type_text":
      case "hotkey":
        return <Keyboard className="w-3.5 h-3.5 text-amber-400" />;
      case "scroll":
        return <Compass className="w-3.5 h-3.5 text-cyan-400" />;
      case "wait":
        return <Clock className="w-3.5 h-3.5 text-zinc-400" />;
      case "done":
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      case "blocked":
        return <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />;
      default:
        return <Eye className="w-3.5 h-3.5 text-zinc-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return (
          <span className="px-2 py-0.5 text-[11px] font-mono bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 rounded-full flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Done
          </span>
        );
      case "blocked":
        return (
          <span className="px-2 py-0.5 text-[11px] font-mono bg-rose-950/60 text-rose-400 border border-rose-800/40 rounded-full flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> Blocked
          </span>
        );
      case "error":
        return (
          <span className="px-2 py-0.5 text-[11px] font-mono bg-red-950/60 text-red-400 border border-red-800/40 rounded-full flex items-center gap-1">
            Error
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-[11px] font-mono bg-cyan-950/60 text-cyan-400 border border-cyan-800/40 rounded-full flex items-center gap-1 animate-pulse">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" /> Active
          </span>
        );
    }
  };

  // Crosshair overlay coordinates calculation
  let targetCoordPercent: { left: string; top: string } | null = null;
  if (currentStep.coordinates && naturalDim && naturalDim.w > 0 && naturalDim.h > 0) {
    const pX = (currentStep.coordinates.x / naturalDim.w) * 100;
    const pY = (currentStep.coordinates.y / naturalDim.h) * 100;
    targetCoordPercent = {
      left: `${Math.max(0, Math.min(100, pX))}%`,
      top: `${Math.max(0, Math.min(100, pY))}%`,
    };
  }

  return (
    <div
      className={`w-full rounded-2xl border border-border/80 bg-zinc-950/70 backdrop-blur-md overflow-hidden shadow-xl transition-all duration-300 my-4 ${className}`}
    >
      {/* Visualizer Top Bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border/50 bg-white/[0.02]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-zinc-800/80 border border-zinc-700/60 flex items-center justify-center text-zinc-300">
            <Monitor className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold tracking-wide text-zinc-200">
                IRIS • Computer Use
              </span>
              {getStatusBadge(currentStep.status)}
            </div>
            <p className="text-[11px] text-zinc-400 truncate max-w-[280px] sm:max-w-md">
              {currentStep.window_title ? `Window: ${currentStep.window_title}` : "Desktop Interface"}
            </p>
          </div>
        </div>

        {/* Step Navigation Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 bg-zinc-900/90 border border-zinc-800 rounded-lg px-2 py-1 text-xs font-mono text-zinc-300">
            <button
              onClick={() => setSelectedStepIndex(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0}
              className="hover:text-white disabled:opacity-30 p-0.5"
              title="Previous Step"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="px-1 text-[11px]">
              {currentStep.step} / {currentStep.max_steps || steps.length}
            </span>
            <button
              onClick={() => setSelectedStepIndex(Math.min(steps.length - 1, currentIndex + 1))}
              disabled={currentIndex === steps.length - 1}
              className="hover:text-white disabled:opacity-30 p-0.5"
              title="Next Step"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 bg-zinc-900/60 border border-zinc-800 transition-colors"
            title={expanded ? "Collapse Screen" : "Expand Screen"}
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Screen Viewport with Action Overlay */}
      <div className="relative bg-black/90 flex items-center justify-center overflow-hidden border-b border-border/40">
        {currentStep.screenshot_b64 ? (
          <div className={`relative ${expanded ? "max-h-[700px]" : "max-h-[380px]"} w-full flex items-center justify-center overflow-hidden`}>
            <img
              ref={imgRef}
              src={`data:image/png;base64,${currentStep.screenshot_b64}`}
              alt={`Screen capture step ${currentStep.step}`}
              onLoad={(e) => {
                const target = e.currentTarget;
                setNaturalDim({ w: target.naturalWidth, h: target.naturalHeight });
              }}
              className="max-w-full max-h-full object-contain select-none"
            />

            {/* Click / Target Coordinates Crosshair Overlay */}
            {targetCoordPercent && (
              <div
                style={{
                  left: targetCoordPercent.left,
                  top: targetCoordPercent.top,
                }}
                className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-none z-10 flex items-center justify-center"
              >
                {/* Outer pulsing ring */}
                <span className="absolute w-8 h-8 rounded-full border-2 border-cyan-400/80 animate-ping" />
                {/* Inner target circle */}
                <span className="w-5 h-5 rounded-full border-2 border-white bg-cyan-500/40 backdrop-blur-xs flex items-center justify-center shadow-lg">
                  <span className="w-1.5 h-1.5 rounded-full bg-white" />
                </span>
                {/* Coordinate label tag */}
                <div className="absolute top-6 px-1.5 py-0.5 rounded bg-black/80 border border-cyan-500/50 text-[10px] font-mono text-cyan-300 whitespace-nowrap shadow-md">
                  ({currentStep.coordinates?.x}, {currentStep.coordinates?.y})
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="py-16 text-center text-zinc-500 flex flex-col items-center gap-2">
            <Monitor className="w-8 h-8 opacity-40 animate-pulse" />
            <span className="text-xs">Awaiting screen capture...</span>
          </div>
        )}

        {/* Live Badge for latest active step */}
        {isLive && isLastStep && currentStep.status === "running" && (
          <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/50 text-cyan-300 text-[10px] font-mono font-medium tracking-wider flex items-center gap-1.5 shadow-lg backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            LIVE SCREEN
          </div>
        )}
      </div>

      {/* Step Details, Thought & Action Footer */}
      <div className="p-4 space-y-3 bg-zinc-900/40">
        {/* Action Badge */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-800/80 border border-zinc-700/60 text-xs font-mono text-zinc-200">
              {getActionIcon(currentStep.action)}
              <span className="font-semibold uppercase">{currentStep.action}</span>
              {currentStep.action_details && (
                <span className="text-zinc-400 text-[11px] ml-1">
                  {currentStep.action === "click" && currentStep.coordinates
                    ? `[${currentStep.coordinates.x}, ${currentStep.coordinates.y}]`
                    : currentStep.action === "type_text"
                    ? `"${currentStep.action_details.text}"`
                    : currentStep.action === "hotkey"
                    ? `[${currentStep.action_details.keys?.join(" + ")}]`
                    : currentStep.action === "scroll"
                    ? `${currentStep.action_details.direction} (${currentStep.action_details.amount})`
                    : ""}
                </span>
              )}
            </div>
          </div>

          <span className="text-[11px] text-zinc-500 font-mono">
            Step {currentIndex + 1} of {steps.length} total
          </span>
        </div>

        {/* Model Observation & Reasoning */}
        {currentStep.thought && (
          <div className="p-2.5 rounded-xl bg-black/40 border border-zinc-800/60 text-xs text-zinc-300 leading-relaxed font-sans font-light">
            <span className="text-zinc-400 font-mono text-[11px] block mb-1 font-medium">
              Observation & Decision:
            </span>
            {currentStep.thought}
          </div>
        )}

        {/* Step Summary / Result */}
        {currentStep.summary && currentStep.summary !== currentStep.thought && (
          <p className="text-xs text-zinc-400 font-mono italic">
            {currentStep.summary}
          </p>
        )}

        {/* Step Thumbnail Filmstrip */}
        {steps.length > 1 && (
          <div className="flex items-center gap-2 pt-2 overflow-x-auto pb-1 custom-scrollbar">
            {steps.map((s, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedStepIndex(idx)}
                className={`relative shrink-0 rounded-lg overflow-hidden border transition-all ${
                  idx === currentIndex
                    ? "border-cyan-400 ring-2 ring-cyan-500/20 shadow-md scale-105"
                    : "border-zinc-800 hover:border-zinc-700 opacity-60 hover:opacity-100"
                }`}
              >
                {s.screenshot_b64 ? (
                  <img
                    src={`data:image/png;base64,${s.screenshot_b64}`}
                    alt={`Step ${s.step}`}
                    className="w-16 h-10 object-cover"
                  />
                ) : (
                  <div className="w-16 h-10 bg-zinc-900 flex items-center justify-center text-[10px] text-zinc-600 font-mono">
                    #{s.step}
                  </div>
                )}
                <div className="absolute bottom-0 inset-x-0 bg-black/70 px-1 py-0.5 text-[9px] font-mono text-center text-zinc-300 truncate">
                  {s.action}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
