# Contributing to C.O.P.P.E.R.

Thank you for your interest in **C.O.P.P.E.R.** (Centralized Omnifunctional Personal Productivity and Execution Routine), an independent, local-first personal AI operating system created and maintained by **Akash Kundu**.

We welcome community feedback, bug reports, documentation refinements, and feature contributions adhering to our **Engineering Quality Gates** and **Microsoft / Google Software Standards**.

---

## 1. Proprietary Licensing & Contributor Terms

C.O.P.P.E.R. is an independent, proprietary project protected by patent-pending architectures, trade secrets, and copyright law. See [`LICENSE`](LICENSE) for complete terms.

By opening a pull request, submitting code, proposing algorithmic changes, or providing documentation (collectively, "Contributions"), you agree that:
1. **Assignment of Rights:** All intellectual property, patent rights, copyright, and title in and to your Contributions are assigned to and become the sole property of **Akash Kundu**.
2. **Original Work:** You warrant that your Contributions are your original work and are free from third-party licenses, proprietary encumbrances, or conflicting employer intellectual property agreements.
3. **No Unsolicited Commercial Claims:** You acknowledge that participation does not grant you patent, trademark, or commercial licensing rights over the C.O.P.P.E.R. codebase or its underlying technology.

---

## 2. Code of Conduct

All contributors and participants must adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable behavior to the project maintainer at `conduct@copper-ai.local`.

---

## 3. Engineering & Code Review Standards

We adhere to strict engineering principles across the repository:

### The "Healthier Codebase" Rule
Every pull request must leave the modified module in a cleaner, better-documented, and better-tested state than when you found it.

### Small, Atomic Pull Requests
- Keep PRs focused on a single concern, fix, or feature ($< 400$ lines modified when feasible).
- Do not submit monolithic PRs combining unrelated refactors, bug fixes, and feature additions.

### Google XYZ Impact Summary Format
All pull request descriptions must follow Google's XYZ impact framework:
> *"Accomplished **[X]** as measured by **[Y]**, by doing **[Z]**."*

### Security & Privacy Integrity
- **Zero Cloud Egress:** Never add background telemetry, analytics calls, or unapproved external network requests.
- **Guardian & Firewall Integrity:** Never weaken the Guardian Safety Engine thresholds or bypass the Zero-Trust Data Firewall redaction patterns.

---

## 4. Development Setup & Quality Gates

### Prerequisites
- **Python:** 3.11+ (Strict typing with `typing` / `mypy` standards)
- **Node.js:** 20+ & npm 9+
- **Electron:** 43+
- **Pytest:** 9+

### Local Environment Setup
```bash
# Clone the repository
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER

# Setup Python Virtual Environment
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## 5. Mandatory Quality Gates

Before opening a pull request, you **MUST** pass all quality gates locally:

```bash
# Gate 1: Full Pytest Test Suite (All 213+ unit and integration tests must pass)
python -m pytest tests/ -v

# Gate 2: Benchmark Evaluation Suite (100% Routing & Guardian accuracy across 1,360 cases)
python backend/eval/benchmark.py

# Gate 3: AI Model Manifest Verification
python scripts/models/verify_models.py

# Gate 4: Code Style & Static Linting
ruff check backend/
cd frontend && npm run lint && cd ..
```

---

## 6. Pull Request Workflow

1. **Fork the repository** and create your branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Commit your changes** using conventional commit messages:
   - `feat(router): add regex negative clause for multi-word queries`
   - `fix(firewall): support hyphenated OpenAI project keys`
   - `test(audio): add stereo tone streaming tests`
   - `docs(architecture): update subagent manifest diagrams`
3. **Pass all Quality Gates** locally.
4. **Push to your fork** and submit a Pull Request to `main`.
5. **Link relevant issues** in the PR description (e.g., `Closes #42`).

