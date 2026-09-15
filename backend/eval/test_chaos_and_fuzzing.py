import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from eval.chaos_harness import ChaosHarness


def test_adversarial_fuzzer_generation():
    harness = ChaosHarness()
    suite = harness.fuzzer.generate_adversarial_suite()
    assert len(suite) >= 50
    techniques = {item["technique"] for item in suite}
    assert "Zero-Width Spaces" in techniques
    assert "Homoglyph Confusion" in techniques
    assert "Base64 Obfuscation" in techniques


def test_adversarial_security_zero_breaches():
    harness = ChaosHarness()
    results = harness.run_adversarial_security_test()
    assert results["escaped_breaches"] == 0
    assert results["catch_rate_pct"] == 100.0


@pytest.mark.asyncio
async def test_vram_pressure_resilience():
    harness = ChaosHarness()
    results = await harness.run_vram_pressure_test()
    assert results["pass"] is True
    assert results["oom_crashes"] == 0
    assert results["evictions_enforced"] > 0


def test_crash_recovery_resilience():
    harness = ChaosHarness()
    results = harness.run_crash_recovery_test()
    assert results["recovery_rate_pct"] == 100.0
    assert results["successful_recoveries"] == results["crashes_simulated"]
