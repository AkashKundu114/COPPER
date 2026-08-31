# Accessibility & Design Tokens Specification

---

## 1. Accessibility (a11y) Standards

C.O.P.P.E.R. strictly adheres to **WCAG 2.1 AA Standards** across web and Tauri desktop interfaces.

### Key Accessibility Features

1. **Reduced Motion Support (`prefers-reduced-motion`):**
   - Automatically disables particle ember drift and node orbital rotations when reduced motion is requested by the OS.
   - Replaces orbital rotation with static deterministic layout.
2. **Keyboard Navigation & Focus Management:**
   - Full keyboard accessibility for input docks, Guardian challenge modals, and drawer components.
   - Explicit `tabIndex` ordering and visible focus rings (`ring-2 ring-copper-molten`).
3. **Contrast Ratios:**
   - Text contrast ratio $\ge 4.5:1$ against obsidian dark background.
   - High-visibility status indicators for degraded agent states.

---

## 2. Typography & Spatial Tokens

- **Font Family:** Inter / Roboto / system-ui stack for primary text; JetBrains Mono for code blocks and audit logs.
- **Font Sizes:**
  - Display Headers: `1.875rem` (`text-3xl`), font-bold.
  - Section Headers: `1.25rem` (`text-xl`), font-semibold.
  - Body Text: `0.875rem` (`text-sm`), font-normal.
  - Micro Badges: `0.75rem` (`text-xs`), font-medium.
- **Spacing Scale:** Standard 4px grid (`p-2`, `p-4`, `p-6`, `gap-4`).
