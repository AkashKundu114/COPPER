import React, { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ACTIVE_AGENTS,
  PLANNED_AGENTS,
  ALL_AGENTS,
  AGENTS,
  TIER_COLORS,
  TIER_LABELS,
} from "../../constants/agents";
import { computeLayout, computeOrbit, hashStr, CENTER, VIEWBOX } from "../../lib/layout";
import type { AgentStats } from "../../lib/api";

export interface NeuralBrainProps {
  agentStats: Record<string, AgentStats>;
  thinking: boolean;
  activeAgent: string | null;
  activeEdge: { from: string; to: string } | null;
  pulseSeq: number;
  selectedAgent: string | null;
  onSelectAgent: (id: string) => void;
}

const NODE_R_BASE = 9;
const NODE_R_ACTIVE = 15;

export const NeuralBrain: React.FC<NeuralBrainProps> = ({
  agentStats,
  thinking,
  activeAgent,
  activeEdge,
  pulseSeq,
  selectedAgent,
  onSelectAgent,
}) => {
  const positions = useMemo(() => computeLayout(), []);

  return (
    <div
      role="region"
      aria-label="COPPER Neural Brain Visualization"
      className="relative w-full h-full flex items-center justify-center"
    >
      {/* Screen Reader Accessible Summary and Agent Directory */}
      <div className="sr-only">
        <h2>Agent Neural Network Overview</h2>
        <p>COPPER Core Engine Status: {thinking ? "Thinking and reasoning active" : "Idle"}.</p>
        <p>Active Agent: {activeAgent ? ALL_AGENTS.find((a) => a.id === activeAgent || a.codename === activeAgent)?.name || activeAgent : "None"}.</p>
        <p>Selected Agent: {selectedAgent ? ALL_AGENTS.find((a) => a.id === selectedAgent || a.codename === selectedAgent)?.name || selectedAgent : "None"}.</p>
        <p>
          Network includes {ACTIVE_AGENTS.length} active specialist agents and {PLANNED_AGENTS.length} planned agents across local neural mesh:
        </p>
        <ul>
          {ALL_AGENTS.map((agent) => {
            const stats = agentStats[agent.id] || (agent.codename ? agentStats[agent.codename] : undefined);
            const isActive = activeAgent === agent.id || activeAgent === agent.codename || activeAgent?.toLowerCase() === agent.id.toLowerCase();
            const isSelected = selectedAgent === agent.id || selectedAgent === agent.codename || selectedAgent?.toLowerCase() === agent.id.toLowerCase();
            const isPlanned = agent.status === "coming_soon";
            return (
              <li key={`sr-${agent.id}`}>
                <button type="button" onClick={() => onSelectAgent(agent.id)}>
                  Select {agent.name}: {agent.domain} ({TIER_LABELS[agent.tier] || agent.tier}).
                  {isPlanned ? " (Planned Agent - Coming Soon)." : ""}
                  {isActive ? " Currently active in mesh." : ""}
                  {isSelected ? " Currently selected." : ""}
                  {stats?.times_invoked ? ` ${stats.times_invoked} jobs handled.` : ""}
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <svg
        viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`}
        className="w-full h-full max-w-[1100px] max-h-[1100px]"
        role="img"
        aria-label="COPPER neural map of active agents, orbiting like a solar system"
      >
        <defs aria-hidden="true">
          <radialGradient id="core-glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.12" />
            <stop offset="60%" stopColor="#27272a" stopOpacity="0.04" />
            <stop offset="100%" stopColor="#000000" stopOpacity="0" />
          </radialGradient>
          <filter id="soft-blur" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" />
          </filter>
          <filter id="tight-blur" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="1.5" />
          </filter>
        </defs>

        {/* Central COPPER Core */}
        <g data-testid="copper-core" role="group" aria-label={`COPPER Core Engine: ${thinking ? "Active Reasoning" : "Idle"}`}>
          <circle
            cx={CENTER}
            cy={CENTER}
            r={95}
            fill="url(#core-glow)"
            className={thinking ? "animate-core-pulse" : ""}
          />
          <motion.circle
            cx={CENTER}
            cy={CENTER}
            r={38}
            fill="#09090b"
            stroke="#ffffff"
            strokeWidth={1.5}
            animate={thinking ? { scale: [1, 1.05, 1] } : { scale: 1 }}
            transition={{ duration: 1.1, repeat: thinking ? Infinity : 0, ease: "easeInOut" }}
            style={{ transformOrigin: `${CENTER}px ${CENTER}px` }}
          />
          <text
            x={CENTER}
            y={CENTER + 5}
            textAnchor="middle"
            className="fill-white font-display font-semibold"
            fontSize="15"
            letterSpacing="1.5"
          >
            COPPER
          </text>
        </g>

        {/* Orbiting Agent Nodes (Active + Dimmed Planned) */}
        {ALL_AGENTS.map((agent) => {
          const pos = positions[agent.id] || { x: CENTER, y: CENTER };
          const orbit = computeOrbit(agent.id, agent.tier);
          const stats = agentStats[agent.id] || (agent.codename ? agentStats[agent.codename] : undefined);
          const glow = stats?.glow ?? 0;
          const isActive = activeAgent === agent.id || activeAgent === agent.codename || activeAgent?.toLowerCase() === agent.id.toLowerCase();
          const isSelected = selectedAgent === agent.id || selectedAgent === agent.codename || selectedAgent?.toLowerCase() === agent.id.toLowerCase();
          const isPlanned = agent.status === "coming_soon";
          const tierColor = TIER_COLORS[agent.tier] || "#06b6d4";
          const radius = isActive ? NODE_R_ACTIVE : NODE_R_BASE + glow * 3;
          const baseOpacity = isPlanned ? 0.22 : 0.35 + glow * 0.65;
          const baseLineOpacity = isPlanned ? 0.06 : 0.12 + glow * 0.35;
          const labelY = pos.y + radius + 12;

          return (
            <g
              key={agent.id}
              data-testid={`agent-group-${agent.id}`}
              style={{
                transformOrigin: `${CENTER}px ${CENTER}px`,
                animation: `orbit ${orbit.durationSec}s linear infinite`,
                animationDirection: orbit.direction,
                animationDelay: `${orbit.delaySec}s`,
                willChange: "transform",
              }}
            >
              {/* Spoke line from core to agent */}
              <motion.line
                aria-hidden="true"
                x1={CENTER}
                y1={CENTER}
                x2={pos.x}
                y2={pos.y}
                stroke={isPlanned ? "#71717a" : tierColor}
                strokeWidth={isPlanned ? 0.8 : 1 + glow * 1.5}
                strokeDasharray={isPlanned ? "3 5" : undefined}
                strokeLinecap="round"
                animate={{ opacity: [baseLineOpacity, baseLineOpacity + (isPlanned ? 0.04 : 0.1), baseLineOpacity] }}
                transition={{
                  duration: 4 + (hashStr(agent.id) % 25) / 10,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: (hashStr(agent.id) % 20) / 10,
                }}
              />

              {/* Edge Pulse Animation */}
              <AnimatePresence>
                {activeEdge?.to === agent.id && (
                  <motion.line
                    key={`pulse-${pulseSeq}`}
                    data-testid={`edge-pulse-${agent.id}`}
                    aria-hidden="true"
                    x1={CENTER}
                    y1={CENTER}
                    x2={pos.x}
                    y2={pos.y}
                    stroke="#ffffff"
                    strokeWidth={2}
                    strokeLinecap="round"
                    filter="url(#tight-blur)"
                    initial={{ opacity: 0, pathLength: 0 }}
                    animate={{ opacity: [0, 1, 1, 0], pathLength: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.9, times: [0, 0.15, 0.7, 1] }}
                  />
                )}
              </AnimatePresence>

              {/* Active ripple ring */}
              {isActive && (
                <motion.circle
                  aria-hidden="true"
                  cx={pos.x}
                  cy={pos.y}
                  r={radius + 10}
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth={1.2}
                  initial={{ opacity: 0.8, r: radius }}
                  animate={{ opacity: 0, r: radius + 18 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "easeOut" }}
                />
              )}

              {/* Agent Node Circle */}
              <motion.circle
                cx={pos.x}
                cy={pos.y}
                fill={isPlanned ? "transparent" : isActive ? "#ffffff" : tierColor}
                filter={isActive ? "url(#soft-blur)" : undefined}
                stroke={isSelected ? "#ffffff" : isPlanned ? tierColor : "transparent"}
                strokeWidth={isSelected ? 1.5 : isPlanned ? 1.2 : 0}
                strokeDasharray={isPlanned ? "3 3" : undefined}
                style={{ transformOrigin: `${pos.x}px ${pos.y}px` }}
                initial={{ r: radius }}
                animate={
                  isActive
                    ? { r: radius, opacity: 1, scale: 1 }
                    : {
                        r: radius,
                        opacity: [baseOpacity, baseOpacity + (isPlanned ? 0.1 : 0.18), baseOpacity],
                        scale: isPlanned ? 1 : [1, 1.05, 1],
                      }
                }
                transition={
                  isActive
                    ? { duration: 0.25 }
                    : {
                        duration: 3.4 + (hashStr(agent.id) % 22) / 10,
                        repeat: Infinity,
                        ease: "easeInOut",
                        delay: (hashStr(agent.id) % 30) / 10,
                      }
                }
                className="cursor-pointer focus-visible:outline-none"
                whileHover={{ scale: isPlanned ? 1.1 : 1.25 }}
                onClick={() => onSelectAgent(agent.id)}
                role="button"
                tabIndex={0}
                aria-pressed={isSelected}
                aria-label={`${agent.name}${isPlanned ? " (Planned Agent - Coming Soon)" : ""}, ${agent.domain}${TIER_LABELS[agent.tier] ? ` - ${TIER_LABELS[agent.tier]}` : ""}${isActive ? ", currently active" : ""}${isSelected ? ", selected" : ""}`}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onSelectAgent(agent.id);
                  }
                }}
              />

              {/* Counter-rotating Label */}
              <g
                aria-hidden="true"
                style={{
                  transformOrigin: `${pos.x}px ${labelY}px`,
                  animation: `orbit ${orbit.durationSec}s linear infinite`,
                  animationDirection: orbit.direction === "normal" ? "reverse" : "normal",
                  animationDelay: `${orbit.delaySec}s`,
                }}
              >
                <text
                  x={pos.x}
                  y={labelY}
                  textAnchor="middle"
                  fontSize="9"
                  className={`font-mono pointer-events-none select-none transition-opacity duration-300 ${
                    isPlanned
                      ? "fill-zinc-500 opacity-40 italic"
                      : isActive || isSelected
                      ? "fill-white opacity-100"
                      : "fill-zinc-400 opacity-60"
                  }`}
                >
                  {agent.name}
                </text>
              </g>
            </g>
          );
        })}
      </svg>

      {/* Visual Legend: Active Agent vs Planned Agent */}
      <div
        role="complementary"
        aria-label="Agent Visualization Legend"
        className="absolute bottom-4 left-4 flex items-center gap-3 px-3 py-1.5 rounded-lg bg-zinc-950/80 border border-zinc-800/70 backdrop-blur-md text-[11px] font-mono select-none pointer-events-none shadow-lg"
      >
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]" />
          <span className="text-zinc-200">Active Agent ({ACTIVE_AGENTS.length})</span>
        </div>
        <div className="w-[1px] h-3 bg-zinc-800" />
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full border border-dashed border-zinc-500 bg-transparent opacity-70" />
          <span className="text-zinc-400">Planned Agent ({PLANNED_AGENTS.length})</span>
        </div>
      </div>
    </div>
  );
};
