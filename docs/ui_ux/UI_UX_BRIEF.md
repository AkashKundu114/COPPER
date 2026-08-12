# C.O.P.P.E.R. UI/UX Design Brief & Desktop Operating System Spec

---

## 1. Design Philosophy & Product Identity

COPPER is positioned as **"Your Personal AI Operating System"**.

### Core Philosophical Pillars
- **Understand me:** Remembers what matters with epistemic precision.
- **Help me execute:** Facilitates scheduling, task planning, and coding.
- **Challenge me when necessary:** Guardian Level 2 friction for risky or off-schedule decisions.
- **Protect my privacy:** 100% local-first operation; zero data egress without explicit permission.
- **Keep me in control:** Transparent controls, no dark patterns, no manipulative shaming.

---

## 2. Desktop Application Structure

COPPER features a responsive, keyboard-friendly desktop application layout:

```
┌────────────────────────────────────────────────────────────────────────┐
│ COPPER                       ● Local   🔒 Private   🎙 Ready  [Profile]│
├──────────────┬─────────────────────────────────────────────────────────┤
│ ❖ Logo       │                                                         │
│ 📊 Dashboard │                                                         │
│ 💬 Chat      │                     MAIN WORKSPACE                      │
│ 📅 Today     │                                                         │
│ ☑ Tasks      │    - Dashboard / Today Overview / Focus Session         │
│ 📁 Projects  │    - Hybrid Text + Voice Chat & Equalizer Bar           │
│ 🧠 Memory    │    - Epistemic Memory Center & Consent                  │
│ 🤖 Agents    │    - Agent Registry & Hot-Swap Manager                  │
│ 📈 Activity  │    - Security Center & Zero-Trust Data Firewall         │
│ 💡 Insights  │    - Self-Healing & Self-Improvement Dashboards         │
│ ⚡ Self-Impr │    - Coding Workspace & Terminal Safety Review          │
│ 🛡️ Security  │                                                         │
│ ⚙️ Settings  │                                                         │
└──────────────┴─────────────────────────────────────────────────────────┘
```

### 13 Persistent Left Sidebar Sections
1. **Dashboard:** Home overview (greeting, schedule cards, priority tasks, productivity status).
2. **Conversation:** Text & Voice hybrid chat workspace.
3. **Today:** Day timeline, schedule recommendations, focus blocks.
4. **Tasks:** Drag-and-drop task management (Inbox, Planned, Active, Blocked, Completed, Archived).
5. **Projects:** Project health indicators (Healthy, At Risk, Blocked) with file/task milestones.
6. **Memory:** Epistemic facts, observations, hypotheses with confidence %, evidence counts, and actions ([Edit], [Confirm], [Forget], [Mark incorrect]).
7. **Agents:** Agent Registry manager showing active models, scores, and hot-swap controls.
8. **Activity:** Execution graph and step-by-step agent run logs.
9. **Insights:** Evidence-based productivity patterns and focus metrics.
10. **Self-Improvement:** Training example evaluator, model benchmarks, and rollback controls.
11. **Security:** Zero-trust Data Firewall, secret masking (`sk-••••`), audit trail, data export/purge.
12. **Food / Nutrition:** Grocery planning, meal logs, and general nutrition information (non-medical).
13. **Settings:** Preferences, Voice STT/TTS devices, Local LLM models, and Developer Mode.

---

## 3. Global Top Bar Status Indicators

- **Left:** Section title / breadcrumb.
- **Center:** Processing indicator & active agent state.
- **Right:**
  - Model Mode: `● Local` (Green) or `☁ Cloud` (Blue, when cloud fallback enabled).
  - Privacy Status: `🔒 Private` (Local encryption active).
  - Voice Status: `🎙 Ready` / `🎙 Listening...` / `🎙 Speaking...`.
  - Profile & Notifications.

---

## 4. Voice Interaction & Privacy UI

- **Voice Controls:** `[ + ] [ Text input... ] [ 🎙 ] [ Send ]`
- **Voice States:** `Ready`, `Listening...`, `Processing...`, `Speaking...`, `Paused`.
- **Playback Controls:** `▶ Play`, `⏸ Pause`, `■ Stop`.
- **Output Toggles:** Switch seamlessly between `Text only`, `Voice only`, `Text + Voice`.
- **Privacy Rule:** Microphone requires explicit consent; visual mic indicator is active whenever audio recording is engaged.

---

## 5. Guardian Disagreement UI

When COPPER challenges a user decision (Level 2 Challenge):

```
┌────────────────────────────────────────────────────────────────────────┐
│ ⚠ COPPER RECOMMENDS AGAINST THIS                                       │
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
│ [ Follow COPPER's Recommendation ]  [ Proceed Anyway ]  [ Discuss ]   │
└────────────────────────────────────────────────────────────────────────┘
```

*Note: Uses neutral, non-manipulative wording. Never uses phrases like "COPPER knows best".*

---

## 6. Terminal Safety & Tool Execution UI

### Terminal Safety Tiers
- **Harmless Commands:** `[Run]`
- **Potentially Destructive Commands:** `[Review Command]` $\rightarrow$ `[Run]` / `[Cancel]`
- **Destructive Commands:** Displays Command, Target, Expected Effect, Risk, and explicit confirmation dialog.

### Tool Execution Progress Bar
- Displays collapsible activity (`✓ Read schedule` $\rightarrow$ `✓ Checked priorities` $\rightarrow$ `→ Updating tasks`).
- Secrets (API keys, passwords, tokens) automatically masked (`sk-••••••••`).

---

## 7. Developer Mode & Observability

When Developer Mode is enabled in Settings:
- Displays LangGraph State, LangCrew Execution, latency metrics, token consumption, and model benchmarks.
- Secrets, private keys, hidden prompts, and chain-of-thought traces remain strictly protected and masked.
