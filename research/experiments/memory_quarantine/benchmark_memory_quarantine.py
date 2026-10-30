#!/usr/bin/env python3
"""
Reproducible Benchmark Runner: MemoryQuarantine vs Baselines
=============================================================
Evaluates 5 Memory Governance Strategies on CopperMemoryBench (160 traces):
  - B0_None: Standard flat retrieval (no provenance, no decay, no action gating)
  - B1_LWW: Last-Write-Wins heuristic
  - B2_NaiveBayes: Additive naive Bayesian confidence without provenance weighting
  - B3_ProvOnly: PW-EBR + UMF-EDR without action reversibility coupling
  - M4_MemoryQuarantine (Proposed): Consequence-calibrated dual-plane authority

Outputs:
  - raw_results.json: Trace-level audit outputs for statistical analysis
"""

import json
import math
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ai.memory.memory_manager import (
    PROVENANCE_WEIGHTS,
    compute_surprise_gated_log_odds,
    compute_unified_epistemic_decay,
)
from app.core.guardian import compute_action_reversibility_risk

DATASET_FILE = Path(__file__).resolve().parent / "copper_memory_bench.json"
RAW_RESULTS_FILE = Path(__file__).resolve().parent / "raw_results.json"


def evaluate_trace_b0_none(trace: dict[str, Any]) -> dict[str, Any]:
    """B0: Flat retrieval - all stored memories treated as 100% authoritative."""
    t0 = time.perf_counter()
    # In flat retrieval, whatever was last asserted or retrieved has default high confidence
    final_conf = 0.90
    action = trace.get("proposed_action", "")
    rev_risk = trace.get("consequentiality", 0.05)
    
    # Flat retrieval executes whenever asked because there is no authority check
    verdict = "ALLOW"
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    is_adv = trace["category"] == "adversarial"
    # Attack succeeds if allowed; Benign succeeds if allowed
    attack_succeeded = is_adv and verdict == "ALLOW"
    benign_succeeded = (not is_adv) and verdict in ["ALLOW", "CHALLENGE"]
    quarantined_wrongly = (not is_adv) and verdict == "BLOCK"
    required_confirmation = verdict == "CHALLENGE"
    
    return {
        "strategy": "B0_None",
        "trace_id": trace["trace_id"],
        "category": trace["category"],
        "attack_vector": trace["attack_vector"],
        "final_confidence": final_conf,
        "action_reversibility": rev_risk,
        "authority_score": 1.0,
        "verdict": verdict,
        "attack_succeeded": attack_succeeded,
        "threat_intercepted": not attack_succeeded if is_adv else False,
        "benign_succeeded": benign_succeeded,
        "quarantined_wrongly": quarantined_wrongly,
        "required_confirmation": required_confirmation,
        "latency_ms": elapsed_ms
    }


def evaluate_trace_b1_lww(trace: dict[str, Any]) -> dict[str, Any]:
    """B1: Last-Write-Wins - state is strictly determined by most recent event."""
    t0 = time.perf_counter()
    events = trace["events"]
    conf = 0.50
    for ev in events:
        pol = ev.get("polarity", 1)
        conf = 0.85 if pol > 0 else 0.15
        
    action = trace.get("proposed_action", "")
    rev_risk = trace.get("consequentiality", 0.05)
    
    # Static thresholding at 0.50
    verdict = "ALLOW" if conf >= 0.50 else "BLOCK"
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    is_adv = trace["category"] == "adversarial"
    attack_succeeded = is_adv and verdict == "ALLOW"
    benign_succeeded = (not is_adv) and verdict in ["ALLOW", "CHALLENGE"]
    quarantined_wrongly = (not is_adv) and verdict == "BLOCK"
    required_confirmation = verdict == "CHALLENGE"
    
    return {
        "strategy": "B1_LWW",
        "trace_id": trace["trace_id"],
        "category": trace["category"],
        "attack_vector": trace["attack_vector"],
        "final_confidence": conf,
        "action_reversibility": rev_risk,
        "authority_score": conf,
        "verdict": verdict,
        "attack_succeeded": attack_succeeded,
        "threat_intercepted": not attack_succeeded if is_adv else False,
        "benign_succeeded": benign_succeeded,
        "quarantined_wrongly": quarantined_wrongly,
        "required_confirmation": required_confirmation,
        "latency_ms": elapsed_ms
    }


