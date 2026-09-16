import React, { useState, useRef, useCallback, useEffect } from "react";
import { soundFX } from "../../lib/soundFX";

interface TactileDialProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit?: string;
  size?: number;
  onChange: (val: number) => void;
  formatValue?: (val: number) => string;
}

export const TactileDial: React.FC<TactileDialProps> = ({
  label,
  value,
  min,
  max,
  step = 1,
  unit = "",
  size = 90,
  onChange,
  formatValue,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const dragStartYRef = useRef<number>(0);
  const startValRef = useRef<number>(value);
  const lastStepTickRef = useRef<number>(value);

  // Map value to angle (-135 deg to +135 deg -> 270 deg total range)
  const range = max - min;
  const progress = Math.max(0, Math.min(1, (value - min) / (range || 1)));
  const angle = -135 + progress * 270;

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    dragStartYRef.current = e.clientY;
    startValRef.current = value;
    lastStepTickRef.current = value;
    soundFX.play("click");
  };

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaY = dragStartYRef.current - e.clientY;
      const sensitivity = (max - min) / 120; // 120px drag across full range
      let nextVal = startValRef.current + deltaY * sensitivity;

      // Snap to step
      if (step > 0) {
        nextVal = Math.round(nextVal / step) * step;
      }
      nextVal = Math.max(min, Math.min(max, nextVal));

      if (nextVal !== lastStepTickRef.current) {
        soundFX.play("tab");
        lastStepTickRef.current = nextVal;
      }
      onChange(nextVal);
    },
    [isDragging, min, max, step, onChange]
  );

  const handleMouseUp = useCallback(() => {
    if (isDragging) {
      setIsDragging(false);
    }
  }, [isDragging]);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const displayVal = formatValue ? formatValue(value) : `${value}${unit}`;

  // SVG arc calculation
  const strokeWidth = 5;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  // 270 degrees is 0.75 of circle
  const arcLength = circumference * 0.75;
  const strokeDashoffset = arcLength * (1 - progress);

  return (
    <div className="flex flex-col items-center select-none group">
      <div
        className={`relative flex items-center justify-center cursor-ns-resize rounded-full transition-shadow duration-200 ${
          isDragging
            ? "shadow-[0_0_20px_rgba(201,124,76,0.35)] scale-105"
            : "hover:shadow-[0_0_12px_rgba(246,230,234,0.12)]"
        }`}
        style={{ width: size, height: size }}
        onMouseDown={handleMouseDown}
        role="slider"
        aria-valuenow={value}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-label={label}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "ArrowUp" || e.key === "ArrowRight") {
            const next = Math.min(max, value + step);
            soundFX.play("tab");
            onChange(next);
          } else if (e.key === "ArrowDown" || e.key === "ArrowLeft") {
            const next = Math.max(min, value - step);
            soundFX.play("tab");
            onChange(next);
          }
        }}
      >
        {/* Background track SVG */}
        <svg
          width={size}
          height={size}
          className="absolute inset-0 -rotate-[225deg] pointer-events-none"
        >
          {/* Rail Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="round"
          />
          {/* Active Value Glow Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#C97C4C"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-[stroke-dashoffset] duration-75"
          />
        </svg>

        {/* Center Metallic / Glass Knob */}
        <div
          className="relative rounded-full flex items-center justify-center border border-white/10 shadow-inner transition-transform duration-75"
          style={{
            width: size - 26,
            height: size - 26,
            background:
              "radial-gradient(circle at 35% 35%, #2A121A 0%, #16080D 80%)",
            transform: `rotate(${angle}deg)`,
          }}
        >
          {/* Rotary Notch Indicator */}
          <div className="absolute top-1.5 w-1.5 h-1.5 rounded-full bg-accent shadow-[0_0_6px_#C97C4C]" />
          <div className="w-1 h-3 -mt-2 rounded-full bg-accent/80" />
        </div>
      </div>

      {/* Numerical Display & Label (inspired by dialkit.dev & typeface.fyi) */}
      <div className="mt-2 text-center">
        <span className="font-mono text-xs font-bold text-white tabular-nums tracking-tight">
          {displayVal}
        </span>
        <span className="block text-[10px] font-mono uppercase tracking-wider text-zinc-400 mt-0.5">
          {label}
        </span>
      </div>
    </div>
  );
};
