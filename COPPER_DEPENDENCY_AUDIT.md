# C.O.P.P.E.R. Supply Chain & Dependency Audit

**Scope:** Python Backend & Node.js Frontend Dependencies  
**Audit Date:** October 16, 2026  
**Tools Employed:** `npm audit`, `pip-audit`, dependency manifest inspection  
**Audit Status:** **CLEAN / ZERO KNOWN HIGH/CRITICAL CVEs**

---

## 1. Executive Summary

A comprehensive supply chain and vulnerability audit was conducted on all packages across the C.O.P.P.E.R. runtime. All critical and high-severity supply chain vulnerabilities previously detected in transitive dependencies have been patched, lockfiles have been reconciled, and automated tests verify that all runtime integrations remain fully operational.

---

## 2. Frontend Dependency Audit (`frontend/`)

### Initial Baseline Vulnerability Finding
During initial scanning of `frontend/package-lock.json`, `npm audit` flagged **17 vulnerabilities**:
- **Critical (1):** Command Injection in `shell-quote` (via transitive dependencies).
- **High (7):** Regular Expression Denial of Service (ReDoS) and Prototype Pollution in `brace-expansion`, `joi`, `http-cache-semantics`, and `undici`.
- **Moderate / Low (9):** Transitive devDependency parsing issues in legacy test utilities.

### Remediation Applied
- Executed `npm.cmd audit fix` to update semver-compatible dependency trees without breaking peer contracts.
- Locked updated sub-dependencies in `frontend/package-lock.json`.
- Validated React 19 and Vite 8 compatibility.

### Post-Remediation Verification
```
$ npm audit
found 0 vulnerabilities

$ npm run test
✓ 41 passed across 6 test suites in 5.43s

$ npm run build
✓ built in 585ms
```

---

## 3. Backend Dependency Audit (`backend/`)

### Core Python Runtime Manifest
The backend leverages modern, hardened Python libraries:

| Library | Version | Role | License | Security Status |
|---|---|---|---|---|
| `fastapi` | 0.141.1 | High-throughput asynchronous REST & WebSocket API | MIT | Clean / Verified |
| `uvicorn` | 0.52.4 | ASGI Server | BSD-3-Clause | Clean / Verified |
| `pydantic` | 2.12.5 | Runtime data validation & schema serialization | MIT | Clean / Verified |
| `sqlalchemy` | 2.0.44 | Typed database ORM | MIT | Clean / Verified |
| `chromadb` | 1.5.9 | Local vector embedding store | Apache-2.0 | Clean / Telemetry Disabled |
| `torch` | 2.14.0 | Local ML inference & tensor manipulation | BSD-3-Clause | Clean / Verified |
| `psutil` | 7.2.2 | Local process monitoring & resource metering | BSD-3-Clause | Clean / Verified |
| `opentelemetry-api` | 1.39.1 | In-process observability and tracing | Apache-2.0 | Clean / Verified |

### Security Observations & Hardening
1. **ChromaDB Telemetry:** In `backend/app/ai/cache/semantic_cache.py`, ChromaDB is initialized with `Settings(anonymized_telemetry=False, is_persistent=True)` to prevent background HTTP pings.
2. **Subprocess Invocations:** All tool-driven subprocess execution (`shell_execute`) is mediated through the AST validator and Guardian Safety Gate. Unsafe command chaining and privilege escalation vectors are blocked before reaching the OS shell.

---

## 4. License Compliance

All included open-source packages belong to permissive business-friendly licenses:
- **MIT:** FastAPI, Pydantic, SQLAlchemy, React, Lucide-React, Vite, Vitest.
- **Apache-2.0:** ChromaDB, OpenTelemetry, HuggingFace Transformers.
- **BSD-3-Clause:** PyTorch, Uvicorn, psutil.

No copyleft GPL/AGPL libraries are packaged into binary client artifacts.
