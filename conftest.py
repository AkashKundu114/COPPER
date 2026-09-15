import os
import sys
from pathlib import Path

# Ensure headless environment variables are set before any test collection
if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":99"
os.environ.setdefault("MPLBACKEND", "Agg")

backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
