import json
import os
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai.training.adapter_manager import adapter_manager
from app.ai.training.data_curator import ChrysalisDataCurator
from app.ai.training.lora_trainer import QLoRATrainer
from app.database.models.lora_adapter import AdapterStatus, CuratedTrainingExample, LoRAAdapter, TrainingJob
from app.database.models.response_evaluation import ResponseEvaluation
from app.database.postgres import SessionLocal, init_db
from app.main import app

TEST_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "test_training"
TEST_JSONL = TEST_DATA_DIR / "test_curated.jsonl"
TEST_ADAPTERS_DIR = TEST_DATA_DIR / "adapters"


@pytest.fixture(autouse=True)
def setup_training_env():
    init_db()
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_ADAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        db.query(ResponseEvaluation).filter(ResponseEvaluation.session_id.like("curate_test_%")).delete(synchronize_session=False)
        db.query(CuratedTrainingExample).filter(CuratedTrainingExample.session_id.like("curate_test_%")).delete(synchronize_session=False)
        db.query(LoRAAdapter).filter(LoRAAdapter.version.like("test_%")).delete(synchronize_session=False)
        db.query(TrainingJob).filter(TrainingJob.status.in_(["running", "pending"])).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.query(ResponseEvaluation).filter(ResponseEvaluation.session_id.like("curate_test_%")).delete(synchronize_session=False)
        db.query(CuratedTrainingExample).filter(CuratedTrainingExample.session_id.like("curate_test_%")).delete(synchronize_session=False)
        db.query(LoRAAdapter).filter(LoRAAdapter.version.like("test_%")).delete(synchronize_session=False)
        db.query(TrainingJob).filter(TrainingJob.status.in_(["running", "pending"])).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


def test_data_curator_cleaning_and_triviality():
    curator = ChrysalisDataCurator(output_path=TEST_JSONL)

    # 1. Clean XML tags
    dirty_text = (
        "<think>Let me calculate the square root</think>\n"
        "<tool_call>{\"name\": \"calculator\"}</tool_call>\n"
        "The square root of 144 is 12.\n"
        "<tool_result>12</tool_result>"
    )
    cleaned = curator.clean_text(dirty_text)
    assert "<think>" not in cleaned
    assert "<tool_call>" not in cleaned
    assert "<tool_result>" not in cleaned
    assert "The square root of 144 is 12." in cleaned

    # 2. Trivial interactions check
    assert curator.is_trivial("hi", "Hello! How can I help you today?") is True
    assert curator.is_trivial("thanks", "You're very welcome!") is True
    assert curator.is_trivial("Explain vector embeddings in vector databases", "Vector embeddings are mathematical representations...") is False


