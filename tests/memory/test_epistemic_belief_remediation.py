"""Targeted Verification and Adversarial Tests for Epistemic Memory & PW-EBR Remediation."""

from datetime import UTC, datetime, timedelta
import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.postgres import Base
from app.database.models.memory_v2 import MemoryStatus, MemoryType, UserMemoryV2
from app.ai.memory.memory_manager import (
    MemoryManager,
    compute_surprise_gated_log_odds,
    compute_unified_epistemic_decay,
    update_epistemic_tier,
)


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_symmetric_epistemic_transitions_promotion_and_demotion():
    """Verify bidirectional state machine eliminates one-way ratchet."""
    mem = UserMemoryV2(
        content="User primary programming language is Python",
        type=MemoryType.OBSERVATION,
        confidence=0.50,
        status=MemoryStatus.ACTIVE,
    )

    # 1. Promote to FACT
    mem.confidence = 0.88
    update_epistemic_tier(mem)
    assert mem.type == MemoryType.FACT, "Confidence >= 0.85 must promote to FACT."

    # 2. Demote from FACT to OBSERVATION
    mem.confidence = 0.72
    update_epistemic_tier(mem)
    assert mem.type == MemoryType.OBSERVATION, "Confidence < 0.85 must demote FACT to OBSERVATION."

    # 3. Demote from OBSERVATION to HYPOTHESIS
    mem.confidence = 0.35
    update_epistemic_tier(mem)
    assert mem.type == MemoryType.HYPOTHESIS, "Confidence < 0.50 must demote OBSERVATION to HYPOTHESIS."

    # 4. Direct demotion from FACT to HYPOTHESIS on catastrophic contradiction
    mem.confidence = 0.95
    mem.type = MemoryType.FACT
    mem.confidence = 0.20
    update_epistemic_tier(mem)
    assert mem.type == MemoryType.HYPOTHESIS, "Contradiction below 0.50 must directly demote FACT to HYPOTHESIS."

    # 5. Direct promotion from HYPOTHESIS to FACT on massive explicit confirmation
    mem.confidence = 0.89
    update_epistemic_tier(mem)
    assert mem.type == MemoryType.FACT, "Confidence >= 0.85 must promote HYPOTHESIS directly to FACT."


def test_contradiction_and_negative_belief_polarity(in_memory_db):
    """Verify contradict_memory applies negative belief updates and triggers status demotion."""
    mgr = MemoryManager()

    # Create an established FACT
    mem = mgr.save_structured_memory(
        db=in_memory_db,
        content="Primary cloud provider is AWS",
        memory_type=MemoryType.FACT,
        category="infrastructure",
        source="explicit_user",
        confidence=0.92,
        importance=0.90,
    )
    assert mem.type == MemoryType.FACT

    # Explicit user contradiction arrives ("No, we migrated completely to local bare-metal")
    updated = mgr.contradict_memory(
        db=in_memory_db,
        memory_id=mem.id,
        provenance="explicit_user",
    )
    assert updated is not None
    # Confidence must significantly drop due to high-surprise negative update from explicit user
    assert updated.confidence < 0.50, f"Contradicted FACT confidence should collapse below 0.50, got {updated.confidence}"
    assert updated.type == MemoryType.HYPOTHESIS, f"Contradicted FACT must be demoted to HYPOTHESIS, got {updated.type}"


def test_dimensional_consistency_in_pwebr():
    """Verify mathematical bounds and dimensional stability of surprise-gated log-odds."""
    # Test boundary prior values
    conf_confirm = compute_surprise_gated_log_odds(
        current_confidence=0.50,
        mem_type=MemoryType.OBSERVATION,
        elapsed_days=0.0,
        provenance_source="explicit_user",
        polarity=1,
    )
    assert 0.80 <= conf_confirm <= 0.90, f"Expected confirmation ~0.85, got {conf_confirm}"

    conf_contradict = compute_surprise_gated_log_odds(
        current_confidence=0.90,
        mem_type=MemoryType.FACT,
        elapsed_days=0.0,
        provenance_source="explicit_user",
        polarity=-1,
    )
    assert conf_contradict <= 0.35, f"Expected sharp drop on high-surprise contradiction, got {conf_contradict}"
    assert conf_contradict >= 0.05, "Confidence must not breach theoretical floor"


def test_retrieval_does_not_inflate_confidence(in_memory_db):
    """Verify record_retrieval increments retrieval_count without fabricating confidence."""
    mgr = MemoryManager()
    mem = mgr.save_structured_memory(
        db=in_memory_db,
        content="A tentative hypothesis that might be wrong",
        memory_type=MemoryType.HYPOTHESIS,
        confidence=0.30,
        importance=0.80,
    )
    initial_conf = mem.confidence
    assert mem.retrieval_count == 0

    # Retrieve 25 times
    for _ in range(25):
        mgr.record_retrieval(in_memory_db, mem.id)

    in_memory_db.refresh(mem)
    assert mem.retrieval_count == 25
    assert mem.confidence == initial_conf, "Retrieval must never artificially increase confidence without evidence."
    assert mem.type == MemoryType.HYPOTHESIS, "Hypothesis must not be promoted simply by being read repeatedly."


def test_memory_lifecycle_operations(in_memory_db):
    """Verify memory quarantine, archival, expiration, and deterministic garbage collection."""
    mgr = MemoryManager()
    mem1 = mgr.save_structured_memory(
        db=in_memory_db,
        content="Suspicious memory from untrusted web document",
        memory_type=MemoryType.OBSERVATION,
        confidence=0.45,
    )
    mgr.quarantine_memory(in_memory_db, mem1.id)
    in_memory_db.refresh(mem1)
    assert mem1.status == MemoryStatus.QUARANTINED

    mem2 = mgr.save_structured_memory(
        db=in_memory_db,
        content="Old hypothesis from last year",
        memory_type=MemoryType.HYPOTHESIS,
        confidence=0.10,
    )
    # Simulate age > 200 days
    mem2.last_confirmed_at = datetime.now(UTC) - timedelta(days=205)
    in_memory_db.commit()

    gc_count = mgr.gc_expired_memories(in_memory_db, max_age_days=180.0)
    assert gc_count >= 1
    in_memory_db.refresh(mem2)
    assert mem2.status == MemoryStatus.EXPIRED
