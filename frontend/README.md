# C.O.P.P.E.R. Frontend (Electron Desktop Application)

This directory contains the front-end source code and Electron container for **C.O.P.P.E.R.** (Centralized Omnifunctional Personal Productivity and Execution Routine).

## Tech Stack

The frontend is a modern, high-performance web application packaged as a native desktop executable via Electron:
- **Core Framework:** React 19 + TypeScript 7 + Vite 8
- **Desktop Runtime:** Electron 44 + electron-builder
- **Styling:** Tailwind CSS 4 + Framer Motion (Molten Copper Theme)
- **State Management:** Zustand 5
- **Data Visualization:** D3 7 + Pure SVG (Neural Brain Visualizer)
- **Testing:** Vitest 5 + Playwright (E2E)

## Architecture & Layout

The UI is built around a persistent 13-section left sidebar and a dynamic workspace:

- **src/pages/ (19 Views):** 
  - TodayView.tsx, DashboardView.tsx, ActivityView.tsx
  - CompanionHUDView.tsx, ResearchView.tsx, MemoryView.tsx
  - BenchmarkMetricsView.tsx, SecurityCenter.tsx, SelfImprovementView.tsx
  - AgentRegistry.tsx, AutomationBuilderView.tsx, TasksView.tsx, ProjectsView.tsx
  - MeetingsView.tsx, EmailView.tsx, Insights.tsx, SettingsView.tsx, FoodView.tsx, EVEView.tsx
- **src/components/ (14 Subsystems):** Includes the chat dock, speaking bar, widget rail (Clock, Calendar, Weather, Network), and the brain/ directory containing the SVG Neural Brain Map.
- **src/lib/:** WebSocket hooks (useBrainSocket.ts) for real-time agent dispatch and hardware metrics, plus the Axios API client (api.ts).

## The Neural Brain Visualizer (src/components/brain/)

A core feature of the UI is the **30-agent radial SVG ganglia map**. 
- It uses deterministic layout math (guaranteeing a minimum of 49px spacing between nodes) rather than unpredictable force-directed physics.
- The map animates organically with CSS orbital rotations and breathing opacities.
- When an agent is invoked via the FastAPI backend, WebSockets stream `copper_thinking`, `route_decision`, and `agent_active` events to trigger electric "molten wire" animations in real-time.

## Development & Build Commands

Ensure you are using **Node.js 20+** and **npm 9+**.

```bash
# Install dependencies
npm install

# Start the Vite development server (Web only)
npm run dev

# Start the full Electron Desktop App (requires running Vite server)
npm run desktop

# Build the React production assets
npm run build

# Package the Electron standalone executable (Windows/macOS/Linux)
npm run dist
```

## Testing & Quality Gates

The frontend enforces strict quality gates via Oxlint and comprehensive testing:

```bash
# Run unit tests and component coverage
npx vitest run

# Run end-to-end desktop verification
npx playwright test
```

## Theme & Accessibility (a11y)

The UI uses a custom **Molten Copper** color palette defined in `tailwind.config.js`. It fully supports `prefers-reduced-motion` queries, disabling all particle drifts and SVG orbital animations in favor of static, accessible layouts when requested by the OS. Keyboard navigation and contrast thresholds strictly adhere to WCAG 2.1 AA standards.

## Design & Architectural Inspirations

The C.O.P.P.E.R. frontend interface draws architectural and visual design inspiration from several premier design systems and developer tools:

1. **[libraries.dev/orbs](https://libraries.dev/orbs) (Thinking Orbs)**:
   - Voice Companion cognitive core visualizer.
   - Replaced static/wireframe indicators with fluid, multi-layered organic plasma orbs that morph between cognitive states (idle, listening, thinking, speaking, alert) and react dynamically to live microphone amplitude.

2. **[glass.samasante.com](https://glass.samasante.com) (Liquid Glass)**:
   - High-fidelity liquid glassmorphism surfaces (`.liquid-glass`, `.liquid-glass-card`).
   - Implements dual-layer inner specular reflection highlights, chromatic edge refraction, and deep frosted backdrop saturation across dialogue bubbles, floating toolbars, and HUD cards.

3. **[dialkit.dev](https://dialkit.dev) (DialKit)**:
   - Tactile rotary parameter dials and scrubbable knobs (`TactileDial.tsx`).
   - Enables live physical adjustment of Voice Companion parameters (VAD Sensitivity, Voice Rate, and Speaker Presence) with rotary notch feedback and precise numerical readouts.

4. **[uisfx.com](https://uisfx.com) (UI SFX)**:
   - Semantic Web Audio feedback system (`soundFX.ts`).
   - Procedural, zero-dependency, 100% offline audio synthesis providing tactile sound cues for clicks, toggles, tabs, microphone activation, and message transmission, with a master mute control.

5. **[typeface.fyi](https://typeface.fyi) (Typeface)**:
   - Editorial typographic hierarchy and proportional tabular figures (`tabular-nums`).
   - Disciplined monospace metadata labels paired with geometric titles for high-density engineering data and telemetry inspection.

6. **[vibeui.online](https://vibeui.online) (Vibe UI)**:
   - Bento-grid card layouts, subtle glowing status pills (`.vibe-pill`), and tactile active press states (`active:scale-[0.985]`) providing modern ergonomic feedback.

7. **Linear & Raycast**:
   - Centered keyboard-first Command Palette (`Ctrl+K`), streamlined zero-clutter top bar controls, and responsive drawer navigation.

8. **Sensor CRT & Tactical Telemetry**:
   - Subtle scanline texture and air-gapped system indicators for tactical workstation monitoring.

