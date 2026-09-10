import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.data_firewall import redact
from app.core.logger import logger

SANDBOX_DIR = Path(__file__).parent.parent.parent / "sandbox"
PYODIDE_RUNNER_SCRIPT = Path(__file__).parent / "pyodide_runner.cjs"
BACKEND_DIR = Path(__file__).parent.parent.parent

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


class BaseSandboxRunner:
    """Abstract base runner for sandbox execution environments."""

    name: str = "base"

    def is_available(self) -> bool:
        raise NotImplementedError

    def run(self, code: str, timeout: int, memory_limit_mb: int, network_enabled: bool) -> dict:
        raise NotImplementedError


class PyodideWasmRunner(BaseSandboxRunner):
    """Executes Python code inside an isolated WebAssembly (Pyodide) VM.
    
    Provides memory isolation via V8 engine memory limits, zero host filesystem access
    via Emscripten in-memory virtual filesystem (MEMFS), and blocks network access primitives.
    """

    name: str = "pyodide"

    def __init__(self, node_executable: str = "node"):
        self.node_executable = node_executable

    def is_available(self) -> bool:
        if not shutil.which(self.node_executable):
            return False
        if not PYODIDE_RUNNER_SCRIPT.exists():
            return False
        # Check node_modules for pyodide
        pyodide_dir = BACKEND_DIR / "node_modules" / "pyodide"
        return pyodide_dir.exists()

    def run(self, code: str, timeout: int, memory_limit_mb: int, network_enabled: bool) -> dict:
        env = dict(os.environ)
        # Ensure node can locate backend node_modules
        node_modules = str(BACKEND_DIR / "node_modules")
        existing_node_path = env.get("NODE_PATH", "")
        env["NODE_PATH"] = f"{node_modules}{os.pathsep}{existing_node_path}" if existing_node_path else node_modules

        # Node V8 memory limit flag: --max-old-space-size
        node_cmd = [
            self.node_executable,
            f"--max-old-space-size={memory_limit_mb}",
            str(PYODIDE_RUNNER_SCRIPT),
        ]

        payload = {
            "code": code,
            "allow_network": network_enabled,
            "memory_limit_mb": memory_limit_mb,
        }

        try:
            proc = subprocess.Popen(
                node_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(BACKEND_DIR),
                env=env,
            )
            stdout, stderr = proc.communicate(input=json.dumps(payload), timeout=timeout)
            if proc.returncode != 0 and not stdout:
                logger.warning(f"Pyodide runner process exited with code {proc.returncode}: {stderr}")
                return {
                    "stdout": "",
                    "stderr": stderr or f"Process exited with code {proc.returncode}",
                    "exit_code": proc.returncode,
                    "error": "ProcessFailure",
                }

            # Parse JSON output from pyodide_runner.cjs
            try:
                result = json.loads(stdout)
                return {
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "exit_code": result.get("exit_code", 0),
                    "error": result.get("error"),
                }
            except json.JSONDecodeError:
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": proc.returncode,
                    "error": "MalformedRunnerOutput" if proc.returncode != 0 else None,
                }
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.communicate(timeout=2)
            except Exception:
                pass
            logger.warning(f"Pyodide execution timed out after {timeout} seconds.")
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "exit_code": 124,
                "error": "TimeoutExpired",
            }
        except Exception as e:
            logger.error(f"Pyodide runner error: {e}")
            return {"stdout": "", "stderr": str(e), "exit_code": 1, "error": str(e)}


