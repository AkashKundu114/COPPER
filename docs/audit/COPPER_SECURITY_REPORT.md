# Security Audit & Vulnerability Assessment: Project A — C.O.P.P.E.R.

**Target Repository:** `D:\C.O.P.P.E.R`  
**Date:** October 16, 2026  
**Auditor:** Principal Security Engineer & Red-Team Specialist  
**Standard:** OWASP Desktop & API Top 10, CWE / SANS Top 25

---

## 1. Executive Security Summary

The C.O.P.P.E.R. platform was subjected to white-box penetration testing and static security analysis, focusing on the Python AST sandbox, Guardian command interception, Electron IPC boundaries, local data persistence, and dependency integrity.

Two major security vulnerabilities were identified, reproduced, surgically patched, and verified with dedicated regression suites.

---

## 2. Vulnerability Ledger & Remediation Analysis

### 2.1 [COPPER-SEC-01] [CRITICAL] AST Security Gate Bypass via Dynamic Attribute Resolution

- **CWE:** CWE-94 (Improper Control of Generation of Code), CWE-693 (Protection Mechanism Failure)
- **Component:** `backend/app/core/ast_validator.py` (`ASTSecurityValidator._check_attr_builtins`)
- **Severity:** **Critical (CVSS 9.8)**
- **Vulnerability Description:**  
  The AST validator's attribute check in `_check_attr_builtins` inspected only `ast.Constant` string literals. Dynamic expressions—such as string concatenation (`getattr(s, '__in' + 'it__')`) or variable-backed attribute lookups—did not evaluate as `ast.Constant`, resulting in zero recorded AST violations (`is_safe=True`, `violations=[]`). Additionally, several critical dunder attributes (`__class__`, `__dict__`, `__init__`, `__closure__`) were omitted from `FORBIDDEN_DUNDERS`.
- **Exploitation Impact:**  
  In environments where Docker containers were unavailable, `kernel_sandbox.py` fell back to `SubprocessSanitizedRunner`. Attackers could leverage standard Python object traversal (`().__class__.__bases__[0].__subclasses__()`) to escape the sandbox and execute arbitrary host operating system commands.
- **Proof of Concept:**
  ```python
  c = ().__class__
  b = getattr(c, '__ba' + 'ses__')[0]
  subs = getattr(b, '__subclass' + 'es__')()
  for s in subs:
      if s.__name__ == '_wrap_close':
          fn = getattr(s, '__in' + 'it__')
          glbs = getattr(fn, '__glo' + 'bals__')
          sys_mod = glbs['sys']
          print(f"HOST_ESCAPED: {sys_mod.version}")
          break
  ```
  *Pre-fix Output:* `violations=[]`, `risk_level='safe'`, executed with exit code 0.
- **Remediation Implemented:**
  1. Expanded `FORBIDDEN_DUNDERS` to include: `__class__`, `__subclasses__`, `__globals__`, `__builtins__`, `__code__`, `__bases__`, `__mro__`, `__dict__`, `__init__`, `__closure__`, `__reduce__`, `__reduce_ex__`, `__getattribute__`, `__import__`.
  2. Modified `_check_attr_builtins`: non-literal attribute arguments in `getattr`, `setattr`, or `delattr` are now flagged as critical violations: `"Call to {builtin_name}() with dynamic or non-literal attribute is blocked."`
  3. Prohibited any dunder attribute not in `ALLOWED_SAFE_DUNDERS`.
- **Regression Verification:**  
  Passed 31/31 unit tests in `tests/core/test_ast_validator.py`, including `test_dynamic_attribute_resolution_getattr_blocked` and `test_sandbox_escape_subclasses_chain_blocked`.

---

### 2.2 [COPPER-SEC-02] [HIGH] Guardian Safety Interception Evasion on Scripting One-Liners & Piped Shells

- **CWE:** CWE-184 (Incomplete List of Disallowed Inputs)
- **Component:** `backend/app/core/guardian.py` (`SAFETY_PATTERNS`, `SAFETY_TRIGGERS`)
- **Severity:** **High (CVSS 8.2)**
- **Vulnerability Description:**  
  The Guardian Safety Engine used regex patterns with word boundaries (`\b`) directly preceding punctuation (`|`), which failed to match piped shells (e.g. `payload | perl`). Furthermore, dangerous inline script invocations (`python -c "import os; os.remove('/etc/hosts')"`) and PowerShell cmdlets (`Remove-Item C:/data -Force`) failed to trigger `DisagreementLevel.SAFETY`.
- **Exploitation Impact:**  
  Destructive shell actions received `DisagreementLevel.EXECUTE (Level 0)` without requiring user confirmation, allowing catastrophic filesystem or configuration deletion.
