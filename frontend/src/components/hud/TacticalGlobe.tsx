import React, { useEffect, useRef, useState } from "react";
import {
  Radio,
  Target,
  RotateCcw,
} from "lucide-react";

interface AgentNode {
  id: string;
  name: string;
  lat: number;
  lon: number;
  tier: string;
  status: "active" | "standby" | "locked";
  threat: string;
}

const AGENT_NODES: AgentNode[] = [
  { id: "guardian", name: "Guardian L2 Core", lat: 37.77, lon: -122.41, tier: "Safety", status: "active", threat: "0.0%" },
  { id: "router", name: "Master Intent Router", lat: 40.71, lon: -74.0, tier: "Dispatcher", status: "active", threat: "0.0%" },
  { id: "deepseek", name: "DeepSeek-R1 Reasoner", lat: 51.5, lon: -0.12, tier: "Cognitive", status: "active", threat: "0.0%" },
  { id: "coder", name: "Qwen-Coder Synthesizer", lat: 35.67, lon: 139.65, tier: "Developer", status: "active", threat: "0.0%" },
  { id: "memory", name: "ChromaDB Epistemic Mesh", lat: 1.35, lon: 103.81, tier: "VectorDB", status: "active", threat: "0.0%" },
  { id: "firewall", name: "Air-Gap Data Firewall", lat: 52.52, lon: 13.4, tier: "Security", status: "active", threat: "0.0%" },
  { id: "vision", name: "Qwen2.5-VL Vision Sensor", lat: -33.86, lon: 151.2, tier: "Multimodal", status: "standby", threat: "0.0%" },
  { id: "audio", name: "Whisper & Piper Audio", lat: 28.61, lon: 77.2, tier: "Voice Ops", status: "active", threat: "0.0%" },
];

