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
- **src/components/ (14 Subsystems):** Includes the chat dock, speaking bar, widget rail (Clock, Calendar, Weather, Network), and the rain/ directory containing the SVG Neural Brain Map.
- **src/lib/:** WebSocket hooks (useBrainSocket.ts) for real-time agent dispatch and hardware metrics, plus the Axios API client (pi.ts).

## The Neural Brain Visualizer (src/components/brain/)

A core feature of the UI is the **30-agent radial SVG ganglia map**. 
- It uses deterministic layout math (guaranteeing a minimum of 49px spacing between nodes) rather than unpredictable force-directed physics.
- The map animates organically with CSS orbital rotations and breathing opacities.
- When an agent is invoked via the FastAPI backend, WebSockets stream copper_thinking, oute_decision, and gent_active events to trigger electric "molten wire" animations in real-time.

## Development & Build Commands

Ensure you are using **Node.js 20+** and **npm 9+**.

`ash
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
`

## Testing & Quality Gates

The frontend enforces strict quality gates via Oxlint and comprehensive testing:

`ash
# Run unit tests and component coverage
npx vitest run

# Run end-to-end desktop verification
npx playwright test
`

## Theme & Accessibility (a11y)

The UI uses a custom **Molten Copper** color palette defined in 	ailwind.config.js. It fully supports prefers-reduced-motion queries, disabling all particle drifts and SVG orbital animations in favor of static, accessible layouts when requested by the OS. Keyboard navigation and contrast thresholds strictly adhere to WCAG 2.1 AA standards.
