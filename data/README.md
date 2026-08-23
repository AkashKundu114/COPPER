# C.O.P.P.E.R. Local Data Architecture

This directory serves as the **100% local, zero-cloud-egress data persistence layer** for C.O.P.P.E.R. (Centralized Omnifunctional Personal Productivity and Execution Routine).

---

## Directory Layout & Data Classification

```
data/
├── memory/                      # SQLite relational state & episodic memory store
│   └── copper_memory.db         # User facts, hypotheses, agent versions & audit entries
├── vector/                      # ChromaDB persistent vector collections (8192-dim embeddings)
│   └── chroma/                  # Local semantic index for document RAG & memory recall
├── conversations/               # Multi-turn chat session histories and transcripts
├── audio/                       # Offline audio buffers and voice cache
│   ├── recordings/              # Temporary microphone input WAV files
│   └── cache/                   # Pre-synthesized Piper TTS audio voice snippets
├── screenshots/                 # Vision agent screen captures and OCR crops
├── reminders/                   # Active alarms, cron schedules & scheduler persistence
└── logs/                        # Structured application runtime logs & security audit trails
    ├── app/                     # Uvicorn backend, router telemetry, and system events
    └── security/                # Red team audit logs, data firewall redaction records
```

---

## Security, Privacy & Retention Policies

| Directory | Data Type | Classification | Retention / Decay Policy |
| :--- | :--- | :--- | :--- |
| **`memory/`** | Epistemic facts & hypotheses | `INTERNAL` | Facts: Permanent; Hypotheses: Bayesian confidence decay |
| **`vector/`** | 8192-dim vector embeddings | `INTERNAL` | Persistent until explicit user deletion |
| **`conversations/`** | Chat dialogue turns | `CONFIDENTIAL` | User-managed; 1-click purge in Security Center |
| **`audio/`** | Voice PCM / WAV streams | `TRANSIENT` | Auto-purged after transcription / playback |
| **`screenshots/`** | Vision screen crops | `CONFIDENTIAL` | Auto-deleted after visual tool parsing |
| **`reminders/`** | Tasks & calendar timers | `INTERNAL` | Persistent until completed or archived |
| **`logs/`** | Structured JSON logs | `AUDIT` | Rolling 30-day window; PII automatically redacted by Data Firewall |

---

## Zero-Cloud-Egress Guarantee
All files residing in `data/` are stored strictly on the local machine and excluded from Git tracking via [`.gitignore`](../.gitignore) to ensure personal data is never inadvertently pushed to public repositories.
