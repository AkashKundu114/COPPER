# COPPER Framework — Backend Database Schema

> **Documentation set:** [PRD](PRD.md) · [TRD](TRD.md) · [App Flow](APP_FLOW.md) · [UI/UX Brief](UI_UX_BRIEF.md) · [Backend Schema](BACKEND_SCHEMA.md) · [Implementation Guide](IMPLEMENTATION.md)

---

## 10. Dual-Database Architecture

> **Architecture Principle:** The system uses three storage layers, each optimized for a different access pattern.

1. **`state.json`** — Ultra-fast volatile relay (microsecond read/write, SSD-resident)
2. **`copper.db` (SQLite)** — Structured persistent storage (serverless, 0 MB idle RAM)
3. **ChromaDB (local)** — Vector embeddings for document retrieval (ephemeral/on-demand)

---

## 11. `state.json` — Active State Schema

`state.json` is the live relay baton passed between agents during a single orchestration cycle (see [App Flow §8](APP_FLOW.md#8-primary-execution-flow-state-persistent-hot-swap)). It must remain under **1 MB** ([TRD §7.4](TRD.md#74-tr-04-state-file-integrity)) and is written atomically.

```json
{
  "session_id": "session_98234",
  "user_prompt": "Open my web browser",
  "next_agent": "HAWK",
  "next_model": "MODEL_4_VISION",
  "system_status": "PROCESSING",
  "SYSTEM_MODE": "NORMAL",
  "force_interrupt": false,
  "interrupt_data": null,

  "telemetry": {
    "active_agent": "HAWK",
    "vram_allocation_mb": 580,
    "current_action": "Analyzing desktop screenshot for browser icon",
    "step_number": 3,
    "total_steps_estimated": 5,
    "last_update": "16:02:45"
  },

  "task_context": {
    "target": "browser_icon",
    "coordinates": null,
    "code_payload": null,
    "search_results": null,
    "file_path": null
  },

  "dialogue_transcript": [
    {"agent": "COPPER", "text": "Routing screen task to HAWK.", "timestamp": "16:02:42"},
    {"agent": "HAWK", "text": "On it. Analyzing display now.", "timestamp": "16:02:44"}
  ],

  "execution_logs": [
    "[16:02:40] [SYSTEM] User prompt received.",
    "[16:02:41] [COPPER] Core Engine loaded (4.8 GB VRAM).",
    "[16:02:43] [SYSTEM] Purging Core Engine. Cache cleared.",
    "[16:02:44] [SYSTEM] Loading Florence-2-base (HAWK) 580 MB VRAM."
  ]
}
```

### Field Reference

| Field | Type | Notes |
|---|---|---|
| `session_id` | string | Foreign key into `sessions.session_id` |
| `user_prompt` | string | Raw user input for the current cycle |
| `next_agent` | string | Agent ID to load next, or `"COMPLETE"` to end the loop |
| `next_model` | string | Key into `MODEL_MAP` (see [Implementation Guide §14.1](IMPLEMENTATION.md#141-main-orchestration-loop)) |
| `system_status` | string | `PROCESSING` \| `CRASHED` \| etc. — drives the Pulse Badge ([UI/UX Brief §3.1](UI_UX_BRIEF.md#31-pulse-badge)) |
| `SYSTEM_MODE` | string | `NORMAL` \| `BOSS` — see [App Flow §8.5](APP_FLOW.md#85-boss-mode-flow) |
| `force_interrupt` | boolean | Set by `clock_daemon.py` / `kinetic_daemon.py` |
| `interrupt_data` | string \| null | Payload describing the interrupt (e.g. `"ALARM: Meet team for Valorant Premier"`) |
| `telemetry.*` | object | Drives the Action Banner and VRAM Gauge |
| `task_context.*` | object | Scratch space for the active agent's working data |
| `dialogue_transcript[]` | array | Last-N entries consumed by sub-agents for peer commentary (last 3, per [Implementation Guide §14.1](IMPLEMENTATION.md#141-main-orchestration-loop)) |
| `execution_logs[]` | array | Rotated to `agent_execution_logs` after 100 entries ([TRD §7.4](TRD.md#74-tr-04-state-file-integrity)) |

---

## 12. SQLite Database Schema (`copper.db`)

### 12.1 Sessions Table

Tracks unique conversation sessions.

```sql
CREATE TABLE sessions (
    session_id   TEXT PRIMARY KEY,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_name TEXT,
    is_active    INTEGER DEFAULT 1
);
```

### 12.2 Chat History Table

Full message archive.

```sql
CREATE TABLE chat_history (
    message_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL,
    sender       TEXT NOT NULL,             -- 'user' | 'COPPER' | agent_name
    content      TEXT NOT NULL,
    message_type TEXT DEFAULT 'DIALOGUE',   -- 'DIALOGUE' | 'TECHNICAL_PAYLOAD'
    timestamp    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

### 12.3 Agent Execution Logs Table

Audit trail for all agent calls.

```sql
CREATE TABLE agent_execution_logs (
    log_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT NOT NULL,
    agent_name        TEXT NOT NULL,   -- 'HAWK', 'CYPHER', 'COPPER', etc.
    model_profile     TEXT,            -- 'MODEL_1', 'MODEL_2', etc.
    task_given        TEXT,
    task_output       TEXT,
    execution_status  TEXT,            -- 'SUCCESS' | 'FAILED' | 'PARTIAL'
    error_message     TEXT,
    vram_peak_mb      INTEGER,
    execution_time_ms INTEGER,
    timestamp         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

### 12.4 Agent Profiles Table

Personality and system prompt data for all 30 agents (see [PRD §3](PRD.md#3-the-30-agents--full-roster) and [Appendix A](PRD.md#appendix-a-agent-personality-reference)).

```sql
CREATE TABLE agent_profiles (
    agent_id            TEXT PRIMARY KEY,   -- 'COPPER', 'CYPHER', 'HAWK', etc.
    display_name        TEXT NOT NULL,
    model_profile       TEXT NOT NULL,      -- 'MODEL_1' through 'MODEL_6'
    lora_adapter_path   TEXT,               -- './adapters/cypher_dev_adapter/'
    system_role         TEXT NOT NULL,      -- Core responsibility description
    personality_traits  TEXT,               -- Human personality descriptor block
    humor_style         TEXT,               -- Humor archetype
    vocabulary_quirks   TEXT,               -- Speech pattern notes
    peer_rivalries      TEXT,               -- JSON: {"ARGUS": "Treats like critic"}
    is_active           INTEGER DEFAULT 1
);
```

> **Note:** Because `agent_id` is the primary key, the duplicate `NEXUS` entry in [PRD §3](PRD.md#3-the-30-agents--full-roster) must be resolved (merge or rename) before seeding this table — otherwise the 30-agent roster will only insert 29 rows.

### 12.5 Episodic Memory Table

Long-term project tracking for proactive greetings.

```sql
CREATE TABLE episodic_memory (
    episode_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category            TEXT,     -- 'CODING' | 'PHOTO_GEN' | 'COLLEGE' | 'GAMING'
    project_name        TEXT,     -- 'autoData stock api', 'portfolio website'
    last_activity_date  DATETIME DEFAULT CURRENT_TIMESTAMP,
    summary_details     TEXT,     -- 'Implemented FastAPI endpoints, waiting on tests'
    logged_by_agent     TEXT,     -- which agent wrote this entry
    importance_score    INTEGER   -- 1 (low) to 5 (critical)
);
```

### 12.6 Temporal Tasks Table

Alarms, reminders, calendar events.

```sql
CREATE TABLE temporal_tasks (
    task_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type          TEXT NOT NULL,   -- 'ALARM' | 'REMINDER' | 'CALENDAR'
    trigger_timestamp  DATETIME NOT NULL,
    payload            TEXT NOT NULL,   -- "Meet team for Valorant Premier"
    repeat_pattern     TEXT,            -- NULL | 'DAILY' | 'WEEKLY'
    is_completed       INTEGER DEFAULT 0,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 12.7 Episodic Tracking Pause Table

Allows the user to pause episodic logging.

```sql
CREATE TABLE tracking_control (
    control_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    is_paused   INTEGER DEFAULT 0,
    paused_at   TIMESTAMP,
    resumed_at  TIMESTAMP,
    reason      TEXT
);
```

### 12.8 Full Schema with Indexes

Performance indexes for `copper.db`:

```sql
-- Speed up common queries
CREATE INDEX idx_chat_session   ON chat_history(session_id);
CREATE INDEX idx_logs_session   ON agent_execution_logs(session_id);
CREATE INDEX idx_logs_agent     ON agent_execution_logs(agent_name);
CREATE INDEX idx_tasks_trigger  ON temporal_tasks(trigger_timestamp, is_completed);
CREATE INDEX idx_episodes_date  ON episodic_memory(last_activity_date DESC);
CREATE INDEX idx_episodes_score ON episodic_memory(importance_score DESC);
```
