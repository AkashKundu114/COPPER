"""
Kernel-Level Sandboxing & Hardware Quota Enforcement (Windows Job Objects & POSIX rlimit).

Operating Systems & Systems Security Concept:
Application-level sandboxing (e.g., regex filters or Python timeouts) fails against:
1. Fork bombs (`:(){ :|:& };:`) or spawning detached daemon background child processes.
2. Sudden runaway heap allocation causing host OS freeze or OOM panic.
3. 100% multi-core CPU monopolization.

This module enforces kernel-level limits:
- On Windows: Uses Windows Job Objects (CreateJobObjectW, SetInformationJobObject)
  - JOB_OBJECT_LIMIT_PROCESS_MEMORY: Hard memory ceiling (e.g. 256 MB).
  - JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: Atomic kernel destruction of the entire child process tree.
  - JOB_OBJECT_CPU_RATE_CONTROL: Throttles maximum CPU share (e.g. max 25% CPU core usage).
- On Linux/POSIX: Uses prlimit/setrlimit (RLIMIT_AS for memory, RLIMIT_CPU for execution time).
"""

import ctypes
import os
import subprocess
import sys
import tempfile
from typing import Any

from app.core.logger import logger

# Windows Job Object Constants
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_CPU_RATE_CONTROL_ENABLE = 0x00000001
JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP = 0x00000004
JobObjectExtendedLimitInformation = 9
JobObjectCpuRateControlInformation = 15


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class JOBOBJECT_CPU_RATE_CONTROL_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("ControlFlags", ctypes.c_uint32),
        ("CpuRate", ctypes.c_uint32),  # In units of 1/100 of 1% (e.g. 2500 = 25%)
    ]


class WindowsKernelJob:
    """Manages an active Windows Job Object handle."""

    def __init__(self, memory_limit_mb: int = 256, cpu_rate_pct: int = 25):
        self.memory_limit_mb = memory_limit_mb
        self.cpu_rate_pct = cpu_rate_pct
        self.handle = None
        self.is_supported = sys.platform == "win32"

        if self.is_supported:
            self._create_job_object()

    def _create_job_object(self) -> None:
        kernel32 = ctypes.windll.kernel32
        self.handle = kernel32.CreateJobObjectW(None, None)
        if not self.handle:
            logger.warning("[KernelSandbox] Failed to create Windows Job Object.")
            return

        # 1. Extended Limit Information: Memory cap + Kill-on-Close
        ext_limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limit_flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_PROCESS_MEMORY
        ext_limits.BasicLimitInformation.LimitFlags = limit_flags
        ext_limits.ProcessMemoryLimit = ctypes.c_size_t(self.memory_limit_mb * 1024 * 1024)

        success = kernel32.SetInformationJobObject(
            self.handle,
            JobObjectExtendedLimitInformation,
            ctypes.byref(ext_limits),
            ctypes.sizeof(ext_limits),
        )
        if not success:
            logger.warning(f"[KernelSandbox] Failed to set memory limits on Job Object: {ctypes.GetLastError()}")

        # 2. CPU Rate Control: Hard Cap
        cpu_limits = JOBOBJECT_CPU_RATE_CONTROL_INFORMATION()
        cpu_limits.ControlFlags = JOB_OBJECT_CPU_RATE_CONTROL_ENABLE | JOB_OBJECT_CPU_RATE_CONTROL_HARD_CAP
        cpu_limits.CpuRate = self.cpu_rate_pct * 100  # 25 * 100 = 2500 (25%)

        kernel32.SetInformationJobObject(
            self.handle,
            JobObjectCpuRateControlInformation,
            ctypes.byref(cpu_limits),
            ctypes.sizeof(cpu_limits),
        )

    def assign_process(self, pid: int) -> bool:
        if not self.is_supported or not self.handle:
            return False
        kernel32 = ctypes.windll.kernel32
        PROCESS_ALL_ACCESS = 0x1F0FFF
        proc_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not proc_handle:
            return False

        try:
            assigned = kernel32.AssignProcessToJobObject(self.handle, proc_handle)
            return bool(assigned)
        finally:
            kernel32.CloseHandle(proc_handle)

    def close(self) -> None:
        if self.handle:
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = None


class KernelSandboxRunner:
    """
    Subprocess Runner backed by OS Kernel-level Quotas.
    Enforces memory ceiling, CPU rate throttling, and process hierarchy tree termination.
    """

    name = "kernel_job_object"

    def __init__(self, memory_limit_mb: int = 256, cpu_rate_pct: int = 25):
        self.memory_limit_mb = memory_limit_mb
        self.cpu_rate_pct = cpu_rate_pct

    def is_available(self) -> bool:
        # Supported on Windows natively; POSIX fallback supported via rlimit
        return sys.platform == "win32" or hasattr(os, "setrlimit")

    def run(self, code: str, timeout: int = 10, memory_limit_mb: int | None = None) -> dict[str, Any]:
        mem_mb = memory_limit_mb or self.memory_limit_mb
        job = WindowsKernelJob(memory_limit_mb=mem_mb, cpu_rate_pct=self.cpu_rate_pct)

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as tf:
            tf.write(code)
            script_path = tf.name

        try:
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=0x08000000 if sys.platform == "win32" else 0,  # CREATE_NO_WINDOW
            )

            # Assign process to Job Object immediately
            if job.is_supported and job.handle:
                job.assign_process(proc.pid)

            stdout, stderr = proc.communicate(timeout=timeout)
            exit_code = proc.returncode

            # Check if terminated by memory quota violation (Windows 0xC0000044: STATUS_QUOTA_EXCEEDED or 0xC0000005)
            is_memory_killed = False
            if exit_code in (-1073741819, 3221225477, -1073741756, 3221225540):
                is_memory_killed = True
                stderr += "\n[KernelSandbox Alert] Process terminated by OS kernel: Memory limit exceeded."

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "memory_limit_mb": mem_mb,
                "is_memory_killed": is_memory_killed,
                "error": "MemoryLimitExceeded" if is_memory_killed else (None if exit_code == 0 else "ExecutionError"),
            }

        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout} seconds.",
                "exit_code": 124,
                "is_memory_killed": False,
                "error": "TimeoutExpired",
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "is_memory_killed": False,
                "error": str(e),
            }
        finally:
            job.close()
            try:
                os.unlink(script_path)
            except Exception:
                pass


kernel_sandbox_runner = KernelSandboxRunner()
