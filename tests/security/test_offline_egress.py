import socket

import pytest
from fastapi.testclient import TestClient

from app.ai.memory.memory_manager import MemoryType, compute_unified_epistemic_decay
from app.core.ast_validator import ast_security_validator
from app.core.data_firewall import redact
from app.core.guardian import guardian_engine
from app.main import app

ALLOWED_HOSTS = {"127.0.0.1", "localhost", "::1", "testclient"}

@pytest.fixture(autouse=True)
def enforce_zero_egress(monkeypatch):
    """Strict socket interceptor fixture."""
    real_connect = socket.socket.connect

    def guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if isinstance(host, str) and host not in ALLOWED_HOSTS and not host.startswith("127."):
            raise AssertionError(f"[AIRGAP VIOLATION] Outbound network egress attempted to: {address}")
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)

def test_api_health_offline_zero_egress():
    """Verify that root and health endpoints execute without external network calls."""
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    res_health = client.get("/health")
    assert res_health.status_code == 200

def test_guardian_offline_zero_egress():
    """Verify that Guardian evaluation runs completely locally without external calls."""
    verdict = guardian_engine.evaluate("List local files in workspace")
    assert verdict is not None
    assert int(verdict.level) == 0

    blocked = guardian_engine.evaluate("rm -rf / --no-preserve-root")
    assert blocked is not None
    assert int(blocked.level) == 3

def test_data_firewall_offline_zero_egress():
    """Verify that Data Firewall redacts credentials in-memory without remote lookups."""
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.fake and api_key=sk-1234567890abcdef1234"
    sanitized = redact(text)
    assert "sk-12345" not in sanitized
    assert "REDACTED" in sanitized

def test_ast_validator_offline_zero_egress():
    """Verify that AST security validation parses and blocks dangerous imports locally."""
    malicious_code = "import os\nos.system('rm -rf /')"
    result = ast_security_validator.validate(malicious_code)
    assert not result.is_safe
    assert len(result.violations) > 0

def test_epistemic_decay_offline_zero_egress():
    """Verify epistemic memory decay mathematics execute entirely in-process."""
    confidence = compute_unified_epistemic_decay(
        confidence=0.90,
        mem_type=MemoryType.FACT,
        elapsed_days=10.0,
        importance=0.8,
        retrieval_count=3
    )
    assert 0.05 <= confidence <= 0.99
