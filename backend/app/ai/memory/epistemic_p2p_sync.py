"""End-to-End Encrypted (E2EE) P2P Epistemic Memory Sync for C.O.P.P.E.R.

Implements multi-device peer-to-peer epistemic memory synchronization:
- Conflict-Free Replicated Data Types (CRDTs) using LWW-Element-Set and Vector Clocks.
- AES-256-GCM Authenticated Encryption for delta state payloads.
- Anti-Replay protection with bounded timestamp skews and HMAC-SHA256 signatures.
- Local-first zero external cloud reliance.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.ai.memory.crdt_sync import p2p_sync_engine
from app.core.logger import logger


@dataclass
class EncryptedSyncPayload:
    payload_id: str
    sender_device_id: str
    recipient_device_id: str
    nonce_b64: str
    ciphertext_b64: str
    signature: str
    timestamp: float
    mutations_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EncryptedSyncPayload:
        return cls(**data)


class EpistemicP2PSyncCoordinator:
    """Manages E2EE peer-to-peer sync of epistemic facts across registered devices."""

    MAX_TIMESTAMP_SKEW_SEC = 300.0  # 5 minutes anti-replay window

    def __init__(self, local_device_id: Optional[str] = None):
        self.local_device_id = local_device_id or f"copper_device_{uuid.uuid4().hex[:8]}"
        self._paired_devices: dict[str, bytes] = {}  # device_id -> 32-byte shared secret key
        self._seen_payload_ids: set[str] = set()

    def pair_device(self, device_id: str, shared_secret_hex: str) -> None:
        """Registers a paired peer device with its 256-bit pre-shared encryption key."""
        clean_id = device_id.strip()
        key_bytes = bytes.fromhex(shared_secret_hex.strip())
        if len(key_bytes) != 32:
            raise ValueError("Shared secret must be exactly 32 bytes (64 hex characters).")
        self._paired_devices[clean_id] = key_bytes
        logger.info(f"[EpistemicSync] Paired device '{clean_id}' successfully.")

    def is_paired(self, device_id: str) -> bool:
        return device_id.strip() in self._paired_devices

    def export_encrypted_delta(self, recipient_device_id: str) -> EncryptedSyncPayload:
        """Exports the local epistemic CRDT delta sealed with AES-256-GCM and HMAC-SHA256."""
        recip_id = recipient_device_id.strip()
        if recip_id not in self._paired_devices:
            raise PermissionError(f"Recipient device '{recip_id}' is not paired.")

        key = self._paired_devices[recip_id]
        raw_state_json = p2p_sync_engine.export_delta_payload()
        state_dict = json.loads(raw_state_json)
        mutations_count = len(state_dict.get("add_set", {})) + len(state_dict.get("remove_set", {}))

        # Generate 12-byte random IV/nonce for AES-GCM
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, raw_state_json.encode("utf-8"), None)

        payload_id = f"sync_{uuid.uuid4().hex[:12]}"
        now = time.time()

        # Compute HMAC signature over header and ciphertext
        sig_data = f"{payload_id}:{self.local_device_id}:{recip_id}:{now}:{base64.b64encode(ciphertext).decode()}".encode()
        signature = hmac.new(key, sig_data, hashlib.sha256).hexdigest()

        return EncryptedSyncPayload(
            payload_id=payload_id,
            sender_device_id=self.local_device_id,
            recipient_device_id=recip_id,
            nonce_b64=base64.b64encode(nonce).decode("utf-8"),
            ciphertext_b64=base64.b64encode(ciphertext).decode("utf-8"),
            signature=signature,
            timestamp=now,
            mutations_count=mutations_count,
        )

    def ingest_encrypted_delta(self, payload: EncryptedSyncPayload | dict[str, Any]) -> dict[str, Any]:
        """Validates, decrypts, and applies an incoming peer epistemic memory payload."""
        if isinstance(payload, dict):
            payload = EncryptedSyncPayload.from_dict(payload)

        sender_id = payload.sender_device_id.strip()
        if sender_id not in self._paired_devices:
            raise PermissionError(f"Sender device '{sender_id}' is not paired.")

        key = self._paired_devices[sender_id]

        # 1. Anti-Replay: Check for seen payload IDs
        if payload.payload_id in self._seen_payload_ids:
            raise ValueError(f"Replay attack detected: Payload '{payload.payload_id}' was already processed.")

        # 2. Anti-Replay: Check timestamp skew
        now = time.time()
        if abs(now - payload.timestamp) > self.MAX_TIMESTAMP_SKEW_SEC:
            raise ValueError(f"Payload timestamp skew ({abs(now - payload.timestamp):.1f}s) exceeds window of {self.MAX_TIMESTAMP_SKEW_SEC}s.")

        # 3. Verify HMAC signature
        expected_sig_data = f"{payload.payload_id}:{sender_id}:{payload.recipient_device_id}:{payload.timestamp}:{payload.ciphertext_b64}".encode()
        expected_sig = hmac.new(key, expected_sig_data, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(payload.signature, expected_sig):
            raise PermissionError("Cryptographic signature verification failed: Payload may be tampered.")

        # 4. Decrypt AES-256-GCM ciphertext
        nonce = base64.b64decode(payload.nonce_b64)
        ciphertext = base64.b64decode(payload.ciphertext_b64)
        aesgcm = AESGCM(key)
        try:
            decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
            raw_state_json = decrypted_bytes.decode("utf-8")
        except Exception as ex:
            raise PermissionError(f"AES-GCM decryption failed: {ex}") from ex

        # 5. Merge CRDT delta into local epistemic store
        mutations_applied = p2p_sync_engine.ingest_peer_payload(raw_state_json)
        self._seen_payload_ids.add(payload.payload_id)

        # 6. Audit Trail
        logger.info(
            f"[EpistemicSync] Successfully synced with peer '{sender_id}'. "
            f"Mutations applied: {mutations_applied} (Payload ID: {payload.payload_id})"
        )

        return {
            "status": "success",
            "sender_device_id": sender_id,
            "payload_id": payload.payload_id,
            "mutations_applied": mutations_applied,
            "timestamp": now,
        }


# Global Epistemic P2P Sync Coordinator Singleton
epistemic_sync_coordinator = EpistemicP2PSyncCoordinator()
