# C.O.P.P.E.R. Issue Tracking & Reporting Guidelines

Welcome to the C.O.P.P.E.R. Issue Tracker guide. We appreciate your help in making C.O.P.P.E.R. stable, secure, and performant! This repository adheres strictly to **Microsoft Code Quality** and **Red Team Security** standards.

---

## Table of Contents
1. [Code of Conduct & Expectations](#1-code-of-conduct--expectations)
2. [Before Submitting an Issue](#2-before-submitting-an-issue)
3. [Reporting Bugs (Production Standard)](#3-reporting-bugs-production-standard)
4. [Guardian False Positive Reports](#4-guardian-false-positive-reports)
5. [Requesting New Features](#5-requesting-new-features)
6. [Security Vulnerabilities](#6-security-vulnerabilities)
7. [Issue Triage & Lifecycle](#7-issue-triage--lifecycle)

---

## 1. Code of Conduct & Expectations
Maintainers and contributors are expected to treat all community members with respect. Please keep discussion technical, constructive, and focused on problem-solving. We follow the "Healthier Codebase" rule: every discussion and PR must leave the project in a better state.

---

## 2. Before Submitting an Issue

Before creating a new GitHub issue:
1. **Search Existing Issues:** Search open and closed issues to avoid duplicates.
2. **Consult Troubleshooting Documentation:** Review `docs/setup/TROUBLESHOOTING.md` for solutions to common Ollama timeouts, Alembic migration errors, or WebSocket disconnects.
3. **Verify Version:** Ensure you are running the latest main branch version or release tag.
4. **Check Quality Gates:** If you are developing locally, ensure `pytest` and `ruff` pass before reporting an issue on your fork.

---

## 3. Reporting Bugs (Production Standard)

When filing a bug report, use the GitHub **Bug Report** template. To ensure rapid triage, you must include:

- **Environment Details:**
  - OS & Version (e.g., Windows 11, macOS Sonoma 14.2, Ubuntu 22.04)
  - Python version (`python --version`)
  - Node.js & npm version (`node -v`)
  - Ollama version & loaded model (e.g., `llama3.1:8b`)
  - Deployment mode (Tauri Desktop App vs Browser SPA vs Docker)
- **Steps to Reproduce:** Clear, deterministic 1-2-3 steps to trigger the bug.
- **Expected vs Actual Behavior:** What should have happened vs what actually happened.
- **Un-truncated Error Logs:** Include backend FastAPI log snippets or browser console errors. Use code blocks (` ``` `).
- **Security Warning:** **DO NOT** post unredacted API keys, private passwords, credit card numbers, or confidential user memory data in public issue threads.

---

## 4. Guardian False Positive Reports

If C.O.P.P.E.R.'s **Guardian Alignment Engine** incorrectly triggers a Level 2 Challenge or Level 3 Safety Boundary on a legitimate prompt:

1. Open a **Guardian False Positive** issue.
2. Provide the sanitized prompt text.
3. Provide the output log from the Security Center audit trail (`/security-center`).
4. Explain why the prompt was safe and how the Guardian Engine miscalculated risk or fatigue scores.

---

## 5. Requesting New Features

Feature requests should explain the *why* as clearly as the *what*. We use the **Google XYZ Formula** to evaluate new features. Include:
- **Impact Statement:** "I want to accomplish [X] as measured by [Y], by doing [Z]."
- **Use Case / User Story:** "As a developer, I want X so that I can accomplish Y."
- **Proposed Solution:** Architectural suggestion or UI/UX mock.
- **Alternatives Considered:** Other approaches evaluated and why the proposed idea is preferred.

---

## 6. Security Vulnerabilities

**DO NOT** file public GitHub issues for security vulnerabilities, zero-day data firewall leaks, or un-redacted PII egress. 

Please report security concerns privately to the maintainers at **security@copper-ai.org** or via GitHub Private Vulnerability Reporting. See `.github/SECURITY.md` for response SLAs and disclosure protocols.

---

## 7. Issue Triage & Lifecycle

All issues are labeled during triage according to the following matrix:

| Label | Description | Action SLA |
| :--- | :--- | :--- |
| `bug: critical` | Data loss, security bypass, or total crash. | $< 24\text{ hours}$ |
| `bug: moderate` | Degraded agent routing or tool execution failure. | $< 3\text{ days}$ |
| `guardian-fp` | Guardian Level 2/3 false positive challenge. | $< 5\text{ days}$ |
| `feature-request` | Proposed new agent, UI widget, or API endpoint. | Evaluated at milestone planning |
| `docs` | Documentation correction or addition. | Community review |
