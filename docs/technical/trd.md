# C.O.P.P.E.R. Technical Requirements Document (TRD)

---

## 1. System Scope & Technical Objectives

This Technical Requirements Document specifies the operational criteria, performance targets, interface contracts, self-healing retries, and desktop/web packaging requirements for **C.O.P.P.E.R.**

---

## 2. System SLAs & Performance Metrics

| Metric | Target SLA | Degraded Threshold | Fallback Action |
| :--- | :--- | :--- | :--- |
| **Local LLM First Token (TTFT)** | $< 800\text{ ms}$ | $> 2500\text{ ms}$ | Warm up model cache / stream placeholder thoughts |
| **Local LLM Throughput** | $> 25\text{ tokens/sec}$ | $< 10\text{ tokens/sec}$ | Offer cloud offload via Data Firewall |
| **Agent Routing Speed** | $< 50\text{ ms}$ | $> 150\text{ ms}$ | Fall back to keyword regex router |
| **Epistemic Memory Retrieval** | $< 35\text{ ms}$ | $> 100\text{ ms}$ | Serve cached core user profile facts |
| **WebSocket Event Latency** | $< 20\text{ ms}$ | $> 75\text{ ms}$ | Re-establish socket ping loop |
| **Self-Healing Recovery SLA** | $< 3.0\text{ sec}$ | $> 8.0\text{ sec}$ | Escalate error frame to user prompt |

---

## 3. Interface Contracts & API Specifications

### 3.1 REST API Standards
All endpoints conform to OpenAPI 3.0 standards and return JSON structures using standard HTTP status codes.

- `POST /api/v1/chat/message`: Send synchronous user message.
- `GET /api/v1/agents`: List all 30 sub-agents, active status, familiarity scores, and orbital tiers.
- `POST /api/v1/agents/{id}/rollback`: Trigger immediate version rollback for specified agent.
- `GET /api/v1/memory`: Fetch epistemic user facts, observations, and hypotheses.
- `POST /api/v1/memory/reset`: Clear all epistemic memories and vector embeddings.
- `GET /api/v1/audit/logs`: Query audit trail records with filters for event type and severity.

### 3.2 WebSocket Streaming Protocol (`/ws/chat`)
Real-time bi-directional streaming for text generation and visualizer node state updates.

#### Outbound Client Payload:
```json
{
  "type": "user_message",
  "content": "Plan a refactor of the database models and check for performance bottlenecks.",
  "session_id": "sess_991823",
  "allow_cloud_fallback": true
}
```

#### Inbound Server Sequence:
1. `copper_thinking`: System initialized request parsing.
2. `route_decision`: Agent selection finalized (e.g., `{"agent_id": "coding_agent", "tier": "execution"}`).
3. `edge_pulse`: Fire visualizer synapse surge along calculated SVG coordinate path.
4. `agent_active`: Target node rest glow changes to active molten state.
5. `guardian_check`: Emits Guardian Level (0–3). If Level 2, fires challenge event payload.
6. `agent_speaking`: Emits response tokens and equalizer audio bar height values.
7. `memory_update`: Emits newly reinforced facts or hypothesis adjustments.
8. `done`: Request cycle complete.

---

## 4. Self-Healing & Fallback Execution Specification

```
                          +-------------------------------+
                          |     Agent Task Execution      |
                          +---------------+---------------+
                                          |
                                   [Error Occurs]
                                          |
                                          v
                          +-------------------------------+
                          | Check Retry Count (Max = 3)   |
                          +---------------+---------------+
                                          |
                 +------------------------+------------------------+
                 | (Count < 3)                                     | (Count >= 3)
                 v                                                 v
  +------------------------------+                  +------------------------------+
  |  Exponential Backoff &       |                  |  Switch Tool / Agent         |
  |  Parameter Adjust (Temp 0.2) |                  |  (Secondary Code/Plan Tool)  |
  +--------------+---------------+                  +--------------+---------------+
                 |                                                 |
                 v                                                 v
  +------------------------------+                  +------------------------------+
  |    Re-execute Task           |                  |  Fallback to Cloud LLM       |
  +------------------------------+                  |  via Data Firewall           |
                                                    +--------------+---------------+
                                                                   |
                                                                   v
                                                    +------------------------------+
                                                    |  Record to Audit Trail Log   |
                                                    +------------------------------+
```

---

## 5. Desktop & Web Packaging Specifications

### 5.1 Tauri Desktop Packaging
- **Target OS:** Windows 10/11 x64, macOS Sonoma+ (ARM64/x64), Linux (Ubuntu 22.04+).
- **Binary Footprint:** $< 45\text{ MB}$ standalone executable (excluding local LLM weights).
- **Process Model:** Rust main process spawning sidecar Python FastAPI server with automatic health monitoring and graceful shutdown.

### 5.2 React Web Interface
- **Dev Server:** Vite with HMR.
- **State Management:** Zustand store managing chat state, active agent nodes, equalizer levels, and modal alerts.
- **Design Language:** Custom Molten Copper theme with tailwind utility extensions and zero-dependency SVG visualizer engine.