@pytest.mark.asyncio
async def test_data_curator_curation_and_deduplication():
    curator = ChrysalisDataCurator(output_path=TEST_JSONL)
    if TEST_JSONL.exists():
        TEST_JSONL.unlink()

    db = SessionLocal()
    try:
        db.query(ResponseEvaluation).filter(ResponseEvaluation.session_id.in_(["curate_test_001", "curate_test_002"])).delete()
        c_hash = curator.compute_content_hash(
            "How do I optimize postgres queries for time-series data?",
            "To optimize PostgreSQL for time-series data, implement declarative table partitioning by range, utilize BRIN indexes on timestamp columns, and tune autovacuum parameters.",
        )
        db.query(CuratedTrainingExample).filter(CuratedTrainingExample.content_hash == c_hash).delete()
        db.commit()

        # Create a high-quality evaluation candidate
        ev_high = ResponseEvaluation(
            session_id="curate_test_001",
            user_message="How do I optimize postgres queries for time-series data?",
            assistant_response="To optimize PostgreSQL for time-series data, implement declarative table partitioning by range, utilize BRIN indexes on timestamp columns, and tune autovacuum parameters.",
            agent_type="coding",
            accuracy=0.95,
            relevance=0.95,
            completeness=0.90,
            helpfulness=0.95,
            voice_consistency=0.90,
            overall_score=0.93,
            failures=[],
            reasoning="Thorough, highly accurate architectural response.",
        )
        # Create a failing evaluation (should be excluded)
        ev_fail = ResponseEvaluation(
            session_id="curate_test_002",
            user_message="What is the capital of Mars?",
            assistant_response="The capital of Mars is Olympus City.",
            agent_type="chat",
            accuracy=0.20,
            relevance=0.50,
            completeness=0.30,
            helpfulness=0.20,
            voice_consistency=0.80,
            overall_score=0.40,
            failures=["HALLUCINATION"],
            reasoning="Hallucinated capital of Mars.",
        )
        db.add(ev_high)
        db.add(ev_fail)
        db.commit()

        # Run curation sweep
        res = await curator.curate_from_evaluations(min_score=0.85, limit=50)
        assert res["curated_new"] >= 1

        # Check curated record exists in DB
        curated_db = db.query(CuratedTrainingExample).filter(CuratedTrainingExample.session_id == "curate_test_001").first()
        assert curated_db is not None
        assert curated_db.quality_score >= 0.85
        assert curated_db.difficulty in ["easy", "medium", "hard"]

        # Check JSONL file was written
        assert TEST_JSONL.exists()
        with open(TEST_JSONL, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        assert any(l["agent_type"] == "coding" for l in lines)

        # Deduplication test: Running curation again should skip existing hash
        res_dedup = await curator.curate_from_evaluations(min_score=0.85, limit=50)
        assert res_dedup["curated_new"] == 0
        assert res_dedup["skipped"] >= 1

        # Check stats
        stats = curator.get_curation_stats()
        assert stats["total_examples"] >= 1
        assert "coding" in stats["agent_distribution"]
    finally:
        db.close()


def test_lora_trainer_artifact_generation():
    trainer = QLoRATrainer(adapters_dir=TEST_ADAPTERS_DIR)
    version = trainer.get_next_version_tag()
    target_dir = TEST_ADAPTERS_DIR / version
    target_dir.mkdir(parents=True, exist_ok=True)

    trainer._save_adapter_artifacts(target_dir, version, "llama3.1:8b", 0.42, 0.45)

    config_path = target_dir / "adapter_config.json"
    meta_path = target_dir / "training_meta.json"
    weights_path = target_dir / "adapter_model.safetensors"

    assert config_path.exists()
    assert meta_path.exists()
    assert weights_path.exists()

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    assert cfg["r"] == 16
    assert cfg["lora_alpha"] == 32
    assert cfg["lora_dropout"] == 0.05
    assert cfg["target_modules"] == ["q_proj", "v_proj", "k_proj", "o_proj"]
    assert cfg["base_model_name_or_path"] == "llama3.1:8b"


def test_adapter_manager_lifecycle():
    db = SessionLocal()
    try:
        # Register a test adapter in DB
        version_tag = "test_lora_lifecycle_v1"
        adapter = LoRAAdapter(
            version=version_tag,
            adapter_dir=str(TEST_ADAPTERS_DIR / version_tag),
            base_model="llama3.1:8b",
            target_agent="coding",
            status=AdapterStatus.CANDIDATE.value,
            training_loss=0.48,
            evaluation_quality_score=0.94,
        )
        db.add(adapter)
        db.commit()
        db.refresh(adapter)

        adapter_id = adapter.id

        # 1. Activate adapter (100%)
        act_res = adapter_manager.activate_adapter(adapter_id)
        assert act_res["success"] is True
        assert act_res["adapter"]["is_active"] is True
        assert act_res["adapter"]["status"] == "active"
        assert act_res["adapter"]["ab_test_percentage"] == 100

        # Verify routing
        routed, routed_v = adapter_manager.should_route_to_adapter("coding")
        assert routed is True
        assert routed_v == version_tag

        # 2. Configure A/B Test (e.g. 50%)
        ab_res = adapter_manager.start_ab_test(adapter_id, percentage=50)
        assert ab_res["success"] is True
        assert ab_res["adapter"]["status"] == "testing"
        assert ab_res["adapter"]["ab_test_percentage"] == 50

        # 3. Deactivate adapter
        deact_res = adapter_manager.deactivate_adapter(adapter_id)
        assert deact_res["success"] is True
        assert deact_res["adapter"]["is_active"] is False

        # 4. Merge adapter
        merge_res = adapter_manager.merge_adapter(adapter_id)
        assert merge_res["success"] is True
        assert merge_res["adapter"]["status"] == "merged"
    finally:
        db.close()


def test_training_api_endpoints():
    client = TestClient(app)

    # 1. GET /api/v1/training/stats
    r_stats = client.get("/api/v1/training/stats")
    assert r_stats.status_code == 200
    sdata = r_stats.json()
    assert "total_examples" in sdata
    assert "difficulty_distribution" in sdata
    assert "agent_distribution" in sdata

    # 2. POST /api/v1/training/curate
    r_curate = client.post("/api/v1/training/curate", json={"min_score": 0.85, "limit": 20})
    assert r_curate.status_code == 200
    assert r_curate.json()["status"] == "success"

    # 3. GET /api/v1/training/adapters
    r_adapters = client.get("/api/v1/training/adapters")
    assert r_adapters.status_code == 200
    assert isinstance(r_adapters.json(), list)

    # 4. GET /api/v1/training/status
    r_status = client.get("/api/v1/training/status")
    assert r_status.status_code == 200

    # 5. POST /api/v1/training/start
    r_start = client.post("/api/v1/training/start", json={"base_model": "llama3.1:8b", "target_agent": "coding"})
    assert r_start.status_code == 200
    jdata = r_start.json()
    assert jdata["status"] == "success"
    assert "job" in jdata
