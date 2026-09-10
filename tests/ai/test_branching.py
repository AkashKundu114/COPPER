import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.ai.branching.branch_manager import BranchManager
from app.ai.branching.diff_analyzer import DiffAnalyzer
from app.ai.memory.persistent_memory import persistent_memory

client = TestClient(app)


# ---------------------------------------------------------
# BranchManager Unit Tests
# ---------------------------------------------------------

def test_branch_conversation_creation(tmp_path):
    storage_file = tmp_path / "branches.json"
    bm = BranchManager(storage_path=str(storage_file))

    # Setup parent session in persistent memory
    session_id = "test_parent_session"
    persistent_memory.sessions[session_id] = [
        {"role": "user", "content": "What is COPPER?"},
        {"role": "assistant", "content": "COPPER is a tactical AI assistant."},
        {"role": "user", "content": "Show me its architecture."},
        {"role": "assistant", "content": "It has three tiers: Reflex, Tactical, and Strategic."},
    ]

    # Create branch diverging after message index 1 (the first assistant response)
    branch = bm.branch_conversation(session_id, message_index=1, title="Architecture Exploration")
    branch_id = branch["branch_id"]

    assert branch_id.startswith(session_id)
    assert "_b" in branch_id
    assert branch["parent_session_id"] == session_id
    assert branch["divergence_index"] == 1
    assert branch["title"] == "Architecture Exploration"
    assert branch["messages_count"] == 2
    assert branch["status"] == "active"

    # Verify messages in the new branch are sliced properly
    branch_history = persistent_memory.get_history(branch_id)
    assert len(branch_history) == 2
    assert branch_history[0]["content"] == "What is COPPER?"
    assert branch_history[1]["content"] == "COPPER is a tactical AI assistant."


def test_branch_isolation(tmp_path):
    storage_file = tmp_path / "branches.json"
    bm = BranchManager(storage_path=str(storage_file))

    session_id = "test_isolation_parent"
    persistent_memory.sessions[session_id] = [
        {"role": "user", "content": "Query 1"},
        {"role": "assistant", "content": "Response 1"},
    ]

    branch = bm.branch_conversation(session_id, message_index=1, title="Divergent Branch")
    branch_id = branch["branch_id"]

    # Append to child branch
    persistent_memory.append_message(branch_id, "user", "Child branch turn")
    persistent_memory.append_message(branch_id, "assistant", "Child response")

    # Parent should remain at 2 messages, child should have 4
    assert len(persistent_memory.get_history(session_id)) == 2
    assert len(persistent_memory.get_history(branch_id)) == 4


def test_list_branches(tmp_path):
    storage_file = tmp_path / "branches.json"
    bm = BranchManager(storage_path=str(storage_file))

    root_id = "root_session_1"
    persistent_memory.sessions[root_id] = [
        {"role": "user", "content": "Start conversation"},
        {"role": "assistant", "content": "Hello!"},
    ]

    branch1 = bm.branch_conversation(root_id, message_index=1, title="Branch 1")
    branch2 = bm.branch_conversation(root_id, message_index=0, title="Branch 2")

    branches = bm.list_branches(root_id)
    assert len(branches) == 3  # Root + 2 branches
    assert any(b["branch_id"] == root_id and b["is_main"] for b in branches)
    assert any(b["branch_id"] == branch1["branch_id"] for b in branches)
    assert any(b["branch_id"] == branch2["branch_id"] for b in branches)


def test_merge_branch(tmp_path):
    storage_file = tmp_path / "branches.json"
    bm = BranchManager(storage_path=str(storage_file))

    parent_id = "merge_parent"
    persistent_memory.sessions[parent_id] = [
        {"role": "user", "content": "Original step 1"},
        {"role": "assistant", "content": "Original step 2"},
    ]

    branch = bm.branch_conversation(parent_id, message_index=1, title="Feature Experiment")
    branch_id = branch["branch_id"]

    # Add divergent turns to branch
    persistent_memory.append_message(branch_id, "user", "Experimental Query")
    persistent_memory.append_message(branch_id, "assistant", "Experimental Solution Found")

    # Perform merge
    result = bm.merge_branch(branch_id, target_session_id=parent_id)
    assert result["status"] == "merged"
    assert result["divergent_turns_count"] == 2
    assert result["branch_id"] == branch_id

    # Verify branch status was updated
    updated_branch = bm.get_branch(branch_id)
    assert updated_branch["status"] == "merged"

    # Verify merge notification was appended to parent
    parent_messages = persistent_memory.get_history(parent_id)
    last_msg = parent_messages[-1]
    assert last_msg["role"] == "assistant"
    assert "Branch Merged" in last_msg["content"]
    assert "Experimental Query" in last_msg["content"]


