from app.core.forge_sandbox import SANDBOX_DIR, forge_sandbox


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
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://copper:supersecret@localhost:5432/db"
    )
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-key-12345")
    res = forge_sandbox.run_python_code(
        "import os\n"
        "print('DB:', os.environ.get('DATABASE_URL'))\n"
        "print('KEY:', os.environ.get('OPENAI_API_KEY'))\n"
    )
    assert res["exit_code"] == 0
    assert "DB: None" in res["stdout"]
    assert "KEY: None" in res["stdout"]


def test_sandbox_blocks_forbidden_destructive_patterns():
    res = forge_sandbox.run_python_code("import shutil\nshutil.rmtree('/')")
    assert res["exit_code"] == 1
    assert "Execution blocked by Forge Sandbox safety filter" in res["stderr"]
    assert res["error"] == "SecurityViolation"
