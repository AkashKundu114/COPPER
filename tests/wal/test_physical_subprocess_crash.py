"""
Pytest integration for physical subprocess crash testing with TaskWAL:
Ensures physical process termination (taskkill/SIGKILL) is recoverable.
"""

import sys
from pathlib import Path
import pytest

# Add scripts to path to import test function
scripts_dir = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))
from test_real_subprocess_crash import run_physical_subprocess_crash_recovery


def test_taskwal_physical_subprocess_crash_recovery():
    success = run_physical_subprocess_crash_recovery()
    assert success is True
