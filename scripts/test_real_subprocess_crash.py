"""
Real OS-Level Subprocess Crash Recovery Test for C.O.P.P.E.R. TaskWAL:
Validates ACID recovery and compensating transactions under physical process termination.
Does NOT use in-process mocks or deterministic memory loops.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def run_worker_process(wal_dir: str, target_dir: str):
    """Entry point for the child worker process that will be killed."""
    # This code runs inside the child process
    worker_script = f"""
import os
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(r"{Path(__file__).resolve().parent.parent / 'backend'}")))

from app.ai.orchestration.wal_executor import TaskWAL, RecordType

wal_dir = Path(r"{wal_dir}")
target_dir = Path(r"{target_dir}")

wal = TaskWAL(dag_id="crashed_dag_001", wal_dir=wal_dir)
wal.append_record(RecordType.DAG_START, {{"dag_id": "crashed_dag_001", "goal": "critical state update"}})
wal.append_record(RecordType.TASK_INTENT, {{"task_id": "task_1", "instruction": "create secret key file"}})

# Perform physical mutation on disk
secret_file = target_dir / "secret_key.txt"
wal.append_record(
    RecordType.MUTATION_RECORD,
    {{"task_id": "task_1", "type": "file_created", "path": str(secret_file)}}
)
secret_file.write_text("PARTIALLY_COMMITTED_ORPHAN_SECRET", encoding="utf-8")

# Modify an existing file with pre-image logging
config_file = target_dir / "config.json"
config_file.write_text('{{"version": 1, "status": "pristine"}}', encoding="utf-8")
wal.append_record(
    RecordType.MUTATION_RECORD,
    {{
        "task_id": "task_1",
        "type": "file_modified",
        "path": str(config_file),
        "pre_image": '{{"version": 1, "status": "pristine"}}',
        "mode": "overwrite"
    }}
)
config_file.write_text('{{"version": 2, "status": "CORRUPTED_INCOMPLETE"}}', encoding="utf-8")

# Flush file buffers to disk
os.sync() if hasattr(os, "sync") else None

# Signal parent that files are written and we are ready to be killed
ready_flag = target_dir / "worker_ready.flag"
ready_flag.write_text("READY", encoding="utf-8")

# Hang indefinitely waiting for brutal SIGKILL / taskkill
while True:
    time.sleep(0.1)
"""
    return worker_script


def run_physical_subprocess_crash_recovery():
    print("==================================================================")
    print("    PHYSICAL SUBPROCESS CRASH & TaskWAL DURABILITY TEST            ")
    print("==================================================================")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        wal_dir = tmp_path / "wal"
        target_dir = tmp_path / "target"
        wal_dir.mkdir()
        target_dir.mkdir()

        worker_script_path = tmp_path / "worker.py"
        worker_code = run_worker_process(str(wal_dir), str(target_dir))
        worker_script_path.write_text(worker_code, encoding="utf-8")

        python_exe = sys.executable
        print(f"[*] Spawning physical worker subprocess via: {python_exe}")
        proc = subprocess.Popen(
            [python_exe, str(worker_script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        print(f"[*] Worker spawned with PID: {proc.pid}")
        ready_flag = target_dir / "worker_ready.flag"

        # Wait up to 5 seconds for worker to write disk mutations and signal ready
        t0 = time.time()
        while not ready_flag.exists() and time.time() - t0 < 5.0:
            time.sleep(0.05)

        if not ready_flag.exists():
            proc.kill()
            raise RuntimeError("Worker process failed to signal ready in time.")

        # Confirm uncommitted files exist in corrupted state on physical disk
        secret_file = target_dir / "secret_key.txt"
        config_file = target_dir / "config.json"
        assert secret_file.exists(), "Secret file must exist before crash"
        assert "CORRUPTED_INCOMPLETE" in config_file.read_text(encoding="utf-8")
        print(f"[+] Verified pre-crash corrupted state on disk (PID: {proc.pid}).")

        # -------------------------------------------------------------
        # BRUTAL PHYSICAL TERMINATION: Force kill subprocess via OS API
        # -------------------------------------------------------------
        print(f"[!] INJECTING HARD CRASH: Terminating worker process {proc.pid}...")
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/PID", str(proc.pid)], check=True, capture_output=True)
        else:
            proc.kill()

        proc.wait(timeout=3.0)
        print(f"[+] Physical process {proc.pid} confirmed DEAD (exit code: {proc.returncode}).")

        # -------------------------------------------------------------
        # RECOVERY PHASE: Run CrashRecoveryEngine in fresh context
        # -------------------------------------------------------------
        # Import CrashRecoveryEngine
        backend_dir = Path(__file__).resolve().parent.parent / "backend"
        sys.path.insert(0, str(backend_dir))
        from app.ai.orchestration.wal_executor import CrashRecoveryEngine, TaskWAL, RecordType

        engine = CrashRecoveryEngine(wal_dir=wal_dir)
        incomplete_dags = engine.find_incomplete_dags()
        print(f"[*] CrashRecoveryEngine scan: found incomplete DAGs: {incomplete_dags}")
        assert "crashed_dag_001" in incomplete_dags, "CrashRecoveryEngine must detect interrupted DAG"

        state_analysis = engine.analyze_dag_state("crashed_dag_001")
        print(f"[*] State analysis: {len(state_analysis['uncommitted_mutations'])} uncommitted mutations detected.")
        assert len(state_analysis["uncommitted_mutations"]) == 2

        # Execute compensating rollback
        print("[*] Executing idempotent crash compensations...")
        compensated_count = engine.rollback_uncommitted_mutations("crashed_dag_001")
        print(f"[+] Compensated mutations count: {compensated_count}")
        assert compensated_count == 2

        # Verify physical disk state post-recovery
        assert not secret_file.exists(), "Orphaned secret file MUST be unlinked/deleted by TaskWAL rollback"
        recovered_config = config_file.read_text(encoding="utf-8")
        assert '{"version": 1, "status": "pristine"}' == recovered_config, "Modified file MUST be restored to pre-image"

        print("[+] PHYSICAL POST-CRASH INTEGRITY VERIFIED: All mutations rolled back cleanly.")
        print("==================================================================")
        return True


if __name__ == "__main__":
    success = run_physical_subprocess_crash_recovery()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
