"""Shamir's Secret Sharing and (t, n) Threshold Cryptosystem Manager.

Implements Stage 12 Zero-Trust Security Architecture:
- Splits master secrets into n cryptographic polynomial shares over a finite prime field.
- Requires any t threshold shares (t <= n) to reconstruct the secret via Lagrange interpolation.
- Guarantees information-theoretic zero-knowledge security for any subset of fewer than t shares.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KeyShare:
    share_id: int
    share_value: int
    threshold: int
    total_shares: int


class ThresholdCryptosystemManager:
    """Manages (t, n) threshold secret sharing and reconstruction over a large prime field."""

    # 256-bit prime modulus
    FIELD_PRIME = 2**256 - 189

    def __init__(self, threshold_t: int = 3, total_shares_n: int = 5) -> None:
        if threshold_t > total_shares_n:
            raise ValueError("Threshold t cannot exceed total shares n")
        self.threshold_t = threshold_t
        self.total_shares_n = total_shares_n

    def _eval_polynomial(self, coefficients: list[int], x: int) -> int:
        """Evaluate polynomial P(x) = c0 + c1*x + c2*x^2 + ... mod FIELD_PRIME."""
        res = 0
        power = 1
        for coeff in coefficients:
            res = (res + coeff * power) % self.FIELD_PRIME
            power = (power * x) % self.FIELD_PRIME
        return res

    def split_secret(self, secret_int: int) -> list[KeyShare]:
        """Split a secret integer into n polynomial shares with threshold t."""
        if secret_int >= self.FIELD_PRIME or secret_int < 0:
            raise ValueError("Secret must be within [0, FIELD_PRIME)")

        # Coefficients: c0 = secret, c1..ct-1 = random
        coeffs = [secret_int] + [secrets.randbelow(self.FIELD_PRIME) for _ in range(self.threshold_t - 1)]

        shares: list[KeyShare] = []
        for x in range(1, self.total_shares_n + 1):
            y = self._eval_polynomial(coeffs, x)
            shares.append(
                KeyShare(
                    share_id=x,
                    share_value=y,
                    threshold=self.threshold_t,
                    total_shares=self.total_shares_n,
                )
            )
        return shares

    def reconstruct_secret(self, shares: list[KeyShare]) -> int:
        """Reconstruct original secret via Lagrange interpolation at x = 0."""
        if len(shares) < self.threshold_t:
            raise ValueError(f"Insufficient shares: got {len(shares)}, required threshold is {self.threshold_t}")

        # Use first t shares
        subset = shares[: self.threshold_t]
        secret = 0

        for i, s_i in enumerate(subset):
            xi, yi = s_i.share_id, s_i.share_value
            num = 1
            den = 1

            for j, s_j in enumerate(subset):
                if i != j:
                    xj = s_j.share_id
                    num = (num * (-xj)) % self.FIELD_PRIME
                    den = (den * (xi - xj)) % self.FIELD_PRIME

            den_inv = pow(den, self.FIELD_PRIME - 2, self.FIELD_PRIME)
            lagrange_i = (num * den_inv) % self.FIELD_PRIME
            secret = (secret + yi * lagrange_i) % self.FIELD_PRIME

        return secret
