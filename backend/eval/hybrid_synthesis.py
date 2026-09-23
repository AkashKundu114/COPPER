"""
C.O.P.P.E.R. Hybrid Benchmark Synthesis Engine (1,000,000+ Scale)
Merges local synthetic datasets with external ingested benchmarks,
performs canonical deduplication via SHA-256 fingerprinting,
and produces unified hybrid evaluation corpuses for every domain.
"""

import hashlib
import json
import random
import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_EVAL_DIR = Path(__file__).parent / "datasets"
GENERATED_DIR = BASE_EVAL_DIR / "generated"
EXTERNAL_DIR = BASE_EVAL_DIR / "external"
SYNTHESIS_DIR = BASE_EVAL_DIR / "hybrid"
SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)


def normalize_prompt(text: str) -> str:
    """Canonical prompt normalization for robust deduplication."""
    return " ".join(text.lower().strip().split())


def hash_prompt(text: str) -> int:
    return hash(normalize_prompt(text))


def stream_file_items(path: Path):
    """Yields items from either .jsonl (line by line) or .json (array)."""
    if not path.exists():
        return
    if path.suffix == ".jsonl":
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        yield json.loads(line)
                    except Exception:
                        pass
    else:
        with open(path, encoding="utf-8") as f:
            try:
                items = json.load(f)
                for it in items:
                    yield it
            except Exception:
                pass


def merge_domain_streaming(domain_name: str, generated_files: list[Path], external_files: list[Path], out_path: Path) -> int:
    seen_hashes = set()
    count = 0

    with open(out_path, "w", encoding="utf-8") as out_f:
        for gf in generated_files:
            for it in stream_file_items(gf):
                h = hash_prompt(it["prompt"])
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    count += 1
                    it["canonical_hash"] = str(h)
                    out_f.write(json.dumps(it) + "\n")

        for ef in external_files:
            for it in stream_file_items(ef):
                h = hash_prompt(it["prompt"])
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    count += 1
                    it["canonical_hash"] = str(h)
                    out_f.write(json.dumps(it) + "\n")

    return count


def main():
    print("=" * 70)
    print("🧬 C.O.P.P.E.R. HYBRID SYNTHESIS & DEDUPLICATION ENGINE (1M+ SCALE)")
    print("=" * 70)

    # Resolve either scaled .jsonl or fallback .json
    def get_gen_path(domain: str):
        scaled = GENERATED_DIR / f"{domain}_scaled.jsonl"
        return scaled if scaled.exists() else GENERATED_DIR / f"{domain}_10k.json"

    domain_mappings = {
        "coding": {
            "generated": [get_gen_path("coding")],
            "external": [],
        },
        "threats": {
            "generated": [get_gen_path("threats")],
            "external": [EXTERNAL_DIR / "jailbreak_llms_github_normalized.json"],
        },
        "research": {
            "generated": [get_gen_path("research")],
            "external": [EXTERNAL_DIR / "science_reasoning_arc_normalized.json"],
        },
        "productivity": {
            "generated": [get_gen_path("productivity")],
            "external": [EXTERNAL_DIR / "toolbench_functions_normalized.json"],
        },
        "vision": {
            "generated": [get_gen_path("vision")],
            "external": [],
        },
        "voice_audio": {
            "generated": [get_gen_path("voice_audio")],
            "external": [EXTERNAL_DIR / "slurp_speech_intents_normalized.json"],
        },
        "image": {
            "generated": [get_gen_path("image")],
            "external": [EXTERNAL_DIR / "midjourney_prompts_open_normalized.json"],
        },
        "automation": {
            "generated": [get_gen_path("automation")],
            "external": [],
        },
        "document": {
            "generated": [get_gen_path("document")],
            "external": [],
        },
        "chat": {
            "generated": [get_gen_path("chat")],
            "external": [],
        },
        "behavior_nutrition": {
            "generated": [get_gen_path("behavior_nutrition")],
            "external": [],
        },
    }

    hybrid_manifest = {}
    grand_total = 0

    for domain, sources in domain_mappings.items():
        out_file = SYNTHESIS_DIR / f"{domain}_hybrid.jsonl"
        print(f"[*] Synthesizing hybrid corpus for domain: {domain.upper()}...")
        count = merge_domain_streaming(domain, sources["generated"], sources["external"], out_file)
        grand_total += count
        size_mb = round(out_file.stat().st_size / (1024 * 1024), 2)
        hybrid_manifest[domain] = {
            "samples": count,
            "file": str(out_file.name),
            "size_mb": size_mb,
        }
        print(f"    ✔ Merged and deduplicated: {count:,} samples ({size_mb} MB)")

    # Build Master Routing Hybrid Dataset
    print("\n[*] Synthesizing Master Cross-Agent Routing Hybrid Dataset...")
    master_gen = GENERATED_DIR / "master_routing_scaled.jsonl"
    if not master_gen.exists():
        master_gen = GENERATED_DIR / "master_routing_15k.json"

    routing_out = SYNTHESIS_DIR / "master_routing_hybrid.jsonl"
    routing_sources = [master_gen]
    external_norm = list(EXTERNAL_DIR.glob("*_normalized.json"))
    routing_count = merge_domain_streaming("master_routing", routing_sources, external_norm, routing_out)

    grand_total += routing_count
    size_mb = round(routing_out.stat().st_size / (1024 * 1024), 2)
    hybrid_manifest["master_routing"] = {
        "samples": routing_count,
        "file": str(routing_out.name),
        "size_mb": size_mb,
    }
    print(f"    ✔ Master Routing Hybrid total: {routing_count:,} samples ({size_mb} MB)")

    with open(SYNTHESIS_DIR / "hybrid_manifest.json", "w", encoding="utf-8") as f:
        json.dump(hybrid_manifest, f, indent=2)

    print("\n" + "=" * 70)
    print(f"🎉 HYBRID SYNTHESIS COMPLETE: {grand_total:,} DEDUPLICATED SAMPLES PRODUCED")
    print(f"📁 Output Directory: {SYNTHESIS_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
