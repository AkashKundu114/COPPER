import React, { useEffect, useRef } from "react";

export type CompanionCoreState = "idle" | "listening" | "thinking" | "speaking" | "alert";

interface HolographicCoreProps {
  state: CompanionCoreState;
  audioLevel?: number; // 0.0 to 1.0 audio amplitude
  size?: number;
  className?: string;
  onInteractivityClick?: () => void;
}

export const HolographicCore: React.FC<HolographicCoreProps> = ({
  state = "idle",
  audioLevel = 0,
  size = 380,
  className = "",
  onInteractivityClick,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rotationRef = useRef({ yaw: 0, pitch: 0.2, roll: 0 });
  const isDraggingRef = useRef(false);
  const lastMouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let time = 0;

    // Generate fixed particle cloud for the inner neural core
    const PARTICLE_COUNT = 90;
    const particles = Array.from({ length: PARTICLE_COUNT }, () => {
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);
      const r = Math.cbrt(Math.random()) * 0.75; // inner sphere
      return {
        x: r * Math.sin(phi) * Math.cos(theta),
        y: r * Math.sin(phi) * Math.sin(theta),
        z: r * Math.cos(phi),
        speed: 0.2 + Math.random() * 0.8,
        pulseOffset: Math.random() * Math.PI * 2,
      };
    });

    const render = () => {
      time += 0.016;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const dpr = window.devicePixelRatio || 1;
      const w = canvas.width / dpr;
      const h = canvas.height / dpr;
      const cx = w / 2;
      const cy = h / 2;
      const radius = Math.min(w, h) * 0.38;

      // Auto-rotation speed depends on state
      let rotSpeed = 0.006;
      if (state === "thinking") rotSpeed = 0.035;
      else if (state === "speaking") rotSpeed = 0.015;
      else if (state === "listening") rotSpeed = 0.010;

      if (!isDraggingRef.current) {
        rotationRef.current.yaw += rotSpeed;
        rotationRef.current.pitch = 0.2 + Math.sin(time * 0.5) * 0.08;
      }

      const { yaw, pitch } = rotationRef.current;

      // Projection helper: 3D point (x,y,z in [-1, 1]) -> 2D (px, py, scale)
      const project = (x: number, y: number, z: number, scaleFactor: number = radius) => {
        // Rotate around Y (yaw)
        const cosY = Math.cos(yaw);
        const sinY = Math.sin(yaw);
        const x1 = x * cosY - z * sinY;
        const z1 = x * sinY + z * cosY;

        // Rotate around X (pitch)
        const cosP = Math.cos(pitch);
        const sinP = Math.sin(pitch);
        const y2 = y * cosP - z1 * sinP;
        const z2 = y * sinP + z1 * cosP;

        // Perspective projection
        const fov = 3.5;
        const scale = fov / (fov + z2);
        return {
          px: cx + x1 * scaleFactor * scale,
          py: cy + y2 * scaleFactor * scale,
          depth: z2,
          scale,
        };
      };

      // State palette definitions
      let primaryColor = "rgba(0, 240, 255, "; // Cyber Cyan
      let secondaryColor = "rgba(0, 255, 170, "; // Verdigris
      let coreGlow = "rgba(0, 240, 255, 0.25)";

      if (state === "thinking") {
        primaryColor = "rgba(255, 180, 0, "; // Amber Gold
        secondaryColor = "rgba(255, 110, 0, "; // Solar Orange
        coreGlow = "rgba(255, 170, 0, 0.35)";
      } else if (state === "speaking") {
        primaryColor = "rgba(70, 140, 255, "; // Deep Blue-Violet
        secondaryColor = "rgba(0, 240, 255, "; // Cyan highlights
        coreGlow = "rgba(70, 140, 255, 0.4)";
      } else if (state === "listening") {
        primaryColor = "rgba(0, 255, 204, "; // Vibrant Mint Cyan
        secondaryColor = "rgba(255, 255, 255, "; // Pure White highlights
        coreGlow = "rgba(0, 255, 204, 0.35)";
      } else if (state === "alert") {
        primaryColor = "rgba(255, 45, 85, "; // Tactical Crimson
        secondaryColor = "rgba(255, 150, 0, "; // Hazard Orange
        coreGlow = "rgba(255, 45, 85, 0.4)";
      }

      // Audio modulation factor
      const dynamicAudio = Math.min(1.0, Math.max(0, audioLevel));
      const pulseScale = 1.0 + dynamicAudio * 0.25 + Math.sin(time * 2.5) * 0.03;

      // ── Layer 1: Ambient Background Core Glow ──
      const glowGrad = ctx.createRadialGradient(cx, cy, 5, cx, cy, radius * 1.3 * pulseScale);
      glowGrad.addColorStop(0, coreGlow);
      glowGrad.addColorStop(0.5, primaryColor + "0.08)");
      glowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius * 1.4 * pulseScale, 0, Math.PI * 2);
      ctx.fill();

      // ── Layer 2: 3D Tactical Concentric Orbital Rings ──
      const draw3DRing = (
        ringRadius: number,
        tiltX: number,
        tiltZ: number,
        lineWidth: number,
        alpha: number,
        dashed: boolean = false,
        segments: number = 72
      ) => {
        ctx.beginPath();
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = primaryColor + `${alpha})`;
        if (dashed) ctx.setLineDash([4, 6]);
        else ctx.setLineDash([]);

        for (let i = 0; i <= segments; i++) {
          const angle = (i / segments) * Math.PI * 2;
          const rx = Math.cos(angle) * ringRadius;
          const rz = Math.sin(angle) * ringRadius;

          // Apply ring inclination tilt
          const x = rx;
          const y = rz * Math.sin(tiltX);
          const z = rz * Math.cos(tiltX) + rx * Math.sin(tiltZ);

          const pt = project(x, y, z);
          if (i === 0) ctx.moveTo(pt.px, pt.py);
          else ctx.lineTo(pt.px, pt.py);
        }
        ctx.stroke();
        ctx.setLineDash([]);
      };

      // Ring 1: Equatorial Gyro Ring with Audio reactive teeth
      draw3DRing(1.0 * pulseScale, 0.1, 0, 1.5, 0.7);
      draw3DRing(1.08 * pulseScale, -0.2, 0.3, 1.0, 0.4, true);

      // Ring 2: Polar Ring
      draw3DRing(0.92, Math.PI / 2 + 0.15, time * 0.5, 1.2, 0.6);

      // Ring 3: Oblique Ring
      draw3DRing(1.22 * pulseScale, 0.7, -time * 0.4, 0.8, 0.3, true);

      // ── Layer 3: Audio Frequency Radial Equalizer Blades (Surrounding Core) ──
      const BLADE_COUNT = 48;
      ctx.lineWidth = 2;
      for (let i = 0; i < BLADE_COUNT; i++) {
        const theta = (i / BLADE_COUNT) * Math.PI * 2 + time * 0.3;
        const wave = Math.sin(theta * 6 + time * 5) * 0.5 + 0.5;
        const bladeHeight = (0.15 + wave * 0.35 * (0.3 + dynamicAudio * 1.5)) * pulseScale;

        const innerR = 1.02;
        const outerR = innerR + bladeHeight;

        const p1 = project(Math.cos(theta) * innerR, Math.sin(theta) * innerR, 0);
        const p2 = project(Math.cos(theta) * outerR, Math.sin(theta) * outerR, 0);

        ctx.strokeStyle = i % 2 === 0 ? primaryColor + "0.75)" : secondaryColor + "0.6)";
        ctx.beginPath();
        ctx.moveTo(p1.px, p1.py);
        ctx.lineTo(p2.px, p2.py);
        ctx.stroke();
      }

      // ── Layer 4: Internal Neural Particle Field ──
      particles.forEach((p) => {
        // Subtle orbital vortex motion inside core
        const angle = time * p.speed * 0.8;
        const cosA = Math.cos(angle);
        const sinA = Math.sin(angle);
        const px = p.x * cosA - p.y * sinA;
        const py = p.x * sinA + p.y * cosA;
        const pz = p.z;

        const pt = project(px, py, pz, radius * 0.75 * pulseScale);
        const pAlpha = 0.3 + 0.7 * Math.sin(time * 3 + p.pulseOffset);

        ctx.fillStyle = secondaryColor + `${pAlpha})`;
        ctx.beginPath();
        ctx.arc(pt.px, pt.py, 1.6 * pt.scale, 0, Math.PI * 2);
        ctx.fill();
      });

      // ── Layer 5: Glowing Holographic Core Nucleus ──
      const nGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius * 0.45 * pulseScale);
      nGrad.addColorStop(0, "rgba(255, 255, 255, 0.9)");
      nGrad.addColorStop(0.3, primaryColor + "0.8)");
      nGrad.addColorStop(0.8, secondaryColor + "0.25)");
      nGrad.addColorStop(1, "rgba(0, 0, 0, 0)");

      ctx.fillStyle = nGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius * 0.45 * pulseScale, 0, Math.PI * 2);
      ctx.fill();

      // ── Layer 6: Cybernetic Target Brackets & Compass Marks ──
      const bracketRadius = radius * 1.35;
      const bLen = 14;
      ctx.strokeStyle = primaryColor + "0.5)";
      ctx.lineWidth = 1.5;

      // Top-Left bracket
      ctx.beginPath();
      ctx.moveTo(cx - bracketRadius, cy - bracketRadius + bLen);
      ctx.lineTo(cx - bracketRadius, cy - bracketRadius);
      ctx.lineTo(cx - bracketRadius + bLen, cy - bracketRadius);
      ctx.stroke();

      // Top-Right bracket
      ctx.beginPath();
      ctx.moveTo(cx + bracketRadius - bLen, cy - bracketRadius);
      ctx.lineTo(cx + bracketRadius, cy - bracketRadius);
      ctx.lineTo(cx + bracketRadius, cy - bracketRadius + bLen);
      ctx.stroke();

      // Bottom-Left bracket
      ctx.beginPath();
      ctx.moveTo(cx - bracketRadius, cy + bracketRadius - bLen);
      ctx.lineTo(cx - bracketRadius, cy + bracketRadius);
      ctx.lineTo(cx - bracketRadius + bLen, cy + bracketRadius);
      ctx.stroke();

      // Bottom-Right bracket
      ctx.beginPath();
      ctx.moveTo(cx + bracketRadius - bLen, cy + bracketRadius);
      ctx.lineTo(cx + bracketRadius, cy + bracketRadius);
      ctx.lineTo(cx + bracketRadius, cy + bracketRadius - bLen);
      ctx.stroke();

      // State text below nucleus
      ctx.fillStyle = primaryColor + "0.9)";
      ctx.font = "bold 10px monospace";
      ctx.textAlign = "center";
      ctx.fillText(state.toUpperCase(), cx, cy + radius * 1.55);

      animationId = requestAnimationFrame(render);
    };

    const handleResize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = size * dpr;
      canvas.height = size * dpr;
      ctx.scale(dpr, dpr);
    };

    handleResize();
    render();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [state, audioLevel, size]);

  // Drag interaction to manually rotate 3D hologram
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMouseRef.current.x;
    const dy = e.clientY - lastMouseRef.current.y;
    rotationRef.current.yaw += dx * 0.01;
    rotationRef.current.pitch += dy * 0.01;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  return (
    <div
      className={`relative flex items-center justify-center cursor-grab active:cursor-grabbing select-none ${className}`}
      style={{ width: size, height: size }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onClick={onInteractivityClick}
    >
      <canvas
        ref={canvasRef}
        style={{ width: size, height: size }}
        className="block"
      />
    </div>
  );
};
