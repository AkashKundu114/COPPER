from typing import Any

from fastapi import APIRouter, HTTPException

from app.ai.evaluation.improvement_tracker import improvement_tracker
from app.ai.evaluation.prompt_optimizer import prompt_optimizer
from app.core.logger import logger

router = APIRouter(prefix="/self-improvement", tags=["self-improvement"])


@router.get("/metrics")
async def get_metrics(days: int = 7) -> dict[str, Any]:
    """Retrieves 7-day rolling quality metrics, dimension scores, trends, and history."""
    try:
        return improvement_tracker.get_rolling_metrics(days=days)
    except Exception as e:
        logger.error(f"Failed to fetch rolling quality metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/failures")
async def get_failures(limit: int = 20) -> dict[str, Any]:
    """Retrieves recent failure analysis and category distribution."""
    try:
        return improvement_tracker.get_failures_analysis(limit=limit)
    except Exception as e:
        logger.error(f"Failed to fetch failure analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposed-edits")
async def get_proposed_edits() -> list[dict[str, Any]]:
    """Retrieves pending and applied prompt optimizations for human review."""
    try:
        return improvement_tracker.get_proposed_edits()
    except Exception as e:
        logger.error(f"Failed to fetch proposed prompt edits: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-rankings")
async def get_model_rankings() -> list[dict[str, Any]]:
    """Retrieves empirical quality and latency performance rankings per model per agent."""
    try:
        from app.ai.evaluation.model_optimizer import model_optimizer

        return model_optimizer.get_all_model_rankings()
    except Exception as e:
        logger.error(f"Failed to fetch model rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply-edit/{edit_id}")
async def apply_edit(edit_id: int) -> dict[str, Any]:
    """Applies an approved prompt edit and re-runs the benchmark to check for regression."""
    try:
        result = await prompt_optimizer.apply_proposed_edit(edit_id)
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to apply edit"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply proposed prompt edit {edit_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-benchmark")
async def run_benchmark_endpoint() -> dict[str, Any]:
    """Triggers a live re-run of the comprehensive 1,740-sample benchmark suite."""
    try:
        from eval.benchmark import run_benchmark

        metrics = await run_benchmark()
        return {
            "status": "success",
            "metrics": metrics,
            "summary": {
                "routing_accuracy_pct": metrics.get("routing", {}).get("overall_accuracy_pct", 0.0),
                "routing_p95_ms": metrics.get("routing", {}).get("latency_metrics_ms", {}).get("p95", 0.0),
                "throughput_qps": metrics.get("routing", {}).get("throughput_qps", 0.0),
                "guardian_accuracy_pct": metrics.get("guardian", {}).get("accuracy_pct", 0.0),
                "guardian_threat_catch_pct": metrics.get("guardian", {}).get(
                    "threat_detection_sensitivity_pct", 0.0
                ),
            },
        }
    except Exception as e:
        logger.error(f"Failed to run benchmark suite: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {e}")


@router.post("/optimize-prompts")
async def optimize_prompts_endpoint() -> dict[str, Any]:
    """Triggers an on-demand prompt optimization cycle over the last 7 days of evaluations."""
    try:
        proposals = await prompt_optimizer.run_optimization_cycle()
        return {
            "status": "success",
            "proposals_generated": len(proposals),
            "proposals": proposals,
        }
    except Exception as e:
        logger.error(f"Prompt optimization cycle failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
