"""Tests for End-to-End Encrypted (E2EE) P2P Epistemic Memory Sync."""

import os
import time
import pytest

from app.ai.memory.crdt_sync import P2PEpistemicSyncEngine
from app.ai.memory.epistemic_p2p_sync import EpistemicP2PSyncCoordinator, EncryptedSyncPayload


def test_device_pairing():
    coordinator = EpistemicP2PSyncCoordinator(local_device_id="node_a")
    key_hex = os.urandom(32).hex()

    coordinator.pair_device("node_b", key_hex)
    assert coordinator.is_paired("node_b") is True
    assert coordinator.is_paired("node_c") is False

    # Invalid key length must raise ValueError
    with pytest.raises(ValueError):
        coordinator.pair_device("node_invalid", "deadbeef")


def test_encrypted_export_and_ingest():
    shared_key_hex = os.urandom(32).hex()

    # Node A setup
    node_a = EpistemicP2PSyncCoordinator(local_device_id="device_alpha")
    node_a.pair_device("device_beta", shared_key_hex)

    # Node B setup
    node_b = EpistemicP2PSyncCoordinator(local_device_id="device_beta")
    node_b.pair_device("device_alpha", shared_key_hex)

    # Export from Node A
    payload = node_a.export_encrypted_delta("device_beta")
    assert payload.sender_device_id == "device_alpha"
    assert payload.recipient_device_id == "device_beta"
    assert len(payload.ciphertext_b64) > 0
    assert len(payload.nonce_b64) > 0
    assert len(payload.signature) == 64

    # Ingest on Node B
    result = node_b.ingest_encrypted_delta(payload)
    assert result["status"] == "success"
    assert result["sender_device_id"] == "device_alpha"
    assert result["payload_id"] == payload.payload_id


def test_anti_replay_protection():
    shared_key_hex = os.urandom(32).hex()

    node_a = EpistemicP2PSyncCoordinator(local_device_id="device_alpha")
    node_a.pair_device("device_beta", shared_key_hex)

    node_b = EpistemicP2PSyncCoordinator(local_device_id="device_beta")
    node_b.pair_device("device_alpha", shared_key_hex)

    payload = node_a.export_encrypted_delta("device_beta")

    # First ingest succeeds
    node_b.ingest_encrypted_delta(payload)

    # Second ingest of same payload must fail with replay error
    with pytest.raises(ValueError, match="Replay attack detected"):
        node_b.ingest_encrypted_delta(payload)


def test_timestamp_skew_rejection():
    shared_key_hex = os.urandom(32).hex()

    node_a = EpistemicP2PSyncCoordinator(local_device_id="device_alpha")
    node_a.pair_device("device_beta", shared_key_hex)

    node_b = EpistemicP2PSyncCoordinator(local_device_id="device_beta")
    node_b.pair_device("device_alpha", shared_key_hex)

    payload = node_a.export_encrypted_delta("device_beta")
    # Simulate expired payload (10 minutes old)
    payload.timestamp = time.time() - 600.0

    with pytest.raises(ValueError, match="timestamp skew"):
        node_b.ingest_encrypted_delta(payload)


def test_tamper_detection():
    shared_key_hex = os.urandom(32).hex()

    node_a = EpistemicP2PSyncCoordinator(local_device_id="device_alpha")
    node_a.pair_device("device_beta", shared_key_hex)

    node_b = EpistemicP2PSyncCoordinator(local_device_id="device_beta")
    node_b.pair_device("device_alpha", shared_key_hex)

    payload = node_a.export_encrypted_delta("device_beta")
    # Tamper with ciphertext
    payload.ciphertext_b64 = payload.ciphertext_b64[:-4] + "AAAA"

    with pytest.raises(PermissionError, match="signature verification failed"):
        node_b.ingest_encrypted_delta(payload)


def test_unpaired_device_rejection():
    node_a = EpistemicP2PSyncCoordinator(local_device_id="device_alpha")
    with pytest.raises(PermissionError, match="not paired"):
        node_a.export_encrypted_delta("unpaired_device")
