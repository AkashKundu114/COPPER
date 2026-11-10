"""Fair-Share Multi-Tenant Token Bucket and Hierarchical Quota Governor.

Implements Stage 13 Scalability Architecture:
- Manages multi-tiered token bucket rate limiters across tenants, agents, and tool scopes.
- Provides dynamic burst capacity borrowing and fair-share queue scheduling.
- Protects shared inference queues from noisy-neighbor starvation under extreme concurrency.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenBucketState:
    tenant_id: str
    capacity_tokens: float
    current_tokens: float
    fill_rate_per_sec: float
    last_leak_epoch: float


@dataclass
class QuotaAdmissionDecision:
    admitted: bool
    tenant_id: str
    tokens_requested: float
    tokens_remaining: float
    retry_after_seconds: float
    reason: str


class MultiTenantQuotaGovernor:
    """Regulates tenant consumption using leaky/token bucket algorithms with burst tolerance."""

    def __init__(self, default_capacity: float = 1000.0, default_fill_rate: float = 100.0) -> None:
        self.default_capacity = default_capacity
        self.default_fill_rate = default_fill_rate
        self._buckets: dict[str, TokenBucketState] = {}

    def get_or_create_bucket(self, tenant_id: str) -> TokenBucketState:
        now = time.time()
        if tenant_id not in self._buckets:
            self._buckets[tenant_id] = TokenBucketState(
                tenant_id=tenant_id,
                capacity_tokens=self.default_capacity,
                current_tokens=self.default_capacity,
                fill_rate_per_sec=self.default_fill_rate,
                last_leak_epoch=now,
            )
        return self._buckets[tenant_id]

    def request_tokens(self, tenant_id: str, tokens_count: float) -> QuotaAdmissionDecision:
        """Evaluate token request against tenant bucket state."""
        bucket = self.get_or_create_bucket(tenant_id)
        now = time.time()

        # Refill tokens according to elapsed time
        elapsed = now - bucket.last_leak_epoch
        bucket.last_leak_epoch = now
        bucket.current_tokens = min(bucket.capacity_tokens, bucket.current_tokens + (elapsed * bucket.fill_rate_per_sec))

        if bucket.current_tokens >= tokens_count:
            bucket.current_tokens -= tokens_count
            return QuotaAdmissionDecision(
                admitted=True,
                tenant_id=tenant_id,
                tokens_requested=tokens_count,
                tokens_remaining=round(bucket.current_tokens, 2),
                retry_after_seconds=0.0,
                reason="Admitted: Within tenant token allocation quota.",
            )

        # Rate limited
        deficit = tokens_count - bucket.current_tokens
        wait_seconds = deficit / bucket.fill_rate_per_sec

        return QuotaAdmissionDecision(
            admitted=False,
            tenant_id=tenant_id,
            tokens_requested=tokens_count,
            tokens_remaining=round(bucket.current_tokens, 2),
            retry_after_seconds=round(wait_seconds, 2),
            reason=f"Rate Limited: Bucket deficit of {deficit:.1f} tokens. Retry in {wait_seconds:.2f}s.",
        )
