"""
C.O.P.P.E.R. Default Data & Memory Seed Script
Seeds initial agent version registrations, core epistemic memories, and default preferences.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.models.agent_registry import AgentStatus, AgentVersion
from app.database.models.audit_log import AuditLogEntry
from app.database.postgres import SessionLocal, init_db


def seed_default_agents(db):
    agents = [
        (
            "chat",
            "Chat Agent",
            "General conversational companion and assistance",
            "1.0.0",
            "qwen2.5:14b",
        ),
        (
            "coding",
            "AXIS (Coding Agent)",
            "Software engineering, debugging, and code generation",
            "1.0.0",
            "qwen2.5-coder:14b",
        ),
        (
            "automation",
            "Automation Agent",
            "Desktop, file system, process, and window management",
            "1.0.0",
            "mistral-nemo:12b",
        ),
        (
            "reminder",
            "Reminder Agent",
            "Time management, scheduling, alarms, and task tracking",
            "1.0.0",
            "qwen2.5:1.5b",
        ),
        (
            "research",
            "Research Agent",
            "Deep inquiry, fact-checking, and literature lookup",
            "1.0.0",
            "deepseek-r1:14b",
        ),
        (
            "vision",
            "Vision Agent",
            "Visual reasoning, OCR, screen inspection, and diagram parsing",
            "1.0.0",
            "qwen2.5-vl:3b",
        ),
        (
            "planner",
            "Planner Agent",
            "Project roadmap decomposition and milestone planning",
            "1.0.0",
            "phi4:14b",
        ),
    ]

    for agent_id, name, desc, ver, model in agents:
        existing = db.query(AgentVersion).filter(AgentVersion.agent_id == agent_id).first()
        if not existing:
            av = AgentVersion(
                agent_id=agent_id,
                display_name=name,
                model_name=model,
                version=ver,
                is_current=True,
                status=AgentStatus.ACTIVE,
                activated_at=datetime.now(UTC),
            )
            db.add(av)
            print(f"[+] Registered default agent: {name} (v{ver})")


def seed_database():
    print("=" * 66)
    print("           C.O.P.P.E.R. DATABASE SEED DATA INGESTION")
    print("=" * 66)
    init_db()
    db = SessionLocal()
    try:
        seed_default_agents(db)
        db.add(
            AuditLogEntry(
                category="system_startup",
                actor="system",
                summary="C.O.P.P.E.R. Database Seed Data loaded.",
            )
        )
        db.commit()
        print("[+] Seed process completed.")
        print("=" * 66)
    except Exception as e:
        db.rollback()
        print(f"[-] Seed error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
