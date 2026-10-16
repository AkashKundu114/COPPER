# Recommended GitHub Issues to File Post-Release

This document lists candidate GitHub issues for community tracking and triage following the `0.1.0-alpha` release.

---

### Issue 1: [Feature] Multi-GPU & Distributed Inference Pool Support
- **Category**: Performance / Infrastructure
- **Description**: Currently `VRAMPager` and `CUDA_VISIBLE_DEVICES` target a primary dedicated GPU (`device 0`). Extend `model_manager` and `ollama_client` to distribute model tiers across multi-GPU setups (e.g., dedicated GPU for continuous wake-word / mini-model, secondary GPU for 14B coding agent).
- **Labels**: `enhancement`, `performance`, `gpu`

---

### Issue 2: [Platform] Native macOS DMG & Linux AppImage Distribution Pipeline
- **Category**: Packaging / Desktop
- **Description**: Add GitHub Actions workflow jobs using macOS and Ubuntu runners to package native DMG and AppImage binaries using Electron Builder.
- **Labels**: `desktop`, `ci/cd`, `packaging`

---

### Issue 3: [Security] Dynamic Sandbox Hardening for Custom Community Skills
- **Category**: Security / Extensibility
- **Description**: Enhance AST static validator to support configurable security policies per plugin skill in `data/learned_skills.json`, allowing fine-grained network access grants for specific trusted extensions.
- **Labels**: `security`, `plugins`, `guardian`

---

### Issue 4: [A11y] Screen Reader High-Contrast Theme Polish
- **Category**: Accessibility / Frontend
- **Description**: Expand ARIA live regions and ensure WCAG 2.1 AAA color contrast ratios across all dynamic SVG graph views in `KnowledgeGraphView.tsx` and `TaskGraphVisualizer.tsx`.
- **Labels**: `a11y`, `frontend`, `ux`
