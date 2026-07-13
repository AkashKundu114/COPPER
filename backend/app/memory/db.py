"""
db.py
======
Thin SQLite wrapper. Three tables:

  user_profile   — facts COPPER has learned about the user, with a
                    confidence score that grows when a fact is reinforced
                    by repeated mentions.
  agent_memory   — per-agent stats: how many times it's been invoked, when
                    it was last active, and its familiarity score (drives
                    the node's glow intensity in the brain visualization).
  interactions   — the append-only job log. Each row is one request handled
                    by one agent — this is "each instance and job stored
                    in each node" from the brief; the brain UI reads this
                    per-node when you click an agent.

Uses stdlib sqlite3 only — no ORM — since the schema is small and stable.
"""

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from app.core.config import settings

_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_profile (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    confidence  REAL NOT NULL DEFAULT 0.4,
    observed_n  INTEGER NOT NULL DEFAULT 1,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_memory (
    agent_id          TEXT PRIMARY KEY,
    times_invoked     INTEGER NOT NULL DEFAULT 0,
    familiarity_score REAL NOT NULL DEFAULT 0,
    last_active       TEXT,
    notes             TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS interactions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id      TEXT NOT NULL,
    user_message  TEXT NOT NULL,
    response      TEXT NOT NULL,
    timestamp     TEXT NOT NULL,
    duration_ms   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_interactions_agent ON interactions(agent_id);
"""


def get_conn() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        Path(settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        conn.commit()
        _local.conn = conn
    return _local.conn


@contextmanager
def cursor():
    conn = get_conn()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ── user_profile ──────────────────────────────────────────────────────────
def upsert_fact(key: str, value: str, confidence_bump: float = 0.15) -> None:
    with cursor() as cur:
        cur.execute("SELECT confidence, observed_n FROM user_profile WHERE key=?", (key,))
        row = cur.fetchone()
        if row:
            new_conf = min(0.97, row["confidence"] + confidence_bump)
            cur.execute(
                "UPDATE user_profile SET value=?, confidence=?, observed_n=observed_n+1, updated_at=? WHERE key=?",
                (value, new_conf, now_iso(), key),
            )
        else:
            cur.execute(
                "INSERT INTO user_profile (key, value, confidence, observed_n, updated_at) VALUES (?,?,?,1,?)",
                (key, value, 0.4, now_iso()),
            )


def get_profile() -> list[dict]:
    with cursor() as cur:
        cur.execute("SELECT key, value, confidence, observed_n, updated_at FROM user_profile ORDER BY confidence DESC")
        return [dict(r) for r in cur.fetchall()]


def reset_profile() -> None:
    with cursor() as cur:
        cur.execute("DELETE FROM user_profile")
        cur.execute("DELETE FROM agent_memory")
        cur.execute("DELETE FROM interactions")


# ── agent_memory ──────────────────────────────────────────────────────────
def bump_agent(agent_id: str) -> dict:
    with cursor() as cur:
        cur.execute("SELECT * FROM agent_memory WHERE agent_id=?", (agent_id,))
        row = cur.fetchone()
        if row:
            new_score = row["familiarity_score"] + 1
            cur.execute(
                "UPDATE agent_memory SET times_invoked=times_invoked+1, familiarity_score=?, last_active=? WHERE agent_id=?",
                (new_score, now_iso(), agent_id),
            )
        else:
            new_score = 1
            cur.execute(
                "INSERT INTO agent_memory (agent_id, times_invoked, familiarity_score, last_active, notes) VALUES (?,1,1,?,'[]')",
                (agent_id, now_iso()),
            )
        cur.execute("SELECT * FROM agent_memory WHERE agent_id=?", (agent_id,))
        return dict(cur.fetchone())


def get_agent_memory(agent_id: str) -> dict | None:
    with cursor() as cur:
        cur.execute("SELECT * FROM agent_memory WHERE agent_id=?", (agent_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_agent_memory() -> dict[str, dict]:
    with cursor() as cur:
        cur.execute("SELECT * FROM agent_memory")
        return {r["agent_id"]: dict(r) for r in cur.fetchall()}


def add_agent_note(agent_id: str, note: str, max_notes: int = 5) -> None:
    mem = get_agent_memory(agent_id)
    notes = json.loads(mem["notes"]) if mem else []
    notes.append(note)
    notes = notes[-max_notes:]
    with cursor() as cur:
        cur.execute("UPDATE agent_memory SET notes=? WHERE agent_id=?", (json.dumps(notes), agent_id))


# ── interactions ──────────────────────────────────────────────────────────
def log_interaction(agent_id: str, user_message: str, response: str, duration_ms: int) -> None:
    with cursor() as cur:
        cur.execute(
            "INSERT INTO interactions (agent_id, user_message, response, timestamp, duration_ms) VALUES (?,?,?,?,?)",
            (agent_id, user_message, response, now_iso(), duration_ms),
        )


def get_agent_history(agent_id: str, limit: int = 20) -> list[dict]:
    with cursor() as cur:
        cur.execute(
            "SELECT * FROM interactions WHERE agent_id=? ORDER BY id DESC LIMIT ?",
            (agent_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def total_interactions() -> int:
    with cursor() as cur:
        cur.execute("SELECT COUNT(*) as n FROM interactions")
        return cur.fetchone()["n"]
