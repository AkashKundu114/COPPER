# C.O.P.P.E.R. Backend Database & Schema Specification

This document details the relational database schemas, vector database structures, and Redis caching keys utilized across C.O.P.P.E.R.

---

## 1. Database Architecture Overview

C.O.P.P.E.R. utilizes a hybrid storage pattern:
1. **Relational Database (PostgreSQL / SQLite):** Stores structured entity data including epistemic user memory, agent registry metadata, system settings, and audit logs.
2. **Vector Database (ChromaDB):** Stores high-dimensional vector embeddings for memory chunks, past interactions, and document knowledge indexing.
3. **In-Memory Store (Redis):** Stores active chat sessions, rate-limit counters, WebSocket state, and self-healing transaction logs.

---

## 2. Relational Schema Definition

### 2.1 `memory_v2` Table (Epistemic Memory Engine)
Stores memory items categorised by epistemic type, confidence metrics, and evidence tracking.

```sql
CREATE TABLE memory_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(64) NOT NULL DEFAULT 'default_user',
    memory_type VARCHAR(32) NOT NULL CHECK (memory_type IN ('fact', 'observation', 'hypothesis')),
    category VARCHAR(64) NOT NULL, -- e.g., 'preference', 'habit', 'project', 'constraint'
    key_phrase VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    confidence_score FLOAT NOT NULL CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    evidence_count INT NOT NULL DEFAULT 1,
    decay_rate FLOAT NOT NULL DEFAULT 0.05, -- Daily confidence decay
    last_reinforced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_memory_user_type ON memory_v2(user_id, memory_type);
CREATE INDEX idx_memory_category ON memory_v2(category);
```

### 2.2 `agent_registry` Table (Dynamic Agent Management)
Manages the 30 specialized agents, active versions, health status, and rollback targets.

```sql
CREATE TABLE agent_registry (
    id VARCHAR(64) PRIMARY KEY, -- e.g., 'planner_agent', 'coding_agent'
    name VARCHAR(128) NOT NULL,
    tier VARCHAR(32) NOT NULL CHECK (tier IN ('core', 'execution', 'knowledge', 'interface')),
    version VARCHAR(32) NOT NULL DEFAULT '1.0.0',
    previous_version VARCHAR(32),
    status VARCHAR(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'degraded', 'disabled', 'testing')),
    description TEXT,
    system_prompt TEXT NOT NULL,
    routing_keywords TEXT[] NOT NULL, -- Array of triggers
    familiarity_score FLOAT DEFAULT 0.0,
    health_check_endpoint VARCHAR(255),
    last_health_check TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_tier ON agent_registry(tier);
CREATE INDEX idx_agent_status ON agent_registry(status);
```

### 2.3 `audit_log` Table (Security Center & Audit Trail)
Stores immutable records of consequential system actions, Data Firewall redactions, and Guardian interventions.

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL, -- e.g., 'GUARDIAN_CHALLENGE', 'FIREWALL_REDACTION', 'AGENT_SWAP', 'TOOL_EXECUTION'
    severity VARCHAR(16) NOT NULL CHECK (severity IN ('INFO', 'WARN', 'CRITICAL')),
    agent_id VARCHAR(64) REFERENCES agent_registry(id),
    guardian_level INT CHECK (guardian_level BETWEEN 0 AND 3),
    raw_prompt_hash VARCHAR(64), -- SHA256 of raw prompt for correlation
    redacted_content TEXT,
    action_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    execution_time_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_severity ON audit_log(severity);
CREATE INDEX idx_audit_created_at ON audit_log(created_at DESC);
```

### 2.4 `interactions` Table (Node History per Agent)
Tracks individual job runs and conversation history mapped to specific agent nodes.

```sql
CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(64) NOT NULL REFERENCES agent_registry(id),
    user_prompt TEXT NOT NULL,
    agent_response TEXT NOT NULL,
    tokens_used INT DEFAULT 0,
    execution_status VARCHAR(32) NOT NULL DEFAULT 'success',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_interactions_agent ON interactions(agent_id, created_at DESC);
```

---

## 3. Vector Database Schema (ChromaDB)

C.O.P.P.E.R. maintains three core collections in ChromaDB using default embeddings (`all-MiniLM-L6-v2` or `nomic-embed-text`):

1. **`copper_epistemic_memory` Collection**
   - **Document:** Text snippet of memory content.
   - **Metadata:** `{ "memory_id": "UUID", "type": "fact|observation|hypothesis", "confidence": 0.85, "category": "preference" }`
2. **`copper_agent_knowledge` Collection**
   - **Document:** Indexed documentation, codebase snippets, research artifacts.
   - **Metadata:** `{ "source": "filepath/url", "agent_tier": "knowledge", "chunk_index": 4 }`
3. **`copper_chat_history` Collection**
   - **Document:** Turn-by-turn conversation messages.
   - **Metadata:** `{ "session_id": "UUID", "sender": "user|assistant", "agent_id": "coding_agent" }`

---

## 4. Redis Key Structure & TTL Policies

| Key Pattern | Data Type | TTL | Purpose |
| :--- | :--- | :--- | :--- |
| `copper:session:{session_id}:state` | Hash | 24 Hours | Current user context, active agent lock, turn count. |
| `copper:ws:active_connections` | Set | Ephemeral | Active WebSocket connection IDs for pub/sub event broadcasting. |
| `copper:rate_limit:{user_id}` | String / Counter | 1 Minute | Slotted window rate limiter for cloud API endpoints. |
| `copper:self_healing:retry:{task_id}` | List / JSON | 1 Hour | Stack trace, attempt counts, and tool retry histories. |
| `copper:agent:health_cache` | Hash | 30 Seconds | Cached health status of all 30 sub-agents. |
