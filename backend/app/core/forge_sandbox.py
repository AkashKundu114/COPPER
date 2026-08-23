import os
import subprocess
import sys
from pathlib import Path

from app.core.logger import logger

SANDBOX_DIR = Path(__file__).parent.parent.parent / "sandbox"

class ForgeSandbox:
    def __init__(self):
        os.makedirs(SANDBOX_DIR, exist_ok=True)

    def run_python_code(self, code: str, timeout: int = 10) -> dict:
        script_path = SANDBOX_DIR / "temp_exec.py"
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            logger.info(f"Forge Sandbox running {script_path}")
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(SANDBOX_DIR),
            )
            return {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode, "error": None}
        except subprocess.TimeoutExpired:
            logger.warning("Forge Sandbox execution timed out.")
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "exit_code": 124,
                "error": "TimeoutExpired",
            }
        except Exception as e:
            logger.error(f"Forge Sandbox error: {e}")
            return {"stdout": "", "stderr": str(e), "exit_code": 1, "error": str(e)}
        finally:
            if script_path.exists():
                try:
                    os.remove(script_path)
                except OSError:
                    pass

forge_sandbox = ForgeSandbox()
