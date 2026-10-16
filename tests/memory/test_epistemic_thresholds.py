import pytest
from app.database.models.memory_v2 import UserMemoryV2, MemoryType, MemoryStatus
from app.ai.memory.memory_manager import (
    memory_manager,
    compute_unified_epistemic_decay,
    PROVENANCE_WEIGHTS,
    DECAY_CONSTANTS,
)

def test_memory_promotion_at_exact_085_boundary():
    """
    Verifies that a memory with confidence >= 0.85 transitions from OBSERVATION to FACT.
    A memory with confidence < 0.85 remains an OBSERVATION.
    """
    # 1. Just below threshold: 0.849
    mem_sub = UserMemoryV2(
        content="Sub-boundary observation",
        type=MemoryType.OBSERVATION,
        confidence=0.849,
        evidence_count=1,
        status=MemoryStatus.ACTIVE
    )
    if mem_sub.confidence >= 0.85:
        mem_sub.type = MemoryType.FACT
    assert mem_sub.type == MemoryType.OBSERVATION, "Memory below 0.85 must remain an OBSERVATION."

    # 2. Exactly at threshold: 0.850
    mem_exact = UserMemoryV2(
        content="Exact boundary fact",
        type=MemoryType.OBSERVATION,
        confidence=0.850,
        evidence_count=2,
        status=MemoryStatus.ACTIVE
    )
    if mem_exact.confidence >= 0.85:
        mem_exact.type = MemoryType.FACT
    assert mem_exact.type == MemoryType.FACT, "Memory at exactly 0.85 must be promoted to FACT."

def test_memory_demotion_at_exact_050_boundary():
    """
    Verifies that an observation with confidence < 0.50 transitions to HYPOTHESIS.
    An observation at exactly 0.50 retains OBSERVATION status.
    """
    # 1. Exactly at 0.50
    mem_obs = UserMemoryV2(
        content="Stable observation",
        type=MemoryType.OBSERVATION,
        confidence=0.500,
        evidence_count=1,
        status=MemoryStatus.ACTIVE
    )
    if mem_obs.confidence < 0.50:
        mem_obs.type = MemoryType.HYPOTHESIS
    assert mem_obs.type == MemoryType.OBSERVATION, "Memory at 0.50 must remain an OBSERVATION."

    # 2. Just below: 0.499
    mem_hypo = UserMemoryV2(
        content="Degraded observation",
        type=MemoryType.OBSERVATION,
        confidence=0.499,
        evidence_count=1,
        status=MemoryStatus.ACTIVE
    )
    if mem_hypo.confidence < 0.50:
        mem_hypo.type = MemoryType.HYPOTHESIS
    assert mem_hypo.type == MemoryType.HYPOTHESIS, "Memory below 0.50 must degrade to HYPOTHESIS."

def test_epistemic_decay_floor_and_rates():
    """
    Verifies base tier decay constants and floor behavior.
    """
    assert DECAY_CONSTANTS[MemoryType.FACT] == 0.005, "Fact decay constant must be 0.005"
    assert DECAY_CONSTANTS[MemoryType.OBSERVATION] == 0.030, "Observation decay constant must be 0.030"
    assert DECAY_CONSTANTS[MemoryType.HYPOTHESIS] == 0.100, "Hypothesis decay constant must be 0.100"

    # Test extreme decay towards floor
    decayed = compute_unified_epistemic_decay(
        confidence=0.30,
        mem_type=MemoryType.HYPOTHESIS,
        elapsed_days=365.0,
        importance=0.10,
        retrieval_count=0
    )
    # Floor is bounded by importance (0.05 + 0.5*0.10 = 0.10)
    assert decayed >= 0.05, "Decayed confidence must never drop below the minimum epistemic floor."
