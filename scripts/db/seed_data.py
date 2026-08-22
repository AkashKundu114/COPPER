"""
C.O.P.P.E.R. Default Data & Memory Seed Script
Seeds initial agent version registrations, core epistemic memories, and default preferences.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.postgres import SessionLocal, init_db
from app.database.models.agent_registry import AgentVersion, AgentStatus
from app.database.models.audit_log import AuditLogEntry


def seed_default_agents(db):
    agents = [
        ("chat", "Chat Agent", "General conversational companion and assistance", "1.0.0"),
        ("coding", "AXIS (Coding Agent)", "Software engineering, debugging, and code generation", "1.0.0"),
        ("automation", "Automation Agent", "Desktop, file system, process, and window management", "1.0.0"),
        ("reminder", "Reminder Agent", "Time management, scheduling, alarms, and task tracking", "1.0.0"),
        ("research", "Research Agent", "Deep inquiry, fact-checking, and literature lookup", "1.0.0"),
        ("vision", "Vision Agent", "Visual reasoning, OCR, screen inspection, and diagram parsing", "1.0.0"),
        ("planner", "Planner Agent", "Project roadmap decomposition and milestone planning", "1.0.0"),
    ]

    for agent_id, name, desc, ver in agents:
        existing = db.query(AgentVersion).filter(AgentVersion.agent_id == agent_id).first()
        if not existing:
            av = AgentVersion(
                agent_id=agent_id,
                version=ver,
                is_current=True,
                status=AgentStatus.ACTIVE,
                activated_at=datetime.now(timezone.utc),
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
        db.add(AuditLogEntry(
            category="system_startup",
            actor="system",
            summary="C.O.P.P.E.R. Database Seed Data loaded."
        ))
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
