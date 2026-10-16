import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx
import psutil

ROOT_DIR = Path(__file__).resolve().parents[2]


def measure_system_hardware():
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)
    cpu_freq = psutil.cpu_freq()
    vm = psutil.virtual_memory()

    # GPU measurement via nvidia-smi if available
    gpu_info = []
    try:
        smi = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,memory.used,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in smi.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                gpu_info.append({
                    "name": parts[0],
                    "vram_total_mb": float(parts[1]),
                    "vram_free_mb": float(parts[2]),
                    "vram_used_mb": float(parts[3]),
                    "driver_version": parts[4],
                })
    except Exception as e:
        gpu_info = [{"error": str(e), "detected": False}]

    # Disk
    disk = shutil.disk_usage(ROOT_DIR)

    return {
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        "cpu": {
            "logical_cores": cpu_count_logical,
            "physical_cores": cpu_count_physical,
            "current_freq_mhz": cpu_freq.current if cpu_freq else None,
            "max_freq_mhz": cpu_freq.max if cpu_freq else None,
        },
        "ram": {
            "total_gb": round(vm.total / (1024**3), 2),
            "available_gb": round(vm.available / (1024**3), 2),
            "used_gb": round(vm.used / (1024**3), 2),
            "percent_used": vm.percent,
        },
        "gpu": gpu_info,
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
        },
    }


def measure_ollama_and_benchmarks():
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_data = {"reachable": False, "models": [], "benchmarks": {}}

    try:
        with httpx.Client(timeout=3.0) as client:
            res = client.get(f"{ollama_url}/api/version")
            if res.status_code == 200:
                ollama_data["reachable"] = True
                ollama_data["version"] = res.json().get("version")

                tags_res = client.get(f"{ollama_url}/api/tags")
                if tags_res.status_code == 200:
                    models = tags_res.json().get("models", [])
                    ollama_data["models"] = [m.get("name") for m in models]

                # If models available, benchmark a prompt
                if ollama_data["models"]:
                    test_model = ollama_data["models"][0]
                    t0 = time.perf_counter()
                    chat_res = client.post(
                        f"{ollama_url}/api/chat",
                        json={
                            "model": test_model,
                            "messages": [{"role": "user", "content": "Respond with one word: 'READY'."}],
                            "stream": False,
                        },
                        timeout=30.0,
                    )
                    t1 = time.perf_counter()
                    if chat_res.status_code == 200:
                        payload = chat_res.json()
                        ollama_data["benchmarks"][test_model] = {
                            "latency_sec": round(t1 - t0, 3),
                            "total_duration_ms": round(payload.get("total_duration", 0) / 1e6, 2),
                            "eval_count": payload.get("eval_count"),
                            "eval_duration_ms": round(payload.get("eval_duration", 0) / 1e6, 2),
                            "prompt_eval_count": payload.get("prompt_eval_count"),
                            "prompt_eval_duration_ms": round(payload.get("prompt_eval_duration", 0) / 1e6, 2),
                        }
    except Exception as e:
        ollama_data["error"] = str(e)

    return ollama_data


def main():
    print("Measuring system hardware and environment baseline...", flush=True)
    hw = measure_system_hardware()
    ollama = measure_ollama_and_benchmarks()

    out = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": hw,
        "ollama": ollama,
    }

    target = ROOT_DIR / "REMEDIATION" / "baseline" / "hardware_measurements.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2), encoding="utf-8")

    log_target = ROOT_DIR / "REMEDIATION" / "logs" / "benchmark_measurements.log"
    log_target.parent.mkdir(parents=True, exist_ok=True)
    log_summary = (
        f"=== COPPER Release Hardware & Benchmark Baseline ===\n"
        f"Timestamp: {out['timestamp']}\n"
        f"OS: {hw['os']['system']} {hw['os']['release']} ({hw['os']['machine']})\n"
        f"CPU: {hw['cpu']['physical_cores']} physical / {hw['cpu']['logical_cores']} logical cores\n"
        f"RAM: {hw['ram']['total_gb']} GB total ({hw['ram']['available_gb']} GB available)\n"
        f"GPU: {json.dumps(hw['gpu'])}\n"
        f"Disk: {hw['disk']['free_gb']} GB free / {hw['disk']['total_gb']} GB total\n"
        f"Ollama Reachable: {ollama.get('reachable')}\n"
        f"Ollama Models: {ollama.get('models')}\n"
        f"Benchmarks: {json.dumps(ollama.get('benchmarks'), indent=2)}\n"
    )
    log_target.write_text(log_summary, encoding="utf-8")
    print(log_summary)


if __name__ == "__main__":
    main()