# ---------------------------------------------------------
# DiffAnalyzer Unit Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_diff_analyzer_llm_parsing():
    analyzer = DiffAnalyzer()

    mock_llm_json = """
    ```json
    {
      "divergence_point": "Turn 2: Decision on Database choice",
      "branch_a_summary": "Explored SQLite for simplicity and embedded zero-config setup.",
      "branch_b_summary": "Explored PostgreSQL for horizontal scalability and pgvector.",
      "key_differences": [
        {
          "aspect": "Scalability",
          "branch_a": "Single-file, local concurrency bottlenecks.",
          "branch_b": "Enterprise cluster, robust vector indexing."
        }
      ],
      "recommendation": "Use PostgreSQL for production or SQLite for testing.",
      "mergeable_insights": [
        "PostgreSQL pgvector supports high-dimensional embeddings seamlessly.",
        "SQLite requires no additional background daemons."
      ]
    }
    ```
    """

    mock_branch_a = {
        "branch_id": "branch_a",
        "title": "SQLite Path",
        "messages": [{"role": "user", "content": "Can we use SQLite?"}],
    }
    mock_branch_b = {
        "branch_id": "branch_b",
        "title": "Postgres Path",
        "messages": [{"role": "user", "content": "Can we use Postgres?"}],
    }

    with patch("app.ai.branching.diff_analyzer.branch_manager.get_branch", side_effect=lambda b_id: mock_branch_a if b_id == "branch_a" else mock_branch_b):
        with patch("app.ai.branching.diff_analyzer.ollama_client.is_available", new_callable=AsyncMock, return_value=True):
            with patch("app.ai.branching.diff_analyzer.ollama_client.chat", new_callable=AsyncMock, return_value=mock_llm_json):
                diff = await analyzer.compare_branches("branch_a", "branch_b")

                assert diff["divergence_point"] == "Turn 2: Decision on Database choice"
                assert "SQLite" in diff["branch_a_summary"]
                assert "PostgreSQL" in diff["branch_b_summary"]
                assert len(diff["key_differences"]) == 1
                assert len(diff["mergeable_insights"]) == 2


@pytest.mark.asyncio
async def test_diff_analyzer_fallback():
    analyzer = DiffAnalyzer()

    mock_branch_a = {
        "branch_id": "branch_a",
        "title": "Alpha",
        "messages": [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
        ],
    }
    mock_branch_b = {
        "branch_id": "branch_b",
        "title": "Beta",
        "messages": [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Alternative Answer 2"},
        ],
    }

    # Test fallback when LLM fails or is unavailable
    with patch("app.ai.branching.diff_analyzer.branch_manager.get_branch", side_effect=lambda b_id: mock_branch_a if b_id == "branch_a" else mock_branch_b):
        with patch("app.ai.branching.diff_analyzer.ollama_client.is_available", new_callable=AsyncMock, return_value=False):
            diff = await analyzer.compare_branches("branch_a", "branch_b")

            assert diff["divergence_point"] is not None
            assert "turn(s)" in diff["branch_a_summary"]
            assert "turn(s)" in diff["branch_b_summary"]
            assert len(diff["key_differences"]) >= 1
            assert len(diff["mergeable_insights"]) >= 1


# ---------------------------------------------------------
# FastAPI Endpoints Integration Tests
# ---------------------------------------------------------

def test_fastapi_branching_routes():
    session_id = "test_api_parent"
    persistent_memory.sessions[session_id] = [
        {"role": "user", "content": "Base query"},
        {"role": "assistant", "content": "Base response"},
    ]

    # 1. Create Branch
    res = client.post("/api/v1/chat/branch", json={
        "session_id": session_id,
        "message_index": 1,
        "title": "API Test Branch",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "branch" in data
    branch = data["branch"]
    assert "branch_id" in branch
    branch_id = branch["branch_id"]
    assert branch["parent_session_id"] == session_id

    # 2. List Branches
    res = client.get(f"/api/v1/chat/branches/{session_id}")
    assert res.status_code == 200
    branches_data = res.json()
    assert "branches" in branches_data
    assert any(b["branch_id"] == branch_id for b in branches_data["branches"])

    # 3. Compare Branches
    res = client.get(f"/api/v1/chat/branches/compare?a={session_id}&b={branch_id}")
    assert res.status_code == 200
    compare_res = res.json()
    assert compare_res["status"] == "success"
    assert "comparison" in compare_res
    compare_data = compare_res["comparison"]
    assert "divergence_point" in compare_data
    assert "branch_a_summary" in compare_data
    assert "branch_b_summary" in compare_data

    # 4. Merge Branch
    res = client.post(f"/api/v1/chat/branches/{branch_id}/merge", json={
        "target_session_id": session_id,
    })
    assert res.status_code == 200
    merge_data = res.json()
    assert merge_data["status"] == "merged"
    assert merge_data["target_session_id"] == session_id
