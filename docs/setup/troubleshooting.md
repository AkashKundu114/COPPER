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
3. Ensure models are pulled:
   ```bash
   ollama pull llama3.1:8b
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
