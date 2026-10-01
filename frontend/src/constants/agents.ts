export type Tier =
  | "MODEL_1_CORE"
  | "MODEL_2_CODE"
  | "MODEL_3_OS"
  | "MODEL_4_VISION"
  | "MODEL_5_WEB"
  | "MODEL_6_AUDIO";

export interface AgentMeta {
  id: string;
  name: string;
  codename: string;
  tier: Tier;
  domain: string;
  blurb: string;
  icon: string;
  color: string;
  bg: string;
  border: string;
  text: string;
  model: string;
  status: "active" | "coming_soon";
}

export const TIER_ORDER: Tier[] = [
  "MODEL_1_CORE",
  "MODEL_2_CODE",
  "MODEL_3_OS",
  "MODEL_4_VISION",
  "MODEL_5_WEB",
  "MODEL_6_AUDIO",
];

export const TIER_LABELS: Record<Tier, string> = {
  MODEL_1_CORE: "Core Reasoning & Planning",
  MODEL_2_CODE: "Software & Code Architecture",
  MODEL_3_OS: "OS & Desktop Automation",
  MODEL_4_VISION: "Vision, OCR & Screen RPA",
  MODEL_5_WEB: "Web Intelligence & Search",
  MODEL_6_AUDIO: "Audio, Speech & Documents",
};

export const TIER_COLORS: Record<Tier, string> = {
  MODEL_1_CORE: "#4ADE9A", // Emerald
  MODEL_2_CODE: "#38BCD8", // Electric Cyan
  MODEL_3_OS: "#5B93F0",   // Sapphire Blue
  MODEL_4_VISION: "#E06E9E", // Neon Pink
  MODEL_5_WEB: "#E8A840",  // Molten Amber
  MODEL_6_AUDIO: "#9B6DD8", // Royal Purple
};

/**
 * ACTIVE AGENTS: Exactly matches the 12 implemented AgentType enum values in backend.
 * Each active agent has a registered backend handler, assigned model, and test suite.
 */
export const ACTIVE_AGENTS: AgentMeta[] = [
  {
    id: "chat",
    name: "Chat",
    codename: "ATLAS",
    tier: "MODEL_1_CORE",
    domain: "Conversational Interface",
    blurb: "Primary conversational companion, intent decomposition, and dialogue orchestrator.",
    icon: "MessageSquare",
    color: "#10b981",
    bg: "bg-emerald-950/30",
    border: "border-emerald-500/40",
    text: "text-emerald-400",
    model: "qwen2.5:14b",
    status: "active",
  },
  {
    id: "coding",
    name: "Coding",
    codename: "VULCAN",
    tier: "MODEL_2_CODE",
    domain: "Software & Code Architecture",
    blurb: "Full-stack code generation, refactoring, reverse engineering, and sandbox execution.",
    icon: "Code2",
    color: "#06b6d4",
    bg: "bg-cyan-950/30",
    border: "border-cyan-500/40",
    text: "text-cyan-400",
    model: "qwen2.5-coder-abliterated:14b",
    status: "active",
  },
  {
    id: "document",
    name: "Document",
    codename: "SCRIBE",
    tier: "MODEL_6_AUDIO",
    domain: "Document Architecture",
    blurb: "Multi-format document generation (PDF, Word DOCX, Markdown, HTML, spreadsheets).",
    icon: "FileText",
    color: "#a855f7",
    bg: "bg-purple-950/30",
    border: "border-purple-500/40",
    text: "text-purple-400",
    model: "phi4:14b",
    status: "active",
  },
  {
    id: "automation",
    name: "Automation",
    codename: "DAEMON",
    tier: "MODEL_3_OS",
    domain: "OS & Desktop Automation",
    blurb: "Autonomous CLI execution, desktop automation, file operations, and tool running.",
    icon: "Terminal",
    color: "#3b82f6",
    bg: "bg-blue-950/30",
    border: "border-blue-500/40",
    text: "text-blue-400",
    model: "mistral-nemo:12b",
    status: "active",
  },
  {
    id: "reminder",
    name: "Reminder",
    codename: "CHRONOS",
    tier: "MODEL_1_CORE",
    domain: "Temporal & Reminders",
    blurb: "Manages daily calendar events, focus blocks, deadlines, and reminders.",
    icon: "Clock",
    color: "#14b8a6",
    bg: "bg-teal-950/30",
    border: "border-teal-500/40",
    text: "text-teal-400",
    model: "qwen2.5:14b",
    status: "active",
  },
  {
    id: "research",
    name: "Research",
    codename: "PROMETHEUS",
    tier: "MODEL_1_CORE",
    domain: "Research & Reasoning",
    blurb: "Hybrid RAG search (vector + BM25 RRF), cross-encoder re-ranking, and citation grounding.",
    icon: "BookOpen",
    color: "#6366f1",
    bg: "bg-indigo-950/30",
    border: "border-indigo-500/40",
    text: "text-indigo-400",
    model: "deepseek-r1:14b",
    status: "active",
  },
  {
    id: "vision",
    name: "Vision",
    codename: "ARGUS",
    tier: "MODEL_4_VISION",
    domain: "Vision & Screen RPA",
    blurb: "Desktop UI perception, bounding box coordinate detection, and computer use.",
    icon: "Eye",
    color: "#ec4899",
    bg: "bg-pink-950/30",
    border: "border-pink-500/40",
    text: "text-pink-400",
    model: "qwen2.5-vl:3b",
    status: "active",
  },
  {
    id: "image",
    name: "Image",
    codename: "PICASSO",
    tier: "MODEL_4_VISION",
    domain: "Image Generation Studio",
    blurb: "100% offline visual asset and image generation studio via local diffusion.",
    icon: "Image",
    color: "#f43f5e",
    bg: "bg-rose-950/30",
    border: "border-rose-500/40",
    text: "text-rose-400",
    model: "local_diffusion",
    status: "active",
  },
  {
    id: "web_search",
    name: "Web Search",
    codename: "RAPTOR",
    tier: "MODEL_5_WEB",
    domain: "Web Intelligence & Search",
    blurb: "Privacy-preserving web search via SearXNG with PII redaction and citation synthesis.",
    icon: "Globe",
    color: "#f59e0b",
    bg: "bg-amber-950/30",
    border: "border-amber-500/40",
    text: "text-amber-400",
    model: "mistral-nemo:12b",
    status: "active",
  },
  {
    id: "campaign_intelligence",
    name: "Campaign Intelligence",
    codename: "DELTA",
    tier: "MODEL_1_CORE",
    domain: "Campaign Intelligence & Ad-Tech",
    blurb: "DeltaX-grade ad campaign anomaly detection, budget allocation optimization, and telemetry.",
    icon: "Target",
    color: "#06b6d4",
    bg: "bg-cyan-950/30",
    border: "border-cyan-500/40",
    text: "text-cyan-400",
    model: "deepseek-r1:14b",
    status: "active",
  },
  {
    id: "planner",
    name: "Planner",
    codename: "NEXUS",
    tier: "MODEL_1_CORE",
    domain: "Strategic Planning & DAG",
    blurb: "Complex instruction decomposition, DAG task graph construction, and multi-agent coordination.",
    icon: "Compass",
    color: "#8b5cf6",
    bg: "bg-violet-950/30",
    border: "border-violet-500/40",
    text: "text-violet-400",
    model: "deepseek-r1:14b",
    status: "active",
  },
  {
    id: "guardian",
    name: "Guardian",
    codename: "AEGIS",
    tier: "MODEL_1_CORE",
    domain: "Safety & Security Gatekeeper",
    blurb: "Constitutional safety boundary enforcement, action reversibility analysis, and friction index scoring.",
    icon: "ShieldAlert",
    color: "#eab308",
    bg: "bg-yellow-950/30",
    border: "border-yellow-500/40",
    text: "text-yellow-400",
    model: "qwen2.5:1.5b",
    status: "active",
  },
];

