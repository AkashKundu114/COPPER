from unittest.mock import MagicMock, patch
from app.core.forge_sandbox import (
    SANDBOX_DIR,
    DockerContainerRunner,
    PyodideWasmRunner,
    forge_sandbox,
)


def test_sandbox_hello_world():
    res = forge_sandbox.run_python_code("print('Hello from Forge')")
    assert res["exit_code"] == 0
    assert "Hello from Forge" in res["stdout"]


def test_sandbox_math_computation():
    res = forge_sandbox.run_python_code("print(sum([x**2 for x in range(10)]))")
    assert res["exit_code"] == 0
    assert "285" in res["stdout"].strip()


def test_sandbox_runtime_division_error():
    res = forge_sandbox.run_python_code("1 / 0")
    assert res["exit_code"] != 0
    assert "ZeroDivisionError" in res["stderr"]


def test_sandbox_syntax_error():
    res = forge_sandbox.run_python_code("def broken_syntax(")
    assert res["exit_code"] != 0
    assert "SyntaxError" in res["stderr"]


def test_sandbox_timeout_enforcement():
    res = forge_sandbox.run_python_code("import time\ntime.sleep(2)", timeout=1)
    assert res["exit_code"] == 124
    assert "timed out" in res["stderr"].lower()
    assert res["error"] == "TimeoutExpired"


def test_sandbox_cleanup():
    temp_script = SANDBOX_DIR / "temp_exec.py"
    forge_sandbox.run_python_code("print('Clean up check')")
    assert not temp_script.exists()


def test_sandbox_environment_sanitization(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://copper:supersecret@localhost:5432/db")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-key-12345")
    res = forge_sandbox.run_python_code(
        "import os\nprint('DB:', os.environ.get('DATABASE_URL'))\nprint('KEY:', os.environ.get('OPENAI_API_KEY'))\n"
    )
    assert res["exit_code"] == 0
    assert "DB: None" in res["stdout"]
    assert "KEY: None" in res["stdout"]


def test_sandbox_blocks_forbidden_destructive_patterns():
    res = forge_sandbox.run_python_code("import shutil\nshutil.rmtree('/')")
    assert res["exit_code"] == 1
    assert "Execution blocked by Forge Sandbox safety filter" in res["stderr"]
    assert res["error"] == "SecurityViolation"


def test_sandbox_pyodide_wasm_execution():
    """Verify Pyodide WebAssembly runner executes and produces structured output."""
    runner = PyodideWasmRunner()
    if not runner.is_available():
        return  # Skipped if environment lacks node/pyodide
    res = forge_sandbox.run_python_code("print('Pyodide WASM active!')", backend="pyodide")
    assert res["exit_code"] == 0
    assert "Pyodide WASM active!" in res["stdout"]
    assert res["backend"] == "pyodide"
    assert res["duration_ms"] > 0


def test_sandbox_filesystem_isolation():
    """Verify code running in Pyodide WASM sandbox is isolated from host filesystem."""
    runner = PyodideWasmRunner()
    if not runner.is_available():
        return
    code = (
        "import os\n"
        "cwd = os.getcwd()\n"
        "files = os.listdir('.')\n"
        "print(f'CWD:{cwd}')\n"
        "print(f'FILES:{files}')\n"
    )
    res = forge_sandbox.run_python_code(code, backend="pyodide")
    assert res["exit_code"] == 0
    assert "/home/pyodide" in res["stdout"]
    # Ensure host files (like pyproject.toml, backend) are NOT in the virtual cwd
    assert "pyproject.toml" not in res["stdout"]


def test_sandbox_network_isolation():
    """Verify network access fails inside sandbox."""
    runner = PyodideWasmRunner()
    if not runner.is_available():
        return
    code = (
        "import urllib.request\n"
        "urllib.request.urlopen('http://127.0.0.1:9999', timeout=1)\n"
    )
    res = forge_sandbox.run_python_code(code, backend="pyodide")
    assert res["exit_code"] != 0
    assert "URLError" in res["stderr"] or "Error" in res["stderr"]


def test_sandbox_audit_logging():
    """Verify that all sandbox executions are captured in audit logs with metadata."""
    res = forge_sandbox.run_python_code("print('audit_test_marker')", session_id="test-session-123")
    assert res["exit_code"] == 0

    recent = forge_sandbox.get_recent_executions(limit=10)
    assert len(recent) > 0

    latest = recent[-1]
    assert latest["category"] == "sandbox_execution"
    assert latest["actor"] == "forge_sandbox"
    assert latest["session_id"] == "test-session-123"
    assert "backend" in latest["metadata"]
    assert "exit_code" in latest["metadata"]
    assert latest["metadata"]["exit_code"] == 0
    assert latest["metadata"]["memory_limit_mb"] > 0


def test_sandbox_audit_blocked_pattern_logging():
    """Verify blocked dangerous patterns trigger safety audit log entries."""
    res = forge_sandbox.run_python_code(":(){ :|:& };:", session_id="blocked-session-99")
    assert res["exit_code"] == 1
    assert res["error"] == "SecurityViolation"

    recent = forge_sandbox.get_recent_executions(limit=5)
    latest = recent[-1]
    assert latest["category"] == "guardian_safety_block"
    assert latest["session_id"] == "blocked-session-99"


def test_sandbox_docker_runner_isolation_flags():
    """Verify DockerContainerRunner invokes docker with strict isolation flags."""
    runner = DockerContainerRunner()

    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.communicate.return_value = ("docker stdout", "")
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        res = runner.run(
            code="print('in docker')",
            timeout=10,
            memory_limit_mb=256,
            network_enabled=False,
        )

        assert res["exit_code"] == 0
        assert res["stdout"] == "docker stdout"

        called_cmd = mock_popen.call_args[0][0]
        # Verify strict security flags
        assert "--network=none" in called_cmd
        assert "--read-only" in called_cmd
        assert "--cap-drop=ALL" in called_cmd
        assert "-m=256m" in called_cmd
        assert "--pids-limit=64" in called_cmd
        assert any("--tmpfs" in arg for arg in called_cmd)


def test_sandbox_execute_python_wrapper():
    """Verify execute_python helper returns expected status and dictionary."""
    res_success = forge_sandbox.execute_python("print('success')")
    assert res_success["status"] == "success"
    assert res_success["exit_code"] == 0

    res_fail = forge_sandbox.execute_python("1 / 0")
    assert res_fail["status"] == "error"
    assert res_fail["exit_code"] != 0
