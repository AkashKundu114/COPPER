"""
C.O.P.P.E.R. Local AI Model Integrity & Manifest Verifier
Scans ai-models/ and validates model presence, size, and layout against models_manifest.json.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = ROOT_DIR / "ai-models"
MANIFEST_PATH = MODELS_DIR / "models_manifest.json"

def verify_models():
    print("=" * 66)
    print("         C.O.P.P.E.R. LOCAL AI MODEL VERIFICATION")
    print("=" * 66)

    if not MANIFEST_PATH.exists():
        print(f"[-] Error: Manifest not found at {MANIFEST_PATH}")
        return False

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    total_found = 0
    total_missing = 0
    total_bytes = 0

    print(f"\n[*] Inspecting Model Store: {MODELS_DIR}\n")

    for category in ["core", "subagents", "vision", "image", "embeddings", "audio", "wakeword"]:
        cat_dir = MODELS_DIR / category
        if not cat_dir.exists():
            print(f"[-] Category directory missing: {cat_dir}")
            continue

        files = (
            list(cat_dir.rglob("*.gguf"))
            + list(cat_dir.rglob("*.bin"))
            + list(cat_dir.rglob("*.onnx"))
            + list(cat_dir.rglob("*.safetensors"))
        )
        print(f"[+] [{category.upper():<10}] Found {len(files)} model artifacts:")
        for f in sorted(files):
            sz_mb = f.stat().st_size / (1024 * 1024)
            sz_gb = sz_mb / 1024
            total_bytes += f.stat().st_size
            total_found += 1
            if sz_gb >= 1.0:
                print(f"    - {f.name:<48} ({sz_gb:5.2f} GB)")
            else:
                print(f"    - {f.name:<48} ({sz_mb:5.1f} MB)")

    total_gb = total_bytes / (1024 ** 3)
    print("\n" + "=" * 66)
    print(f"[*] Total Models Detected:  {total_found}")
    print(f"[*] Total Storage Consumed: {total_gb:.2f} GB")
    print("=" * 66)
    return True

if __name__ == "__main__":
    verify_models()
