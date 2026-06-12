# COPPER Framework — UI/UX Design Brief

> **Documentation set:** [PRD](PRD.md) · [TRD](TRD.md) · [App Flow](APP_FLOW.md) · [UI/UX Brief](UI_UX_BRIEF.md) · [Backend Schema](BACKEND_SCHEMA.md) · [Implementation Guide](IMPLEMENTATION.md)
>
> **Theme source:** AeroNet Visualization Dashboard (Neuform Featured template) — adapted for the COPPER 30-agent telemetry dashboard described in [App Flow §9](APP_FLOW.md#9-frontend-dashboard-flow).

---

## 1. Design Language Overview

The COPPER dashboard adopts the **AeroNet** visual language: a dense, dark, operational "mission control" aesthetic built around modular surface panels, monospace technical labels, and a restrained near-monochrome palette punctuated by a single accent. AeroNet's source composition — a relay-network dashboard with live metric counters ("19.5 TB/s +924", "820 GB/s +418") and a central "Planet Core" focal visualization — maps directly onto COPPER's own domain: a live relay (`state.json`), real-time metrics (VRAM allocation, step counters), and a central "core" visualization representing the currently active model.

**Guiding principle:** preserve AeroNet's information density, modular panel rhythm, and first-screen composition. Do not flatten COPPER's telemetry into a generic SaaS card grid — the dashboard should feel like an engineering instrument panel, not a marketing page.

---

## 2. Design Tokens

These tokens are carried over directly from the AeroNet source and form the COPPER dashboard's `tailwind.config.js` theme extension.

### 2.1 Color Palette

| Token | Value | COPPER Usage |
|---|---|---|
| `primary` | `#FFFFFF` | Primary text on dark surfaces, primary button fill on light contexts |
| `secondary` | `#000000` | High-contrast text, outlines on light surfaces |
| `accent` | `#FFFFFF` | Default accent for active states (overridden by status accents — see §3) |
| `background` | `#FFFFFF` | App shell background (light mode base) |
| `surface` | `#18181B` | Panel/card background — used for **all telemetry panels** (Dialogue Log, System Log, VRAM Gauge, Action Banner) |
| `text-primary` | `#111827` | Primary copy on light surfaces |
| `text-secondary` | `#4B5563` | Secondary/meta copy, timestamps, log prefixes |
| `border` | `#E5E7EB` | Card borders, dividers, input outlines |

> **Contrast pattern:** Background, surface, text, and border roles must remain distinct so that dark telemetry panels (`surface: #18181B`) sit on a light app shell (`background: #FFFFFF`), exactly mirroring AeroNet's dark-panel-on-light-shell composition.

### 2.2 Typography

| Token | Font | Size | Weight | Line Height | COPPER Usage |
|---|---|---|---|---|---|
| `display-lg` | Inter | 64px | 500 | 1.04 | Hero/empty-state headline (e.g. "COPPER" wordmark on first load) |
| `body-md` | Inter | 16px | 400 | 1.6 | Dialogue Log entries, agent responses, modal body copy |
| `label-md` | JetBrains Mono | 12px | 600 | 1.2 | All technical metadata: `agent_name`, timestamps, VRAM figures, log line prefixes, status pills |

> JetBrains Mono (or an equivalent mono face) is **mandatory** for anything that reads as machine-generated telemetry — this is the strongest visual link to AeroNet's "Metrics / Docs / Log In / Deploy Node" technical label treatment.

### 2.3 Spacing & Radius

| Token | Value | COPPER Usage |
|---|---|---|
| `spacing.base` | 8px | Atomic spacing unit for all internal component gaps |
| `spacing.gap` | 16px | Gap between dashboard panels (Pulse Badge ↔ Action Banner ↔ VRAM Gauge, etc.) |
| `spacing.card-padding` | 24px | Internal padding for every panel (Dialogue Log, System Log, etc.) |
| `spacing.section-padding` | 80px | Outer margin around the full dashboard viewport on desktop |
| `rounded.card` | 16px | Panel corner radius (Dialogue Log, System Log, VRAM Gauge, Action Banner) |
| `rounded.control` | 8px | Inputs, buttons, Confirmation Modal action buttons |
| `rounded.pill` | 9999px | **Pulse Badge** and all status chips |

---

## 3. Component Specifications

### 3.1 Pulse Badge

The Pulse Badge is the single highest-priority element on screen — it must be legible at a glance. It is rendered as a `rounded.pill` chip using `label-md` (JetBrains Mono, 12px, weight 600) on a `surface` (`#18181B`) background.

**Status → Color mapping** (the one deliberate departure from AeroNet's near-monochrome palette — semantic status color is treated as a functional accent layered on top of the base theme, per the AeroNet guardrail "do not swap the color mode unless the source clearly supports it" — here the source's relay-status indicators justify a small accent set):

| `system_status` | Pulse Badge Color | Meaning |
|---|---|---|
| `IDLE` / Green | `#10B981` | COPPER ACTIVE |
| `PROCESSING` / Blue | `#3B82F6` | SUB-AGENT RUNNING |
| `HOT-SWAPPING` / Yellow | `#F59E0B` | VRAM HOT-SWAPPING |
| `CRASHED` / Red | `#EF4444` | CRASHED / ATTENTION REQUIRED |

The badge dot itself pulses (see §5 Motion) to reinforce "live" status — directly echoing AeroNet's "Relay established successfully" live-status language.

### 3.2 Action Banner

A full-width `surface` card (`rounded.card`, `card-padding: 24px`) directly beneath the Pulse Badge. Displays `telemetry.current_action` in `body-md` Inter, with the active agent name rendered as a `label-md` JetBrains Mono prefix chip (e.g. `[HAWK]` before "Analyzing desktop screenshot for browser icon").

### 3.3 VRAM Gauge

A horizontal live bar chart styled as a metric counter panel — directly modeled on AeroNet's headline metric blocks ("19.5 TB/s +924"). The gauge shows:

- A large `label-md` numeric readout of `telemetry.vram_allocation_mb` (e.g. `580 MB / 5500 MB`)
- A horizontal fill bar inside a `surface` track, filled with the active model profile's accent (Model 1–6 each get a subtle tonal variant of `#FFFFFF`/`#18181B` to stay within the AeroNet palette, differentiated primarily via the `label-md` profile tag, e.g. `MODEL_4_VISION`)
- A secondary small-caps label showing the hardware ceiling: `≤ 5.5 GB` (from [TRD §7.7](TRD.md))

### 3.4 Dialogue Log

The "personality" surface of the dashboard. Each entry is a `surface` card row containing:

- `label-md` agent name chip (e.g. `HAWK`)
- `body-md` dialogue text ("On it. Analyzing display now.")
- `label-md` right-aligned timestamp (`16:02:44`)

Scrolls within a fixed-height `rounded.card` panel, auto-scrolling to the newest entry. When `SYSTEM_MODE: BOSS` is active, this panel collapses/hides entirely (see [App Flow §8.5](APP_FLOW.md#85-boss-mode-flow)) — the layout should reflow the System Log to take the freed space without a jarring resize (use the masked-reveal motion in §5).

### 3.5 System Log

An append-only, monospace (`label-md`) terminal panel on a `surface` background, mirroring AeroNet's technical/operational tone. Each line follows the `[HH:MM:SS] [AGENT] message` format directly from `execution_logs[]`. Auto-scrolls to bottom; supports a subtle scanline/CRT-style ambient texture as an optional low-cost nod to AeroNet's "atmospheric effects" guidance (§6) — kept fully behind the text layer and disabled on low-power displays.

### 3.6 Prompt Input

A glassmorphism overlay panel, triggered by `Alt+Space` or a floating action button. Background uses `surface` at reduced opacity with backdrop blur, `rounded.card` corners, and a `border` outline at low opacity. Text entry uses `body-md`; a `label-md` hint row beneath shows the wake-word alternative ("or say 'Hey COPPER'").

### 3.7 Confirmation Modal

Reserved for TALON/AXIS destructive-action confirmations ([TRD §7.6](TRD.md#76-tr-06-security-guardrails-axis--talon)). Rendered as a centered `surface` card with an **amber border** (`#F59E0B`, 2px) overriding the default `border` token to signal risk. Contains:

- `label-md` header: `CONFIRMATION REQUIRED`
- `body-md` description of the pending action (e.g. the shell command or click target)
- Two `rounded.control` buttons: `Y — Approve` (primary fill) and `N — Cancel` (outline only)

This is the **only** component permitted to break the otherwise restrained palette with a saturated warning color, consistent with AeroNet's guardrail to keep buttons, cards, and badges aligned to the same radius/border language while still allowing functional emphasis.

---

## 4. Layout & Composition

- **Grid direction:** Single-column on mobile/narrow widths; a 12-column responsive grid on desktop, with the VRAM Gauge and Pulse Badge occupying the top band, Action Banner spanning full width beneath it, and Dialogue Log / System Log split into two columns (or stacked tabs on narrower viewports).
- **Max-width behavior:** Dashboard content is constrained to a centered max-width container with `section-padding: 80px` outer margins on desktop, collapsing to `card-padding: 24px` on mobile.
- **Card density:** All panels share `rounded.card` (16px) and `card-padding` (24px), with `spacing.gap` (16px) between adjacent panels — preserving AeroNet's "modular panels, interface rhythm" without devolving into a generic card grid (panels vary in width/height according to telemetry importance, not a uniform grid).
- **Responsive stacking:** On narrow viewports, the Pulse Badge and Action Banner remain pinned to the top as a persistent status bar; Dialogue Log and System Log stack vertically beneath, each collapsible.

---

## 5. Motion

Preserve AeroNet's restrained, ambient motion language:

- **Masked reveal:** New Dialogue Log and System Log entries slide/fade in from below the panel mask rather than popping in instantly.
- **Staggered entrance:** On dashboard load, panels (Pulse Badge → Action Banner → VRAM Gauge → Dialogue/System Logs) animate in with a short stagger (~60–80ms offset each).
- **Hover lift:** Interactive elements (Prompt Input trigger, Confirmation Modal buttons) lift with a subtle shadow/translate on hover.
- **Pulse Badge animation:** The status dot uses a soft pulsing opacity/scale loop, synced loosely to the 300ms `state.json` poll cycle, to visually represent the "live relay" — directly analogous to AeroNet's "Relay established successfully" live indicator.
- **Hot-swap transition:** When `system_status` transitions to `HOT-SWAPPING` (yellow), the VRAM Gauge bar briefly drains to zero and the active-agent label in the Action Banner cross-fades to the incoming agent — visualizing the GPU hard reset from [App Flow §8.2.3](APP_FLOW.md#823-step-3--gpu-hard-reset).

Easing should remain smooth and restrained throughout (`ease-out`, ~200–300ms durations) — no bouncing or playful overshoot, in keeping with the "mission control" tone.

---

## 6. WebGL & Ambient Effects ("Model Core" Visualization)

AeroNet's source composition features a central "Planet Core" focal object with atmospheric/particle effects behind the interface. For COPPER, this is reinterpreted as a **Model Core** visualization:

- A subtle, ambient WebGL/Three.js or canvas layer sits **behind** the dashboard content, representing the currently loaded model profile (Model 1–6) as a glowing core.
- The core's intensity/pulse rate scales with `telemetry.vram_allocation_mb` — brighter and faster during active inference, dimming to near-still when VRAM returns to 0 MB (idle).
- During a Hot-Swap transition, the core briefly dims to black (GPU hard reset) before re-illuminating with the new model profile's tonal variant.
- This layer must remain **performant, responsive, and strictly secondary** — it should never compete with telemetry legibility, and must degrade gracefully (static gradient fallback) on low-power hardware, consistent with the AeroNet guardrail to keep such effects as supporting layers, not focal distractions.

---

## 7. Guardrails (Adapted from AeroNet)

- Do not flatten the telemetry panels into a generic card grid — panel size/placement should reflect information priority (Pulse Badge and VRAM Gauge are always top-most).
- Do not introduce additional saturated colors beyond the four status accents (§3.1) and the Confirmation Modal amber border (§3.7) — the base palette remains near-monochrome.
- Preserve the first-viewport signal: Pulse Badge + Action Banner + VRAM Gauge must be visible without scrolling on desktop and mobile.
- Keep all panels, buttons, and badges aligned to the radius language in §2.3 (`card` = 16px, `control` = 8px, `pill` = 9999px) — no ad-hoc radii.
- Boss Mode ([App Flow §8.5](APP_FLOW.md#85-boss-mode-flow)) must visually simplify the dashboard (hide Dialogue Log, suppress motion flourishes) without changing the underlying grid — panels collapse, they don't rearrange.
