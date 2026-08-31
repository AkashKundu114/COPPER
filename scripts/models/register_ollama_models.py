"""
C.O.P.P.E.R. Local Ollama Model Importer / Linker
Iterates through ai-models/models_manifest.json and registers local GGUF files
into Ollama via `ollama create` so no external pulls are required.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = ROOT_DIR / "ai-models"
MANIFEST_PATH = MODELS_DIR / "models_manifest.json"


def get_existing_ollama_tags() -> set[str]:
    try:
        res = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        lines = res.stdout.strip().splitlines()
        tags = set()
        for line in lines[1:]:
            parts = line.split()
            if parts:
                tags.add(parts[0])
        return tags
    except Exception as e:
        print(f"[-] Warning: Failed to list Ollama models: {e}")
        return set()


def extract_model_mappings(data: dict) -> list[tuple[str, Path]]:
    mappings = []

    def walk(obj):
        if isinstance(obj, dict):
            if "ollama_tag" in obj and "file" in obj:
                tag = obj["ollama_tag"]
                rel_file = obj["file"]
                full_path = MODELS_DIR / rel_file
                mappings.append((tag, full_path))
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)
    return mappings


def register_models(force: bool = False):
    print("=" * 66, flush=True)
    print("    C.O.P.P.E.R. OLLAMA LOCAL GGUF IMPORTER / LINKER", flush=True)
    print("=" * 66, flush=True)

    if not MANIFEST_PATH.exists():
        print(f"[-] Error: Manifest not found at {MANIFEST_PATH}", flush=True)
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    existing_tags = get_existing_ollama_tags()
    mappings = extract_model_mappings(manifest)

    # De-duplicate by tag
    seen_tags = set()
    unique_mappings = []
    for tag, path in mappings:
        if tag not in seen_tags:
            seen_tags.add(tag)
            unique_mappings.append((tag, path))

    print(f"[*] Found {len(unique_mappings)} model tags defined in manifest.\n", flush=True)

    success_count = 0
    skipped_count = 0
    failed_count = 0

    for tag, model_path in unique_mappings:
        if not model_path.exists():
            print(f"[-] [MISSING GGUF] {tag:<30} -> {model_path}", flush=True)
            failed_count += 1
            continue

        if not force and (tag in existing_tags or f"{tag}:latest" in existing_tags):
            print(f"[=] [ALREADY LINKED] {tag:<30} -> {model_path.name}", flush=True)
            skipped_count += 1
            continue

        print(f"[+] [LINKING] {tag:<30} from {model_path.name}...", flush=True)

        # Create temporary Modelfile
        modelfile_content = f"FROM {model_path.as_posix()}\n"
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".Modelfile") as tmp:
            tmp.write(modelfile_content)
            tmp_path = tmp.name

        try:
            cmd = ["ollama", "create", tag, "-f", tmp_path]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if proc.returncode == 0:
                print(f"    [OK] Successfully linked {tag}", flush=True)
                success_count += 1
            else:
                print(f"    [FAIL] Could not register {tag}: {proc.stderr.strip()}", flush=True)
                failed_count += 1
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    print("\n" + "=" * 66, flush=True)
    print(f"[*] Done! Newly Linked: {success_count} | Already Linked: {skipped_count} | Failed: {failed_count}", flush=True)
    print("=" * 66, flush=True)


if __name__ == "__main__":
    force_rebuild = "--force" in sys.argv
    register_models(force=force_rebuild)
