from app.core.forge_sandbox import forge_sandbox

def test_forge_sandbox_basic():
    res = forge_sandbox.run_python_code("print('Hello from Forge')")
    assert res["exit_code"] == 0
    assert "Hello from Forge" in res["stdout"]

def test_forge_sandbox_error():
    res = forge_sandbox.run_python_code("1 / 0")
    assert res["exit_code"] != 0
    assert "ZeroDivisionError" in res["stderr"]

def test_forge_sandbox_timeout():
    # Will timeout after 10 seconds
    res = forge_sandbox.run_python_code("import time\ntime.sleep(12)")
    assert res["exit_code"] == 124
    assert "timed out" in res["stderr"]
