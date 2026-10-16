# C.O.P.P.E.R. REST API Specification

**Version**: `0.1.0-alpha`  
**Base URL**: `http://127.0.0.1:8000`  
**OpenAPI Interactive UI**: `http://127.0.0.1:8000/docs`  
**ReDoc Reference**: `http://127.0.0.1:8000/redoc`  

---

## 1. Overview & Security Architecture

The C.O.P.P.E.R. backend is built with FastAPI, providing an asynchronous, typed REST API for local desktop and CLI interactions.

### Security Boundaries
- **Loopback Binding**: By default, the server binds exclusively to `127.0.0.1` (`localhost`).
- **Zero Egress**: All endpoints process queries locally through Ollama, SQLite, and ChromaDB with zero network telemetry or outbound internet calls.
- **CORS Allowlist**: Restricted strictly to the local Electron/Vite frontend origin (`http://localhost:5173`, `http://127.0.0.1:5173`, and `tauri://localhost`).

---

## 2. Core Endpoints

### 2.1 System & Health

#### `GET /health`
Returns the operational health, database connectivity, and runtime mode of the backend service.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0-alpha",
  "demo_mode": false,
  "database": "connected",
  "chroma": "ready"
}
```

#### `GET /api/system/status`
Returns real-time CPU, RAM, and VRAM telemetry from the local host.

---

### 2.2 Chat & Dialogue Orchestration

#### `POST /api/chat`
Dispatches a user message to the active multi-agent router (`TFP-Router`). Evaluates intent, retrieves relevant context from epistemic memory, and streams or returns the model response.

**Request**:
```json
{
  "message": "Summarize my morning schedule and draft an email to the dev team.",
  "stream": false,
  "agent_override": null
}
```

**Response**:
```json
{
  "response": "Here is your morning schedule...",
  "agent": "chat",
  "model": "qwen2.5:14b",
  "context_retrieved": 3,
  "guardian_level": 0
}
```

---

### 2.3 Epistemic Memory & Beliefs

#### `GET /api/memory`
Retrieves stored memory facts with their epistemic confidence scores, decay rates, and provenance tiers.

**Query Parameters**:
- `min_confidence` (float, default `0.0`): Filter memories by minimum epistemic confidence.
- `tier` (string, optional): Filter by `fact` (>=0.85), `observation` (0.50-0.85), or `hypothesis` (<0.50).

#### `POST /api/memory`
Stores an episodic observation or reinforced user fact.

**Request**:
```json
{
  "content": "User prefers concise terminal commands without markdown formatting.",
  "confidence": 0.90,
  "importance": 0.80,
  "provenance": "user_explicit"
}
```

---

### 2.4 Guardian Safety & Friction

#### `POST /api/guardian/evaluate`
Pre-execution AST and safety review of a proposed agent action or tool invocation.

**Request**:
```json
{
  "tool_name": "terminal_exec",
  "command": "rm -rf /tmp/scratch"
}
```

**Response**:
```json
{
  "allowed": true,
  "friction_level": 2,
  "requires_user_confirmation": true,
  "challenge": "Destructive file removal detected on directory /tmp/scratch."
}
```

---

### 2.5 Voice & Wake-Word

#### `POST /api/voice/transcribe`
Submits an audio PCM buffer to the offline Whisper engine for transcription.

#### `POST /api/voice/synthesize`
Generates offline speech audio using the Kokoro-82M ONNX model (<80ms response).

---

### 2.6 Multi-Agent Registry

#### `GET /api/agents`
Returns the status, assigned hardware tier, and description of all registered agents in `backend/app/core/agent_registry.py`.

---

## 3. Error Handling

All endpoints return standard RFC 7807 problem details or structured JSON errors:
```json
{
  "detail": "Action blocked by Guardian Level 3 safety boundary."
}
```
No raw Python stack traces are leaked to clients.
