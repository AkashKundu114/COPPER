# C.O.P.P.E.R. UI/UX Design Brief & Desktop Operating System Spec

---

## 1. Design Philosophy & Product Identity

COPPER is positioned as **"Your Personal AI Operating System"**.

### Core Philosophical Pillars
- **Understand me:** Remembers what matters with epistemic precision across conversations, workflows, and long-term memory.
- **Help me execute:** Orchestrates complex workflows, day planning, meeting intelligence, multi-agent campaigns, and coding.
- **Challenge me when necessary:** Guardian Level 2 friction for high-risk actions, off-schedule behaviors, or conflicting decisions.
- **Protect my privacy:** 100% local-first operation; offline GGUF inference with zero data egress without explicit user consent.
- **Keep me in control:** Transparent controls, auditable reasoning, explicit permission gates, and zero manipulative shaming or dark patterns.

---

## 2. Forge Design System Foundation

COPPER's visual language is defined by the **Forge Design System** — an industrial, warm-noir aesthetic pairing a deep obsidian canvas with molten copper conductivity accents. Dormant elements remain muted metallic bronze, while active execution flaring channels energy across conductors.

### Color Tokens

| Token Category | Token Name | Value | Usage |
| :--- | :--- | :--- | :--- |
| **Surface Ladder** | `canvas` | `#0A0808` | Primary application root background |
| | `surface.base` | `#121010` | Sidebar, panels, card backgrounds |
| | `surface.elevated` | `#1A1716` | Popovers, modals, dropdown containers |
| | `surface.hover` | `#231F1D` | Interactive element hover states |
| | `surface.active` | `#2D2724` | Active tabs, pressed buttons, selected list rows |
| | `surface.spotlight` | `#362F2B` | Highlighted cards, focal containers |
| **Brand Accent** | `copper.DEFAULT` | `#D4845A` | Primary brand accent, active conductors, key actions |
| | `copper.bright` | `#E8A47A` | Focused interactive states, lit filaments |
| | `copper.dim` | `#9A6040` | Muted badges, secondary accents |
| | `copper.subtle` | `rgba(212, 132, 90, 0.12)` | Tinted tag fills, subtle indicator backdrops |
| | `copper.glow` | `rgba(212, 132, 90, 0.25)` | Conductive edge pulses, active agent node glow |
| **Text Hierarchy** | `text.DEFAULT` | `#F2EDEA` | High-contrast body text and primary labels |
| | `text.secondary` | `#9A918B` | Subtitles, descriptive text, metadata |
| | `text.tertiary` | `#5C5550` | Disabled text, subtle hints, placeholder text |
| | `text.inverse` | `#0A0808` | Dark text on bright copper accent surfaces |
| **Semantic / Status** | `success` | `#5FC992` | Healthy states, completed tasks, local-mode badge |
| | `warning` | `#FFB84D` | Advisory warnings, pending actions, latency flags |
| | `danger` | `#F06060` | Guardian challenges, destructive confirmation, errors |
| | `info` | `#6BB3E0` | Neutral telemetry, contextual notes, cloud fallback badge |
| **Borders** | `border.DEFAULT` | `rgba(255, 255, 255, 0.05)` | Default hairline dividers |
| | `border.subtle` | `rgba(255, 255, 255, 0.08)` | Card and panel frame boundaries |
| | `border.highlight` | `rgba(255, 255, 255, 0.14)` | Hovered element outline |
| | `border.copper` | `rgba(212, 132, 90, 0.40)` | Active focus borders, selected node ring |

### Typography

- **Primary Sans:** `'Inter Variable'`, `Inter`, `-apple-system`, `BlinkMacSystemFont`, `'Segoe UI'`, `sans-serif` — Used for all primary interface labels, navigation, conversation text, and metrics.
- **Monospace:** `'Geist Mono Variable'`, `'Geist Mono'`, `'JetBrains Mono'`, `Menlo`, `monospace` — Used for code generation, terminal execution, system telemetry, JSON payloads, and token metrics.
- **Brand Wordmark:** `'Moon Walk'`, `'Inter Variable'`, `sans-serif` — Used for the COPPER brand masthead.

---

## 3. Desktop Application Structure & Layout

COPPER operates as an Electron desktop application built on React 19, TypeScript, and Tailwind CSS 4 with a persistent, collapsible 3-group navigation rail and a dynamic main workspace:

```
┌────────────────────────────────────────────────────────────────────────┐
│ COPPER                       Local   Private   Ready  [Profile]        │
├──────────────┬─────────────────────────────────────────────────────────┤
│ WORKSPACE    │                                                         │
│ • Dashboard  │                                                         │
│ • Chat       │                     MAIN WORKSPACE                      │
│ • Voice      │                                                         │
│ • Campaigns  │    - Dashboard / Today Overview / Focus Session         │
│ PRODUCTIVITY │    - Hybrid Text + Voice Chat & Equalizer Bar           │
│ • Today      │    - Multi-Agent Campaign Intelligence & Goals          │
│ • Meetings   │    - Epistemic Memory Center & Consent Explorer         │
│ • Alerts     │    - Agent Swarm Registry & Hot-Swap Manager            │
│ • Wellness   │    - Zero-Trust Security Center & Data Firewall         │
│ INTELLIGENCE │    - Self-Improvement & Benchmark Telemetry             │
│ • Memory     │    - Activity Execution Graph & System Health Logs      │
│ • Agents     │                                                         │
│ • Benchmarks │                                                         │
│ • Security   │                                                         │
│ • Activity   │                                                         │
│ • Insights   │                                                         │
│ • Optimiz.   │                                                         │
│ • Settings   │                                                         │
└──────────────┴─────────────────────────────────────────────────────────┘
```

### 16 Persistent Navigation Items Across 3 Groups

#### Group 1: WORKSPACE
1. **Dashboard** (`dashboard`): Central operating overview including contextual greetings, live daily timeline, high-priority tasks, active campaign summaries, and system telemetry.
2. **Chat** (`chat`): Hybrid text conversational workspace powered by the 30-agent swarm, streaming token responses, code blocks with syntax highlighting, and dynamic agent handoffs.
3. **Voice** (`companion`): Real-time interactive voice interface featuring on-device Whisper speech-to-text, Piper neural speech synthesis, and live waveform frequency visualization.
4. **Campaigns** (`campaigns`): Multi-agent strategic planning interface for complex, long-running initiatives, goal decomposition, milestone tracking, and autonomous execution pipelines.

#### Group 2: PRODUCTIVITY
5. **Today** (`today`): Time-blocked day planner, agenda timelines, calendar event synchronizer, and focus block recommendations.
6. **Meetings** (`meetings`): Pre-meeting briefing preparation, participant context, live audio transcription, and post-call action item extraction.
7. **Alerts** (`email`): Unified notification center triaging critical events, calendar alerts, background execution results, and communication updates.
8. **Wellness** (`food`): Daily habit tracking, non-medical nutrition logging, meal planning, hydration monitoring, and focus fatigue break suggestions.

#### Group 3: INTELLIGENCE
9. **Memory** (`memory`): Epistemic memory browser showing facts, user preferences, observations, and hypotheses with confidence percentages, evidence counts, and user actions (`Edit`, `Confirm`, `Forget`, `Mark Incorrect`).
10. **Agents** (`agents`): Swarm registry viewer displaying active models, tier categories (Core, Code, OS, Vision, Web, Audio), familiarity scores, and hot-swap controls.
11. **Benchmarks** (`benchmarks`): Local model performance evaluations, latency benchmarking (time-to-first-token, generation tokens/sec), memory footprint, and quality metrics.
12. **Security** (`security`): Zero-Trust Data Firewall, secret masking (`sk-••••`), tool permission policies, sandboxed execution audits, and granular data purge/export tools.
13. **Activity** (`activity`): Real-time execution logs, TFP-Router dispatch traces, TaskGraph DAG step logs, tool outputs, and system telemetry (VRAM, CPU, RAM).
14. **Insights** (`insights`): Evidence-based productivity analytics, recurring pattern detection, deep focus metrics, and work-rest rhythm reports.
15. **Optimization** (`self-improvement`): Self-healing engine, prompt distillation results, training exemplar review, routing weight adjustments, and rollback controls.
16. **Settings** (`settings`): Global system preferences, audio I/O hardware selectors, local GGUF model paths, API fallback configurations, Forge theme toggles, and Developer Mode.

---

## 4. Global Top Bar Status Indicators

- **Left:** Active section title, breadcrumb path, and sidebar collapse/expand toggle.
- **Center:** Active agent attribution pill (e.g., `AXIS`, `GUARDIAN`, `NEXUS`) and neural reasoning activity indicator.
- **Right:**
  - **Model Mode:** `Local` (Green badge; 100% on-device GGUF inference) or `Cloud` (Blue badge; opt-in external fallback enabled).
  - **Privacy Status:** `Private` (Local zero-egress encryption active).
  - **Voice Status:** `Ready` / `Listening...` / `Processing...` / `Speaking...`.
  - **Hardware Gauge:** Real-time VRAM allocation and memory headroom indicator.
  - **Command Palette:** Quick-trigger shortcut trigger (`Ctrl+K` / `Cmd+K`).
  - **Profile & Notification Bell:** User profile drawer toggle and system alert badges.