class DockerContainerRunner(BaseSandboxRunner):
    """Executes Python code inside an isolated Docker container.
    
    Provides strict Linux container isolation:
    - Resource limits: CPU limit (--cpus), memory limit (-m), PIDs limit (--pids-limit)
    - Network isolation: disabled (--network none) by default
    - Filesystem isolation: read-only root (--read-only) with ephemeral tmpfs (/tmp)
    - Capabilities: dropped all (--cap-drop=ALL)
    """

    name: str = "docker"

    def __init__(self, docker_executable: str = "docker", image: Optional[str] = None):
        self.docker_executable = docker_executable
        self.image = image or getattr(settings, "SANDBOX_DOCKER_IMAGE", "python:3.12-slim")

    def is_available(self) -> bool:
        if not shutil.which(self.docker_executable):
            return False
        try:
            res = subprocess.run(
                [self.docker_executable, "info"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def run(self, code: str, timeout: int, memory_limit_mb: int, network_enabled: bool) -> dict:
        cpu_limit = str(getattr(settings, "SANDBOX_CPU_LIMIT", 1.0))
        net_flag = "bridge" if network_enabled else "none"

        docker_cmd = [
            self.docker_executable,
            "run",
            "--rm",
            "-i",
            f"--network={net_flag}",
            f"--cpus={cpu_limit}",
            f"-m={memory_limit_mb}m",
            "--memory-swap",
            f"{memory_limit_mb}m",
            "--pids-limit=64",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--cap-drop=ALL",
            self.image,
            "python",
            "-",
        ]

        try:
            proc = subprocess.Popen(
                docker_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = proc.communicate(input=code, timeout=timeout)
            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": proc.returncode,
                "error": None if proc.returncode == 0 else "ExecutionError",
            }
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.communicate(timeout=2)
            except Exception:
                pass
            logger.warning(f"Docker sandbox execution timed out after {timeout} seconds.")
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "exit_code": 124,
                "error": "TimeoutExpired",
            }
        except Exception as e:
            logger.error(f"Docker sandbox runner error: {e}")
            return {"stdout": "", "stderr": str(e), "exit_code": 1, "error": str(e)}


class SubprocessSanitizedRunner(BaseSandboxRunner):
    """Fallback runner with environment sanitization and process timeout.
    Used when neither Docker nor Node/Pyodide is available in the host environment.
    """

    name: str = "subprocess_sanitized"

    def __init__(self):
        os.makedirs(SANDBOX_DIR, exist_ok=True)

    def is_available(self) -> bool:
        return True

    def _get_sanitized_env(self) -> dict[str, str]:
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

    def run(self, code: str, timeout: int, memory_limit_mb: int, network_enabled: bool) -> dict:
        script_id = uuid.uuid4().hex
        script_path = SANDBOX_DIR / f"temp_exec_{script_id}.py"
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(SANDBOX_DIR),
                stdin=subprocess.DEVNULL,
                env=self._get_sanitized_env(),
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "error": None if result.returncode == 0 else "ExecutionError",
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "exit_code": 124,
                "error": "TimeoutExpired",
            }
        except Exception as e:
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


