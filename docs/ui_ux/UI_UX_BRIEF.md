# C.O.P.P.E.R. UI/UX Design Brief & Aesthetics Guide

---

## 1. Visual Language & Aesthetics Strategy

The visual identity of **C.O.P.P.E.R.** moves away from standard generic AI aesthetics (acid green / dark blue tech dashboards). Instead, it draws inspiration from **Molten Copper Physics**:
- **Dormant State:** Dim bronze filaments, subtle metallic textures, organic breathing movements.
- **Active State:** The instant a task is routed through a node, synapse lines flare white-hot / electric blue—resembling high current passing through copper wire.
- **Familiarity-Based Resting Glow:** Nodes belonging to agents with higher familiarity scores glow warmer even while resting, visually representing deep user-assistant relationships.

---

## 2. Core UI Components Specification

### 2.1 Fixed Radial Ganglia Map (`NeuralBrain.tsx`)
- **Deterministic 30-Node Radial Layout:** Nodes positioned dynamically across four orbital tiers (Core Reasoning, Task Execution, Specialized Knowledge, Interface & Audio).
- **Orbital Mechanics:** Inner tiers complete revolutions faster than outer tiers; alternating clockwise/counter-clockwise orbits with counter-rotating labels for constant legibility.
- **Synapse Filaments:** SVG paths connecting COPPER core to agent nodes. Synapses pulse with animated traveling sparks during WebSocket events.

### 2.2 Glass Chat Dock & Speaking Bar (`ChatDock.tsx` & `SpeakingBar.tsx`)
- **Minimal Glassmorphism:** Translucent glass surface (`backdrop-blur-md`, subtle copper border glows).
- **Audio Equalizer Bar:** Dynamic multi-bar equalizer that rises smoothly from the bottom dock whenever COPPER or an agent is "speaking", synchronized with response stream duration.

### 2.3 Guardian Challenge Modal (`GuardianChallengeModal.tsx`)
- **Friction-Based Alert:** High-contrast amber/red backdrop filter.
- **Clear Information Hierarchy:** Displays Risk Score, Objections, Suggested Alternatives, and explicit "Override Guardian" button.

### 2.4 Security Center & Memory Inspector (`SecurityCenter.tsx` & `SideDrawer.tsx`)
- **Epistemic Fact Cards:** Categorized view of stored user memory with interactive confidence progress bars.
- **Audit Log Inspector:** Filterable log of Data Firewall redactions and Guardian challenges with instant encrypted JSON export and permanent `delete-all` trigger.

---

## 3. Color Palette & Token Definitions

| Token Name | Hex Code | Purpose |
| :--- | :--- | :--- |
| `--copper-core` | `#B87333` | Primary copper brand accent. |
| `--copper-molten` | `#FF5722` | Active routing node glow & white-hot synapse highlights. |
| `--copper-bronze` | `#4A3B32` | Dormant node background & resting filament lines. |
| `--electric-blue` | `#00E5FF` | Secondary signal pulse & Data Firewall encryption indicator. |
| `--bg-dark` | `#0D0D11` | Deep obsidian backdrop background. |
| `--glass-border` | `rgba(184, 115, 51, 0.15)` | Glassmorphism container border glow. |
