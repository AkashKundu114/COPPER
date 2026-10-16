# Changelog & Verification Record: Project A — C.O.P.P.E.R.

All notable changes made to C.O.P.P.E.R. during the October 16, 2026 Deep Audit are documented here.

---

## [3.1.0-audit] - 2026-10-16

### Security & Privacy Fixes (P0 - P2)

- **AST Sandbox Escape Hardening (`backend/app/core/ast_validator.py`):**
  - Expanded `FORBIDDEN_DUNDERS` to include `__class__`, `__dict__`, `__init__`, `__closure__`, `__reduce__`, `__reduce_ex__`, `__getattribute__`, and `__import__`.
  - Updated `_check_attr_builtins`: non-literal dynamic attribute lookups in `getattr()`, `setattr()`, and `delattr()` (such as `'__in' + 'it__'`) are now rejected as critical AST violations.
  - Prohibited unverified dunder attribute access.
- **Guardian Defense Interception Hardening (`backend/app/core/guardian.py`):**
  - Added regex for piped shell invocations (`\|\s*(bash|sh|zsh|powershell|pwsh|iex|perl|python|ruby)\b`) without boundary restrictions.
  - Added regex patterns for inline Python deletion one-liners (`(os|shutil)\.(remove|unlink|rmdir|rmtree)` and `python -c ...`).
  - Added regex for PowerShell deletion commands (`remove-item(\s+.*)?`).
  - Updated `SAFETY_TRIGGERS` with `| perl`, `| python`, `| ruby`, `| pwsh`, `remove-item`.
- **Guardian Streaming & DB-Bypass Fixes (`backend/app/services/chat_service.py`):**
  - Enforced `verdict.level >= DisagreementLevel.CHALLENGE` check prior to token streaming in `stream_message()`, aborting prompt generation on destructive requests.
  - Removed database gating condition so Guardian challenges execute unconditionally.
- **File Tools Sandbox Confinement (`backend/app/ai/tools/builtin/file_tools.py` & `executor.py`):**
  - Added `validate_safe_path()` restricting `file_read`, `file_write`, `file_list`, and `file_search` within `DOCUMENTS_DIR`, project root, and system temp directories.
  - Denied access to OS system folders (`C:\Windows`, `/etc/`) and sensitive secret files (`.env`, `id_rsa`, `.ssh`, `.aws`).
  - Set `is_destructive=True` for all `file_write` modes (overwrite and append) in `ToolExecutor`.
- **Git Command-Line Flag Injection Hardening (`backend/app/ai/ambient/code_review_agent.py`):**
  - Added `_sanitize_git_ref()` to validate git branch and commit parameters against option injection.
  - Added `--` delimiters to git subprocess calls.
- **Zero-Egress ChromaDB Settings (`backend/app/ai/memory/vector_store.py` & `semantic_cache.py`):**
  - Configured `Settings(anonymized_telemetry=False, is_persistent=True)` across all ChromaDB persistent and HTTP clients.
- **Offline TTS & Zero-Egress Audio (`backend/app/core/config.py` & `audio_service.py`):**
  - Added `TTS_OFFLINE_ONLY = True` configuration and blocked public Microsoft `edge-tts` internet requests.
- **WebSocket CSWSH Defense (`backend/app/api/websocket/manager.py`):**
  - Added `Origin` header validation against `settings.ALLOWED_ORIGINS` to eliminate Cross-Site WebSocket Hijacking.
- **Hardcoded Secrets Redaction (`research/ieee_latexqc_report.json`):**
  - Replaced legacy AWS Access Key, HMAC signatures, and Overleaf JWT with redacted tokens.
- **Resilient Audio & Wake-Word Pipeline (`backend/app/services/wake_word_service.py`):**
  - Added `PortAudioError` recovery in `_run_openwakeword` with automatic fallback to whisper buffer ingestion.
  - Added `push_audio_chunk()` and asynchronous speech window queue retrieval.
- **Truthful Benchmark Reporting (`backend/eval/benchmark.py`):**
  - Replaced hardcoded `(0 Breaches)` string and static sensitivity claims with dynamically evaluated false-negative metrics.

### Electron & Desktop IPC Fixes (P2)

- **Preload Whitelist Synchronization (`frontend/electron-main.cjs`):**
  - Registered safe IPC handlers for `get-activation-status`, `activate-local-gpu`, `activate-owner-code`, `get-system-info`, and `run-setup-wizard`.
  - Added uncaught exception and unhandled rejection handlers to the Electron main process.
  - Enforced minimum window bounds (`800x600`) in `electron-main.cjs`.

### Regression Tests Added

- `tests/core/test_ast_validator.py`:
  - `test_dynamic_attribute_resolution_getattr_blocked`: verifies dynamic attribute resolution is intercepted.
  - `test_sandbox_escape_subclasses_chain_blocked`: verifies object traversal via `__subclasses__` is blocked.
- `tests/core/test_guardian.py`:
  - `test_guardian_adversarial_evasion_intercepted`: verifies destructive Python one-liners, `find -delete`, and piped shells trigger `DisagreementLevel.SAFETY`.
- `tests/core/test_file_sandbox_security.py`:
  - `test_validate_safe_path_blocks_secrets_and_traversal`: verifies path traversal and `.env`/`.ssh` secret access are blocked.
  - `test_file_read_and_write_sandbox_confinement`: verifies tool-level sandbox enforcement for `file_read`, `file_write`, `file_list`, and `file_search`.
  - `test_sanitize_git_ref_prevents_flag_injection`: verifies git ref validation and dash-prefixed flag rejection.

### Verification

- 635+ Backend Pytest tests passed (100% pass rate).
- 41 Frontend Vitest tests passed.
- Production TypeScript/Vite frontend build succeeded in 1.13s with 0 errors.