/**
 * PLANNED AGENTS: Architectural roadmap targets currently in design.
 * Rendered with visual differentiation (dimmed/dashed) in the neural map.
 */
export const PLANNED_AGENTS: AgentMeta[] = [
  {
    id: "behavior",
    name: "Behavior",
    codename: "PSYCHE",
    tier: "MODEL_1_CORE",
    domain: "Behavioral & Habit Analysis",
    blurb: "Circadian rhythms, fatigue modeling, and user behavioral preference optimization.",
    icon: "Activity",
    color: "#64748b",
    bg: "bg-canvas/20",
    border: "border-border-subtle",
    text: "text-text-secondary",
    model: "planned:qwen2.5:14b",
    status: "coming_soon",
  },
  {
    id: "nutrition",
    name: "Nutrition",
    codename: "SOLIS",
    tier: "MODEL_3_OS",
    domain: "Biometric & Nutrition Telemetry",
    blurb: "Biometric intake tracking, meal scheduling, and cognitive health correlations.",
    icon: "HeartPulse",
    color: "#64748b",
    bg: "bg-canvas/20",
    border: "border-border-subtle",
    text: "text-text-secondary",
    model: "planned:smollm2:1.7b",
    status: "coming_soon",
  },
  {
    id: "evaluator",
    name: "Evaluator",
    codename: "JUSTICIA",
    tier: "MODEL_1_CORE",
    domain: "LLM-as-a-Judge Evaluation",
    blurb: "Autonomous hallucination verification, rubric scoring, and synthetic output judging.",
    icon: "Scale",
    color: "#64748b",
    bg: "bg-canvas/20",
    border: "border-border-subtle",
    text: "text-text-secondary",
    model: "planned:deepseek-r1:14b",
    status: "coming_soon",
  },
  {
    id: "orchestrator",
    name: "Orchestrator",
    codename: "SYMPHONY",
    tier: "MODEL_1_CORE",
    domain: "Autonomous Swarm Orchestrator",
    blurb: "High-density dynamic subagent swarming and consensus aggregation.",
    icon: "GitFork",
    color: "#64748b",
    bg: "bg-canvas/20",
    border: "border-border-subtle",
    text: "text-text-secondary",
    model: "planned:qwen2.5:14b",
    status: "coming_soon",
  },
  {
    id: "voice",
    name: "Voice",
    codename: "ECHO",
    tier: "MODEL_6_AUDIO",
    domain: "Full-Duplex Speech & Audio",
    blurb: "Sub-300ms bidirectional voice conversation with barge-in detection.",
    icon: "Mic",
    color: "#64748b",
    bg: "bg-canvas/20",
    border: "border-border-subtle",
    text: "text-text-secondary",
    model: "planned:kokoro+whisper",
    status: "coming_soon",
  },
];

/**
 * Standard AGENTS array exports ACTIVE_AGENTS to guarantee exact parity
 * with backend AgentType (12 implemented agents).
 */
export const AGENTS: AgentMeta[] = ACTIVE_AGENTS;

/**
 * Combined list containing active implemented agents and planned roadmap agents.
 */
export const ALL_AGENTS: AgentMeta[] = [...ACTIVE_AGENTS, ...PLANNED_AGENTS];

export const AGENT_MAP: Record<string, AgentMeta> = Object.fromEntries(
  ALL_AGENTS.map((a) => [a.id, a]),
);
