"""
Unit tests for Speculative Decoding Engine.
Verifies draft-verification sampling, rejection handling, and speedup metrics.
"""

import pytest

from app.ai.llm.speculative_engine import SpeculativeDecodingEngine


def test_speculative_verify_tokens_all_accepted():
    engine = SpeculativeDecodingEngine(acceptance_threshold=0.70)
    draft_tokens = ["def", "calculate_sum", "(", "a"]
    probs = [0.95, 0.88, 0.92, 0.75]

    accepted, fallback, count = engine.verify_tokens(draft_tokens, probs)
    assert count == 4
    assert accepted == draft_tokens
    assert fallback is None
    assert engine.metrics.acceptance_rate_pct == 100.0


def test_speculative_verify_tokens_partial_rejection():
    engine = SpeculativeDecodingEngine(acceptance_threshold=0.70)
    draft_tokens = ["import", "numpy", "as", "np"]
    # 3rd token (as) fails threshold (0.50 < 0.70)
    probs = [0.95, 0.90, 0.50, 0.80]

    accepted, fallback, count = engine.verify_tokens(draft_tokens, probs)
    # Only first 2 tokens should be accepted
    assert count == 2
    assert accepted == ["import", "numpy"]
    # Fallback should be generated for rejected token
    assert fallback is not None
    # Remaining token "np" should be discarded
    assert "np" not in accepted


@pytest.mark.asyncio
async def test_speculative_engine_generation_and_speedup():
    engine = SpeculativeDecodingEngine(lookahead_k=3, acceptance_threshold=0.75)

    async def mock_draft(prefix: str, k: int) -> list[str]:
        return ["hello", "world", "!"]

    async def mock_verify(prefix: str, candidates: list[str]) -> list[float]:
        # Accept all
        return [0.90, 0.85, 0.80]

    res = await engine.generate(
        prompt="Greeting:",
        max_tokens=6,
        draft_fn=mock_draft,
        verify_fn=mock_verify,
    )

    assert res["total_tokens"] >= 6
    assert res["acceptance_rate_pct"] == 100.0
    assert res["speedup_ratio"] > 1.0

    telem = engine.get_telemetry()
    assert telem["total_drafted"] >= 6
    assert telem["total_accepted"] >= 6
    assert telem["empirical_speedup"] > 1.0
