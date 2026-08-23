import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from app.database.postgres import init_db

    init_db()
except Exception:
    pass


@pytest.fixture(scope="session")
def db_session():
    """Mock or session fixture for database operations."""
    return


@pytest.fixture
def sample_user_messages():
    return [
        "Write a python quicksort function",
        "Open Chrome and go to reddit.com",
        "Remind me to buy groceries at 6pm",
        "Explain the theory of special relativity",
        "Inspect this screenshot and read the button text",
        "Create a roadmap for the quarterly release",
        "How are you doing today?",
    ]
