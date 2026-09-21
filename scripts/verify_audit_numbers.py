import os
import sys
import json
import glob
from pathlib import Path

def audit_workspace():
    print("=" * 80)
    print("C.O.P.P.E.R. WORKSPACE ARTIFACT & METRICS AUDIT")
    print("=" * 80)

    # 1. Physical Checkpoint Sizes in ai-models/
    models_dir = Path("ai-models")
    print("\n--- 1. PHYSICAL MODEL CHECKPOINTS ON DISK ---")
    total_bytes = 0
    model_files = []
    for root, dirs, files in os.walk(models_dir):
        for f in files:
            p = Path(root) / f
            size = p.stat().st_size
            rel_p = p.relative_to(models_dir)
            total_bytes += size
            model_files.append((str(rel_p), size))

    # Sort by size descending
    model_files.sort(key=lambda x: x[1], reverse=True)
    for rel_p, size in model_files:
        size_gb = size / (1024 ** 3) # GiB
        size_mb = size / (1024 ** 2)
        print(f"  {rel_p:<55} : {size_gb:6.2f} GiB ({size_mb:8.1f} MiB)")

    print(f"\nTotal Storage in ai-models/: {total_bytes / (1024**3):.2f} GiB ({total_bytes / 1e9:.2f} GB)")

    # 2. Inspect models_manifest.json
    manifest_path = models_dir / "models_manifest.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print("\n--- 2. MANIFEST SPECIFICATIONS (models_manifest.json) ---")
        print(f"  Meta Agent Full Title: {manifest.get('sovereign_meta_agent', {}).get('full_title')}")
        print(f"  Target Idle VRAM:      {manifest.get('vram_policy', {}).get('target_idle_vram_gb')} GB")
        
        print("\n  Declared Models in Manifest:")
        declared_total_gb = 0
        all_models = []
        if "gatekeeper" in manifest:
            for k, v in manifest["gatekeeper"].items():
                all_models.append((f"gatekeeper.{k}", v.get("name"), v.get("agent_codename"), v.get("size_gb", 0), v.get("file")))
        if "always_on_mini_model" in manifest:
            v = manifest["always_on_mini_model"]
            all_models.append(("always_on", v.get("name"), v.get("agent_codename"), v.get("size_gb", 0), v.get("file")))
        if "core_agents" in manifest:
            for k, v in manifest["core_agents"].items():
                all_models.append((f"core.{k}", v.get("name"), v.get("agent_codename"), v.get("size_gb", 0), v.get("file")))
        if "subagents" in manifest:
            for k, v in manifest["subagents"].items():
                all_models.append((f"subagent.{k}", v.get("name"), v.get("agent_codename"), v.get("size_gb", 0), v.get("file")))
        if "vision_agents" in manifest:
            for k, v in manifest["vision_agents"].items():
                all_models.append((f"vision.{k}", v.get("name"), v.get("agent_codename"), v.get("size_gb", 0), v.get("file")))
        if "image_studio" in manifest:
            v = manifest["image_studio"]
            all_models.append(("image_studio", "sd_turbo", "PICASSO", v.get("size_gb", 0), v.get("primary_model_path")))
        if "embeddings" in manifest:
            for k, v in manifest["embeddings"].items():
                all_models.append((f"embedding.{k}", v.get("name"), "EMBED", v.get("size_gb", 0), v.get("file")))

        for role, name, codename, sz, fpath in all_models:
            declared_total_gb += sz
            print(f"    [{role:<18}] {codename:<10} ({name:<30}) : {sz:5.2f} GB  -> {fpath}")

        print(f"  Declared Sum of Model Sizes: {declared_total_gb:.2f} GB")

    # 3. Data Manifests in backend/eval/datasets/
    print("\n--- 3. DATASET MANIFESTS & EXACT COUNTS ---")
    routing_dir = Path("backend/eval/datasets/routing")
    if routing_dir.exists():
        print("  Routing Datasets:")
        master_routing = routing_dir / "master_routing_dataset.json"
        if master_routing.exists():
            with open(master_routing, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"    master_routing_dataset.json: {len(data)} total samples")
            # Count per category
            cats = {}
            for item in data:
                c = item.get("expected_agent", item.get("category", "unknown"))
                cats[c] = cats.get(c, 0) + 1
            for c, cnt in sorted(cats.items()):
                print(f"      - {c:<15}: {cnt} samples")
        
        for p in routing_dir.glob("*.json"):
            if p.name != "master_routing_dataset.json":
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                print(f"    {p.name:<32}: {len(d):5d} items")

    guardian_dir = Path("backend/eval/datasets/guardian")
    if guardian_dir.exists():
        print("\n  Guardian Datasets:")
        master_guardian = guardian_dir / "master_guardian_dataset.json"
        if master_guardian.exists():
            with open(master_guardian, "r", encoding="utf-8") as f:
                gdata = json.load(f)
            print(f"    master_guardian_dataset.json: {len(gdata)} total samples")
            types = {}
            for item in gdata:
                t = item.get("type", item.get("category", "unknown"))
                types[t] = types.get(t, 0) + 1
            for t, cnt in sorted(types.items()):
                print(f"      - {t:<25}: {cnt} samples")

        for p in guardian_dir.glob("*.json"):
            if p.name != "master_guardian_dataset.json":
                with open(p, "r", encoding="utf-8") as f:
                    d = json.load(f)
                print(f"    {p.name:<32}: {len(d):5d} items")

    # 4. Benchmark Metrics from JSON
    print("\n--- 4. STORED BENCHMARK EVALUATION OUTPUTS ---")
    bm_metrics_path = Path("backend/eval/benchmark_metrics.json")
    if bm_metrics_path.exists():
        with open(bm_metrics_path, "r", encoding="utf-8") as f:
            bm = json.load(f)
        routing = bm.get("routing", bm)
        guardian = bm.get("guardian", bm)
        print(f"  Routing Accuracy:   {routing.get('overall_accuracy_pct', routing.get('routing_accuracy'))}%")
        print(f"  Weighted F1:        {routing.get('weighted_f1_score_pct', routing.get('weighted_f1'))}%")
        print(f"  Total Samples:      {routing.get('total_samples', routing.get('total_routing_samples'))}")
        print(f"  Correct Samples:    {routing.get('correct', routing.get('correct_routing_samples'))}")
        lat = routing.get("latency_metrics_ms", {})
        print(f"  Latency Mean:       {lat.get('avg', routing.get('routing_latency_mean_ms'))} ms")
        print(f"  Latency P50:        {lat.get('median_p50', routing.get('routing_latency_p50_ms'))} ms")
        print(f"  Latency P95:        {lat.get('p95', routing.get('routing_latency_p95_ms'))} ms")
        print(f"  Latency P99:        {lat.get('p99', routing.get('routing_latency_p99_ms'))} ms")
        print(f"  Routing QPS:        {routing.get('throughput_qps', routing.get('routing_qps'))}")
        print(f"  Guardian Accuracy:  {guardian.get('accuracy_pct', guardian.get('guardian_accuracy'))}%")
        print(f"  Guardian Samples:   {guardian.get('total_samples', guardian.get('total_guardian_samples'))}")
        print(f"  Guardian Latency:   {guardian.get('avg_latency_ms', guardian.get('guardian_latency_mean_ms'))} ms")

    belief_metrics_path = Path("backend/eval/benchmark_belief_metrics.json")
    if belief_metrics_path.exists():
        with open(belief_metrics_path, "r", encoding="utf-8") as f:
            b_bm = json.load(f)
        print(f"  Belief UMF-EDR Acc: {b_bm.get('umf_edr_accuracy')}%")
        print(f"  Belief LWW Acc:     {b_bm.get('lww_accuracy')}%")
        print(f"  Belief Naive Acc:   {b_bm.get('naive_accuracy')}%")

    print("=" * 80)

if __name__ == "__main__":
    audit_workspace()
