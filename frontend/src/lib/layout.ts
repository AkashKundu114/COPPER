
import { AGENTS, TIER_ORDER, type Tier } from "../data/agents";

export const VIEWBOX = 1000;
export const CENTER = VIEWBOX / 2;

const RING_RADIUS: Record<Tier, number> = {
  MODEL_1_CORE: 130,
  MODEL_2_CODE: 205,
  MODEL_3_OS: 280,
  MODEL_4_VISION: 355,
  MODEL_5_WEB: 425,
  MODEL_6_AUDIO: 485,
};

const RING_OFFSET_DEG: Record<Tier, number> = {
  MODEL_1_CORE: 0,
  MODEL_2_CODE: 18,
  MODEL_3_OS: 9,
  MODEL_4_VISION: 27,
  MODEL_5_WEB: 4,
  MODEL_6_AUDIO: 22,
};

export function hashStr(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) {
    h = (h * 31 + s.charCodeAt(i)) & 0xffffffff;
  }
  return Math.abs(h);
}

const RING_ORBIT_SECONDS: Record<Tier, number> = {
  MODEL_1_CORE: 46,
  MODEL_2_CODE: 62,
  MODEL_3_OS: 80,
  MODEL_4_VISION: 98,
  MODEL_5_WEB: 118,
  MODEL_6_AUDIO: 140,
};

export interface OrbitParams {
  durationSec: number;
  direction: "normal" | "reverse";
  delaySec: number;
}

export function computeOrbit(agentId: string, tier: Tier): OrbitParams {
  const h = hashStr(agentId);
  const jitter = 1 + (((h % 100) / 100) - 0.5) * 0.3; 
  return {
    durationSec: RING_ORBIT_SECONDS[tier] * jitter,
    direction: h % 2 === 0 ? "normal" : "reverse",
    delaySec: -((h >> 4) % 400) / 10, 
  };
}

export interface NodePosition {
  id: string;
  x: number;
  y: number;
  angleDeg: number;
  radius: number;
}

export function computeLayout(): Record<string, NodePosition> {
  const positions: Record<string, NodePosition> = {};

  for (const tier of TIER_ORDER) {
    const tierAgents = AGENTS.filter((a) => a.tier === tier);
    const n = tierAgents.length;
    const baseRadius = RING_RADIUS[tier];
    const offset = RING_OFFSET_DEG[tier];

    tierAgents.forEach((agent, i) => {
      const h = hashStr(agent.id);
      const jitterAngle = ((h % 100) / 100 - 0.5) * (360 / n) * 0.28;
      const jitterRadius = ((h >> 8) % 100) / 100 * 16 - 8;

      const angleDeg = (360 / n) * i + offset + jitterAngle;
      const radius = baseRadius + jitterRadius;
      const rad = (angleDeg * Math.PI) / 180;

      positions[agent.id] = {
        id: agent.id,
        x: CENTER + radius * Math.cos(rad),
        y: CENTER + radius * Math.sin(rad),
        angleDeg,
        radius,
      };
    });
  }

  return positions;
}
