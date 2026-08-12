# C.O.P.P.E.R. Backend Database & State Schema Specification

This document specifies the 3-layer state architecture (Live `state.json`, Relational SQLite DB, and ChromaDB Vector Store) specified in the **C.O.P.P.E.R. Master System Prompt**.

---

## 1. The 3-Layer State Architecture

```
+-----------------------------------------------------------------------------------+
| LAYER 1: Portable Live State (state.json)                                         |
| - Compact human-readable JSON representing active session, current task,          |
|   pending schedule recommendations, and active agent locks.                       |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 2: Persistent Structured Relational Storage (SQLite)                        |
| - 14 ACIDs-compliant tables tracking goals, projects, tasks, schedules,           |
|   epistemic memories, conversations, tool runs, audit logs, and self-healing.     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| LAYER 3: In-Process Semantic Vector Store (ChromaDB)                              |
| - High-dimensional vector embeddings for epistemic memory RAG search.             |
+-----------------------------------------------------------------------------------+
```

---

## 2. Portable Live State Schema (`state.json`)

`state.json` maintains real-time active session context:

```json
{
  "version": "1.0.0",
  "last_updated": "2026-08-12T17:40:00Z",
  "active_session": {
    "session_id": "sess_891823",
    "user_id": "default_user",
    "offline_mode": true,
    "privacy_status": "LOCAL_PRIVATE",
    "voice_status": "READY"
  },
  "current_context": {
    "active_task_id": "task_4019",
    "current_project_id": "proj_102",
    "active_agent_id": "coding_agent",
    "pending_guardian_challenge": null
  },
  "live_system_health": {
    "agents": "healthy",
    "database": "healthy",
    "tools": "healthy",
    "model_runtime": "healthy"
  }
}
```

---

## 3. Relational Schema Specification (14 Core Tables)

### 3.1 Core Relational Tables (SQLite / PostgreSQL)

```sql
-- 1. Users Table
CREATE TABLE users (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    guardian_mode VARCHAR(32) DEFAULT 'balanced' CHECK (guardian_mode IN ('passive', 'balanced', 'strong')),
    cloud_fallback_enabled BOOLEAN DEFAULT FALSE,
    voice_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Goals Table (Goal Hierarchy: Vision -> Goal -> Project)
CREATE TABLE goals (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_date DATE,
    status VARCHAR(32) DEFAULT 'active'
);

-- 3. Projects Table
CREATE TABLE projects (
    id VARCHAR(64) PRIMARY KEY,
    goal_id VARCHAR(64) REFERENCES goals(id),
    title VARCHAR(255) NOT NULL,
    health_status VARCHAR(32) DEFAULT 'healthy' CHECK (health_status IN ('healthy', 'at_risk', 'blocked')),
    health_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tasks Table
CREATE TABLE tasks (
    id VARCHAR(64) PRIMARY KEY,
    project_id VARCHAR(64) REFERENCES projects(id),
    title VARCHAR(255) NOT NULL,
    priority VARCHAR(16) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    estimated_duration_min INT DEFAULT 60,
    deadline TIMESTAMP,
    status VARCHAR(32) DEFAULT 'inbox' CHECK (status IN ('inbox', 'planned', 'active', 'blocked', 'completed', 'archived'))
);

-- 5. Schedules Table
CREATE TABLE schedules (
    id VARCHAR(64) PRIMARY KEY,
    task_id VARCHAR(64) REFERENCES tasks(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    adherence_status VARCHAR(32) DEFAULT 'scheduled'
);

-- 6. Epistemic Memories Table (v2)
CREATE TABLE memory_v2 (
    id VARCHAR(64) PRIMARY KEY,
    memory_type VARCHAR(32) NOT NULL CHECK (memory_type IN ('fact', 'observation', 'hypothesis')),
    category VARCHAR(64) NOT NULL,
    key_phrase VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    evidence_count INT DEFAULT 1,
    decay_rate FLOAT DEFAULT 0.05,
    last_reinforced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Conversations Table
CREATE TABLE conversations (
    id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    sender VARCHAR(16) NOT NULL CHECK (sender IN ('user', 'assistant')),
    agent_id VARCHAR(64),
    content TEXT NOT NULL,
    is_voice BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Experiences Table (Continual Experience Learning)
CREATE TABLE experiences (
    id VARCHAR(64) PRIMARY KEY,
    task_type VARCHAR(64) NOT NULL,
    user_prompt TEXT NOT NULL,
    cop_decision TEXT NOT NULL,
    outcome VARCHAR(32) NOT NULL CHECK (outcome IN ('success', 'user_rejected', 'failed')),
    quality_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Agent Runs Table
CREATE TABLE agent_runs (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    model_used VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'completed',
    duration_ms INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Tool Calls Table
CREATE TABLE tool_calls (
    id VARCHAR(64) PRIMARY KEY,
    agent_run_id VARCHAR(64) REFERENCES agent_runs(id),
    tool_name VARCHAR(64) NOT NULL,
    parameters JSONB NOT NULL,
    execution_result TEXT,
    is_destructive BOOLEAN DEFAULT FALSE,
    user_approved BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Evaluations Table
CREATE TABLE evaluations (
    id VARCHAR(64) PRIMARY KEY,
    agent_run_id VARCHAR(64) REFERENCES agent_runs(id),
    accuracy_score FLOAT,
    goal_alignment_score FLOAT,
    safety_passed BOOLEAN DEFAULT TRUE
);

-- 12. Agent Versions Table (Agent Registry & Hot-Swap)
CREATE TABLE agent_versions (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL,
    model_name VARCHAR(64) NOT NULL,
    evaluation_score FLOAT DEFAULT 0.0,
    status VARCHAR(32) DEFAULT 'active' CHECK (status IN ('active', 'candidate', 'disabled'))
);

-- 13. Incidents Table (Self-Healing Incident Tracker)
CREATE TABLE incidents (
    id VARCHAR(64) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    failure_reason TEXT NOT NULL,
    recovery_steps JSONB NOT NULL,
    status VARCHAR(32) DEFAULT 'recovered' CHECK (status IN ('recovered', 'escalated', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. Training Examples Table (Self-Improvement Benchmarking)
CREATE TABLE training_examples (
    id VARCHAR(64) PRIMARY KEY,
    context_snippet TEXT NOT NULL,
    decision_rationale TEXT NOT NULL,
    user_feedback VARCHAR(32),
    benchmark_quality_score FLOAT DEFAULT 0.0,
    is_included_in_training BOOLEAN DEFAULT TRUE
);
```

---

## 4. ChromaDB Vector Store Collections

1. `copper_epistemic_memory`: Embedded memory snippets for RAG search.
2. `copper_project_knowledge`: Codebase snippets, markdown docs, project context.
3. `copper_conversation_history`: Dialogue context vector index.
