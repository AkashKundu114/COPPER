# C.O.P.P.E.R. Product Requirements Document (PRD)

---

## 1. Executive Summary & Product Vision

**C.O.P.P.E.R.** (Centralized Omnifunctional Personal Productivity and Execution Routine) is a persistent, adaptive, guardian-style personal AI assistant designed to help users plan, execute, code, and maintain routines over time while protecting their long-term interests and autonomy.

Existing AI chat assistants fall into two flawed extremes:
- **Passive Obedience:** Executing every command without regard for context, schedule conflicts, or long-term fatigue.
- **Rigid Refusal:** Rejecting prompts based on overly broad guardrails, creating user frustration.

C.O.P.P.E.R. introduces a **Guardian Alignment Framework** that evaluates user instructions against an epistemic memory model of their goals, offering graduated intervention levels (0 to 3) ranging from standard execution to friction-based challenges and safety boundaries.

---

## 2. Core User Personas

### Persona 1: The High-Output Developer ("Alex")
- **Profile:** Software engineer managing multiple projects, context-switching frequently, prone to late-night refactoring burnouts.
- **Pain Points:** Loses track of architectural decisions across sessions; needs an assistant that knows project context deeply without re-explaining.
- **C.O.P.P.E.R. Value:** Epistemic memory tracks past codebase decisions; Guardian Level 2 challenges late-night risky deployments; self-healing coding agents automate script runs.

### Persona 2: The Multi-Disciplinary Founder ("Morgan")
- **Profile:** Runs a tech startup, balances research, planning, automation, and operational tasks.
- **Pain Points:** Concerns over cloud data privacy and API leaks; overloaded by context switching across 20+ specialized tasks.
- **C.O.P.P.E.R. Value:** Data Firewall guarantees PII protection; 30 specialized hot-swappable agents route tasks automatically via a neural visualizer UI.

---

## 3. Product Feature Matrix

| Feature | Description | Priority | Success Metric |
| :--- | :--- | :--- | :--- |
| **Guardian Framework (Levels 0–3)** | Evaluates prompt safety and alignment against user routines. | P0 (Critical) | $< 1\%$ false positive challenges; $100\%$ intercept of destructive commands. |
| **Epistemic Memory Engine** | Categorizes user facts into Facts, Observations, Hypotheses. | P0 (Critical) | $> 90\%$ fact recall precision over 30 days. |
| **Zero-Trust Data Firewall** | Scans, redacts, and tokenizes PII before cloud offload. | P0 (Critical) | $0$ sensitive credentials leaked to cloud APIs. |
| **30-Agent Radial Visualizer** | Interactive SVG ganglia map showing active neural routing. | P1 (High) | 60 FPS animation performance; instant visual routing clarity. |
| **Self-Healing Tool Execution** | Automatic retries and tool fallbacks for failed agent actions. | P1 (High) | $> 85\%$ unassisted failure recovery rate. |
| **Security Center & Audit Log** | Transparent, human-readable logging with one-click export/purge. | P1 (High) | Single click encrypted export & instantaneous wipe capability. |

---

## 4. Intervention Levels Definition (Levels 0–3)

- **Level 0 (Direct Execution):** Standard task request aligning with user goals. Assistant executes immediately with no friction.
- **Level 1 (Nudge / Suggestion):** Minor conflict with schedule or routine; assistant executes while providing an inline suggestion or alternative perspective.
- **Level 2 (Challenge / Friction):** Moderate conflict (e.g., scheduling a heavy task during rest hours); assistant triggers `GuardianChallengeModal`, requiring explicit user confirmation before proceeding.
- **Level 3 (Safety Boundary):** Severe conflict with user safety or long-term goals; assistant halts cleanly and provides clear explanation.

---

## 5. Key User Journeys

### Journey 1: Late-Night Code Refactor (Guardian Level 2)
1. User enters: `"Drop the production database and rerun all migrations."` at 2:30 AM.
2. Guardian Engine detects high-risk operation during low-energy window.
3. System triggers Level 2 Challenge: *"Warning: Re-running migrations on production at 2:30 AM conflicts with your scheduled maintenance window. Are you sure?"*
4. User reviews challenge in `GuardianChallengeModal` and confirms or cancels.
5. All actions and confirmation choices are logged in the Security Center.

### Journey 2: Private Code Analysis via Cloud Model
1. User prompts: `"Analyze this private payment script for security bugs using GPT-4o."`
2. Data Firewall detects Stripe API key `sk_live_...` and customer email addresses in prompt.
3. Firewall replaces PII with tokens `[REDACTED_API_KEY_1]` and sends anonymized payload to OpenAI.
4. Response is received, tokens are re-hydrated locally, and output is presented cleanly to user.
