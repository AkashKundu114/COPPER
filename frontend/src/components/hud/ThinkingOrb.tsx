import React, { useEffect, useRef, useState, useCallback } from "react";
import { soundFX } from "../../lib/soundFX";

export type CompanionCoreState = "idle" | "listening" | "thinking" | "speaking" | "alert";

interface ThinkingOrbProps {
  state?: CompanionCoreState;
  audioLevel?: number; 
  size?: number;
  className?: string;
  onInteractivityClick?: () => void;
}

export const ThinkingOrb: React.FC<ThinkingOrbProps> = ({
  state = "idle",
  audioLevel = 0,
  size = 360,
  className = "",
  onInteractivityClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const clickRipplesRef = useRef<Array<{ radius: number; maxRadius: number; opacity: number; speed: number }>>([]);
  const rotationAngleRef = useRef(0);
  const smoothAudioRef = useRef(0);


  const handleClick = useCallback(() => {
    soundFX.play("click");
    clickRipplesRef.current.push({
      radius: size * 0.15,
      maxRadius: size * 0.48,
      opacity: 0.9,
      speed: 3.5,
    });
    if (onInteractivityClick) {
      onInteractivityClick();
    }
  }, [size, onInteractivityClick]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let time = 0;


    const FILAMENT_COUNT = 8;
    const filaments = Array.from({ length: FILAMENT_COUNT }, (_, i) => ({
      baseAngle: (i * 2 * Math.PI) / FILAMENT_COUNT,
      phase: i * 0.78,
      speed: 0.8 + (i % 3) * 0.4,
      lengthRatio: 0.65 + (i % 2) * 0.25,
    }));

    const render = () => {
      time += 0.02;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const dpr = window.devicePixelRatio || 1;
      const w = canvas.width / dpr;
      const h = canvas.height / dpr;
      const cx = w / 2;
      const cy = h / 2;
      const baseRadius = Math.min(w, h) * 0.28;


      smoothAudioRef.current += (audioLevel - smoothAudioRef.current) * 0.15;
      const curAudio = smoothAudioRef.current;


      let spinSpeed = 0.008;
      if (state === "thinking") spinSpeed = 0.032;
      else if (state === "speaking") spinSpeed = 0.018;
      else if (state === "listening") spinSpeed = 0.014;
      rotationAngleRef.current += spinSpeed;
      const rot = rotationAngleRef.current;


      let primaryColor = "rgba(201, 124, 76, "; 
      let secondaryColor = "rgba(246, 230, 234, "; 
      let coreGlow = "rgba(255, 140, 90, "; 
      let auraColor = "rgba(100, 25, 45, "; 

      if (state === "listening") {
        primaryColor = "rgba(6, 182, 212, "; 
        secondaryColor = "rgba(95, 168, 143, ";
        coreGlow = "rgba(125, 240, 220, ";
        auraColor = "rgba(10, 45, 55, ";
      } else if (state === "thinking") {
        primaryColor = "rgba(168, 85, 247, "; 
        secondaryColor = "rgba(244, 114, 182, ";
        coreGlow = "rgba(216, 180, 254, ";
        auraColor = "rgba(45, 15, 65, ";
      } else if (state === "speaking") {
        primaryColor = "rgba(251, 146, 60, "; 
        secondaryColor = "rgba(254, 240, 138, ";
        coreGlow = "rgba(255, 215, 0, ";
        auraColor = "rgba(70, 30, 15, ";
      } else if (state === "alert") {
        primaryColor = "rgba(239, 68, 68, "; 
        secondaryColor = "rgba(252, 165, 165, ";
        coreGlow = "rgba(254, 202, 202, ";
        auraColor = "rgba(60, 10, 15, ";
      }


      const auraBreath = Math.sin(time * 1.5) * 0.08 + (state === "speaking" ? curAudio * 0.35 : 0);
      const auraGrad = ctx.createRadialGradient(
        cx,
        cy,
        baseRadius * 0.4,
        cx,
        cy,
        baseRadius * (1.8 + auraBreath)
      );
      auraGrad.addColorStop(0, auraColor + "0.65)");
      auraGrad.addColorStop(0.5, auraColor + "0.22)");
      auraGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = auraGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, baseRadius * (1.8 + auraBreath), 0, Math.PI * 2);
      ctx.fill();


      if (state === "listening" || state === "speaking" || curAudio > 0.05) {
        const ringCount = state === "listening" ? 3 : 4;
        for (let r = 1; r <= ringCount; r++) {
          const ringPhase = (time * 1.8 + r * 0.8) % (Math.PI * 2);
          const ringProgress = ringPhase / (Math.PI * 2);
          const ringRad = baseRadius * (1.1 + ringProgress * 0.65 + curAudio * 0.45);
          const ringAlpha = (1 - ringProgress) * (0.35 + curAudio * 0.5);

          ctx.beginPath();
          ctx.strokeStyle = primaryColor + ringAlpha + ")";
          ctx.lineWidth = 1.2;
          ctx.setLineDash([4, 6]);
          ctx.arc(cx, cy, ringRad, 0, Math.PI * 2);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      }


      ctx.save();
      ctx.translate(cx, cy);

      const dynamicRadius = baseRadius * (1 + Math.sin(time * 2) * 0.04 + curAudio * 0.25);


      filaments.forEach((f) => {
        const currentAngle = f.baseAngle + rot * f.speed;
        const pulse = Math.sin(time * 3 + f.phase) * 0.15;
        const petRadius = dynamicRadius * (f.lengthRatio + pulse);

        const px = Math.cos(currentAngle) * petRadius;
        const py = Math.sin(currentAngle) * petRadius;

        const filamentGrad = ctx.createRadialGradient(px * 0.5, py * 0.5, 0, px, py, dynamicRadius * 0.9);
        filamentGrad.addColorStop(0, primaryColor + "0.45)");
        filamentGrad.addColorStop(0.6, secondaryColor + "0.25)");
        filamentGrad.addColorStop(1, "rgba(0, 0, 0, 0)");

        ctx.fillStyle = filamentGrad;
        ctx.beginPath();
        ctx.arc(px * 0.35, py * 0.35, dynamicRadius * 0.72, 0, Math.PI * 2);
        ctx.fill();
      });


      const bodyGrad = ctx.createRadialGradient(
        -dynamicRadius * 0.25,
        -dynamicRadius * 0.25,
        dynamicRadius * 0.05,
        0,
        0,
        dynamicRadius
      );
      bodyGrad.addColorStop(0, coreGlow + "0.9)");
      bodyGrad.addColorStop(0.35, primaryColor + "0.75)");
      bodyGrad.addColorStop(0.75, secondaryColor + "0.35)");
      bodyGrad.addColorStop(1, "rgba(22, 8, 13, 0.85)");

      ctx.fillStyle = bodyGrad;
      ctx.beginPath();
      ctx.arc(0, 0, dynamicRadius, 0, Math.PI * 2);
      ctx.fill();


      const ringTilt = Math.sin(time) * 0.35;
      ctx.save();
      ctx.rotate(rot * 0.8);
      ctx.scale(1, 0.38 + ringTilt * 0.1);
      ctx.beginPath();
      ctx.strokeStyle = secondaryColor + "0.45)";
      ctx.lineWidth = 1.5;
      ctx.arc(0, 0, dynamicRadius * 1.25, 0, Math.PI * 2);
      ctx.stroke();


      const sparkX = Math.cos(rot * 2) * dynamicRadius * 1.25;
      const sparkY = Math.sin(rot * 2) * dynamicRadius * 1.25;
      ctx.beginPath();
      ctx.fillStyle = coreGlow + "1)";
      ctx.shadowColor = primaryColor + "1)";
      ctx.shadowBlur = 10;
      ctx.arc(sparkX, sparkY, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.restore();


      ctx.save();
      ctx.beginPath();
      ctx.ellipse(
        -dynamicRadius * 0.28,
        -dynamicRadius * 0.32,
        dynamicRadius * 0.38,
        dynamicRadius * 0.18,
        -Math.PI / 4,
        0,
        Math.PI * 2
      );
      const specGrad = ctx.createLinearGradient(
        -dynamicRadius * 0.45,
        -dynamicRadius * 0.45,
        -dynamicRadius * 0.1,
        -dynamicRadius * 0.1
      );
      specGrad.addColorStop(0, "rgba(255, 255, 255, 0.65)");
      specGrad.addColorStop(0.5, "rgba(255, 255, 255, 0.2)");
      specGrad.addColorStop(1, "rgba(255, 255, 255, 0)");
      ctx.fillStyle = specGrad;
      ctx.fill();
      ctx.restore();

      ctx.restore(); 


      clickRipplesRef.current = clickRipplesRef.current.filter((ripple) => {
        ripple.radius += ripple.speed;
        ripple.opacity -= 0.025;

        if (ripple.opacity > 0) {
          ctx.beginPath();
          ctx.strokeStyle = primaryColor + ripple.opacity + ")";
          ctx.lineWidth = 1.8;
          ctx.arc(cx, cy, ripple.radius, 0, Math.PI * 2);
          ctx.stroke();
          return true;
        }
        return false;
      });

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [state, audioLevel, size]);

  return (
    <div
      className={`relative flex items-center justify-center select-none cursor-pointer transition-transform duration-200 ${
        isHovered ? "scale-[1.02]" : "scale-100"
      } ${className}`}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role="button"
      tabIndex={0}
      aria-label={`Companion Thinking Orb, current state: ${state}`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          handleClick();
        }
      }}
    >
      <canvas
        ref={canvasRef}
        width={size * (typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1)}
        height={size * (typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1)}
        style={{ width: `${size}px`, height: `${size}px` }}
        className="touch-none"
      />

      <div className="absolute -bottom-1 flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/40 backdrop-blur-md border border-white/10 shadow-lg text-[10px] font-mono tracking-wider uppercase text-zinc-300 pointer-events-none">
        <span
          className={`w-1.5 h-1.5 rounded-full animate-pulse ${
            state === "listening"
              ? "bg-cyan-400"
              : state === "thinking"
              ? "bg-purple-400"
              : state === "speaking"
              ? "bg-accent"
              : "bg-zinc-400"
          }`}
        />
        <span>{state}</span>
      </div>
    </div>
  );
};
