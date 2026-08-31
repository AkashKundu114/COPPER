# C.O.P.P.E.R. Implementation & Developer Guide

---

## 1. Repository Layout & Module Architecture

```
C.O.P.P.E.R/
├── backend/
│   ├── app/
│   │   ├── ai/                      # AI Core & Agent Subsystems
│   │   │   ├── agents/              # 30 Sub-agent definitions & implementations
│   │   │   ├── llm/                 # Ollama & OpenAI provider connectors
│   │   │   ├── memory/              # Epistemic learner & ChromaDB RAG logic
│   │   │   └── orchestration/       # Pipeline: Route -> Animate -> Respond -> Remember
│   │   ├── api/                     # REST & WebSocket Route handlers
│   │   │   └── routes/              # chat.py, guardian.py, agents.py, audit.py
│   │   ├── core/                    # Core System Services
│   │   │   ├── config.py            # Environment configurations & settings
│   │   │   ├── data_firewall.py     # PII Scanner & Anonymizer engine
│   │   │   ├── guardian.py          # Level 0-3 Guardian evaluation engine
│   │   │   ├── logger.py            # Structured JSON logger
│   │   │   └── self_healing.py      # Retries, tool fallback & execution recovery
│   │   ├── data/                    # Static registries & database seed files
│   │   ├── database/                # Relational Models & Alembic Migrations
│   │   │   └── models/              # memory_v2.py, agent_registry.py, audit_log.py
│   │   ├── services/                # Business logic services
│   │   └── main.py                  # FastAPI application entrypoint
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── brain/               # NeuralBrain.tsx (SVG radial ganglia map)
│   │   │   ├── chat/                # ChatDock.tsx, GuardianChallengeModal.tsx, SpeakingBar.tsx
│   │   │   ├── profile/             # SideDrawer.tsx (Memory inspector & Job logs)
│   │   │   └── widgets/             # ClockWidget, WeatherWidget, CalendarWidget, NetworkWidget
│   │   ├── lib/                     # WebSocket hooks, layout engines, API client
│   │   ├── pages/                   # AgentRegistry.tsx, SecurityCenter.tsx, Insights.tsx
│   │   └── App.tsx                  # Core App Shell & router setup
│   ├── tailwind.config.js           # Molten Copper theme configuration
│   └── package.json
└── docs/                            # Project Documentation Suite
```

---

## 2. Adding & Customizing Agents

To introduce a new agent or modify existing agent behaviors:

### Step 1: Define Agent Metadata in Database Model
Add your agent parameters into `backend/app/data/agents.py` or insert via DB migration:

```python
NEW_AGENT = {
    "id": "database_architect_agent",
    "name": "Database Architect",
    "tier": "execution",
    "version": "1.0.0",
    "description": "Optimizes SQL queries, manages migrations, and designs schemas.",
    "system_prompt": "You are a specialized Database Architect agent...",
    "routing_keywords": ["sql", "database", "schema", "postgres", "migration", "query"],
    "color": "#F59E0B",
}
```

### Step 2: Implement Agent Logic Class
Inherit from `BaseAgent` in `backend/app/ai/agents/database_architect.py`:

```python
from app.ai.agents.base import BaseAgent


class DatabaseArchitectAgent(BaseAgent):
    async def execute(self, prompt: str, context: dict) -> str:
        # Tool execution, query analysis, schema generation
        return await self.llm_service.generate(...)
```

---

## 3. Registering Epistemic Fact Parsers

In `backend/app/ai/memory/learner.py`, add custom regex patterns or heuristics to automatically capture user habits and preferences:

```python
FACT_PATTERNS = [
    (r"I prefer (?P<fact>.*)", "preference", 0.75),
    (r"I am working on (?P<fact>.*)", "project", 0.85),
    (r"My schedule is (?P<fact>.*)", "habit", 0.80),
]
```

---

## 4. Running Database Migrations

C.O.P.P.E.R. uses Alembic for database schema management:

```bash
cd backend

# Generate a new migration script
alembic revision --autogenerate -m "Add new epistemic memory columns"

# Apply migrations to local database
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```
