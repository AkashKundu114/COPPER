"""
generate_all_agents.py
========================
Runs generate_agent_dataset.py's logic for every agent defined in
agent_configs.py, writing each agent's train/val/test splits to
./dataset/<AGENT>/ (matching the original repo's layout) and producing a
single top-level manifest summarizing every agent's dataset.

Usage:
  python generate_all_agents.py                          # all 27 agents, 1500 records each
  python generate_all_agents.py --size 2000               # all agents, 2000 records each
  python generate_all_agents.py --agents AXIS,AEON,CYPHER  # just a subset
  python generate_all_agents.py --outdir ./data --seed 7
"""

import argparse
import json
from pathlib import Path

from agent_configs import AGENT_CONFIGS, MODEL_MAP
from generate_agent_dataset import generate_dataset, split_records, write_jsonl, write_manifest


def main():
    p = argparse.ArgumentParser(description="Generate fine-tuning datasets for all COPPER sub-agents")
    p.add_argument("--size", type=int, default=1500, help="Records per agent (1000-2000 recommended)")
    p.add_argument("--outdir", type=str, default="./dataset", help="Root output directory")
    p.add_argument("--agents", type=str, default="", help="Comma-separated subset of agents (default: all)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--multiturn_pct", type=float, default=0.12)
    args = p.parse_args()

    agent_list = (
        [a.strip().upper() for a in args.agents.split(",") if a.strip()]
        if args.agents else sorted(AGENT_CONFIGS)
    )

    unknown = [a for a in agent_list if a not in AGENT_CONFIGS]
    if unknown:
        raise SystemExit(f"Unknown agent(s): {unknown}. Known: {sorted(AGENT_CONFIGS)}")

    root = Path(args.outdir)
    summary = {"total_agents": len(agent_list), "records_per_agent_requested": args.size, "agents": {}}

    for i, agent in enumerate(agent_list, 1):
        # Vary the seed per agent so datasets aren't correlated, but stay reproducible
        agent_seed = args.seed + i
        records = generate_dataset(agent, args.size, seed=agent_seed, multiturn_pct=args.multiturn_pct)
        train, val, test = split_records(records, seed=agent_seed)

        outdir = root / agent
        write_jsonl(train, outdir / f"{agent.lower()}_train.jsonl")
        write_jsonl(val, outdir / f"{agent.lower()}_val.jsonl")
        write_jsonl(test, outdir / f"{agent.lower()}_test.jsonl")
        write_manifest(agent, outdir, train, val, test)

        summary["agents"][agent] = {
            "model_tier": MODEL_MAP.get(agent, "UNKNOWN"),
            "total_records": len(records),
            "train": len(train), "val": len(val), "test": len(test),
        }
        print(f"[{i:>2}/{len(agent_list)}] ✅ {agent:<10} "
              f"({MODEL_MAP.get(agent):<16}) → {len(records)} records")

    with open(root / "all_agents_manifest.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    total = sum(v["total_records"] for v in summary["agents"].values())
    print(f"\n🎉 Done. {len(agent_list)} agents, {total} total records → {root}/")
    print(f"   Combined manifest → {root}/all_agents_manifest.json")


if __name__ == "__main__":
    main()
