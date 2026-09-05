import os
import subprocess
import sys
import uuid
from pathlib import Path

from app.core.logger import logger

SANDBOX_DIR = Path(__file__).parent.parent.parent / "sandbox"

FORBIDDEN_CODE_PATTERNS = [
    ":(){ :|:& };:",
    "shutil.rmtree('/')",
    'shutil.rmtree("/")',
    'shutil.rmtree("C:\\\\")',
    "shutil.rmtree('C:\\\\')",
    "os.system('rm -rf /')",
    'os.system("rm -rf /")',
    "format c:",
    "del /f /s /q c:\\",
]


class ForgeSandbox:
    def __init__(self):
        os.makedirs(SANDBOX_DIR, exist_ok=True)

    def _get_sanitized_env(self) -> dict[str, str]:
        """Provides a sanitized execution environment stripped of sensitive API keys and secrets."""
        safe_keys = {
            "PATH",
            "SYSTEMROOT",
            "SYSTEMDRIVE",
            "WINDIR",
            "COMSPEC",
            "PATHEXT",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "HOMEDRIVE",
            "HOMEPATH",
            "LANG",
            "LC_ALL",
            "PYTHONPATH",
            "PYTHONHOME",
        }
        sanitized = {k: v for k, v in os.environ.items() if k.upper() in safe_keys}
        sanitized["PYTHONDONTWRITEBYTECODE"] = "1"
        sanitized["PYTHONUNBUFFERED"] = "1"
        return sanitized

    def run_python_code(self, code: str, timeout: int = 10) -> dict:
        code_lower = code.lower()
        for pattern in FORBIDDEN_CODE_PATTERNS:
            if pattern in code_lower:
                logger.warning(f"Forge Sandbox blocked dangerous code pattern: {pattern}")
                return {
                    "stdout": "",
                    "stderr": f"Execution blocked by Forge Sandbox safety filter: forbidden pattern '{pattern}'.",
                    "exit_code": 1,
                    "error": "SecurityViolation",
                }

        script_id = uuid.uuid4().hex
        script_path = SANDBOX_DIR / f"temp_exec_{script_id}.py"
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
                stdin=subprocess.DEVNULL,
                env=self._get_sanitized_env(),
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
            legacy_path = SANDBOX_DIR / "temp_exec.py"
            if legacy_path.exists():
                try:
                    os.remove(legacy_path)
                except OSError:
                    pass

    def execute_python(self, code: str, timeout_seconds: int = 10) -> dict:
        res = self.run_python_code(code, timeout=timeout_seconds)
        status = "success" if res.get("exit_code") == 0 else "error"
        return {"status": status, **res}


forge_sandbox = ForgeSandbox()
