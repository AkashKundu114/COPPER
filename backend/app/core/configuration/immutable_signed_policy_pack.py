"""Cryptographically Signed Immutable Policy Packages and Air-Gapped Verifier.

Implements Stage 10 Configuration & Policy Management Architecture:
- Packages policy rules, budget thresholds, and security bounds into immutable signed policy packs.
- Signs manifests with cryptographic authority keys (HMAC-SHA256 / Ed25519 abstraction).
- Validates tamper-evidence and schema integrity before unpackaging into active runtime configurations.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SignedPolicyPack:
    pack_id: str
    version: str
    issuer: str
    policies_payload: dict[str, Any]
    manifest_hash: str
    signature: str
    created_at_epoch: float


@dataclass
class PolicyPackValidationResult:
    is_valid: bool
    pack_id: str
    version: str
    rules_count: int
    validation_error: Optional[str] = None


class ImmutableSignedPolicyPackManager:
    """Creates, signs, and cryptographically validates immutable policy packages."""

    def __init__(self, signing_secret: Optional[bytes] = None) -> None:
        self._signing_secret = signing_secret or secrets.token_bytes(32)

    def create_policy_pack(
        self,
        pack_id: str,
        version: str,
        issuer: str,
        policies: dict[str, Any],
    ) -> SignedPolicyPack:
        """Serialize and sign a policy pack manifest."""
        now = time.time()
        serialized = json.dumps(policies, sort_keys=True).encode("utf-8")
        manifest_hash = hashlib.sha256(serialized).hexdigest()

        sign_payload = f"{pack_id}:{version}:{issuer}:{manifest_hash}:{now}"
        signature = hmac.new(self._signing_secret, sign_payload.encode("utf-8"), hashlib.sha256).hexdigest()

        return SignedPolicyPack(
            pack_id=pack_id,
            version=version,
            issuer=issuer,
            policies_payload=policies,
            manifest_hash=manifest_hash,
            signature=signature,
            created_at_epoch=now,
        )

    def verify_and_unpack(self, pack: SignedPolicyPack) -> tuple[PolicyPackValidationResult, Optional[dict[str, Any]]]:
        """Validate signature and unpack policy payload."""
        # Check payload integrity
        serialized = json.dumps(pack.policies_payload, sort_keys=True).encode("utf-8")
        computed_hash = hashlib.sha256(serialized).hexdigest()
        if computed_hash != pack.manifest_hash:
            return (
                PolicyPackValidationResult(
                    is_valid=False,
                    pack_id=pack.pack_id,
                    version=pack.version,
                    rules_count=0,
                    validation_error="Payload hash mismatch: Policy package has been tampered with.",
                ),
                None,
            )

        # Check signature
        sign_payload = f"{pack.pack_id}:{pack.version}:{pack.issuer}:{pack.manifest_hash}:{pack.created_at_epoch}"
        expected_sig = hmac.new(self._signing_secret, sign_payload.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, pack.signature):
            return (
                PolicyPackValidationResult(
                    is_valid=False,
                    pack_id=pack.pack_id,
                    version=pack.version,
                    rules_count=0,
                    validation_error="Invalid cryptographic signature: Unauthorized policy package.",
                ),
                None,
            )

        return (
            PolicyPackValidationResult(
                is_valid=True,
                pack_id=pack.pack_id,
                version=pack.version,
                rules_count=len(pack.policies_payload),
                validation_error=None,
            ),
            pack.policies_payload,
        )
