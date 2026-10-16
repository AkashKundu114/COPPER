import json
import os
import re
import subprocess
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path("d:/C.O.P.P.E.R")
LOGS_DIR = REPO_ROOT / "REMEDIATION" / "logs"
BASELINE_DIR = REPO_ROOT / "REMEDIATION" / "baseline"
REMEDIATION_DIR = REPO_ROOT / "REMEDIATION"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
BASELINE_DIR.mkdir(parents=True, exist_ok=True)

def run_cmd(cmd, cwd=REPO_ROOT):
    try:
        res = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return res.returncode, res.stdout, res.stderr
    except Exception as e:
        return -1, "", str(e)

print("Starting Comprehensive Repository Audit...")

# 1. Tree, Sizes, Large Files, Databases, Artifacts
print("1. Scanning file tree and sizes...")
large_files = []
database_files = []
audio_recordings = []
chroma_dirs = []
pycache_dirs = []
node_modules_dirs = []

ext_counts = defaultdict(int)
ext_lines = defaultdict(lambda: {"total": 0, "blank": 0, "comment": 0, "code": 0})

IGNORED_DIRS = {".git", "node_modules", "dist", "dist-electron", ".pytest_cache", ".ruff_cache", "venv", ".venv"}

for root, dirs, files in os.walk(REPO_ROOT):
    rel_root = Path(root).relative_to(REPO_ROOT)
    parts = rel_root.parts
    if any(p in IGNORED_DIRS for p in parts):
        continue

    if "__pycache__" in dirs:
        pycache_dirs.append(str(rel_root / "__pycache__"))
    if "chroma" in str(rel_root).lower():
        chroma_dirs.append(str(rel_root))

    for f in files:
        fpath = Path(root) / f
        rel_path = fpath.relative_to(REPO_ROOT)
        try:
            size = fpath.stat().st_size
        except Exception:
            continue

        ext = fpath.suffix.lower()
        ext_counts[ext] += 1

        if size > 1024 * 1024:
            large_files.append((str(rel_path), size))

        if ext in {".db", ".sqlite", ".sqlite3"}:
            database_files.append((str(rel_path), size))

        if ext in {".wav", ".mp3", ".ogg", ".flac", ".m4a"}:
            audio_recordings.append((str(rel_path), size))

        if ext in {".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".html", ".sh", ".ps1", ".sql", ".yml", ".yaml", ".json", ".md"}:
            try:
                with open(fpath, encoding="utf-8", errors="ignore") as fp:
                    for line in fp:
                        sline = line.strip()
                        ext_lines[ext]["total"] += 1
                        if not sline:
                            ext_lines[ext]["blank"] += 1
                        elif sline.startswith(("#", "//", "/*", "*", "<!--", "--")):
                            ext_lines[ext]["comment"] += 1
                        else:
                            ext_lines[ext]["code"] += 1
            except Exception:
                pass

# 2. Secret & Privacy Scanning (Working tree and Git history)
print("2. Scanning secrets & privacy patterns...")
secret_patterns = {
    "generic_api_key": re.compile(r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|private[_-]?key)\s*[:=]\s*['\"]([a-zA-Z0-9_\-\.]{16,})['\"]"),
    "hardcoded_jwt": re.compile(r"eyJ[a-zA-Z0-9_\-]{20,}\.eyJ[a-zA-Z0-9_\-]{20,}\.[a-zA-Z0-9_\-]{20,}"),
    "postgres_uri_with_password": re.compile(r"postgresql(?:\+asyncpg)?://([^:]+):([^@]+)@"),
    "redis_uri_with_password": re.compile(r"redis://:[^@]+@"),
    "absolute_windows_user_path": re.compile(r"C:\\Users\\[a-zA-Z0-9_\-]+", re.IGNORECASE),
    "absolute_unix_home_path": re.compile(r"/home/[a-zA-Z0-9_\-]+"),
    "personal_email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"),
}

working_tree_findings = defaultdict(list)

for root, dirs, files in os.walk(REPO_ROOT):
    rel_root = Path(root).relative_to(REPO_ROOT)
    parts = rel_root.parts
    if any(p in {".git", "node_modules", "dist", ".pytest_cache", ".ruff_cache", "venv"} for p in parts):
        continue
    if "REMEDIATION" in parts:
        continue

    for f in files:
        fpath = Path(root) / f
        rel_path = str(fpath.relative_to(REPO_ROOT))

        # skip binary files
        if fpath.suffix.lower() in {".exe", ".dll", ".pyc", ".png", ".jpg", ".ico", ".woff2", ".bin", ".onnx"}:
            continue

        try:
            with open(fpath, encoding="utf-8", errors="ignore") as fp:
                for line_num, line in enumerate(fp, 1):
                    for p_name, regex in secret_patterns.items():
                        m = regex.search(line)
                        if m:
                            match_str = m.group(0)
                            # filter known benign/test patterns
                            if "test_data_firewall.py" in rel_path or "test_forge_sandbox.py" in rel_path:
                                continue
                            if "example" in match_str.lower() or "your_" in match_str.lower() or "dummy" in match_str.lower():
                                continue
                            if "github.com" in match_str.lower() and p_name == "personal_email":
                                pass # record for privacy inventory
                            working_tree_findings[p_name].append({
                                "file": rel_path,
                                "line": line_num,
                                "match": match_str[:120]
                            })
        except Exception:
            pass

# Scan Git history for sensitive patterns
print("3. Scanning git commit log for secret patterns...")
code, log_out, _ = run_cmd('git log -p -S "password" -S "API_KEY" -S "SECRET" -n 50')
git_log_findings = []
if log_out:
    for line in log_out.splitlines():
        if any(kw in line.lower() for kw in ["password=", "secret=", "api_key=", "private_key"]) and line.startswith(("+", "-")):
            if not any(x in line for x in ["test", "dummy", "example", "os.getenv", "settings.", "Config"]):
                git_log_findings.append(line[:120])

print("Audit scan complete.")

report = {
    "ext_counts": dict(ext_counts),
    "ext_lines": {k: dict(v) for k, v in ext_lines.items()},
    "large_files": large_files,
    "database_files": database_files,
    "audio_recordings": audio_recordings,
    "chroma_dirs": chroma_dirs,
    "pycache_dirs": pycache_dirs,
    "working_tree_findings": {k: v[:50] for k, v in working_tree_findings.items()},
    "git_log_findings_count": len(git_log_findings)
}

with open(BASELINE_DIR / "scan_raw_data.json", "w", encoding="utf-8") as fp:
    json.dump(report, fp, indent=2)

print("Saved raw scan data to REMEDIATION/baseline/scan_raw_data.json")
