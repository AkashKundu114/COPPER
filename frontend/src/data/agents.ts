// Mirrors backend/app/data/agents.py — static identity + layout metadata.
// Dynamic stats (familiarity, glow, history) are fetched from the API/WS
// at runtime and merged with this on the frontend.

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
  tier: Tier;
  domain: string;
  blurb: string;
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
  MODEL_1_CORE: "Core Reasoning",
  MODEL_2_CODE: "Code Engineering",
  MODEL_3_OS: "OS & Automation",
  MODEL_4_VISION: "Vision & RPA",
  MODEL_5_WEB: "Web & Streaming",
  MODEL_6_AUDIO: "Audio & Language",
};

// Warms progressively from pale gold (core reasoning) to deep rust (audio) —
// dormant color; active "firing" state always renders as electric spark blue
// regardless of tier, so the tier color reads as identity, not state.
export const TIER_COLORS: Record<Tier, string> = {
  MODEL_1_CORE: "#e8c07d",
  MODEL_2_CODE: "#eab676",
  MODEL_3_OS: "#e0985f",
  MODEL_4_VISION: "#d97b52",
  MODEL_5_WEB: "#c2654a",
  MODEL_6_AUDIO: "#a8524a",
};

export const AGENTS: AgentMeta[] = [
  { id: "CHRONOS", name: "Chronos", tier: "MODEL_1_CORE", domain: "Architecture & Planning", blurb: "Breaks big asks into phased, dependency-aware roadmaps." },
  { id: "MNEMONIC", name: "Mnemonic", tier: "MODEL_1_CORE", domain: "Memory & Recall", blurb: "Stores and surfaces past decisions, preferences, and context." },

  { id: "CYPHER", name: "Cypher", tier: "MODEL_2_CODE", domain: "Code Generation", blurb: "Writes clean implementation code, fast, minimal commentary." },
  { id: "CRUCIBLE", name: "Crucible", tier: "MODEL_2_CODE", domain: "Debugging", blurb: "Finds why code breaks, treats every bug like a crime scene." },
  { id: "FORGE", name: "Forge", tier: "MODEL_2_CODE", domain: "System & Schema Design", blurb: "Designs data models, APIs, and service boundaries." },
  { id: "NEXUS", name: "Nexus", tier: "MODEL_2_CODE", domain: "Version Control", blurb: "Handles git carefully, explains risk before anything destructive." },
  { id: "ARGUS", name: "Argus", tier: "MODEL_2_CODE", domain: "Security & Review", blurb: "Audits code for vulnerabilities, doesn't soften the findings." },

  { id: "AXIS", name: "Axis", tier: "MODEL_3_OS", domain: "Shell & System Admin", blurb: "Executes terminal commands precisely, flags anything risky." },
  { id: "ATLAS", name: "Atlas", tier: "MODEL_3_OS", domain: "File Management", blurb: "Organizes, moves, and cleans up files and directories." },
  { id: "KINETIC", name: "Kinetic", tier: "MODEL_3_OS", domain: "Scheduling", blurb: "Sets up timers, cron jobs, and recurring triggers." },
  { id: "PULSE", name: "Pulse", tier: "MODEL_3_OS", domain: "Hardware Monitoring", blurb: "Reports on CPU, memory, disk, and process health." },
  { id: "ZENITH", name: "Zenith", tier: "MODEL_3_OS", domain: "Focus Mode", blurb: "Blocks distractions and enforces productivity on request." },
  { id: "LEDGER", name: "Ledger", tier: "MODEL_3_OS", domain: "Data Analysis", blurb: "Crunches CSVs and datasets, reports numbers not vibes." },
  { id: "VAULT", name: "Vault", tier: "MODEL_3_OS", domain: "Secrets & Credentials", blurb: "Stores and rotates passwords, API keys, and tokens securely." },

  { id: "HAWK", name: "Hawk", tier: "MODEL_4_VISION", domain: "Screen Analysis", blurb: "Detects and locates UI elements from screenshots." },
  { id: "TALON", name: "Talon", tier: "MODEL_4_VISION", domain: "RPA Execution", blurb: "Performs precise mouse and keyboard interactions." },
  { id: "PORTAL", name: "Portal", tier: "MODEL_4_VISION", domain: "App Lifecycle", blurb: "Launches, closes, and focuses windows and apps." },
  { id: "IRIS", name: "Iris", tier: "MODEL_4_VISION", domain: "OCR", blurb: "Extracts readable text from images, scans, and screenshots." },

  { id: "RAPTOR", name: "Raptor", tier: "MODEL_5_WEB", domain: "Static Scraping", blurb: "Extracts data from HTML without needing a browser." },
  { id: "PHANTOM", name: "Phantom", tier: "MODEL_5_WEB", domain: "Headless Browser", blurb: "Handles JavaScript-heavy sites, Playwright-style." },
  { id: "VANGUARD", name: "Vanguard", tier: "MODEL_5_WEB", domain: "Research", blurb: "Finds documentation, news, and best practices on the web." },
  { id: "AETHER", name: "Aether", tier: "MODEL_5_WEB", domain: "Video Extraction", blurb: "Pulls transcripts, metadata, and media from video sources." },
  { id: "BEACON", name: "Beacon", tier: "MODEL_5_WEB", domain: "Stream Monitoring", blurb: "Watches live-status APIs for streamers and channels." },
  { id: "DIRECTOR", name: "Director", tier: "MODEL_5_WEB", domain: "Broadcast Control", blurb: "Issues OBS commands for scenes, sources, and recording." },
  { id: "GLITCH", name: "Glitch", tier: "MODEL_5_WEB", domain: "Error Recovery", blurb: "Handles failed automation steps: retry, fall back, or escalate." },

  { id: "SONAR", name: "Sonar", tier: "MODEL_6_AUDIO", domain: "Speech-to-Text", blurb: "Transcribes audio quickly and literally." },
  { id: "ORACLE", name: "Oracle", tier: "MODEL_6_AUDIO", domain: "Text-to-Speech", blurb: "Synthesizes natural-sounding audio from text." },
  { id: "HERMES", name: "Hermes", tier: "MODEL_6_AUDIO", domain: "Email & Messaging", blurb: "Drafts correspondence with the right tone for the situation." },
  { id: "AEON", name: "Aeon", tier: "MODEL_6_AUDIO", domain: "Calendar", blurb: "Manages events, thinks in timezones, durations, conflicts." },
  { id: "POLYGLOT", name: "Polyglot", tier: "MODEL_6_AUDIO", domain: "Translation", blurb: "Translates and localizes speech and text between languages." },
];

export const AGENT_MAP: Record<string, AgentMeta> = Object.fromEntries(
  AGENTS.map((a) => [a.id, a])
);
