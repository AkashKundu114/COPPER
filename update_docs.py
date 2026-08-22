import os

updates = {
    'docs/technical/MODEL_SELECTION.md': [
        ('| **`router`** | `Llama-3.2-1B-Instruct` | Q4_K_M | 770 MB | Fallback sub-40ms user intent classifier |', '| **`router`** | `Llama-3.2-1B-Instruct` | Q4_K_M | 770 MB | Fallback sub-40ms user intent classifier |\n| **`telemetry`** | `SmolLM2-360M-Instruct` | Q4_K_M | 258 MB | System hardware & process anomaly analysis |')
    ],
    'docs/architecture/ARCHITECTURE_OVERVIEW.md': [
        ('│ ⚙️ Settings  │                                                         │', '│ ⚡ Benchmarks│                                                         │\n│ ⚙️ Settings  │                                                         │'),
        ('### 4.3 Forge Sandbox Engine', '### 4.3 Live Telemetry & Hardware Profiler\n- Polls CPU package temps, 8GB VRAM allocation splits, GPU hotspots, and system RAM usage dynamically via `psutil` and simulated hardware fallbacks.\n- Feeds directly into the Desktop UI (Benchmarks Tab) on a 1.5-second interval for real-time observability.\n\n### 4.4 Forge Sandbox Engine')
    ],
    'docs/architecture/DATA_FIREWALL_AND_SECURITY.md': [
        ('# Data Firewall & Security Pipeline', '# Data Firewall & Security Pipeline\n\n## 🛡️ CodeQL Advanced Security Integrations\n\nCOPPER employs **GitHub Advanced CodeQL** (`.github/workflows/codeql.yml`) ensuring:\n- **Backend:** FastAPI routes are hardened against injection attacks.\n- **Frontend:** React/Electron views are protected from Cross-Site Scripting (XSS) and unauthorized IPC context bypasses.\n\n---')
    ],
    'CONTRIBUTING.md': [
        ('## Pull Request Process', '## Pull Request Process\n\nWe enforce **GitHub Actions CodeQL** for all incoming PRs. Ensure you run local security checks before submitting.')
    ]
}

for filepath, replacements in updates.items():
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        for old, new in replacements:
            content = content.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {filepath}')