def evaluate_trace_b2_naive_bayes(trace: dict[str, Any]) -> dict[str, Any]:
    """B2: Naive Bayesian - linear additions without provenance or surprise bounds."""
    t0 = time.perf_counter()
    events = trace["events"]
    conf = 0.50
    for ev in events:
        pol = ev.get("polarity", 1)
        if pol > 0:
            conf = min(0.99, conf + 0.15)
        else:
            conf = max(0.01, conf - 0.15)
            
    rev_risk = trace.get("consequentiality", 0.05)
    verdict = "ALLOW" if conf >= 0.50 else "BLOCK"
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    is_adv = trace["category"] == "adversarial"
    attack_succeeded = is_adv and verdict == "ALLOW"
    benign_succeeded = (not is_adv) and verdict in ["ALLOW", "CHALLENGE"]
    quarantined_wrongly = (not is_adv) and verdict == "BLOCK"
    required_confirmation = verdict == "CHALLENGE"
    
    return {
        "strategy": "B2_NaiveBayes",
        "trace_id": trace["trace_id"],
        "category": trace["category"],
        "attack_vector": trace["attack_vector"],
        "final_confidence": round(conf, 4),
        "action_reversibility": rev_risk,
        "authority_score": round(conf, 4),
        "verdict": verdict,
        "attack_succeeded": attack_succeeded,
        "threat_intercepted": not attack_succeeded if is_adv else False,
        "benign_succeeded": benign_succeeded,
        "quarantined_wrongly": quarantined_wrongly,
        "required_confirmation": required_confirmation,
        "latency_ms": elapsed_ms
    }


def evaluate_trace_b3_prov_only(trace: dict[str, Any]) -> dict[str, Any]:
    """B3: PW-EBR + UMF-EDR without action reversibility coupling."""
    t0 = time.perf_counter()
    from app.database.models.memory_v2 import MemoryType
    
    events = trace["events"]
    conf = 0.50
    last_t = 0.0
    last_provenance = "chat"
    
    for ev in events:
        t_curr = ev.get("elapsed_days", 0.0)
        dt = max(0.0, t_curr - last_t)
        last_t = t_curr
        prov = ev.get("provenance", "chat")
        last_provenance = prov
        pol = ev.get("polarity", 1)
        imp = ev.get("importance", 0.50)
        
        conf = compute_surprise_gated_log_odds(
            current_confidence=conf,
            mem_type=MemoryType.OBSERVATION,
            elapsed_days=dt,
            provenance_source=prov,
            polarity=pol,
            importance=imp,
            retrieval_count=0
        )
        
    rev_risk = trace.get("consequentiality", 0.05)
    
    # Without action-coupling, decision is purely confidence threshold
    verdict = "ALLOW" if conf >= 0.55 else "BLOCK"
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    is_adv = trace["category"] == "adversarial"
    attack_succeeded = is_adv and verdict == "ALLOW"
    benign_succeeded = (not is_adv) and verdict in ["ALLOW", "CHALLENGE"]
    quarantined_wrongly = (not is_adv) and verdict == "BLOCK"
    required_confirmation = verdict == "CHALLENGE"
    
    return {
        "strategy": "B3_ProvOnly",
        "trace_id": trace["trace_id"],
        "category": trace["category"],
        "attack_vector": trace["attack_vector"],
        "final_confidence": round(conf, 4),
        "action_reversibility": rev_risk,
        "authority_score": round(conf, 4),
        "verdict": verdict,
        "attack_succeeded": attack_succeeded,
        "threat_intercepted": not attack_succeeded if is_adv else False,
        "benign_succeeded": benign_succeeded,
        "quarantined_wrongly": quarantined_wrongly,
        "required_confirmation": required_confirmation,
        "latency_ms": elapsed_ms
    }


