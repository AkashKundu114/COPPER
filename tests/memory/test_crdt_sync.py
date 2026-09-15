"""
Unit tests for Conflict-Free Replicated Data Types (CRDTs) & Offline P2P Memory Sync.
Verifies LWW-Element-Set, Vector Clocks, idempotency, and partition convergence.
"""

import pytest

from app.ai.memory.crdt_sync import (
    LWWElementSet,
    P2PEpistemicSyncEngine,
    VectorClock,
)


def test_vector_clock_ticks_and_merges():
    c1 = VectorClock("node_a")
    c1.tick()
    c1.tick()
    assert c1.get_time() == 2

    c2 = VectorClock("node_b")
    c2.tick()

    c1.merge(c2.to_dict())
    # c1 clock should have max of node_b (1) and incremented local clock (3)
    assert c1.clock["node_b"] == 1
    assert c1.clock["node_a"] == 3


def test_lww_element_set_add_and_lookup():
    crdt = LWWElementSet("laptop")
    crdt.add("user_name", "Akash Kundu")
    crdt.add("preferred_theme", "molten_copper")

    assert crdt.lookup("user_name") == "Akash Kundu"
    assert crdt.lookup("preferred_theme") == "molten_copper"
    assert crdt.lookup("nonexistent") is None


def test_lww_element_set_remove_and_tombstone():
    crdt = LWWElementSet("laptop")
    crdt.add("temp_token", "secret123")
    assert crdt.lookup("temp_token") == "secret123"

    crdt.remove("temp_token")
    assert crdt.lookup("temp_token") is None


def test_crdt_partition_convergence_and_commutativity():
    # Simulate two offline nodes (laptop and desktop)
    node_a = LWWElementSet("laptop")
    node_b = LWWElementSet("desktop")

    # Initial shared state
    node_a.add("editor", "vscode")
    node_b.merge(node_a.export_state())
    assert node_b.lookup("editor") == "vscode"

    # Network partition: both nodes make concurrent conflicting updates
    node_a.add("editor", "neovim")  # tick 2
    node_b.add("compiler", "clang")  # tick 2
    node_b.add("editor", "cursor")  # tick 3 (newer!)

    # Merge in both directions: A -> B and B -> A
    state_a = node_a.export_state()
    state_b = node_b.export_state()

    # Node A ingests B
    node_a.merge(state_b)
    # Node B ingests A
    node_b.merge(state_a)

    # Strong Eventual Consistency: both states MUST be identical
    assert node_a.lookup("compiler") == "clang"
    assert node_b.lookup("compiler") == "clang"
    # "cursor" had a higher clock tick in B, so it must win on both nodes!
    assert node_a.lookup("editor") == "cursor"
    assert node_b.lookup("editor") == "cursor"
    assert node_a.read_all() == node_b.read_all()


def test_p2p_sync_engine_end_to_end():
    engine_local = P2PEpistemicSyncEngine("local_workstation")
    engine_remote = P2PEpistemicSyncEngine("remote_laptop")

    engine_local.set_memory_fact("target_gpu", "RTX 5060")
    engine_remote.set_memory_fact("preferred_model", "qwen2.5:14b")

    # Export delta from local and ingest in remote
    delta = engine_local.export_delta_payload()
    mutations = engine_remote.ingest_peer_payload(delta)

    assert mutations >= 1
    assert engine_remote.get_memory_fact("target_gpu") == "RTX 5060"
    assert engine_remote.get_memory_fact("preferred_model") == "qwen2.5:14b"
    assert engine_remote.sync_stats["total_syncs"] == 1
