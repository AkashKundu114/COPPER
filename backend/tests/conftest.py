import os
import sys
from pathlib import Path

# Ensure headless environment variables
if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"
os.environ.setdefault("MPLBACKEND", "Agg")

# Add backend directory to sys.path so 'app' is importable
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
root_dir = backend_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from app.database.postgres import init_db
    init_db()
except Exception:
    pass
