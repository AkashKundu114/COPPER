# C.O.P.P.E.R. Security & Privacy Architecture

**Zero-Cloud-Egress, Defense-in-Depth, Sandboxing, and Alignment Security Specification**

---

## 1. Zero-Cloud-Egress & Airgap Architecture

C.O.P.P.E.R. operates with an uncompromising **local-first, zero-cloud-egress** security posture. No prompt text, user profile facts, audio recordings, or execution outputs are transmitted to external servers:

- **Local Neural Inference:** Powered exclusively via local Ollama (`127.0.0.1:11434`) running quantized GGUF checkpoints.
- **Local Embedded Typography:** Removed all external Google Fonts dependencies (`fonts.googleapis.com`); all typography is bundled locally as variable WOFF2/OTF fonts in [`frontend/public/fonts/`](file:///D:/C.O.P.P.E.R/frontend/public/fonts/).
- **Disabled Telemetry:** OpenTelemetry exporters (`OTEL_ENABLED=false`) and ChromaDB telemetry are deactivated by default.
- **Host Binding Isolation:** Backend binds strictly to `127.0.0.1:8000`, refusing external network routing.

---

## 2. Threat Model & Trust Boundaries

```mermaid
graph TD
    subgraph Untrusted Zone ["Untrusted / User Input"]
        Input["User Prompts, Obfuscated Payloads, Shell Commands"]
    end

    subgraph Boundary 1 ["Boundary 1: Data Firewall & Normalizer"]
        Firewall["Regex PII / API Key Sanitizer"]
        Normalizer["Unicode Homoglyph & Base64/Hex Decoder"]
    end

    subgraph Boundary 2 ["Boundary 2: Guardian Alignment Gate"]
        DFM["DFM-Guard Friction Engine<br/>(Level 0: Execute, Level 1: Nudge,<br/>Level 2: Challenge, Level 3: Refuse)"]
    end

    subgraph Boundary 3 ["Boundary 3: Forge Code Sandbox"]
        AST["Layer 1: AST Validator<br/>(Blocks os, sys, dunders)"]
        Kernel["Layer 2: Kernel Sandbox<br/>(DEVNULL stdin, 256MB cap, 15s timeout)"]
    end

    subgraph Trusted Zone ["Trusted Local Persistence"]
        DB["SQLite WAL & ChromaDB Vector Store"]
    end

    Input --> Boundary 1
    Boundary 1 --> Boundary 2
    Boundary 2 -->|Safe Tool Call| Boundary 3
    Boundary 3 --> Trusted Zone
```

---

## 3. Defense-in-Depth Mechanisms

### 3.1 Zero-Trust Data Firewall
- **File:** [`backend/app/core/data_firewall.py`](file:///D:/C.O.P.P.E.R/backend/app/core/data_firewall.py)
- Scrubs high-entropy API tokens (OpenAI `sk-proj-`, Anthropic `sk-ant-`, AWS access keys, JWT Bearer tokens), Social Security Numbers (SSNs), credit card numbers, and sensitive filesystem paths prior to storage or inference.
- Rejects sensitive tokens from being indexed into the semantic vector response cache or user memory profiles (`active_user.json`).

### 3.2 Adversarial Obfuscation Defenses
- **File:** [`backend/app/core/guardian.py`](file:///D:/C.O.P.P.E.R/backend/app/core/guardian.py)
- **Recursive Normalization:**
  - Unmasks Cyrillic/Greek homoglyphs and removes zero-width invisible characters.
  - Recursively decodes unquoted Base64 CLI arguments (`-EncodedCommand ...`, `echo ... | base64 -d`).
  - Decodes byte-hex sequences (`bytes.fromhex(...)`, `certutil -decodehex`).
- **Destructive Command Interception:**
  - Intercepts LOLBAS executables (`regsvr32`, `mshta`, `bitsadmin`, `certutil`).
  - Intercepts destructive PowerShell cmdlets (`Clear-Disk`, `Format-Volume`, `Remove-Item -Recurse -Force`, `vssadmin delete shadows`).
  - Intercepts outbound exfiltration commands (`Invoke-RestMethod`, `curl -T`, SSH tunneling).

### 3.3 Two-Layer Sandbox Isolation
- **Layer 1: AST Static Security Gate ([`ast_validator.py`](file:///D:/C.O.P.P.E.R/backend/app/core/ast_validator.py)):**
  - Statically analyzes Python syntax trees before execution.
  - Blocks unauthorized imports (`os`, `sys`, `subprocess`, `ctypes`, `socket`, `importlib`).
  - Blocks dangerous builtins (`eval`, `exec`, `__import__`).
  - Blocks dynamic dunder access (`getattr(obj, '__' + 'class__')`, `__subclasses__`, `__globals__`).
- **Layer 2: Kernel OS Sandbox ([`kernel_sandbox.py`](file:///D:/C.O.P.P.E.R/backend/app/core/kernel_sandbox.py)):**
  - Isolates subprocess execution with `stdin=subprocess.DEVNULL` to prevent terminal hanging.
  - Enforces 256 MB memory ceilings and 15-second execution timeouts.

---

## 4. Known Security Boundaries & Recommendations

1. **Host Storage Encryption:**
   - Because C.O.P.P.E.R. stores memory and session history locally on disk (`data/copper_memory.db`), users should maintain whole-disk encryption (BitLocker on Windows, FileVault on macOS, LUKS on Linux) to prevent offline physical theft of local database files.
2. **Local Root Boundaries:**
   - If the host operating system user account is fully compromised, local files can be inspected. C.O.P.P.E.R. runs as an unprivileged user process and does not require administrative or root privileges.
3. **Model Evasion Risk:**
   - Local language models can be subject to subtle prompt manipulations. The Guardian Safety Engine intercepts known prompt injections deterministically via regex and heuristic safety boundaries before the LLM receives the input.
