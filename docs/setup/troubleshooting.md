# C.O.P.P.E.R. Troubleshooting & Operational Guide

---

## 1. Common Startup & Connection Issues

### Issue 1.1: Ollama Connection Refused
**Symptom:** Backend log shows `httpx.ConnectError: Cannot connect to http://localhost:11434`.
**Cause:** Ollama desktop application or docker service is not running.
**Resolution:**
1. Check if Ollama service is active:
   ```bash
   curl http://localhost:11434/api/version
   ```
2. If running via Docker:
   ```bash
   docker-compose start ollama
   ```
3. Ensure models are linked/registered:
   ```bash
   python scripts/models/register_ollama_models.py
   ```

### Issue 1.2: Database Migration Errors (`Alembic Target Database Out of Date`)
**Symptom:** FastAPI fails to launch with `alembic.util.exc.CommandError: Target database is not up to date.`
**Resolution:**
1. Apply pending database migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
2. If schema conflict occurs during local development, reset local SQLite/Postgres DB:
   ```bash
   python -c "from app.database import reset_db; reset_db()"
   alembic upgrade head
   ```

---

## 2. WebSocket & Frontend Diagnostic Guide

### Issue 2.1: Neural Visualizer Nodes Stuck in Dormant State
**Symptom:** UI displays agent map, but nodes do not light up or pulse during user chat.
**Resolution:**
1. Open browser developer console (F12) and inspect WebSocket network frames under `/ws/chat`.
2. Verify socket received `copper_thinking` and `route_decision` messages.
3. If WebSocket connection failed, check CORS settings in `backend/app/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173", "http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## 3. Data Firewall & Self-Healing Diagnostics

### Issue 3.1: False Positive PII Redaction
**Symptom:** Data Firewall masks non-sensitive code variables (e.g. `secret_key_var`).
**Resolution:**
1. Inspect PII detection rules in `backend/app/core/data_firewall.py`.
2. Add excluded variable patterns to `FIREWALL_WHITELIST_PATTERNS`.
3. Review audit log entries in Security Center (`/security-center`) to inspect raw match reasons.

### Issue 3.2: Self-Healing Retry Loop Max Reached
**Symptom:** Execution halts with `SelfHealingException: Retry limit (3) exceeded for task tool_exec_41`.
**Resolution:**
1. View diagnostic trace in `audit_log` table or Security Center UI.
2. Check if local LLM context length was exceeded (switch task model to 32k context model).
3. Confirm script execution permissions if running local CLI tool.

---

## 4. Hardware Licensing & Storage Diagnostics

### Issue 4.1: GPU Not Detected / Code Stuck on "Detecting..." or "COPPER-..."
**Symptom:** On initial launch, the Activation screen shows GPU Device as `Detecting...` and Hardware Code as `COPPER-...`.
**Cause:** 
1. The FastAPI backend is not running on `127.0.0.1:8000`.
2. The Vite dev server was accessed directly without routing `/api` to the backend.
**Resolution:**
1. Launch both services together using `.\scripts\start_copper.bat` (or start `.\scripts\start_backend.bat` before `.\scripts\start_frontend.bat`).
2. Verify Vite dev proxy in `frontend/vite.config.ts` forwards `/api` to `http://127.0.0.1:8000`.
3. Click the **"↻ Refresh"** button on the Activation screen once the backend is initialized.

### Issue 4.2: Master Activation Code vs. Remote GPU Sharing
**Symptom:** User wonders if sharing their master activation code (`COPPER-XXXX-XXXX-XXXX`) connects remote peers to their GPU.
**Clarification:**
- The activation code is an **offline DRM licensing gate** only; it validates offline software authorization without cloud accounts.
- It **does not** stream or share physical GPU kernels over the network. The recipient's machine runs models locally using their own hardware.
- To share inference over the network, expose the local Ollama daemon (`OLLAMA_HOST=0.0.0.0:11434`) over a secure mesh VPN (e.g., Tailscale) and configure `OLLAMA_BASE_URL` on the client.

### Issue 4.3: Low Disk Space on C: or D: Drive
**Symptom:** System warning on low disk space due to temp build artifacts or duplicate model files.
**Resolution:**
1. **C: Drive Temp Cleanup:** Clear `%LOCALAPPDATA%\Temp` and run `cleanmgr.exe /d C:`.
2. **D: Drive Model Deduplication:** C.O.P.P.E.R. models are managed directly via Ollama (`D:\Ollama\Models\blobs`). Any standalone `.gguf` copies under `ai-models/core` or `ai-models/subagents` are redundant and can be removed without impacting Ollama or runtime operations.