class ForgeSandbox:
    """Unified isolated sandbox execution engine with resource limits and audit logging."""

    def __init__(self):
        os.makedirs(SANDBOX_DIR, exist_ok=True)
        self.pyodide_runner = PyodideWasmRunner()
        self.docker_runner = DockerContainerRunner()
        self.subprocess_runner = SubprocessSanitizedRunner()
        self._audit_history: deque[Dict[str, Any]] = deque(maxlen=100)

    def _select_runner(self, backend: Optional[str] = None) -> BaseSandboxRunner:
        selected_backend = (backend or getattr(settings, "SANDBOX_BACKEND", "auto")).lower()
        if selected_backend == "docker":
            if self.docker_runner.is_available():
                return self.docker_runner
            logger.warning("Docker backend requested but Docker daemon unavailable; falling back to Pyodide WASM.")
            if self.pyodide_runner.is_available():
                return self.pyodide_runner
            return self.subprocess_runner

        if selected_backend == "pyodide":
            if self.pyodide_runner.is_available():
                return self.pyodide_runner
            logger.warning("Pyodide WASM runner unavailable; falling back to sanitized subprocess runner.")
            return self.subprocess_runner

        # Auto detection: prefer Docker if running, otherwise Pyodide WASM
        if self.docker_runner.is_available():
            return self.docker_runner
        if self.pyodide_runner.is_available():
            return self.pyodide_runner
        return self.subprocess_runner

    def _log_audit_entry(
        self,
        code: str,
        result: dict,
        backend_used: str,
        duration_ms: float,
        session_id: Optional[str] = None,
        is_blocked: bool = False,
    ) -> None:
        """Persists audit record of execution to PostgreSQL and memory history."""
        category = "guardian_safety_block" if is_blocked else "sandbox_execution"
        summary = (
            f"Sandbox blocked dangerous code pattern"
            if is_blocked
            else f"Sandbox executed via {backend_used} (exit {result.get('exit_code')}) in {duration_ms:.1f}ms"
        )
        metadata = {
            "backend": backend_used,
            "exit_code": result.get("exit_code"),
            "duration_ms": duration_ms,
            "error": result.get("error"),
            "memory_limit_mb": getattr(settings, "SANDBOX_MEMORY_LIMIT_MB", 256),
            "network_enabled": getattr(settings, "SANDBOX_NETWORK_ENABLED", False),
            "cpu_limit": getattr(settings, "SANDBOX_CPU_LIMIT", 1.0),
        }

        # Keep in-memory trail
        audit_record = {
            "id": uuid.uuid4().hex,
            "session_id": session_id,
            "category": category,
            "actor": "forge_sandbox",
            "summary": summary,
            "metadata": metadata,
            "timestamp": time.time(),
        }
        self._audit_history.append(audit_record)

        # Persist to database if available
        try:
            from app.database.models.audit_log import AuditLogEntry
            from app.database.postgres import SessionLocal

            db = SessionLocal()
            try:
                entry = AuditLogEntry(
                    session_id=session_id,
                    category=category,
                    actor="forge_sandbox",
                    summary=redact(summary[:300]),
                    detail=redact(f"Code:\n{code[:500]}\n\nStderr:\n{result.get('stderr', '')[:500]}"),
                    scope="local",
                    extra_metadata=metadata,
                )
                db.add(entry)
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"Audit log DB persistence skipped/failed: {e}")

    def get_recent_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent in-memory audit execution logs."""
        return list(self._audit_history)[-limit:]

    def run_python_code(
        self,
        code: str,
        timeout: Optional[int] = None,
        backend: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """Executes Python code with sandbox isolation, resource limits, and audit logging."""
        effective_timeout = timeout or getattr(settings, "SANDBOX_TIMEOUT_SECONDS", 15)
        memory_limit_mb = getattr(settings, "SANDBOX_MEMORY_LIMIT_MB", 256)
        network_enabled = getattr(settings, "SANDBOX_NETWORK_ENABLED", False)

        start_time = time.perf_counter()

        # Static safety filter layer
        code_lower = code.lower()
        for pattern in FORBIDDEN_CODE_PATTERNS:
            if pattern in code_lower:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.warning(f"Forge Sandbox blocked dangerous code pattern: {pattern}")
                blocked_res = {
                    "stdout": "",
                    "stderr": f"Execution blocked by Forge Sandbox safety filter: forbidden pattern '{pattern}'.",
                    "exit_code": 1,
                    "error": "SecurityViolation",
                    "backend": "safety_filter",
                    "duration_ms": duration_ms,
                }
                self._log_audit_entry(
                    code,
                    blocked_res,
                    backend_used="safety_filter",
                    duration_ms=duration_ms,
                    session_id=session_id,
                    is_blocked=True,
                )
                return blocked_res

        runner = self._select_runner(backend)
        logger.info(f"Forge Sandbox running with runner: {runner.name}")

        result = runner.run(
            code=code,
            timeout=effective_timeout,
            memory_limit_mb=memory_limit_mb,
            network_enabled=network_enabled,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000
        result["backend"] = runner.name
        result["duration_ms"] = duration_ms

        # Audit logging of all sandbox executions
        self._log_audit_entry(
            code=code,
            result=result,
            backend_used=runner.name,
            duration_ms=duration_ms,
            session_id=session_id,
            is_blocked=False,
        )

        return result

    def execute_python(
        self,
        code: str,
        timeout_seconds: Optional[int] = None,
        backend: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """Legacy helper matching execute_python interface with status flag."""
        res = self.run_python_code(
            code,
            timeout=timeout_seconds,
            backend=backend,
            session_id=session_id,
        )
        status = "success" if res.get("exit_code") == 0 else "error"
        return {"status": status, **res}


forge_sandbox = ForgeSandbox()
