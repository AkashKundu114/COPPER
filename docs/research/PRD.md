# C.O.P.P.E.R. Product Requirements Document (PRD)

---

## 1. Executive Summary & Product Identity

**C.O.P.P.E.R.** (Centralized Omnifunctional Personal Productivity and Execution Routine) is positioned as:

> **"Your Personal AI Operating System"**

COPPER is a persistent, adaptive, local-first personal productivity and guardian AI environment. It combines persistent user memory, daily scheduling, task execution, coding assistance, project management, behavioral tracking, nutrition organization, research, and multi-agent orchestration into a desktop operating environment.

### Core Philosophical Identity
- **Understand me:** Remembers what matters with epistemic precision.
- **Help me execute:** Facilitates scheduling, coding, and workflow tasks.
- **Challenge me when necessary:** Level 2 Guardian friction for off-schedule or high-risk decisions.
- **Protect my privacy:** Operates 100% offline by default; zero data egress without explicit confirmation.
- **Keep me in control:** Human-in-the-loop approval, no dark patterns, no manipulative shaming.

---

## 2. Desktop Application Structure & 13 Core Sections

COPPER is structured around a persistent 13-section navigation sidebar:

1. **Dashboard:** Home screen greeting ("Good morning. You have 4 important things today."), schedule overview, productivity status (neutral metrics, no shaming).
2. **Conversation:** Text & Voice hybrid input/output dock with equalizer visualizer.
3. **Today:** Day/Week/Month schedule timeline with focus blocks and COPPER schedule recommendations.
4. **Tasks:** Drag-and-drop task cards (Inbox, Planned, Active, Blocked, Completed, Archived).
5. **Projects:** Project health indicators (Healthy, At Risk, Blocked) with evidence explanations.
6. **Memory:** Epistemic facts, observations, hypotheses with confidence scores, evidence counts, and user controls ([Edit], [Confirm], [Forget], [Mark incorrect]).
7. **Agents:** Agent Registry manager showing active models, scores, and hot-swap controls.
8. **Activity:** Agent run history and step-by-step execution traces.
9. **Insights:** Evidence-based focus statistics and working pattern analytics.
10. **Self-Improvement:** Training example inspector, candidate model benchmarks, and rollback controls.
11. **Security:** Zero-trust Data Firewall, secret masking (`sk-••••`), human-readable audit log, export & purge.
12. **Food / Nutrition:** Grocery list, meal log, budget tracking, general nutrition information (non-medical).
13. **Settings:** Voice devices, Local LLMs, Keyboard shortcuts, Developer Mode.

---

## 3. Guardian Alignment Framework (Levels 0–3)

Evaluates user instructions against schedule commitments, fatigue, and long-term goals:

- **Level 0 (Direct Execution):** Standard task request. Execute immediately.
- **Level 1 (Nudge / Suggestion):** Minor optimization opportunity. Provide inline tip while executing.
- **Level 2 (Challenge / Friction):** Moderate conflict (e.g., late-night heavy task before deadline). Trigger `GuardianChallengeModal` with evidence, confidence, recommendation, and options ([Follow recommendation], [Proceed anyway], [Discuss]).
- **Level 3 (Safety Boundary):** Severe conflict with data integrity or system safety. Halt cleanly with clear explanation.

---

## 4. Voice Privacy & Interaction Specifications

- **Voice Controls:** Push-to-talk, click-to-speak, recording state (`Ready`, `Listening...`, `Processing...`, `Speaking...`, `Paused`).
- **Privacy Rule:** Microphone requires explicit user permission; top bar displays `🎙 Ready` or active recording pulse. Never record silently.
- **Output Toggles:** Switch between `Text only`, `Voice only`, and `Text + Voice`.

---

## 5. Security & Privacy Architecture

- **100% Offline Default:** Local model execution via Ollama.
- **Secret Masking:** Automatically masks API keys, passwords, tokens (`sk-••••••••`).
- **Data Firewall:** Scans all outgoing payloads for PII redaction if cloud fallback is enabled.
- **Audit Log:** Human-readable log of all agent runs, tool calls, and API events.
- **Data Export & Deletion:** Granular memory deletion, encrypted JSON export, and permanent `delete-all` capability.
