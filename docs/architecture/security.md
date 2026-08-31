# C.O.P.P.E.R. Data Firewall & Security Specification

This document details the security architecture, Data Firewall rules, privacy classification, and zero-trust cloud offloading mechanism.

---

## 1. Zero-Trust Data Privacy Philosophy

C.O.P.P.E.R. operates under a **Zero-Trust Local First Privacy Model**:
1. All user prompts and local files remain private within the local environment by default.
2. Local inference via Ollama is prioritized.
3. If cloud offloading is explicitly requested or required due to model capability limits, no payload leaves the machine without passing through the **Data Firewall**.
4. All external API transactions land in the human-readable **Security Center Audit Log**, featuring one-click export and instant permanent deletion (`delete-all`).

---

## 2. Data Firewall Architecture

![Zero-Trust Data Firewall Flow](../images/data_firewall_pipeline.png)
                                +---------------------------+
                                | User Prompt / File Input  |
                                +-------------+-------------+
                                              |
                                              v
                                +---------------------------+
                                |   Data Firewall Scanner   |
                                |  (Regex + NER Model)      |
                                +-------------+-------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
             [No Sensitivity]                                 [Sensitive PII Detected]
                     |                                                 |
                     v                                                 v
        +--------------------------+                      +--------------------------+
        | Pass Raw Payload to Cloud|                      |  Anonymizer Engine       |
        +--------------------------+                      |  Token Substitution      |
                                                          +------------+-------------+
                                                                       |
                                                                       v
                                                          +--------------------------+
                                                          |  Send Anonymized Payload |
                                                          |  to Cloud Provider       |
                                                          +------------+-------------+
                                                                       |
                                                                       v
                                                          +--------------------------+
                                                          |  Receive Cloud Response  |
                                                          +------------+-------------+
                                                                       |
                                                                       v
                                                          +--------------------------+
                                                          |  De-Anonymizer Engine    |
                                                          |  Re-hydrate Local Tokens |
                                                          +------------+-------------+
                                                                       |
                                                                       v
                                                          +--------------------------+
                                                          | Deliver Final Output to  |
                                                          | User & Write Audit Log   |
                                                          +--------------------------+
```

---

## 3. PII Classification & Detection Matrix

The Data Firewall scans all egress text across five sensitivity tiers:

| Sensitivity Tier | Data Types Detected | Detection Engine | Action |
| :--- | :--- | :--- | :--- |
| **Tier 0 (Credentials)** | API Keys, Passwords, RSA Private Keys, Tokens | Regex Patterns + Entropy Analysis | **HARD BLOCK / REDACT** |
| **Tier 1 (Identity)** | SSNs, Passport #s, Credit Card #s, Bank Accounts | Regex + Luhn Validation | **HARD BLOCK / REDACT** |
| **Tier 2 (Contact PII)**| Email Addresses, Phone Numbers, Physical Addresses | Spacy NER + Regex | **REDACT & TOKENIZE** |
| **Tier 3 (Personal)** | Names, Company Names, Custom User Keys | Epistemic Memory Match | **USER-CONFIGURED TOKENIZE** |
| **Tier 4 (Public/Code)**| Generic Code, General Queries, Open Docs | None | **ALLOW RAW EGRESS** |

---

## 4. Anonymization & Token Mapping

When sensitive data is detected, the Data Firewall generates ephemeral session-bound replacement tokens:

- `sk-proj-9a8b7c6d5e4f...` $\rightarrow$ `[REDACTED_API_KEY_01]`
- `john.doe@company.com` $\rightarrow$ `[REDACTED_EMAIL_01]`
- `+1 (555) 019-2834` $\rightarrow$ `[REDACTED_PHONE_01]`

### Ephemeral Vault Storage
Token mappings are stored temporarily in volatile Redis memory (`copper:firewall:session:{session_id}`) with a 15-minute TTL. Maps are discarded immediately after response synthesis or session termination.

---

## 5. Security Center & Audit Trail Integration

Every interaction evaluated by the Data Firewall generates a structured entry in the `audit_log` table:

```json
{
  "timestamp": "2026-08-12T17:20:00Z",
  "event_type": "FIREWALL_REDACTION",
  "severity": "WARN",
  "session_id": "sess_88192a",
  "cloud_provider": "OpenAI",
  "redaction_summary": {
    "api_keys_redacted": 1,
    "emails_redacted": 2,
    "tokens_mapped": ["REDACTED_API_KEY_01", "REDACTED_EMAIL_01"]
  },
  "raw_prompt_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### User Audit Controls
- **One-Click Export:** Exports all stored audit logs, memories, and interactions as an encrypted JSON archive.
- **Immediate Purge (`delete-all`):** Erases PostgreSQL records, ChromaDB vectors, and Redis keys instantly upon user request.