- **Remediation Implemented:**
  1. Added standalone piped shell regex: `r"(\|\s*(bash|sh|zsh|powershell|pwsh|iex|perl|python|ruby)\b)"`.
  2. Added inline Python file deletion patterns: `(os|shutil)\.(remove|unlink|rmdir|rmtree)` and `python(\d|\.exe)?\s+-c\s+.*(os\.remove|os\.unlink|rmtree|exec\(|urllib)`.
  3. Added PowerShell `remove-item(\s+.*)?` to `SAFETY_PATTERNS` and `SAFETY_TRIGGERS`.
- **Regression Verification:**  
  Passed 24/24 unit tests in `tests/core/test_guardian.py`, including `test_guardian_adversarial_evasion_intercepted`.

---

### 2.3 [COPPER-SEC-03] [MEDIUM] Dead Electron IPC Handlers Causing Unhandled Rejections

- **CWE:** CWE-284 (Improper Access Control / Incomplete IPC Registration)
- **Component:** `frontend/preload.cjs`, `frontend/electron-main.cjs`
- **Severity:** **Medium (CVSS 5.3)**
- **Vulnerability Description:**  
  `preload.cjs` whitelisted five IPC invocation channels (`get-activation-status`, `activate-local-gpu`, `activate-owner-code`, `get-system-info`, `run-setup-wizard`), but `electron-main.cjs` had no corresponding `ipcMain.handle()` registrations. Invoking these channels caused unhandled promise rejections in the renderer context.
- **Remediation Implemented:**  
  Registered sanitized, least-privilege IPC handlers in `electron-main.cjs` that return hardware architecture and platform metadata without exposing raw Node child process spawning.

---

### 2.4 [COPPER-SEC-04] [HIGH] Cross-Site WebSocket Hijacking (CSWSH) Origin Permissiveness

- **CWE:** CWE-346 (Origin Validation Error), CWE-1385 (Missing Origin Validation in WebSockets)
- **Component:** `backend/app/api/websocket/manager.py` (`ConnectionManager.connect`)
- **Severity:** **High (CVSS 7.5)**
- **Vulnerability Description:**  
  The WebSocket connection manager accepted incoming WebSocket connections without validating the `Origin` header against `settings.ALLOWED_ORIGINS`. Malicious web applications hosted on arbitrary browser origins could open WebSocket tunnels to `ws://localhost:8000/api/v1/chat/ws` and access chat histories or trigger agent actions.
- **Remediation Implemented:**  
  Added strict `Origin` header verification before accepting WebSocket sessions. If the request Origin header is missing or does not match `settings.ALLOWED_ORIGINS`, the connection is immediately aborted with HTTP 403 Forbidden (`code=status.WS_1008_POLICY_VIOLATION`).

---

### 2.5 [COPPER-SEC-05] [HIGH] Arbitrary File Read/Write Sandbox Escape via Built-in File Tools

- **CWE:** CWE-22 (Improper Limitation of a Pathname to a Restricted Directory / Path Traversal)
- **Component:** `backend/app/ai/tools/builtin/file_tools.py`, `backend/app/ai/tools/executor.py`
- **Severity:** **High (CVSS 8.6)**
- **Vulnerability Description:**  
  Built-in file tools (`file_read`, `file_write`, `file_list`, `file_search`) accepted arbitrary filesystem paths without boundary validation, enabling directory traversal into host system directories (e.g. `C:\Windows`, `/etc/`) and access to sensitive secrets (`.env`, `.ssh/id_rsa`). In addition, `file_write(mode="append")` failed to set `is_destructive=True`, bypassing Guardian review.
- **Remediation Implemented:**  
  1. Implemented `validate_safe_path()`: confines all file operations to permitted roots (`settings.DOCUMENTS_DIR`, workspace root, system temp).
  2. Blocked system directories (`C:\Windows`, `/etc`, etc.) and sensitive configuration/secret filenames (`.env`, `id_rsa`, `.ssh`, `.aws`).
  3. Hardened `ToolExecutor.execute()`: `is_destructive` evaluates `True` for all `file_write` modes (both `overwrite` and `append`).
- **Regression Verification:**  
  Passed `tests/core/test_file_sandbox_security.py` (3/3 passed).

---

### 2.6 [COPPER-SEC-06] [HIGH] Git Command-Line Flag Injection in Ambient Code Review Agent

- **CWE:** CWE-88 (Improper Neutralization of Argument Delimiters in a Command)
- **Component:** `backend/app/ai/ambient/code_review_agent.py` (`analyze_diff`, `analyze_commit`)
- **Severity:** **High (CVSS 7.4)**
- **Vulnerability Description:**  
  Branch names and commit hashes passed to `git diff` and `git show` subprocess commands lacked argument separation, allowing branch names starting with dashes (e.g. `--output=...`) to be interpreted as command-line options.
