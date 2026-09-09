"""
C.O.P.P.E.R. Epistemic Memory & Belief Revision Evaluation Suite
Benchmarks PW-EBR against:
1. Baseline A: Last-Write-Wins (LWW)
2. Baseline B: Naive Bayesian Update (without provenance weighting or surprise gating)
3. Proposed Method: PW-EBR (Surprise-Gated Log-Odds with Provenance Weighting & Temporal Decay)

Evaluated under three core challenges identified in 2024-2026 agent memory literature:
- Challenge 1: Noise/Poisoning Resistance against ambient speculative statements.
- Challenge 2: Instant Convergence under explicit user directives/corrections.
- Challenge 3: Continuous temporal drift & contradiction adaptation after elapsed time.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.memory.memory_manager import (
    compute_surprise_gated_log_odds,
)
from app.database.models.memory_v2 import MemoryType

OUTPUT_FILE = Path(__file__).parent / "benchmark_belief_metrics.json"


@dataclass
class EvaluationSample:
    stream_id: str
    attribute: str
    events: list[dict]
    ground_truth: str


def run_lww_baseline(events: list[dict]) -> float:
    """Last-Write-Wins: Overwrites belief state on every observation."""
    confidence = 0.5
    for ev in events:
        confidence = 0.90 if ev["polarity"] > 0 else 0.10
    return confidence


def run_naive_bayesian_baseline(events: list[dict]) -> float:
    """Naive Bayesian Update: Linear addition without provenance or surprise bounding."""
    conf = 0.50
    for ev in events:
        if ev["polarity"] > 0:
            conf = min(0.99, conf + 0.10)
        else:
            conf = max(0.01, conf - 0.10)
    return conf


def run_pwebr_algorithm(events: list[dict], mem_type: MemoryType = MemoryType.OBSERVATION) -> float:
    """Proposed PW-EBR: Surprise-gated log-odds with provenance weighting and temporal decay."""
    conf = 0.50
    for ev in events:
        conf = compute_surprise_gated_log_odds(
            current_confidence=conf,
            mem_type=mem_type,
            elapsed_days=ev.get("elapsed_days", 0.0),
            provenance_source=ev.get("provenance", "chat"),
            polarity=ev.get("polarity", 1),
        )
    return conf


def generate_benchmark_scenarios() -> list[EvaluationSample]:
    return [
        # Scenario 1: Poisoning Defense (Ambient speculative noise followed by explicit user statement)
        EvaluationSample(
            stream_id="poison_defense_01",
            attribute="editor_theme",
            events=[
                {
                    "statement": "Maybe I should try light theme tomorrow",
                    "value": "light",
                    "provenance": "ambient_inferred",
                    "elapsed_days": 0.0,
                    "polarity": 1,
                },
                {
                    "statement": "Light theme looks bright in that screenshot",
                    "value": "light",
                    "provenance": "speculative",
                    "elapsed_days": 1.0,
                    "polarity": 1,
                },
                {
                    "statement": "What if light theme is better for daytime",
                    "value": "light",
                    "provenance": "ambient_inferred",
                    "elapsed_days": 2.0,
                    "polarity": 1,
                },
                {
                    "statement": "Remember that I exclusively use dark theme",
                    "value": "dark",
                    "provenance": "explicit_user",
                    "elapsed_days": 3.0,
                    "polarity": -1,
                },
            ],
            ground_truth="dark",
        ),
        # Scenario 2: Instant Convergence on User Correction
        EvaluationSample(
            stream_id="instant_convergence_02",
            attribute="user_name",
            events=[
                {
                    "statement": "Call me Akash Kundu",
                    "value": "Akash Kundu",
                    "provenance": "explicit_user",
                    "elapsed_days": 0.0,
                    "polarity": 1,
                },
            ],
            ground_truth="Akash Kundu",
        ),
        # Scenario 3: Temporal Decay with Preference Shift
        EvaluationSample(
            stream_id="temporal_shift_03",
            attribute="frontend_framework",
            events=[
                {
                    "statement": "I write React components",
                    "value": "React",
                    "provenance": "chat",
                    "elapsed_days": 0.0,
                    "polarity": 1,
                },
                {
                    "statement": "Building React dashboard",
                    "value": "React",
                    "provenance": "tool_success",
                    "elapsed_days": 10.0,
                    "polarity": 1,
                },
                # 60 days elapsed without mention (decay period)
                {
                    "statement": "I have completely migrated my stack to Vue 3",
                    "value": "Vue 3",
                    "provenance": "explicit_user",
                    "elapsed_days": 60.0,
                    "polarity": -1,
                },
            ],
            ground_truth="Vue 3",
        ),
        # Scenario 4: Multi-Turn Corroboration via Tool Successes
        EvaluationSample(
            stream_id="tool_verification_04",
            attribute="test_suite",
            events=[
                {
                    "statement": "Using pytest for testing",
                    "value": "pytest",
                    "provenance": "chat",
                    "elapsed_days": 0.0,
                    "polarity": 1,
                },
                {
                    "statement": "392 pytest tests passed",
                    "value": "pytest",
                    "provenance": "tool_success",
                    "elapsed_days": 1.0,
                    "polarity": 1,
                },
                {
                    "statement": "Automated pytest suite execution verified",
                    "value": "pytest",
                    "provenance": "tool_success",
                    "elapsed_days": 2.0,
                    "polarity": 1,
                },
            ],
            ground_truth="pytest",
        ),
    ]


def run_benchmark():
    scenarios = generate_benchmark_scenarios()
    results = []

    print("==================================================================")
    print("    C.O.P.P.E.R. PW-EBR BELIEF REVISION BENCHMARK EVALUATION      ")
    print("==================================================================")

    pwebr_accuracy = 0
    lww_accuracy = 0
    naive_accuracy = 0

    for sc in scenarios:
        lww_conf = run_lww_baseline(sc.events)
        naive_conf = run_naive_bayesian_baseline(sc.events)
        pwebr_conf = run_pwebr_algorithm(sc.events, MemoryType.OBSERVATION)

        if sc.stream_id in ["poison_defense_01", "temporal_shift_03"]:
            pwebr_correct = pwebr_conf <= 0.35
            lww_correct = lww_conf <= 0.35
            naive_correct = naive_conf <= 0.35
        else:
            pwebr_correct = pwebr_conf >= 0.85
            lww_correct = lww_conf >= 0.85
            naive_correct = naive_conf >= 0.85

        if pwebr_correct:
            pwebr_accuracy += 1
        if lww_correct:
            lww_accuracy += 1
        if naive_correct:
            naive_accuracy += 1

        print(f"[*] Stream: {sc.stream_id:25} | Attribute: {sc.attribute:20}")
        print(f"    - LWW Baseline Confidence:     {lww_conf:.2f} (Status: {'PASS' if lww_correct else 'FAIL'})")
        print(f"    - Naive Bayes Confidence:      {naive_conf:.2f} (Status: {'PASS' if naive_correct else 'FAIL'})")
        print(f"    - PW-EBR (Ours) Confidence:    {pwebr_conf:.2f} (Status: {'PASS' if pwebr_correct else 'FAIL'})")

        results.append(
            {
                "stream_id": sc.stream_id,
                "attribute": sc.attribute,
                "lww_conf": round(lww_conf, 2),
                "naive_conf": round(naive_conf, 2),
                "pwebr_conf": round(pwebr_conf, 2),
                "pwebr_correct": pwebr_correct,
            }
        )

    pwebr_rate = (pwebr_accuracy / len(scenarios)) * 100.0
    lww_rate = (lww_accuracy / len(scenarios)) * 100.0
    naive_rate = (naive_accuracy / len(scenarios)) * 100.0

    print("------------------------------------------------------------------")
    print(f"[*] Overall Evaluation Rate - PW-EBR (Ours): {pwebr_rate:.1f}%")
    print(f"[*] Overall Evaluation Rate - Naive Bayes:   {naive_rate:.1f}%")
    print(f"[*] Overall Evaluation Rate - LWW Baseline:  {lww_rate:.1f}%")
    print("==================================================================")

    metrics_data = {
        "pwebr_accuracy": pwebr_rate,
        "naive_accuracy": naive_rate,
        "lww_accuracy": lww_rate,
        "eval_scenarios": results,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)


if __name__ == "__main__":
    run_benchmark()
