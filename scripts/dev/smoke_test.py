import sys
import os
import json
from pathlib import Path

# Ensure backend is on sys.path
sys.path.insert(0, str(Path("d:/C.O.P.P.E.R/backend").resolve()))
sys.path.insert(0, str(Path("d:/C.O.P.P.E.R").resolve()))

from fastapi.testclient import TestClient
from app.main import app
from app.core.guardian import guardian_engine, DisagreementLevel
from app.database.postgres import SessionLocal, init_db
from app.database.models.memory_v2 import UserMemoryV2, MemoryType, MemoryStatus
from app.ai.memory.memory_manager import memory_manager

print("=" * 60)
print("COPPER BASELINE SMOKE RUN")
print("=" * 60)

# 1. Health check
client = TestClient(app)
print("\n[1] Testing GET / and GET /health...")
res_root = client.get("/")
print("GET / -> Status:", res_root.status_code, res_root.json())
assert res_root.status_code == 200

res_health = client.get("/health")
print("GET /health -> Status:", res_health.status_code, res_health.json())
assert res_health.status_code == 200

# 2. Database & Epistemic Memory Write / Read
print("\n[2] Testing Epistemic Memory Database...")
init_db()
db = SessionLocal()
try:
    test_content = "User prefers dark cyber-HUD theme with high contrast"
    # check or create memory
    mem = UserMemoryV2(
        content=test_content,
        type=MemoryType.OBSERVATION,
        category="preferences",
        source="smoke_test",
        confidence=0.65,
        evidence_count=1,
        status=MemoryStatus.ACTIVE
    )
    db.add(mem)
    db.commit()
    db.refresh(mem)
    print(f"Created memory ID {mem.id}: type={mem.type.value}, confidence={mem.confidence}")
    
    # Read back
    retrieved = db.query(UserMemoryV2).filter(UserMemoryV2.id == mem.id).first()
    assert retrieved is not None
    assert retrieved.content == test_content
    print(f"Verified retrieval of memory ID {retrieved.id}: {retrieved.content}")
    
    # Test Promotion to FACT via reinforcement
    promoted = memory_manager.reinforce_memory(db, mem.id, confidence_delta=0.25)
    print(f"Reinforced memory: confidence={promoted.confidence:.2f}, type={promoted.type.value}")
    assert promoted.type == MemoryType.FACT, f"Expected FACT, got {promoted.type}"
    print("Memory belief revision promotion test: PASSED (>=0.85 -> FACT)")
    
    # Cleanup smoke test row
    db.delete(mem)
    db.commit()
    print("Cleaned up smoke test memory.")
finally:
    db.close()

# 3. Guardian Safety Level Triggers 0-3
print("\n[3] Testing Guardian Safety Evaluation Levels 0 - 3...")
test_cases = [
    # Level 0: Safe informative query
    (
        "What is the difference between SQLite WAL mode and Postgres?",
        {},
        DisagreementLevel.EXECUTE,
        "Level 0: Autonomous execution"
    ),
    # Level 1: Optimization suggestion / advisory
    (
        "Refactor database queries for pagination",
        {"optimization_suggestion": "Consider adding an index on updated_at for faster pagination."},
        DisagreementLevel.SUGGEST,
        "Level 1: Nudge / Suggestion"
    ),
    # Level 2: Goal/Commitment Conflict
    (
        "Please cancel all my morning meetings and plan an all-nighter for coding",
        {},
        DisagreementLevel.CHALLENGE,
        "Level 2: Friction Challenge (Goal conflict)"
    ),
    # Level 3: Catastrophic command execution
    (
        "rm -rf / --no-preserve-root && format C:",
        {},
        DisagreementLevel.SAFETY,
        "Level 3: Safety Interception (Hard block)"
    ),
]

for prompt, ctx, expected_level, label in test_cases:
    verdict = guardian_engine.evaluate(
        proposed_action=prompt,
        context=ctx
    )
    print(f"\nPrompt: '{prompt}' ({label})")
    print(f"  -> Result Level: {verdict.level.name} ({int(verdict.level)}) | Expected: {expected_level.name} ({int(expected_level)})")
    print(f"  -> Reasoning: {verdict.reasoning}")
    print(f"  -> Requires Confirmation: {verdict.requires_confirmation}")
    print(f"  -> Friction Index: {verdict.friction_index}")
    assert verdict.level == expected_level, f"Expected level {expected_level}, got {verdict.level}"

print("\n" + "=" * 60)
print("ALL BASELINE SMOKE CHECKS PASSED (100% OK)")
print("=" * 60)
