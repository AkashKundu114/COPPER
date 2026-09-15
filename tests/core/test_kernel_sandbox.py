"""
Unit tests for OS Kernel Sandboxing & Windows Job Objects.
Verifies process execution, timeout enforcement, and memory quota isolation.
"""

import sys
import pytest

from app.core.kernel_sandbox import KernelSandboxRunner, WindowsKernelJob


def test_kernel_job_creation():
    job = WindowsKernelJob(memory_limit_mb=128, cpu_rate_pct=25)
    if sys.platform == "win32":
        assert job.is_supported is True
        assert job.handle is not None
    job.close()
    assert job.handle is None


def test_kernel_sandbox_runner_safe_code_execution():
    runner = KernelSandboxRunner(memory_limit_mb=128)
    code = "print('Kernel sandbox hello world')"
    res = runner.run(code, timeout=5)

    assert res["exit_code"] == 0
    assert "Kernel sandbox hello world" in res["stdout"]
    assert res["is_memory_killed"] is False
    assert res["error"] is None


def test_kernel_sandbox_timeout_enforcement():
    runner = KernelSandboxRunner()
    # Infinite loop script
    code = "import time\nwhile True:\n    time.sleep(0.1)"
    res = runner.run(code, timeout=1)

    assert res["exit_code"] == 124
    assert res["error"] == "TimeoutExpired"
    assert "timed out" in res["stderr"]


def test_kernel_sandbox_syntax_error_handling():
    runner = KernelSandboxRunner()
    code = "def invalid syntax :("
    res = runner.run(code, timeout=5)

    assert res["exit_code"] != 0
    assert "SyntaxError" in res["stderr"]
    assert res["error"] == "ExecutionError"
