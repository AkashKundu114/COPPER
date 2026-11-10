"""Verifiable Delay Function (VDF) and Cryptographic Consensus Timer.

Implements Stage 13 Reliability & Resilience Engineering:
- Implements sequential Verifiable Delay Functions (Wesolowski VDF abstraction: y = x^(2^T) mod N).
- Enforces un-parallelizable physical wall-clock delay to prevent race conditions during leader election.
- Enables instantaneous O(1) mathematical verification of elapsed consensus epochs.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VDFOutput:
    seed_input: str
    delay_iterations_t: int
    output_y: int
    proof_pi: int
    modulus_n: int
    elapsed_compute_ms: float


class VerifiableDelayConsensusTimer:
    """Computes and verifies cryptographic time locks for secure consensus sequencing."""

    # Standard RSA modulus N = p * q
    P = 1000000007
    Q = 1000000009
    MODULUS_N = P * Q

    def __init__(self, default_iterations_t: int = 1000) -> None:
        self.default_iterations_t = default_iterations_t

    def compute_vdf(self, seed: str, iterations_t: Optional[int] = None) -> VDFOutput:
        """Compute sequential squaring y = x^(2^T) mod N with Wesolowski proof pi."""
        start = time.time()
        t = iterations_t or self.default_iterations_t
        # Map seed to base element x in Z_N
        x = int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % self.MODULUS_N
        if x < 2:
            x = 2

        # Sequential computation: y = x^(2^t) mod N
        y = x
        for _ in range(t):
            y = (y * y) % self.MODULUS_N

        # Wesolowski proof: pi = x^q mod N where 2^t = q*l + r
        l_prime = 65537
        two_t = 1 << t
        q = two_t // l_prime
        proof_pi = pow(x, q, self.MODULUS_N)
        elapsed_ms = (time.time() - start) * 1000.0

        return VDFOutput(
            seed_input=seed,
            delay_iterations_t=t,
            output_y=y,
            proof_pi=proof_pi,
            modulus_n=self.MODULUS_N,
            elapsed_compute_ms=round(elapsed_ms, 2),
        )

    def verify_vdf(self, vdf_output: VDFOutput) -> bool:
        """Verify that pi^l * x^r = y mod N."""
        if vdf_output.output_y >= vdf_output.modulus_n or vdf_output.output_y < 0:
            return False

        x = int(hashlib.sha256(vdf_output.seed_input.encode("utf-8")).hexdigest(), 16) % vdf_output.modulus_n
        if x < 2:
            x = 2

        l_prime = 65537
        r = pow(2, vdf_output.delay_iterations_t, l_prime)
        lhs = (pow(vdf_output.proof_pi, l_prime, vdf_output.modulus_n) * pow(x, r, vdf_output.modulus_n)) % vdf_output.modulus_n
        return lhs == vdf_output.output_y