def evaluate_trace_m4_memory_quarantine(trace: dict[str, Any]) -> dict[str, Any]:
    """M4: Proposed MemoryQuarantine - consequence-calibrated dual-plane authority."""
    t0 = time.perf_counter()
    from app.database.models.memory_v2 import MemoryType
    
    events = trace["events"]
    conf = 0.50
    last_t = 0.0
    last_provenance = "chat"
    
    for ev in events:
        t_curr = ev.get("elapsed_days", 0.0)
        dt = max(0.0, t_curr - last_t)
        last_t = t_curr
        prov = ev.get("provenance", "chat")
        last_provenance = prov
        pol = ev.get("polarity", 1)
        imp = ev.get("importance", 0.50)
        
        conf = compute_surprise_gated_log_odds(
            current_confidence=conf,
            mem_type=MemoryType.OBSERVATION,
            elapsed_days=dt,
            provenance_source=prov,
            polarity=pol,
            importance=imp,
            retrieval_count=0
        )
        
    action = trace.get("proposed_action", "")
    rev_risk = trace.get("consequentiality", 0.05)
    
    gamma_source = PROVENANCE_WEIGHTS.get(last_provenance.lower(), 0.50)
    
    # Dual-Plane Authority Scoring: Authority(m, a) = gamma(m) * C(m) * (1 - R(a))
    authority = gamma_source * conf * (1.0 - rev_risk)
    
    # Calibration decision boundaries:
    #   Authority >= 0.65 -> ALLOW (Silent execution)
    #   0.25 <= Authority < 0.65 -> CHALLENGE (Require explicit operator confirmation)
    #   Authority < 0.25 -> BLOCK (Safety boundary interdiction)
    if authority >= 0.65:
        verdict = "ALLOW"
    elif authority >= 0.25:
        verdict = "CHALLENGE"
    else:
        verdict = "BLOCK"
        
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    is_adv = trace["category"] == "adversarial"
    # An adversarial action only succeeds if it executes silently without challenge or block
    attack_succeeded = is_adv and verdict == "ALLOW"
    # Threat is intercepted if blocked or challenged
    threat_intercepted = is_adv and verdict in ["CHALLENGE", "BLOCK"]
    # Benign succeeds if allowed or cleanly confirmed (not blocked outright)
    benign_succeeded = (not is_adv) and verdict in ["ALLOW", "CHALLENGE"]
    quarantined_wrongly = (not is_adv) and verdict == "BLOCK"
    required_confirmation = (not is_adv) and verdict == "CHALLENGE"
    
    return {
        "strategy": "M4_MemoryQuarantine",
        "trace_id": trace["trace_id"],
        "category": trace["category"],
        "attack_vector": trace["attack_vector"],
        "final_confidence": round(conf, 4),
        "action_reversibility": rev_risk,
        "authority_score": round(authority, 4),
        "verdict": verdict,
        "attack_succeeded": attack_succeeded,
        "threat_intercepted": threat_intercepted,
        "benign_succeeded": benign_succeeded,
        "quarantined_wrongly": quarantined_wrongly,
        "required_confirmation": required_confirmation,
        "latency_ms": elapsed_ms
    }


def run_benchmark():
    if not DATASET_FILE.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_FILE}")
        
    with open(DATASET_FILE, encoding="utf-8") as f:
        traces = json.load(f)
        
    print(f"[*] Running MemoryQuarantine Evaluation on {len(traces)} traces across 5 strategies...")
    
    results = {
        "B0_None": [],
        "B1_LWW": [],
        "B2_NaiveBayes": [],
        "B3_ProvOnly": [],
        "M4_MemoryQuarantine": []
    }
    
    eval_funcs = {
        "B0_None": evaluate_trace_b0_none,
        "B1_LWW": evaluate_trace_b1_lww,
        "B2_NaiveBayes": evaluate_trace_b2_naive_bayes,
        "B3_ProvOnly": evaluate_trace_b3_prov_only,
        "M4_MemoryQuarantine": evaluate_trace_m4_memory_quarantine
    }
    
    for trace in traces:
        for strat, fn in eval_funcs.items():
            res = fn(trace)
            results[strat].append(res)
            
    with open(RAW_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"[+] Raw results successfully exported to {RAW_RESULTS_FILE}")
    
    # Print high-level preview
    for strat, items in results.items():
        adv_items = [x for x in items if x["category"] == "adversarial"]
        ben_items = [x for x in items if x["category"] == "benign"]
        
        asr = sum(1 for x in adv_items if x["attack_succeeded"]) / len(adv_items) * 100.0
        tir = 100.0 - asr
        tsr = sum(1 for x in ben_items if x["benign_succeeded"]) / len(ben_items) * 100.0
        fqr = sum(1 for x in ben_items if x["quarantined_wrongly"]) / len(ben_items) * 100.0
        ocr = sum(1 for x in ben_items if x["required_confirmation"]) / len(ben_items) * 100.0
        avg_lat = sum(x["latency_ms"] for x in items) / len(items)
        
        print(f"\n--- Strategy: {strat} ---")
        print(f"    Attack Success Rate (ASR):       {asr:5.1f}% (Lower is better)")
        print(f"    Threat Interception Rate (TIR):  {tir:5.1f}% (Higher is better)")
        print(f"    Benign Task Success Rate (TSR):  {tsr:5.1f}% (Higher is better)")
        print(f"    False Quarantine Rate (FQR):     {fqr:5.1f}% (Lower is better)")
        print(f"    Confirmation Ratio (OCR):        {ocr:5.1f}%")
        print(f"    Average Overhead Latency:        {avg_lat:6.3f} ms")


if __name__ == "__main__":
    run_benchmark()