---

## 5. Voice Interaction & Privacy UI

- **Voice Controls:** `[ + ] [ Text input... ] [ Mic ] [ Send ]` integrated into the chat dock.
- **Equalizer Bar:** Dynamic audio waveform (`SpeakingBar` component) that animates during speech synthesis and audio playback.
- **Voice States:** Seamless transitions through `Ready`, `Listening...`, `Processing...`, `Speaking...`, and `Paused`.
- **Playback Controls:** Inline audio controls for `Play`, `Pause`, and `Stop`.
- **Output Modalities:** Quick toggle between `Text only`, `Voice only`, and `Text + Voice`.
- **Privacy-First Audio Protocol:** Microphone capture requires explicit user activation; an unambiguous visual recording indicator remains active whenever audio hardware is open; speech processing is executed locally via Whisper with zero audio transmission to external servers.

---

## 6. Guardian Disagreement UI & Friction Tiers

When COPPER identifies high risk, conflicting goals, or schedule deviations, the Guardian agent intervenes through graduated friction:

- **Level 1 (Advisory Warning):** Non-intrusive contextual inline banner with evidence.
- **Level 2 (Active Challenge Modal):** Full friction challenge requiring explicit user confirmation before high-impact or conflicting operations proceed:

```
┌────────────────────────────────────────────────────────────────────────┐
│ COPPER RECOMMENDS AGAINST THIS                                         │
│                                                                        │
│ I disagree with this plan because it conflicts with tomorrow's         │
│ interview deadline.                                                    │
│                                                                        │
│ Evidence:                                                              │
│ • Interview scheduled for tomorrow 9:00 AM                             │
│ • 2 preparation tasks remain incomplete                                │
│ • Only 45 minutes of preparation completed today                       │
│                                                                        │
│ Confidence: High (92%)                                                 │
│ Recommendation: Complete preparation tasks first.                      │
│                                                                        │
│ [ Follow COPPER's Recommendation ]  [ Proceed Anyway ]  [ Discuss ]    │
└────────────────────────────────────────────────────────────────────────┘
```

*Note: Phrased in neutral, objective, non-manipulative language. Never uses patronizing expressions such as "COPPER knows best" or emotional pressure.*

---

## 7. Terminal Safety, Forge Sandbox & Tool Execution UI

### Safety Tiers
- **Tier 1 (Harmless / Read-Only):** Direct execution (`ls`, `git status`, file read) with instant `[Run]` button.
- **Tier 2 (State-Altering / Consequential):** Requires preview modal (`[Review Command]` $\rightarrow$ `[Run]` / `[Cancel]`).
- **Tier 3 (Destructive / High-Risk):** Displays Command, Target Path/Resource, Expected Effects, Risk Severity, and requires explicit typed or two-step confirmation before execution.

### Tool Execution Progress & Sandboxing
- Collapsible DAG step pipeline (`[Done] Read schedule` $\rightarrow$ `[Active] Checking priorities` $\rightarrow$ `[Pending] Updating tasks`).
- Code and shell scripts run inside the Forge Sandbox isolation environment with resource limits.
- Automatic secret masking: API keys, access tokens, and private credentials are automatically redacted across all display surfaces and logs (`sk-••••••••`).

---

## 8. Developer Mode & Deep Observability

When Developer Mode is enabled in Settings, COPPER exposes deep engine telemetry:

- **TFP-Router Trace:** Visualizes the Topological Failure-Predicting Router pipeline (Stage 0 dynamic memory match, Stage 1 fast smalltalk filter, Stage 2 weighted keyword pattern matching with negative rule suppressions, Stage 3 consequential safety check, routing entropy $H(R)$, and DAG cascade risk metrics).
- **NEXUS TaskGraph DAG Execution:** Interactive topological dependency graph displaying concurrent task layers, inter-agent messages passed over the ContextBus, intermediate step artifacts, and execution latency per node.
- **Hardware & Inference Telemetry:** Real-time VRAM allocation tracking, llama-cpp-python context window usage, tokens/sec generation rates, time-to-first-token (TTFT), and Piper TTS / Whisper inference latency.
- **Zero-Trust Boundary Inspection:** Displays data isolation verification ensuring secrets, private keys, hidden system prompts, and internal chain-of-thought traces remain shielded from user-facing logs and exports.
