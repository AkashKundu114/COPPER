# C.O.P.P.E.R. Deployment Security Guide

This guide provides operational hardening instructions for deploying C.O.P.P.E.R. on single-user developer workstations and isolated enterprise enclaves.

---

## 1. Operator Key & Authentication Setup

C.O.P.P.E.R. automatically provisions a cryptographically strong host operator key upon first startup:
- **Default Location:** `data/copper_operator.key`
- **File Permissions:** Enforce read/write restricted strictly to the host user (`chmod 600 data/copper_operator.key` on Linux/macOS; NTFS user ACL on Windows).
- **Environment Variable Override:** To supply an external key via secret manager or container environment:
  ```bash
  export COPPER_API_KEY="your_secure_256bit_operator_key_here"
  ```
- **Strict Authentication Enforcement:** By default, in local desktop mode, unauthenticated loopback requests resolve to the local operator. For zero-trust production mode, enable strict authentication in `.env`:
  ```ini
  AUTH_ENFORCED=True
  ```
  Once active, all non-exempt requests must provide:
  - `X-API-Key: <key>` OR
  - `Authorization: Bearer <key>`

---

## 2. Network Isolation & Egress Configuration

Configure the desired network isolation boundary in `.env`:

```ini
# Options: offline_airgap | local_services | user_authorized_egress
NETWORK_MODE=user_authorized_egress

# Enable/disable outbound search engine integration
WEB_SEARCH_ENABLED=True

# Enable deterministic SSRF blocking for RFC 1918 subnets and cloud metadata
SSRF_PROTECTION_ENABLED=True
```

For ultra-secure air-gapped enclaves:
```ini
NETWORK_MODE=offline_airgap
WEB_SEARCH_ENABLED=False
```

---

## 3. Sandboxing & Code Execution Hardening

C.O.P.P.E.R. executes Python code via `ForgeSandbox`. Recommended configuration in `.env`:

```ini
# Preferred runner backend: auto | docker | pyodide | kernel
SANDBOX_BACKEND=auto

# Hard execution quotas
SANDBOX_TIMEOUT_SECONDS=15
SANDBOX_MEMORY_LIMIT_MB=256
SANDBOX_CPU_LIMIT=1.0
SANDBOX_NETWORK_ENABLED=False
```

When Docker is available on the host:
- The runner automatically spawns ephemeral containers with `--read-only`, `--network=none`, `--cap-drop=ALL`, `--tmpfs /tmp:size=64m`.
- The container image defaults to `python:3.12-slim`.

On Windows without Docker:
- `KernelSandbox` activates Windows Job Objects (`SetInformationJobObject`) with `JOB_OBJECT_LIMIT_PROCESS_MEMORY` and hard CPU rate caps.

---

## 4. API Rate Limiting Configuration

Protect the system from denial-of-service and VRAM exhaustion:

```ini
RATE_LIMIT_ENABLED=True
```

The built-in sliding window rate limiter protects sensitive endpoints (`/api/v1/chat/message`, `/api/v1/audit/delete-all`, `/api/v1/agents/activate`) to 20 req/min and standard endpoints to 120 req/min with burst damping.
