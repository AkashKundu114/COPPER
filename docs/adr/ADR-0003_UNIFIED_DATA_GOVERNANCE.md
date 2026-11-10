# ADR-0003: Unified 5-Tier Data Governance & Verifiable Deletion

## Status
**Accepted**

## Context
COPPER stores data across five heterogeneous storage tiers: PostgreSQL/SQLite relational tables, ChromaDB vector collections, Redis in-memory caches, filesystem WAL/DLQ logs, and user artifact directories. Prior to governance standardization, deleting user memory in SQL left orphaned semantic vectors in ChromaDB, creating data leakage and privacy violations.

## Decision
1. **5-Tier Data Classification**: Tag all persistent data as `PUBLIC`, `INTERNAL`, `PERSONAL`, `SENSITIVE`, or `RESTRICTED` with explicit retention TTLs and local-only egress restrictions.
2. **Synchronous Cross-Store Cascading Erasure**: Deletion requests cascade atomically across SQL tables, ChromaDB collections, Redis keys, and filesystem artifacts.
3. **Cryptographic Deletion Receipts**: Every deletion produces an auditable, tamper-evident SHA-256 `DeletionReceipt` proving exact record counts erased across each store.

## Consequences
- **Positive**: Strict GDPR/CCPA alignment, complete elimination of orphaned vector embeddings, and non-repudiable proof of deletion.
- **Negative**: Multi-store deletion operations require coordinated synchronization.
