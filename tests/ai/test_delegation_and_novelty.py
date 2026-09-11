import pytest
import uuid
import numpy as np
from datetime import datetime, UTC

from app.ai.ambient.email_agent import email_agent, EmailMessage
from app.ai.ambient.code_review_agent import code_review_agent
from app.ai.ambient.research_pipeline import research_pipeline
from app.ai.ambient.skill_learner import skill_learner
from app.ai.memory.differential_privacy import dp_engine
from app.ai.memory.provenance import provenance_tracker
from app.ai.knowledge.causal_engine import causal_engine, CausalEvent
from app.ai.training.federated_learner import federated_learner


@pytest.mark.asyncio
async def test_email_agent_classification_and_lifecycle():
    email = EmailMessage(
        email_id=str(uuid.uuid4()),
        from_addr="lead@copper-ai.org",
        to_addr="dev@copper-ai.org",
        subject="Can you review the PR by tomorrow?",
        body="Hey, can you review the new differential privacy PR when you have a moment?",
        received_at=datetime.now(),
        priority="fyi"
    )
    email_agent.emails.append(email)

    classification = await email_agent.classify_email(email)
    assert classification in ["urgent", "needs_response", "fyi", "spam"]

    appr = email_agent.approve_draft(email.email_id)
    assert appr["status"] == "success"

    rej = email_agent.reject_draft(email.email_id)
    assert rej["status"] == "success"


def test_code_review_agent_diff_parsing():
    sample_diff = (
        "diff --git a/backend/app/main.py b/backend/app/main.py\n"
        "--- a/backend/app/main.py\n"
        "+++ b/backend/app/main.py\n"
        "@@ -10,3 +10,4 @@\n"
        "+from app.ai.memory.provenance import provenance_tracker\n"
        "-# old comment\n"
    )
    files, ins, dels = code_review_agent._parse_diff_stats(sample_diff)
    assert files == 1
    assert ins >= 1
    assert dels >= 1

    changed = code_review_agent._get_changed_files(sample_diff)
    assert "backend/app/main.py" in changed

    gaps = code_review_agent._detect_test_gaps(["app/ai/provenance.py"])
    assert len(gaps) == 1


def test_research_pipeline_query_generation():
    queries = research_pipeline._generate_search_queries("Differential Privacy in AI OS")
    assert isinstance(queries, list)
    assert len(queries) >= 3
    assert any("Differential Privacy" in q for q in queries)


def test_skill_learner_extraction_and_matching():
    task_desc = "extract audio file and convert to wav"
    steps = [
        {"tool": "ffmpeg", "action": "extract_audio", "input": "test.mp4"},
        {"tool": "ffmpeg", "action": "convert_wav", "input": "test.aac"}
    ]
    skill = skill_learner.extract_skill(task_desc, steps, {"status": "ok"})
    assert skill is not None
    assert skill.skill_id in skill_learner.skills

    matched = skill_learner.find_matching_skill("extract audio file and convert")
    assert matched is not None
    assert "extract_audio" in matched.name


def test_differential_privacy_engine():
    # Noise on embeddings
    orig_emb = [0.1, 0.2, 0.3, 0.4, 0.5]
    noised_emb = dp_engine.add_noise_to_embedding(orig_emb, sensitivity=1.0)
    assert len(noised_emb) == len(orig_emb)
    assert noised_emb != orig_emb

    # Noise on query results
    res = [{"id": "doc1", "distance": 0.42}]
    noised_res = dp_engine.add_noise_to_query_results(res)
    assert "distance" in noised_res[0]

    # Budget tracking
    init_spent = dp_engine.budget.total_epsilon_spent
    spent_ok = dp_engine.spend_budget(0.05)
    assert spent_ok is True
    assert dp_engine.budget.total_epsilon_spent > init_spent

    status = dp_engine.get_budget_status()
    assert "remaining" in status
    assert "epsilon" in status

    guarantee = dp_engine.get_privacy_guarantee()
    assert "differential privacy" in guarantee.lower()


def test_provenance_tracker():
    fact = f"Alice is the project maintainer for COPPER {uuid.uuid4()}"
    rec = provenance_tracker.record_fact(
        fact=fact,
        source_type="chat_interaction",
        source_id="session_001",
        confidence=0.85
    )
    assert rec is not None
    assert rec.fact == fact
    assert rec.current_confidence == 0.85

    # Confirm fact increases confidence
    old_conf = rec.current_confidence
    provenance_tracker.confirm_fact(rec.fact_hash, "session_002", confidence=0.9)
    assert rec.current_confidence >= old_conf

    # Contradict fact decreases confidence
    provenance_tracker.contradict_fact(rec.fact_hash, "session_003", "Alice stepped down", confidence=0.7)
    assert rec.current_confidence < 1.0


def test_causal_engine_traversal():
    evt1 = causal_engine.record_event(
        description="User started coding on memory module",
        category="workspace",
        source="context_watcher",
        entities=["memory", "Code.exe"]
    )
    evt2 = causal_engine.record_event(
        description="High context switching detected due to compile error",
        category="cognitive",
        source="cognitive_load",
        entities=["memory", "compile_error"]
    )
    assert evt1 is not None
    assert evt2 is not None

    link = causal_engine.add_causal_link(
        cause_id=evt1.event_id,
        effect_id=evt2.event_id,
        relationship="leads_to",
        confidence=0.9
    )
    assert link is not None
    assert link.cause_id == evt1.event_id


def test_federated_learner_mesh():
    federated_learner.register_self(name="COPPER-Node-Alpha", port=8001)
    assert federated_learner.self_name == "COPPER-Node-Alpha"
    assert federated_learner.self_peer_id is not None

    peer = federated_learner.add_peer(name="COPPER-Node-Beta", host="192.168.1.100", port=8002)
    assert peer is not None
    assert peer.name == "COPPER-Node-Beta"

    peers = federated_learner.discover_peers()
    assert len(peers) > 0