export const TacticalGlobe: React.FC<{ className?: string }> = ({
  className = "",
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNode, setSelectedNode] = useState<AgentNode>(AGENT_NODES[0]);
  const [isRotating, setIsRotating] = useState(true);
  const [activeLayers, setActiveLayers] = useState({
    satellites: true,
    radarSweep: true,
    agentMesh: true,
  });

  // Camera angles
  const rotationRef = useRef({ yaw: 0.6, pitch: 0.25 });
  const isDraggingRef = useRef(false);
  const lastMouseRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationId: number;
    let radarAngle = 0;

    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // Spherical to 3D Cartesian coordinates
    const toCartesian = (lat: number, lon: number, radius: number) => {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lon + 180) * (Math.PI / 180);
      const x = -(radius * Math.sin(phi) * Math.cos(theta));
      const z = radius * Math.sin(phi) * Math.sin(theta);
      const y = radius * Math.cos(phi);
      return { x, y, z };
    };

    // Rotate 3D vector by yaw and pitch
    const rotate3D = (
      p: { x: number; y: number; z: number },
      yaw: number,
      pitch: number
    ) => {
      // Rotate around Y axis (yaw)
      const cosY = Math.cos(yaw);
      const sinY = Math.sin(yaw);
      const x1 = p.x * cosY + p.z * sinY;
      const z1 = -p.x * sinY + p.z * cosY;

      // Rotate around X axis (pitch)
      const cosP = Math.cos(pitch);
      const sinP = Math.sin(pitch);
      const y2 = p.y * cosP - z1 * sinP;
      const z2 = p.y * sinP + z1 * cosP;

      return { x: x1, y: y2, z: z2 };
    };

    // Render loop
    const render = () => {
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      const cx = w / 2;
      const cy = h / 2;
      const radius = Math.min(w, h) * 0.38;

      ctx.clearRect(0, 0, w, h);

      if (isRotating && !isDraggingRef.current) {
        rotationRef.current.yaw += 0.0035;
      }
      radarAngle = (radarAngle + 0.025) % (Math.PI * 2);

      const { yaw, pitch } = rotationRef.current;

      // 1. Globe Ambient Aura & Glow
      const glowGrad = ctx.createRadialGradient(cx, cy, radius * 0.5, cx, cy, radius * 1.3);
      glowGrad.addColorStop(0, "rgba(0, 240, 255, 0.08)");
      glowGrad.addColorStop(0.7, "rgba(0, 240, 255, 0.02)");
      glowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, radius * 1.3, 0, Math.PI * 2);
      ctx.fill();

      // 2. Outer Globe Halo Ring
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(0, 240, 255, 0.25)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // 3. Latitude parallels
      const latSteps = [-60, -30, 0, 30, 60];
      latSteps.forEach((lat) => {
        ctx.beginPath();
        let isFirst = true;
        for (let lon = -180; lon <= 180; lon += 5) {
          const pt = toCartesian(lat, lon, radius);
          const r = rotate3D(pt, yaw, pitch);
          if (r.z > 0) {
            // Front side of globe
            const alpha = 0.08 + (r.z / radius) * 0.22;
            ctx.strokeStyle = lat === 0 ? `rgba(0, 240, 255, ${alpha * 1.5})` : `rgba(0, 240, 255, ${alpha})`;
            ctx.lineWidth = lat === 0 ? 1.2 : 0.8;
            if (isFirst) {
              ctx.moveTo(cx + r.x, cy + r.y);
              isFirst = false;
            } else {
              ctx.lineTo(cx + r.x, cy + r.y);
            }
          } else {
            isFirst = true;
          }
        }
        ctx.stroke();
      });

      // 4. Longitude meridians
      const lonSteps = [-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150, 180];
      lonSteps.forEach((lon) => {
        ctx.beginPath();
        let isFirst = true;
        for (let lat = -90; lat <= 90; lat += 5) {
          const pt = toCartesian(lat, lon, radius);
          const r = rotate3D(pt, yaw, pitch);
          if (r.z > 0) {
            const alpha = 0.08 + (r.z / radius) * 0.22;
            ctx.strokeStyle = lon === 0 ? `rgba(201, 124, 76, ${alpha * 1.4})` : `rgba(0, 240, 255, ${alpha})`;
            ctx.lineWidth = lon === 0 ? 1.2 : 0.8;
            if (isFirst) {
              ctx.moveTo(cx + r.x, cy + r.y);
              isFirst = false;
            } else {
              ctx.lineTo(cx + r.x, cy + r.y);
            }
          } else {
            isFirst = true;
          }
        }
        ctx.stroke();
      });

      // 5. Radar Sweep Beam (God's Eye signature)
      if (activeLayers.radarSweep) {
        ctx.save();
        ctx.translate(cx, cy);
        const sweepGrad = ctx.createConicGradient(radarAngle, 0, 0);
        sweepGrad.addColorStop(0, "rgba(0, 240, 255, 0.28)");
        sweepGrad.addColorStop(0.12, "rgba(0, 240, 255, 0.04)");
        sweepGrad.addColorStop(0.13, "transparent");
        sweepGrad.addColorStop(1, "transparent");

        ctx.beginPath();
        ctx.arc(0, 0, radius, 0, Math.PI * 2);
        ctx.fillStyle = sweepGrad;
        ctx.fill();

        // Leading line
        const lx = Math.cos(radarAngle) * radius;
        const ly = Math.sin(radarAngle) * radius;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(lx, ly);
        ctx.strokeStyle = "rgba(0, 240, 255, 0.85)";
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.restore();
      }

      // 6. Orbital Satellite Trajectories
      if (activeLayers.satellites) {
        const orbits = [
          { tilt: 0.35, rotSpeed: 0.008, satAngle: radarAngle * 0.9, r: radius * 1.22, color: "#00f0ff" },
          { tilt: -0.45, rotSpeed: 0.006, satAngle: radarAngle * 1.2 + 2, r: radius * 1.34, color: "#ffaa00" },
          { tilt: 0.8, rotSpeed: 0.005, satAngle: radarAngle * 0.7 + 4, r: radius * 1.15, color: "#00ff88" },
        ];

        orbits.forEach((orb) => {
          ctx.beginPath();
          for (let a = 0; a <= Math.PI * 2; a += 0.08) {
            const rawX = Math.cos(a) * orb.r;
            const rawZ = Math.sin(a) * orb.r;
            const rawY = Math.sin(a) * orb.r * orb.tilt;
            const pt = rotate3D({ x: rawX, y: rawY, z: rawZ }, yaw * 0.3, pitch);
            if (a === 0) ctx.moveTo(cx + pt.x, cy + pt.y);
            else ctx.lineTo(cx + pt.x, cy + pt.y);
          }
          ctx.strokeStyle = "rgba(0, 240, 255, 0.12)";
          ctx.setLineDash([3, 6]);
          ctx.stroke();
          ctx.setLineDash([]);

          // Orbiting Satellite Vehicle
          const satRawX = Math.cos(orb.satAngle) * orb.r;
          const satRawZ = Math.sin(orb.satAngle) * orb.r;
          const satRawY = Math.sin(orb.satAngle) * orb.r * orb.tilt;
          const satPt = rotate3D({ x: satRawX, y: satRawY, z: satRawZ }, yaw * 0.3, pitch);

          ctx.fillStyle = orb.color;
          ctx.beginPath();
          ctx.arc(cx + satPt.x, cy + satPt.y, 3, 0, Math.PI * 2);
          ctx.fill();

          // Beacon ping pulse
          ctx.strokeStyle = orb.color;
          ctx.beginPath();
          ctx.arc(cx + satPt.x, cy + satPt.y, 7 + Math.sin(radarAngle * 4) * 2, 0, Math.PI * 2);
          ctx.lineWidth = 0.8;
          ctx.stroke();
        });
      }

      // 7. Agent Mesh Nodes on Surface
      if (activeLayers.agentMesh) {
        const visibleNodes: { node: AgentNode; x: number; y: number; z: number }[] = [];

        AGENT_NODES.forEach((node) => {
          const pt = toCartesian(node.lat, node.lon, radius);
          const r = rotate3D(pt, yaw, pitch);
          if (r.z > 0) {
            visibleNodes.push({ node, x: cx + r.x, y: cy + r.y, z: r.z });
          }
        });

        // Inter-node telemetry mesh connections
        ctx.strokeStyle = "rgba(0, 240, 255, 0.15)";
        ctx.lineWidth = 0.8;
        ctx.beginPath();
        for (let i = 0; i < visibleNodes.length; i++) {
          for (let j = i + 1; j < visibleNodes.length; j++) {
            ctx.moveTo(visibleNodes[i].x, visibleNodes[i].y);
            ctx.lineTo(visibleNodes[j].x, visibleNodes[j].y);
          }
        }
        ctx.stroke();

        // Render each node blip
        visibleNodes.forEach(({ node, x, y }) => {
          const isSelected = selectedNode?.id === node.id;
          const color =
            node.id === "guardian"
              ? "#ffaa00"
              : node.id === "deepseek"
              ? "#a855f7"
              : "#00f0ff";

          // Reticle Target Ring
          ctx.beginPath();
          ctx.arc(x, y, isSelected ? 8 : 4.5, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.shadowColor = color;
          ctx.shadowBlur = isSelected ? 12 : 6;
          ctx.fill();
          ctx.shadowBlur = 0;

          if (isSelected) {
            // Sci-fi Target Reticle Brackets around selected node
            ctx.strokeStyle = "#00f0ff";
            ctx.lineWidth = 1.2;
            const sz = 12;
            ctx.strokeRect(x - sz, y - sz, sz * 2, sz * 2);

            // Label
            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 10px 'IBM Plex Mono', monospace";
            ctx.fillText(node.name.toUpperCase(), x + 16, y + 3);

            ctx.fillStyle = "rgba(0, 240, 255, 0.75)";
            ctx.font = "8px 'IBM Plex Mono', monospace";
            ctx.fillText(`LOC: ${node.lat}°N, ${Math.abs(node.lon)}°W`, x + 16, y + 14);
          }
        });
      }

      // 8. Crosshair reticles on canvas corners
      const chSize = 14;
      ctx.strokeStyle = "rgba(0, 240, 255, 0.35)";
      ctx.lineWidth = 1;

      // Top-left
      ctx.beginPath();
      ctx.moveTo(16, 16);
      ctx.lineTo(16 + chSize, 16);
      ctx.moveTo(16, 16);
      ctx.lineTo(16, 16 + chSize);
      ctx.stroke();

      // Top-right
      ctx.beginPath();
      ctx.moveTo(w - 16, 16);
      ctx.lineTo(w - 16 - chSize, 16);
      ctx.moveTo(w - 16, 16);
      ctx.lineTo(w - 16, 16 + chSize);
      ctx.stroke();

      // Bottom-left
      ctx.beginPath();
      ctx.moveTo(16, h - 16);
      ctx.lineTo(16 + chSize, h - 16);
      ctx.moveTo(16, h - 16);
      ctx.lineTo(16, h - 16 - chSize);
      ctx.stroke();

      // Bottom-right
      ctx.beginPath();
      ctx.moveTo(w - 16, h - 16);
      ctx.lineTo(w - 16 - chSize, h - 16);
      ctx.moveTo(w - 16, h - 16);
      ctx.lineTo(w - 16, h - 16 - chSize);
      ctx.stroke();

      animationId = requestAnimationFrame(render);
    };

    animationId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      cancelAnimationFrame(animationId);
    };
  }, [isRotating, activeLayers, selectedNode]);

  // Mouse drag handlers for manual 3D globe rotation
  const handleMouseDown = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMouseRef.current.x;
    const dy = e.clientY - lastMouseRef.current.y;
    rotationRef.current.yaw += dx * 0.008;
    rotationRef.current.pitch = Math.max(-1.2, Math.min(1.2, rotationRef.current.pitch + dy * 0.008));
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  return (
    <div
      className={`relative w-full rounded-2xl bg-[#05080e]/95 border border-cyber-cyan/25 overflow-hidden shadow-2xl select-none font-mono flex flex-col ${className}`}
    >
      {/* HUD Header Bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-cyber-cyan/20 bg-gradient-to-r from-cyber-cyan/10 via-[#070d18] to-[#05080e]">
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-cyber-cyan animate-ping" />
          <span className="text-[12px] font-bold text-cyber-cyan tracking-wider flex items-center gap-2">
            <Radio size={14} className="text-cyber-cyan" />
            GOD'S EYE // ORBITAL SPATIAL RECONNAISSANCE
          </span>
          <span className="hidden md:inline px-2 py-0.5 rounded bg-cyber-cyan/15 border border-cyber-cyan/30 text-[9px] text-cyber-cyan font-bold">
            SAT-FEED LIVE
          </span>
        </div>

        {/* Layer Toggles & Orbit Controls */}
        <div className="flex items-center gap-2 text-xs">
          <button
            onClick={() => setIsRotating((p) => !p)}
            className={`px-2.5 py-1 rounded-md text-[10px] font-bold border transition-all flex items-center gap-1.5 ${
              isRotating
                ? "bg-cyber-cyan/20 text-cyber-cyan border-cyber-cyan/50 shadow-sm"
                : "bg-zinc-800 text-zinc-400 border-zinc-700"
            }`}
            title="Toggle Orbital Auto-Rotation"
          >
            <RotateCcw size={11} className={isRotating ? "animate-spin" : ""} />
            <span>{isRotating ? "AUTO-ORBIT" : "MANUAL"}</span>
          </button>

          <button
            onClick={() =>
              setActiveLayers((p) => ({ ...p, satellites: !p.satellites }))
            }
            className={`px-2 py-1 rounded-md text-[10px] font-bold border transition-all ${
              activeLayers.satellites
                ? "bg-cyber-cyan/15 text-cyber-cyan border-cyber-cyan/40"
                : "bg-transparent text-zinc-500 border-zinc-800"
            }`}
          >
            SATS
          </button>

          <button
            onClick={() =>
              setActiveLayers((p) => ({ ...p, radarSweep: !p.radarSweep }))
            }
            className={`px-2 py-1 rounded-md text-[10px] font-bold border transition-all ${
              activeLayers.radarSweep
                ? "bg-cyber-cyan/15 text-cyber-cyan border-cyber-cyan/40"
                : "bg-transparent text-zinc-500 border-zinc-800"
            }`}
          >
            SWEEP
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div
        className="relative w-full h-[360px] cursor-grab active:cursor-grabbing bg-radial from-[#091222] via-[#05080e] to-[#020408]"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <canvas ref={canvasRef} className="w-full h-full block" />

        {/* Live Coordinate Overlay HUD (Top Left) */}
        <div className="absolute top-4 left-5 pointer-events-none space-y-1 font-mono text-[10px] text-cyber-cyan/80 bg-black/60 backdrop-blur-md p-2.5 rounded-lg border border-cyber-cyan/20">
          <div className="flex items-center gap-1.5 text-cyber-cyan font-bold">
            <Target size={12} />
            <span>GEO-TELEMETRY LOCK</span>
          </div>
          <p className="text-zinc-400">
            LAT: <span className="text-white font-bold">{selectedNode.lat.toFixed(2)}° N</span>
          </p>
          <p className="text-zinc-400">
            LON: <span className="text-white font-bold">{Math.abs(selectedNode.lon).toFixed(2)}° W</span>
          </p>
          <p className="text-zinc-400">
            ALT: <span className="text-cyber-cyan">420.5 KM LEO</span>
          </p>
          <p className="text-zinc-400">
            CARRIER: <span className="text-verdigris font-bold">142.800 MHz ENCRYPTED</span>
          </p>
        </div>

        {/* Node Selector Drawer / Telemetry Card (Bottom Right) */}
        <div className="absolute bottom-4 right-5 w-64 bg-black/75 backdrop-blur-xl p-3 rounded-xl border border-cyber-cyan/30 text-[11px] font-mono shadow-2xl">
          <div className="flex items-center justify-between text-[10px] text-zinc-400 border-b border-cyber-cyan/20 pb-1.5 mb-2">
            <span className="text-cyber-cyan font-bold">TRACKED AGENT NODE</span>
            <span className="text-verdigris font-bold">LOCKED</span>
          </div>

          <div className="space-y-1">
            <div className="text-white font-bold text-sm tracking-tight font-display">
              {selectedNode.name}
            </div>
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-zinc-400">Role:</span>
              <span className="text-cyber-cyan font-semibold">{selectedNode.tier}</span>
            </div>
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-zinc-400">Security Threat:</span>
              <span className="text-verdigris font-bold">0.0% SECURE</span>
            </div>
          </div>

          {/* Quick Select Buttons */}
          <div className="mt-3 pt-2 border-t border-white/10 flex flex-wrap gap-1">
            {AGENT_NODES.map((n) => (
              <button
                key={n.id}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNode(n);
                }}
                className={`px-1.5 py-0.5 rounded text-[9px] transition-all font-mono ${
                  selectedNode.id === n.id
                    ? "bg-cyber-cyan text-black font-bold"
                    : "bg-white/5 text-zinc-400 hover:text-white"
                }`}
              >
                {n.id.slice(0, 4).toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Recon Scanning Watermark */}
        <div className="absolute bottom-4 left-5 pointer-events-none text-[9px] font-mono text-zinc-500 uppercase tracking-widest flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-verdigris animate-pulse" />
          <span>AIR-GAPPED 100% LOCAL RECON // NO CLOUD EGRESS</span>
        </div>
      </div>
    </div>
  );
};
