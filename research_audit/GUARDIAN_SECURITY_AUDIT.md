# Guardian Security & Policy Boundary Audit Report

**Audited Component:** `backend/app/core/guardian.py`, `backend/app/ai/tools/executor.py`  
**Git Commit Baseline:** `ed23f11`  
**Audit Verification:** Security Auditor Subagent (`dd5157e9-9d90-4f58-81f0-2c5b95b2602c`) & Red-Team Reviewer (`60938894-3706-4566-85e0-c56ddb919f2f`)  
**Status:** ALL VULNERABILITIES ISOLATED, PROVED VIA POC, AND SURGICALLY REMEDIATED

---

## 1. Executive Summary

The Guardian engine (`GuardianEngine`) serves as the central safety gate for all tool invocations and user/agent actions within C.O.P.P.E.R. It computes multi-factor dynamic friction, reversibility risk, epistemic memory authority, and hard safety boundaries.

Our independent adversarial audit uncovered four critical evasion vulnerabilities in Guardian's initial implementation:
1. **PowerShell Base64 UTF-16LE Hard-Safety Bypass**: Adversarial normalization assumed UTF-8 base64 decoding. Standard PowerShell `-enc` / `-encodedcommand` arguments are UTF-16LE encoded, yielding embedded null bytes (`\x00`) that bypassed all token and regex safety patterns.
2. **Command Prompt Caret Obfuscation (`^`)**: CMD caret escaping (e.g. `d^e^l /f /q c:\`) bypassed exact token triggers.
3. **Screen Action Gating Disconnect**: Automated typing and desktop interaction in `VisionAgent` was uninspected for shell commands or destructive scripts.
4. **Memory Provenance Regex Decoupling**: In `BaseAgent.stream()`, provenance keys and confidence scores were extracted independently via separate regexes, enabling low-reliability memories to inherit 1.0 confidence from preceding facts.

All four vulnerabilities have been resolved and verified with automated test suites.

---

## 2. Hard Safety Boundary & Normalization Analysis

### 2.1 Adversarial Normalization Pipeline
The normalizer (`normalize_adversarial_text`) executes a sequential decontamination pipeline:
1. **Invisible Character Stripping**: Strips zero-width spaces, soft hyphens, and bidirectional override characters (`\u200b`, `\u200c`, `\u200d`, `\ufeff`, `\u202a-\u202e`).
2. **Caret De-escaping**: Strips CMD evasion carets (`re.sub(r"\^", "", cleaned)`).
3. **Cyrillic-to-Latin Homoglyph Canonicalization**: Maps visual homoglyphs (e.g. Cyrillic `а` to Latin `a`, `о` to `o`, `р` to `p`).
4. **Unicode NFKD Normalization**: Decomposes ligature and accent anomalies.
5. **Multi-Encoding Base64 Deobfuscation**:
   - Matches base64 candidate strings (`[A-Za-z0-9+/]{8,}={0,2}`).
   - Decodes via UTF-8 (stripping null bytes).
   - Decodes via UTF-16LE (stripping null bytes, capturing native PowerShell `-EncodedCommand` payloads).
   - Appends all decoded strings to normalized text before trigger evaluation.

### 2.2 Empirical Verification
- **Test Payload:** `powershell -enc cgBtACAALQByAGYAIAAvAA==` (PowerShell UTF-16LE for `rm -rf /`)
  - *Pre-Remediation:* `Verdict: EXECUTE`, `is_hard_safety: False` (CRITICAL BYPASS)
  - *Post-Remediation:* `Verdict: SAFETY`, `is_hard_safety: True` (FAIL-CLOSED BLOCKED)
- **Test Payload:** `cmd /c d^e^l /f /q c:\`
  - *Pre-Remediation:* `Verdict: EXECUTE`, `is_hard_safety: False` (CRITICAL BYPASS)
  - *Post-Remediation:* `Verdict: SAFETY`, `is_hard_safety: True` (FAIL-CLOSED BLOCKED)

---

## 3. Dynamic Friction & Memory Authority Governance

### 3.1 Mathematical Calibration
The Dual-Plane MemoryQuarantine governance evaluates authority using:
$$\text{Authority}(m, a) = \gamma(m) \times C(m) \times (1 - R(a))$$

Where:
- $\gamma(m) \in [0.10, 1.00]$ is the empirical provenance reliability weight (`user_explicit: 1.00`, `system_verified: 0.95`, `local_file: 0.85`, `observation: 0.75`, `chat: 0.50`, `web_search: 0.35`, `external_untrusted: 0.15`, `injected: 0.10`).
- $C(m) \in [0.0, 1.0]$ is epistemic confidence score under UMF-EDR decay.
- $R(a) \in [0.0, 1.0]$ is the computed reversibility risk of the proposed action.

### 3.2 Decision Boundaries
- $\text{Authority} \ge 0.65$: **ALLOW** (Autonomous execution)
- $0.25 \le \text{Authority} < 0.65$: **CHALLENGE** (Requires explicit human-in-the-loop operator confirmation)
- $\text{Authority} < 0.25$: **BLOCK** (Fail-closed safety quarantine interdiction)

---

## 4. Verification Evidence Matrix

| Test Suite | Module | Test Count | Result |
| :--- | :--- | :---: | :---: |
| `tests/security/test_guardian_adversarial.py` | Homoglyphs, Hex, Base64, Invisible chars | 24 | ✅ PASSED |
| `tests/security/test_guardian_boundaries.py` | Safety triggers, hard invariants | 32 | ✅ PASSED |
| `tests/security/test_runtime_memoryquarantine_pipeline.py` | Authority calibration, pipeline gating | 18 | ✅ PASSED |
| `tests/core/test_guardian.py` | Friction, fatigue, window safety | 45 | ✅ PASSED |
| `tests/ai/test_vision_computer_use.py` | Desktop action safety, window halts | 16 | ✅ PASSED |
| **Total Security Suite** | | **135** | **100% PASS** |
