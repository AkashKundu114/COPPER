# ADR-0004: Cryptographic Hash-Chained Audit Logging

## Status
**Accepted**

## Context
Standard database logs and flat audit tables are mutable by database administrators or compromised processes. Forensic accountability requires that historical records cannot be modified, reordered, or deleted without cryptographic detection.

## Decision
1. **Append-Only Merkle-Chained Audit Stream**: Every significant event is recorded in an `AuditEvent` linked to its predecessor via SHA-256:
   $$H_i = \text{SHA-256}(H_{i-1} \parallel \text{Seq}_i \parallel \text{Timestamp}_i \parallel \text{Payload}_i)$$
2. **Deterministic Genesis Block**: The chain is anchored to a known, hardcoded Genesis hash ($0^{64}$).
3. **Concurrency-Safe Serialization**: In-memory async mutexes and database row locks serialize chaining to eliminate fork/race conditions in multi-worker environments.
4. **Verifiable Audit API**: `GET /api/audit/verify` re-computes every block signature from Genesis to tip to confirm uncompromised historical integrity.

## Consequences
- **Positive**: Forensic immutability, independent auditability, and immediate detection of unauthorized tampering.
- **Negative**: Re-indexing or re-ordering past audit events is architecturally impossible.
