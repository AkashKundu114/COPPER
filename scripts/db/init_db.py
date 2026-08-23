"""
C.O.P.P.E.R. Database Initialization Script
Ensures all SQL schemas, tables, and constraints are created in PostgreSQL / SQLite.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database.postgres import engine, init_db


def run_init():
    print("=" * 66)
    print("           C.O.P.P.E.R. DATABASE SCHEMA INITIALIZATION")
    print("=" * 66)
    print(f"[*] Target Database: {engine.url}")
    try:
        init_db()
        print("[+] All database tables initialized successfully.")
        print("=" * 66)
        return True
    except Exception as e:
        print(f"[-] Database initialization failed: {e}")
        print("=" * 66)
        return False


if __name__ == "__main__":
    run_init()
