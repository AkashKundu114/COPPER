# COPPER v3.0.0 — Interface Specification & UI/UX Architecture

> **Document Version:** 3.0.0  
> **Design System:** Forge (Warm Noir & Molten Copper)  
> **Target Framework:** Electron 44.0.0 + React 19 + TypeScript 7 + Tailwind CSS 4 + Vite 8  
> **Status:** Production Specification  

---

## 1. Executive Summary & Design Philosophy

[COPPER](file:///d:/C.O.P.P.E.R/README.md) (**Cognitive Offline Personal Partner & Epistemic Reasoner**) is an air-gapped desktop companion application designed for local-first intelligence. The interface is engineered to bridge deep systems engineering with an intuitive, highly tactile user experience. It orchestrates a local fleet of 12 active specialized agents alongside 5 roadmap targets running entirely offline across consumer GPUs and CPUs.

### Design Principles
1. **The Forge Aesthetic (Warm Noir & Molten Copper):** Unlike sterile flat dashboards or stereotypical dark-black/neon-green AI terminals, COPPER uses an organic dark canvas (`#0A0808`) accented with warm burnished copper tones (`#D4845A`). Dormant subsystems register as dim metallic filaments; active inferences flare with molten white and radiant amber currents.
2. **Epistemic Transparency:** All cognitive state transitions—intent routing, DAG execution waterfalls, memory consolidation, and constitutional guardrail challenges—are visually exposed in real time rather than masked behind generic spinners.
3. **High Information Density with Cognitive Ergonomics:** Clean spatial separation, 1px alpha hairline borders, deterministic layout grids, and keyboard-first accelerators (`Ctrl+K`, `Alt+Space`) enable friction-free operation for technical users.
4. **Air-Gap Assurance:** Constant visual reassurance of zero cloud egress via status indicators, air-gap badges, and explicit network isolation controls.

---

## 2. Design System Tokens (The Forge System)

The design system tokens are codified in [`tailwind.config.js`](file:///d:/C.O.P.P.E.R/frontend/tailwind.config.js) and [`index.css`](file:///d:/C.O.P.P.E.R/frontend/src/index.css).

### 2.1 Color Palette & Surface Ladder

| Token Name | Hex / Value | Semantic Role |
| :--- | :--- | :--- |
| `canvas` | `#0A0808` | Primary application root background (deep noir) |
| `surface.base` | `#121010` | Sidebar, TopBar, panel bases |
| `surface.elevated` | `#1A1716` | Card backgrounds, tool containers, docked surfaces |
| `surface.hover` | `#231F1D` | Interactive element hover state |
| `surface.active` | `#2D2724` | Active button/item selection background |
| `surface.spotlight`| `#362F2B` | Popover highlights, focused search hits |
| `copper.DEFAULT` | `#D4845A` | Brand accent, active focus borders, primary action highlights |
| `copper.bright` | `#E8A47A` | Pulsing synapse sparks, active node cores |
| `copper.dim` | `#9A6040` | Muted copper badges, secondary borders |
| `copper.subtle` | `rgba(212, 132, 90, 0.12)` | Tinted badge fills, input focus glows, selection fills |
| `copper.glow` | `rgba(212, 132, 90, 0.25)` | Drop shadows on active reasoning cores |
| `text.DEFAULT` | `#F2EDEA` | High-contrast readable body text |
| `text.secondary` | `#9A918B` | Labels, subtitles, inactive nav items |
| `text.tertiary` | `#5C5550` | Dividers, timestamps, shortcut badges |
| `text.inverse` | `#0A0808` | Inverted text on solid copper buttons |

### 2.2 Semantic Status & Agent Tier Palette

```
Status Colors:
  ├── success: #5FC992 (dim: rgba(95, 201, 146, 0.12))  — Operational / Online / Clean
  ├── warning: #FFB84D (dim: rgba(255, 184, 77, 0.12))  — Degradation / Review Needed
  ├── danger:  #F06060 (dim: rgba(240, 96, 96, 0.12))   — Blocked / Constitutional Violation
  └── info:    #6BB3E0 (dim: rgba(107, 179, 224, 0.12))  — Informational Telemetry

Agent Tier Palette:
  ├── Tier 1 (Core Reasoning):   #4ADE9A (Emerald)
  ├── Tier 2 (Code Architecture): #38BCD8 (Electric Cyan)
  ├── Tier 3 (OS & Automation):  #5B93F0 (Sapphire Blue)
  ├── Tier 4 (Vision & RPA):     #E06E9E (Neon Pink)
  ├── Tier 5 (Web Intelligence): #E8A840 (Molten Amber)
  └── Tier 6 (Audio & Speech):   #9B6DD8 (Royal Purple)
```

### 2.3 Typography Stack

Configured via variable font assets loaded in [`index.css`](file:///d:/C.O.P.P.E.R/frontend/src/index.css):

1. **Sans-Serif (Primary UI):** `"Inter Variable", Inter, sans-serif`  
   - OpenType Features enabled: `cv02`, `cv03`, `cv04`, `cv11`, `tnum` (tabular numbers for telemetry).  
   - Tracking: `-0.01em` body baseline for sharp legibility on dark displays.
2. **Monospace (Telemetry & Code):** `"Geist Mono Variable", "Geist Mono", monospace`  
   - Utilized for hardware gauges, timestamps, JSON payloads, and terminal outputs.
3. **Brand / Display:** `"Moon Walk", "Inter Variable", sans-serif`  
   - Applied to the COPPER wordmark and major module hero titles.

### 2.4 Motion Presets & Micro-Interactions

Defined in [`motion.ts`](file:///d:/C.O.P.P.E.R/frontend/src/lib/motion.ts) using Framer Motion:

- **`pageTransition`:** `{ initial: { opacity: 0, y: 8 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -4 }, transition: { duration: 0.15, ease: [0.16, 1, 0.3, 1] } }`
- **`springEnter`:** Desktop micro-spring (`stiffness: 400, damping: 30, mass: 0.8`) for card entrances.
- **`springModal`:** Snappy spring (`stiffness: 350, damping: 28`) for the Command Palette and challenge modals.
- **`springTab`:** Smooth glide (`stiffness: 500, damping: 35`) for sliding navigation indicators.
- **Accessibility:** Motion curves automatically degrade gracefully when `prefers-reduced-motion: reduce` is detected.

---

## 3. Desktop Shell & Window Architecture

COPPER v3.0.0 is packaged as a dedicated desktop client powered by Electron 44.0.0.

```
┌────────────────────────────────────────────────────────────────────────┐
│ TopBar (h-11, 44px) — Section Title | Git Air-Gap Badge | Search | Clock│
├───────────┬────────────────────────────────────────────────────────────┤
│ Sidebar   │ Main Viewport (flex-1)                                     │
│ (w-60 ↔   │                                                            │
│  w-14)    │ Page Component (AnimatePresence Transition)                │
│           │                                                            │
│ 240px ↔   │                                                            │
│ 56px      │                                                            │
│           │                                                            │
│           │                                                            │
│           ├────────────────────────────────────────────────────────────┤
│           │ Dock / Overlay Rail (ChatDock / QuickBar / Toast Layer)    │
└───────────┴────────────────────────────────────────────────────────────┘
```

### 3.1 Electron Shell Implementation

Defined in [`electron-main.cjs`](file:///d:/C.O.P.P.E.R/frontend/electron-main.cjs) and [`preload.cjs`](file:///d:/C.O.P.P.E.R/frontend/preload.cjs):

- **Single-Instance Mutex:** Guaranteed via `app.requestSingleInstanceLock()`. Second instances forward focus to the primary window.
- **Hardware Acceleration:** Starts with `force_high_performance_gpu` to enforce discrete NVIDIA GPU usage for WebGL, D3 graphs, and canvas pipelines.
- **Accessibility Engine:** Flags `force-renderer-accessibility` to guarantee screen-reader compatibility with JAWS, NVDA, and Windows Narrator.
- **Frameless Window with Drag Region:** Standard window chrome is replaced with `titleBarStyle: "hidden"` and custom `.drag-region` CSS classes on the header, paired with native Windows min/max/close controls via `titleBarOverlay`.
- **Global QuickBar (`Alt+Space`):** A floating, borderless spotlight window (`680px × 72px` up to `500px`) registered globally via `globalShortcut.register("Alt+Space", toggleQuickBar)`. Auto-centers on the active monitor's cursor position and hides automatically on blur.
- **Security Boundary & IPC Whitelist:** Renderer runs under strict context isolation (`contextIsolation: true`, `nodeIntegration: false`, `webSecurity: true`). All communication passes through `window.copperAPI` with explicit channel whitelisting:
  - Allowed Channels: `quick-bar-hide`, `quick-bar-resize`, `quick-bar-focus-main`, `get-backend-status`, `start-backend`, `stop-backend`, `get-accessibility-status`, `get-activation-status`, `activate-local-gpu`, `activate-owner-code`, `get-system-info`, `run-setup-wizard`.

### 3.2 Layout Structure

- **Collapsible Sidebar ([`Sidebar.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/layout/Sidebar.tsx)):**
  - Expanded: `240px` (`w-60`). Shows brand mark, title, section categories, nav items, and real-time GPU VRAM telemetry gauge.
  - Collapsed: `56px` (`w-14`). Shows icon-only rail with tooltip flyouts and quick-collapse toggle.
  - Telemetry: Polls `/api/system/telemetry` every 4 seconds to display VRAM utilization (e.g. `0.22 / 8.00 GB (2.8%)`).
- **TopBar ([`TopBar.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/layout/TopBar.tsx)):**
  - Height: Fixed `44px` (`h-11`), styled with backdrop blur (`surface-base/90`) and subtle border.
  - Left: Active section title, repository/branch indicator, and `AIR-GAP` security badge.
  - Center: Command Palette quick-search input button (`Ctrl+K`).
  - Right: System time displays (UTC and Local), SoundFX toggle, smart clipboard drawer trigger, and cognitive status badge.

---

## 4. The 16 Primary Application Views

The interface routes between 16 dedicated views managed in [`App.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/App.tsx) and partitioned across three sidebar categories:

```
WORKSPACE
  ├── 1. Dashboard         — Mission Cockpit & System Health
  ├── 2. Chat              — Pair Programming & Conversation Branching
  ├── 3. Voice Companion   — Holographic HUD, ThinkingOrb & Full-Duplex Audio
  └── 4. Campaigns         — DeltaX Campaign Intelligence & Ad-Tech Telemetry

PRODUCTIVITY
  ├── 5. Today             — Daily Standup, Priorities & Focus Blocks
  ├── 6. Meetings          — Architecture Notes, Transcripts & Action Items
  ├── 7. Alerts            — High-Priority System Events & Security Feeds
  └── 8. Wellness          — Cognitive Ergonomics & Nutrition Telemetry

INTELLIGENCE
  ├── 9. Memory            — D3 Knowledge Graph, Causal Explorer & Provenance
  ├── 10. Agents           — Agent Registry, Tool Fleet, Personas & Skills
  ├── 11. Benchmarks       — Real-Time Latency, Token/s & Hardware Gauges
  ├── 12. Security         — Guardian Gatekeeper, Friction Index & Audit Trail
  ├── 13. Activity         — OpenTelemetry Trace Waterfall & Task Graph Visualizer
  ├── 14. Insights         — Epistemic Analytics, Cognitive Load & Habit Trends
  ├── 15. Optimization     — Self-Improvement Loop, Synthetic Judge & LoRA Fine-Tuning
  └── 16. Settings         — Model Fleet Configuration, Audio Devices & Air-Gap Flags
```

### 4.1 Detailed View Specifications

| View Name | Route ID | Primary Purpose & Key Components | Backend API Backing |
| :--- | :--- | :--- | :--- |
| **Dashboard** | `dashboard` | Mission Cockpit, GPU memory gauge, quick actions, active agent status, recent episodes, system health summary. | [`/api/system/telemetry`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/telemetry_routes.py), `/api/episodes` |
| **Chat** | `chat` | Multi-turn conversational interface with tree branching ([`BranchHeader`](file:///d:/C.O.P.P.E.R/frontend/src/components/chat/BranchHeader.tsx), [`BranchCompareModal`](file:///d:/C.O.P.P.E.R/frontend/src/components/chat/BranchCompareModal.tsx)), syntax-highlighted streaming markdown, and inline DAG execution blocks. | [`/api/chat`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/chat.py), `/api/chat/branches` |
| **Voice Companion** | `companion` | Immersive full-screen HUD with [`ThinkingOrb`](file:///d:/C.O.P.P.E.R/frontend/src/components/hud/ThinkingOrb.tsx), continuous hands-free VAD, push-to-talk, ambient [`VisionViewfinder`](file:///d:/C.O.P.P.E.R/frontend/src/components/hud/VisionViewfinder.tsx), and speech transcript overlays. | [`/api/voice`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/voice.py), [`/api/wake`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/wake.py) |
| **Campaigns** | `campaigns` | DeltaX-grade ad campaign anomaly detection, budget allocation optimization, and telemetry. | [`/api/campaigns`](file:///d:/C.O.P.P.E.R/backend/app/api/campaign_routes.py) |
| **Today** | `today` | Daily standup briefing, schedule timeline, priority tasks, focus block timers, and cognitive energy tracker. | [`/api/schedule`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/schedule.py), `/api/reminders` |
| **Meetings** | `meetings` | Architecture notes, meeting transcript summarization, action item extraction, and speaker diarization. | [`/api/meetings`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/meetings.py) |
| **Alerts** | `email` | Aggregated notification feed, priority system warnings, alert triage, and automated action execution. | [`/api/notifications`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/notifications.py), `/api/email` |
| **Wellness** | `food` | Workday ergonomics, biometric fatigue models, meal intake tracking, and cognitive health correlations. | [`/api/system/wellness`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/system.py) |
| **Memory** | `memory` | Multi-tab memory console: D3 Knowledge Graph ([`KnowledgeGraphView`](file:///d:/C.O.P.P.E.R/frontend/src/components/knowledge/KnowledgeGraphView.tsx)), Epistemic Fact Store, Causal Explorer, and Provenance Lineage. | [`/api/memory`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/memory.py), `/api/knowledge-graph`, `/api/causal` |
| **Agents** | `agents` | Fleet directory for 12 active + 5 planned agents, tool execution catalog, agency personas editor, and scientific skills matrix. | [`/api/agents`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/agents.py), `/api/skills`, `/api/catalog` |
| **Benchmarks** | `benchmarks` | Real-time routing benchmarks, latency percentiles, VRAM load profiling, and token generation speed counters. | [`/api/telemetry`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/telemetry_routes.py), `/api/routing-analytics` |
| **Security** | `security` | Safety firewall overview, Guardian friction index configuration, constitutional policies, and tamper-proof audit trail. | [`/api/guardian`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/guardian.py), `/api/audit` |
| **Activity** | `activity` | Distributed OpenTelemetry trace waterfall visualizer, task graph execution logs, and live system log stream. | [`/api/orchestration/traces`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/orchestration.py) |
| **Insights** | `insights` | Long-term epistemic analytics, knowledge acquisition velocity, topic clusters, and cognitive load heatmaps. | [`/api/cognitive`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/cognitive.py), `/api/insights` |
| **Optimization** | `self-improvement` | Autonomous reflection engine, synthetic judge failure analysis, prompt evolution diffs, and LoRA adapter training. | [`/api/self-improvement`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/self_improvement.py), `/api/training` |
| **Settings** | `settings` | Hardware acceleration overrides, LLM model directory paths, audio I/O selector, and full memory reset tools. | [`/api/system/settings`](file:///d:/C.O.P.P.E.R/backend/app/api/routes/system.py) |

---

## 5. Key Interactive Components

### 5.1 NeuralBrain & Knowledge Graph Visualizers
- **Orbital Agent Visualizer ([`NeuralBrain.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/brain/NeuralBrain.tsx)):**
  - Renders all 12 active specialist agents and 5 roadmap targets in concentric orbital tiers around the central COPPER core.
  - Orbit physics use native CSS `transform: rotate()` animations (faster inner orbits, slower outer rings), ensuring zero CPU overhead on the React thread.
  - Synapse pathways flare from dim bronze to molten white-hot when thoughts route through specific agents.
  - Full screen-reader directory included via accessible semantic list and ARIA status attributes.
- **D3 Force Knowledge Graph ([`KnowledgeGraphView.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/knowledge/KnowledgeGraphView.tsx)):**
  - Utilizes `d3.forceSimulation` with many-body charge repulsion (`-300`), center gravity, and collision radius buffers.
  - Features curved multi-edges for dual-relationship nodes, pan/zoom canvas controls, and click-to-inspect entity drawers.

### 5.2 Command Palette ([`CommandPalette.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/common/CommandPalette.tsx))
- Triggered globally via `Ctrl+K` or top navigation search trigger.
- Fuzzy-searches across all 16 views, active agents, tools, memory entities, and system actions.
- Keyboard navigation (arrows + enter + escape) with snappy spring modal animation.

### 5.3 Guardian Challenge Modal ([`GuardianChallengeModal.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/chat/GuardianChallengeModal.tsx))
- Blocks execution whenever an agent proposes an action exceeding safety boundaries (e.g. file deletion, shell execution, or high-risk parameters).
- Displays friction index score, reversibility assessment, and three explicit options: *Follow Recommendation*, *Proceed Anyway*, or *Discuss in Chat*.

### 5.4 Conversation Branching ([`BranchHeader.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/chat/BranchHeader.tsx) & [`BranchCompareModal.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/chat/BranchCompareModal.tsx))
- Allows users to branch conversations from any previous message to test alternate prompts or model solutions.
- Displays branch switcher, branch metadata, side-by-side diff comparison, and branch merge back to `default`.

### 5.5 Smart Clipboard Drawer ([`SmartClipboardDrawer.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/ambient/SmartClipboardDrawer.tsx))
- Sliding side drawer triggered from TopBar or ambient clipboard events.
- Performs automatic content classification (code snippet, URL, tabular data, log stack) with one-click dispatch to specialist agents.

### 5.6 SpiderSense Toast ([`SpiderSenseToast.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/alerts/SpiderSenseToast.tsx))
- Proactive alert toast anchored in the lower viewport corner.
- Surfaces background system health alerts, calendar schedule warnings, and autonomous recommendations with Snooze/Dismiss/Intervene actions.

### 5.7 Document Reader Modal ([`DocumentReaderModal.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/components/documents/DocumentReaderModal.tsx))
- Ingestion and reading surface supporting Markdown, PDF, DOCX, and raw code.
- Features semantic chunk inspection, extraction confidence scoring, and direct agent reference tagging.

---

## 6. Audio & Multimodal Voice Architecture

COPPER v3.0.0 incorporates a complete, real offline speech and audio pipeline. The interface is tightly coupled with backend audio services to provide fluid, sub-300ms multimodal interaction without any cloud dependency.

```
┌─────────────────┐       ┌────────────────┐       ┌────────────────────────┐
│ openWakeWord    │ ───>  │ Silero VAD v5  │ ───>  │ Whisper Large v3 Turbo │
│ ("Hey COPPER")  │       │ (Speech Cuts)  │       │ (faster-whisper INT8)  │
└─────────────────┘       └────────────────┘       └────────────────────────┘
                                                                │
                                                                ▼
┌─────────────────┐       ┌────────────────┐       ┌────────────────────────┐
│ Real-Time Audio │ <───  │ Kokoro-82M     │ <───  │ LLM Inference Engine   │
│ Playback & HUD  │       │ ONNX TTS       │       │ (14B Sovereign Core)   │
└─────────────────┘       └────────────────┘       └────────────────────────┘
```

### 6.1 Audio Subsystem Specifications

1. **Acoustic Wake Word Listener ([`wake_word_service.py`](file:///d:/C.O.P.P.E.R/backend/app/services/wake_word_service.py)):**
   - Engine: `openWakeWord` running `hey_copper.onnx` (continuous CPU-only acoustic scoring, ~1-3% CPU on a single core, 0% GPU).
   - In-memory 50-chunk audio ring buffer. Zero raw audio persisted to disk.
   - On detection: Triggers instant WebSocket broadcast `{"type": "wake_detected"}` to animate the frontend listening pulse.
2. **Voice Activity Detection (VAD):**
   - `Silero VAD v5` detects precise speech boundaries and handles barge-in interruptions when the user speaks while COPPER is outputting voice.
3. **Speech-To-Text (STT):**
   - Engine: `Whisper Large v3 Turbo` via `faster-whisper` (INT8 quantized on CPU/CUDA).
   - Delivers sub-second transcription with automated language probability scoring.
4. **Neural Text-To-Speech (TTS) ([`audio_service.py`](file:///d:/C.O.P.P.E.R/backend/app/services/audio_service.py)):**
   - Primary: `Kokoro-82M ONNX` neural speech synthesis (<80ms first-chunk latency, high prosody).
   - Voice Bank: Includes neural profiles (*Bella, Nicole, Michael, Emma*).
   - Fallback Tiers: `Piper ONNX` local synthesis $\to$ Windows SAPI5 (`Microsoft Zira`) $\to$ synthetic tone generator.
5. **Smart Spoken Summarization:**
   - Implemented via `audio_service.py:format_spoken_summary()`.
   - Long code blocks, tables, and bullet lists are automatically detected and omitted from voice audio. COPPER speaks a punchy 1-2 sentence overview (*"I've generated the code and placed it on your screen for you."*), ensuring speech remains conversational while full data is presented in the chat feed.
6. **Voice Companion HUD ([`CompanionHUDView.tsx`](file:///d:/C.O.P.P.E.R/frontend/src/pages/CompanionHUDView.tsx)):**
   - Integrates the official `thinking-orbs` component reacting to live states:
     - `breathing`: Idle standby.
     - `listening`: Recording user speech.
     - `solving`: LLM reasoning and intent routing.
     - `weaving`: Kokoro TTS streaming audio output.
     - `connecting`: Hands-free standby connection.

---

## 7. Multi-Agent Fleet Parity Matrix

The interface reflects the exact 12 implemented backend agents defined in [`agents.ts`](file:///d:/C.O.P.P.E.R/frontend/src/constants/agents.ts) and backend service handlers, plus 5 planned architectural roadmap targets.

### 7.1 Active Specialist Agents (12 Implemented)

| Codename | Agent Name | Tier | Domain & Capability | Primary Local Model |
| :--- | :--- | :--- | :--- | :--- |
| **ATLAS** | Chat | Tier 1 (Core) | Conversational dialogue & intent decomposition | `qwen2.5:14b` |
| **VULCAN** | Coding | Tier 2 (Code) | Full-stack generation, refactoring, code sandbox | `qwen2.5-coder-abliterated:14b` |
| **SCRIBE** | Document | Tier 6 (Audio) | Document generation (PDF, DOCX, Markdown) | `phi4:14b` |
| **DAEMON** | Automation | Tier 3 (OS) | CLI execution, desktop automation, file tools | `mistral-nemo:12b` |
| **CHRONOS** | Reminder | Tier 1 (Core) | Calendar scheduling, focus blocks, deadlines | `qwen2.5:14b` |
| **PROMETHEUS**| Research | Tier 1 (Core) | Hybrid RAG (vector + BM25 RRF), re-ranking | `deepseek-r1:14b` |
| **ARGUS** | Vision | Tier 4 (Vision) | Desktop UI perception, bounding box coordinate detection | `qwen2.5-vl:3b` |
| **PICASSO** | Image | Tier 4 (Vision) | 1-step offline image generation studio | `sd_turbo.safetensors` |
| **RAPTOR** | Web Search | Tier 5 (Web) | Privacy search via SearXNG with PII scrubbing | `mistral-nemo:12b` |
| **DELTA** | Campaign | Tier 1 (Core) | Ad-tech telemetry, anomaly detection, budget optimization | `deepseek-r1:14b` |
| **NEXUS** | Planner | Tier 1 (Core) | Task decomposition, DAG construction, agent swarming | `deepseek-r1:14b` |
| **AEGIS** | Guardian | Tier 1 (Core) | Safety gatekeeper, reversibility scoring, friction policies | `qwen2.5:1.5b` |

### 7.2 Architectural Roadmap Targets (5 Planned)

| Codename | Agent Name | Tier | Intended Domain | Target Architecture |
| :--- | :--- | :--- | :--- | :--- |
| **PSYCHE** | Behavior | Tier 1 (Core) | Circadian rhythms, fatigue modeling, habit optimization | `qwen2.5:14b` |
| **SOLIS** | Nutrition | Tier 3 (OS) | Biometric intake tracking, meal scheduling | `smollm2:1.7b` |
| **JUSTICIA** | Evaluator | Tier 1 (Core) | Hallucination verification, rubric scoring, LLM judge | `deepseek-r1:14b` |
| **SYMPHONY** | Orchestrator | Tier 1 (Core) | High-density dynamic subagent swarming & consensus | `qwen2.5:14b` |
| **ECHO** | Voice | Tier 6 (Audio) | Sub-300ms full-duplex speech with barge-in | `kokoro+whisper` |

---

## 8. Verified Codebase File Map

The frontend and backend implementation paths referenced across this specification:

```
frontend/
  ├── electron-main.cjs               # Electron 44 main process, GPU flags, QuickBar, single-instance lock
  ├── preload.cjs                     # Context isolation script, secure IPC channel whitelist
  ├── package.json                    # Dependencies: React 19, TypeScript 7, Tailwind 4, Vite 8, Electron 44
  ├── tailwind.config.js              # Forge design system color tokens, radii, shadows, font families
  └── src/
      ├── App.tsx                     # Root shell, sidebar collapse state, modals, active section switcher
      ├── index.css                   # Font imports, base reset, focus-visible styles, scrollbar styling
      ├── constants/
      │   └── agents.ts               # Fleet definition: 12 ACTIVE_AGENTS + 5 PLANNED_AGENTS, tier metadata
      ├── components/
      │   ├── layout/
      │   │   ├── Sidebar.tsx         # 240px ↔ 56px navigation rail, VRAM telemetry gauge
      │   │   └── TopBar.tsx          # 44px header, section title, air-gap badge, time display, mute toggle
      │   ├── brain/
      │   │   └── NeuralBrain.tsx     # Orbital multi-agent visualization, tier rings, thinking pulse
      │   ├── knowledge/
      │   │   └── KnowledgeGraphView.tsx # D3 force-directed simulation, interactive inspect drawer
      │   ├── chat/
      │   │   ├── ChatDock.tsx        # Glass-morphic chat input dock with mic & action controls
      │   │   ├── MessageFeed.tsx     # Streaming message thread with DAG task visualizer
      │   │   ├── BranchHeader.tsx    # Branch switcher, branch create, and compare trigger
      │   │   └── BranchCompareModal.tsx # Side-by-side branch comparison and merge dialog
      │   ├── hud/
      │   │   ├── ThinkingOrb.tsx     # Official ThinkingOrb audio visualizer wrapper
      │   │   ├── HolographicCore.tsx # HUD core visualizer interface
      │   │   └── VisionViewfinder.tsx# Ambient screen capture and vision inspection viewfinder
      │   ├── common/
      │   │   └── CommandPalette.tsx  # Global Ctrl+K spotlight modal
      │   └── alerts/
      │       └── SpiderSenseToast.tsx# Proactive system anomaly & suggestion toasts
      └── pages/
          ├── DashboardView.tsx       # Cockpit view with hardware metrics & episode history
          ├── CompanionHUDView.tsx    # Full-duplex voice companion HUD
          ├── MemoryView.tsx          # Multi-tab memory console (Graph, Epistemic, Causal, Provenance)
          ├── AgentRegistry.tsx       # Agent catalog, tools, agency personas, scientific skills
          ├── ActivityView.tsx        # OpenTelemetry distributed trace waterfall visualizer
          ├── SelfImprovementView.tsx # Self-reflection, synthetic judge, LoRA training interface
          ├── BenchmarkMetricsView.tsx# Hardware throughput, latency percentiles, memory profiling
          ├── SecurityCenter.tsx      # Guardian safety firewall & constitutional audit trail
          └── SettingsView.tsx        # System configuration, model paths, audio I/O settings

backend/
  └── app/
      ├── core/
      │   ├── config.py               # Pydantic v2 settings (paths, models, wake-word, sandbox)
      │   └── logger.py               # Structured logger
      ├── database/
      │   ├── postgres.py             # SQLite / PostgreSQL async engine abstraction
      │   └── models/                 # SQLAlchemy schemas (agent_registry, memory_v2, episode, etc.)
      ├── services/
      │   ├── audio_service.py        # Whisper STT, Kokoro-82M TTS, Piper fallback, spoken summarization
      │   ├── wake_word_service.py    # openWakeWord "Hey COPPER" acoustic listener & VAD gating
      │   ├── chat_service.py         # Multi-turn dialogue orchestration & model inference
      │   └── guardian_service.py     # Constitutional boundary validation & friction index scoring
      └── api/
          ├── websocket/manager.py    # Real-time WebSocket connection manager & event dispatch
          └── routes/                 # FastAPI routes (chat, voice, wake, memory, agents, telemetry, etc.)
```
