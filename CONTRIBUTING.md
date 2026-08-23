# Contributing to C.O.P.P.E.R.

Thank you for your interest in contributing to **C.O.P.P.E.R.**! We welcome contributions, bug reports, and enhancements adhering to **Microsoft Open Source & Engineering Standards**.

---

## Code of Conduct

This project adheres to the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## Microsoft Engineering & Code Review Practices

We adhere to the following principles across our codebase:

### 1. The "Healthier Codebase" Rule
Every pull request must leave the modified code in a cleaner, better-tested state than when you found it.

### 2. Small, Atomic Pull Requests
- Keep PRs focused on a single concern or feature ($< 400$ lines modified when feasible).
- Avoid monolithic PRs combining refactors, bug fixes, and new features.

### 3. Google XYZ Impact Format in PRs
Structure your pull request summary using Google's XYZ impact framework:
> *"Accomplished **[X]** as measured by **[Y]**, by doing **[Z]**."*

### 4. Code Review Etiquette
- **Prefix Non-Blocking Comments:** Use `Nit:` for minor style or naming feedback that does not block merging.
- **Explain Rationale:** Always provide the architectural or security reason behind requested changes.
- **Respect User Autonomy:** Never weaken the Guardian or Data Firewall security layers.

---

## Development Setup & Quality Gates

### 1. Prerequisites
- **Python:** 3.11+ (Strict typing with `mypy` / `typing`)
- **Node.js:** 20+ & npm 9+
- **Electron:** 43+
- **Pytest:** 9+

### 2. Local Setup
```bash
# Clone repository
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER

# Setup Python Virtual Environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # On Windows
source .venv/bin/activate     # On Linux/macOS

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## Quality Gate Verification

Before opening a pull request, you **MUST** pass all quality gates locally:

```bash
# Gate 1: Run Full Pytest Suite (All 213+ tests must pass)
python -m pytest tests/ -v

# Gate 2: Run Evaluation Benchmark Suite (100% Routing & Guardian precision)
python backend/eval/benchmark.py

# Gate 3: Verify AI Model Manifest
python scripts/models/verify_models.py
```

---

## Pull Request Workflow

1. **Fork the repository** and create your branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Commit your changes** using conventional commit messages:
   - `feat(router): add regex negative clause for multi-word queries`
   - `fix(firewall): support hyphenated OpenAI project keys`
   - `test(audio): add stereo tone streaming tests`
   - `docs(architecture): update subagent manifest diagrams`
3. **Push to your fork** and submit a Pull Request.
4. **Link relevant issues** in the PR description (e.g., `Fixes #42`).
