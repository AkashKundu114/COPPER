"""
Unit tests for the C.O.P.P.E.R. GPU hardware activation and licensing engine.
"""

import hashlib
import json
from pathlib import Path

import pytest

from app.core.gpu_activation import (
    ACTIVATION_FILE,
    ActivationState,
    HardwareFingerprint,
    activate_local_gpu,
    activate_with_owner_code,
    detect_gpu,
    generate_fingerprint,
    is_activated,
    load_activation,
    revoke_activation,
    validate_owner_code,
)


@pytest.fixture(autouse=True)
def clean_activation_state(monkeypatch, tmp_path):
    """Isolate activation state file to a temporary directory."""
    temp_file = tmp_path / "activation.json"
    temp_dir = tmp_path
    monkeypatch.setattr("app.core.gpu_activation.ACTIVATION_DIR", temp_dir)
    monkeypatch.setattr("app.core.gpu_activation.ACTIVATION_FILE", temp_file)
    yield


def test_hardware_fingerprint_deterministic():
    """Verify hardware fingerprint produces consistent SHA-256 hash and format."""
    fp1 = HardwareFingerprint(
        gpu_name="NVIDIA GeForce RTX 5060 Laptop GPU",
        gpu_vram_mb=8151,
        cpu_name="AMD Ryzen 7",
        os_type="Windows",
        machine_id="UUID-1234-TEST",
    )
    fp2 = HardwareFingerprint(
        gpu_name="NVIDIA GeForce RTX 5060 Laptop GPU",
        gpu_vram_mb=8151,
        cpu_name="AMD Ryzen 7",
        os_type="Windows",
        machine_id="UUID-1234-TEST",
    )
    assert fp1.fingerprint_hash == fp2.fingerprint_hash
    assert fp1.activation_code.startswith("COPPER-")
    assert len(fp1.activation_code.split("-")) == 4


def test_detect_gpu_structure():
    """Verify detect_gpu returns required telemetry keys."""
    gpu = detect_gpu()
    assert "name" in gpu
    assert "vram_mb" in gpu
    assert "available" in gpu
    assert "driver" in gpu


def test_activate_local_gpu():
    """Verify local GPU self-activation creates state file and marks activated."""
    assert not is_activated()
    state = activate_local_gpu()
    assert state.activated is True
    assert state.mode == "local_gpu"
    assert state.activation_code.startswith("COPPER-")
    assert is_activated() is True

    loaded = load_activation()
    assert loaded.activated is True
    assert loaded.mode == "local_gpu"
    assert loaded.activation_code == state.activation_code


def test_validate_and_activate_with_owner_code():
    """Verify owner master code validation using pre-calculated hash."""
    test_code = "COPPER-TEST-1234-ABCD"
    test_hash = hashlib.sha256(test_code.encode("utf-8")).hexdigest()

    # Invalid code
    assert validate_owner_code("COPPER-WRONG-CODE", expected_hash=test_hash) is False
    failed_state = activate_with_owner_code("COPPER-WRONG-CODE", expected_hash=test_hash)
    assert failed_state.activated is False

    # Valid code (case and whitespace insensitive)
    assert validate_owner_code("  copper-test-1234-abcd  ", expected_hash=test_hash) is True
    success_state = activate_with_owner_code("copper-test-1234-abcd", expected_hash=test_hash)
    assert success_state.activated is True
    assert success_state.mode == "owner_code"
    assert success_state.activation_code == test_code
    assert is_activated() is True


def test_revoke_activation():
    """Verify revocation clears the license state."""
    activate_local_gpu()
    assert is_activated() is True

    revoked = revoke_activation()
    assert revoked is True
    assert is_activated() is False