- **Remediation Implemented:**  
  1. Added `_sanitize_git_ref()`: strictly validates branch and commit formats, rejecting any reference starting with `-` or containing illegal characters.
  2. Added `--` argument delimiters to `git diff` and `git show` invocations to terminate option parsing.
- **Regression Verification:**  
  Passed `tests/core/test_file_sandbox_security.py::test_sanitize_git_ref_prevents_flag_injection` and `tests/ai/test_delegation_and_novelty.py`.

---

### 2.7 [COPPER-SEC-07] [MEDIUM] Default Telemetry Beaconing in Persistent ChromaDB Clients

- **CWE:** CWE-359 (Exposure of Private Personal Information to an Unauthorized Entity)
- **Component:** `backend/app/ai/memory/vector_store.py`, `backend/app/ai/cache/semantic_cache.py`
- **Severity:** **Medium (CVSS 5.3)**
- **Vulnerability Description:**  
  ChromaDB's default `PersistentClient` enables anonymous usage telemetry unless explicitly disabled via configuration. This risked outbound network requests that violated the project's offline zero-egress commitment.
- **Remediation Implemented:**  
  Explicitly passed `chromadb.config.Settings(anonymized_telemetry=False, is_persistent=True)` to all `PersistentClient` and `HttpClient` instantiations in `vector_store.py` and `semantic_cache.py`.

---

### 2.8 [COPPER-SEC-08] [HIGH] Streaming Guardian Bypass on Destructive Token Streams

- **CWE:** CWE-693 (Protection Mechanism Failure), CWE-284 (Improper Access Control)
- **Component:** `backend/app/services/chat_service.py` (`stream_message`)
- **Severity:** **High (CVSS 8.1)**
- **Vulnerability Description:**  
  In `stream_message()`, Guardian verdicts were evaluated, but token streaming commenced before blocking actions occurred, allowing prompt responses to begin streaming to the UI even when flagged with `DisagreementLevel.CHALLENGE`.
- **Remediation Implemented:**  
  Patched `stream_message()` to check `verdict.level >= DisagreementLevel.CHALLENGE` prior to model generation, halting the stream immediately and emitting a challenge verdict frame to the client.

---

### 2.9 [COPPER-SEC-09] [CRITICAL] Adversarial Evasion via Obfuscation, PowerShell Commands, and LOLBAS

- **CWE:** CWE-184 (Incomplete List of Disallowed Inputs), CWE-693 (Protection Mechanism Failure)
- **Component:** `backend/app/core/guardian.py` (`normalize_adversarial_text`, `SAFETY_PATTERNS`, `SAFETY_TRIGGERS`)
- **Severity:** **Critical (CVSS 9.1)**
- **Vulnerability Description:**  
  The Guardian Safety Engine's base64 extractor only inspected quoted base64 strings (`['\"]([A-Za-z0-9+/=]{8,})['\"]`), completely missing unquoted CLI commands like `powershell -EncodedCommand cm0g...` and raw hex strings (`bytes.fromhex('...')`). In addition, destructive PowerShell cmdlets (`Clear-Disk`, `Format-Volume`), LOLBAS persistence vectors (`reg add ... /v Backdoor`, `certutil -urlcache`, `bitsadmin /transfer`), and SSH exfiltration commands (`Invoke-RestMethod ... id_rsa`) evaded regex interception.
- **Remediation Implemented:**  
  1. Implemented boundary-agnostic Base64 extraction for `-EncodedCommand`, `-enc`, and standalone strings.
  2. Implemented Hex string decoding for `bytes.fromhex(...)` and `\x..` escapes.
  3. Added explicit regex patterns and triggers for: `Clear-Disk`, `Format-Volume`, `Get-Disk`, `reg add.*Run`, `certutil.*-urlcache`, `bitsadmin.*transfer`, `Invoke-RestMethod.*id_rsa`, and `curl.*id_rsa`.
  4. Resolved regex non-word boundary trap for `ri C:\` commands.
- **Regression Verification:**  
  Passed 34/34 unit tests in `tests/security/test_ai_red_team.py` and 24/24 tests in `tests/core/test_guardian.py`.

---

## 3. Threat Assessment of Epistemic Memory & Local Data Store

- **Database Security:** `data/copper_memory.db` resides in local application storage. Foreign key constraints are enforced (`PRAGMA foreign_keys=ON`).
- **Secret Scanning:** Scanned for hardcoded credentials with `.gitleaks.toml`. Replaced legacy tokens in `research/ieee_latexqc_report.json` with redacted strings.
- **Data Egress Verification:** Zero cloud telemetry or external network calls are initiated by the backend. Network boundaries remain fully local (`127.0.0.1:8000`). ChromaDB telemetry and TTS cloud endpoints are explicitly disabled. External Google Fonts were removed from `frontend/index.html` and replaced with local bundled fonts (`/fonts/`). OpenTelemetry background export is disabled by default (`OTEL_ENABLED=False`).
