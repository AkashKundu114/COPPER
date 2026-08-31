# C.O.P.P.E.R. — Wake-Word Voice Activation & Tiered Inference Master Prompt

**Status:** New engineering spec (Phase 2.5, sits between "Guardian Engine & Zero-Trust Firewall" and "Multi-Device Sync" on the roadmap).
**Supersedes:** Nothing — this is additive. It does not change the Guardian, Data Firewall, or Epistemic Memory specs.
**Companion doc:** `COPPER_CONSCIOUSNESS_MASTER_PROMPTS.md` (this spec assumes that runtime system prompt is already in place; the Gatekeeper persona below is a *sibling* of COPPER, not a replacement).

---

## 1. Problem Statement

Today COPPER only "wakes up" when the user clicks the mic button or types. Two things are missing:

1. **Ambient activation.** A real personal-OS assistant should be listening for its name ("Hey COPPER" / "COPPER") the way Google Assistant or Alexa does, without the user touching the keyboard.
2. **VRAM discipline.** The current design loads whichever 7B–8B model the router picks, for every single turn, on an 8GB laptop GPU. That's fine for one active conversation, but it means:
   - Every "hello" or "what time is it" pays the multi-second load time of a full 7B model if it isn't already warm.
   - There is no small, always-resident brain to do wake-word confirmation, routing, and trivial replies without ever touching the big models.

This spec defines both: an offline wake-word pipeline, and a **tiered inference architecture** where exactly one small "Gatekeeper" model is pinned in VRAM at all times, and every heavier model is loaded on demand and unloaded after idle.

---

## 2. Design Principles (carried over from the rest of COPPER)

- **100% local, zero cloud egress** — the wake-word engine and the Gatekeeper model both run fully offline. No hotword audio ever leaves the device.
- **One pinned resident model, everything else transient.** VRAM budget is a first-class constraint, not an afterthought.
- **Guardian and Data Firewall are not bypassed** by voice. A voice-originated request goes through the exact same `GuardianEngine.evaluate()` and `classify_and_redact()` paths as a typed one — the wake word only changes *how a turn starts*, never what's allowed to happen in it.
- **Graceful degradation.** If the acoustic wake-word engine isn't installed/trained yet, COPPER falls back to a cheap phrase-spotting mode using infrastructure it already has (`faster-whisper` tiny), rather than doing nothing.

---

## 3. System Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │   ALWAYS-ON, ZERO-GPU-COST LISTENING LAYER   │
                     │   (CPU only — this never touches the GPU)    │
                     │                                               │
                     │  Mic stream → VAD (webrtcvad) → Acoustic     │
                     │  wake-word model (openWakeWord, ~1-2% CPU)   │
                     └───────────────────┬───────────────────────────┘
                                         │ "hey_copper" trigger (score > 0.5)
                                         ▼
                     ┌─────────────────────────────────────────────┐
                     │   GATEKEEPER — the ONE model pinned in VRAM  │
                     │   Qwen2.5-0.5B-Instruct (Q4_K_M, ~380 MB)    │
                     │   keep_alive = -1 (never unloads)            │
                     │                                               │
                     │  1. Confirmation pass on the STT'd phrase     │
                     │     ("was this actually meant for me?")       │
                     │  2. Fast intent routing (reuses the existing  │
                     │     DynamicRoutingMemory + regex cascade —    │
                     │     the Gatekeeper LLM is ONLY the fallback   │
                     │     for genuinely ambiguous phrasing)          │
                     │  3. Answers trivial turns directly (greetings,│
                     │     clock/date, "are you there") with NO      │
                     │     heavy-model load at all                    │
                     └───────────────────┬───────────────────────────┘
                                         │ needs a specialist
                                         ▼
                     ┌─────────────────────────────────────────────┐
                     │   ON-DEMAND HEAVY TIER (7B–8B, GPU-resident   │
                     │   only while working)                         │
                     │   AXIS (coding) · FORGE (automation) ·        │
                     │   OMNI (research) · SCRIBE (documents, new)   │
                     │   keep_alive = idle-timeout (default 4 min)   │
                     └───────────────────┬───────────────────────────┘
                                         │ idle timeout OR explicit
                                         │ "unload models" / VRAM pressure
                                         ▼
                     ┌─────────────────────────────────────────────┐
                     │   Ollama unloads the heavy model.             │
                     │   Gatekeeper remains resident. VRAM returns   │
                     │   to ~0.5-1.0 GB baseline.                    │
                     └─────────────────────────────────────────────┘
```

**Key point:** the acoustic wake-word stage costs *no GPU time whatsoever*. It's a small CPU-only ONNX model running continuously on the raw audio stream. The GPU only wakes up once a wake word has already fired, and even then the first thing that runs is the tiny 0.5B Gatekeeper — not a 7B model.

---

## 4. Wake-Word Engine

### 4.1 Primary path — openWakeWord (recommended)
- Library: `openwakeword` (Apache-2.0, fully offline, ONNX runtime backend, CPU-only).
- Ships with pretrained wake words ("hey jarvis", "alexa", etc.) as a bootstrap, but **"Hey COPPER" requires a custom-trained model** — openWakeWord provides a training notebook that synthesizes training audio from TTS + augmentation, no need to hand-record thousands of samples. Budget ~1–2 hours of one-time setup to produce `hey_copper.onnx` and drop it into `ai-models/wakeword/`.
- Runtime cost: ~1–3% of one CPU core, continuous, zero VRAM.

### 4.2 Fallback path — phrase-spotting via faster-whisper (works today, zero new deps)
Since `faster-whisper` (tiny/base, CPU, int8) is already in the stack for STT, the fallback listener:
1. Buffers audio in ~1.5s rolling windows using `webrtcvad` to only transcribe when speech is present (skips silence, keeps CPU cost low).
2. Runs `WhisperModel("tiny", device="cpu", compute_type="int8")` on each speech window.
3. Regex-matches the transcript against `r"\b(hey\s+)?copper\b"` (case-insensitive).
4. On match, the rest of that same audio window (post wake-word) plus the next capture window is treated as the command — avoids a second "listening" round-trip when the user says "Hey Copper, what's my schedule" in one breath.

This fallback is intentionally simple and a little wasteful of CPU, but requires zero new pretrained wake-word assets, so it's the correct default until `hey_copper.onnx` exists.

### 4.3 Voice Activity Detection (VAD)
`webrtcvad` gates both paths so neither the acoustic model nor the whisper fallback runs against pure silence — this is what keeps "always listening" from being a real CPU/battery cost on a laptop.

### 4.4 Privacy contract
- Raw audio never touches disk except the rolling in-memory buffer (never persisted) and the already-existing transient STT recording flow once a real command starts.
- No audio, transcript, or wake-word telemetry leaves the device. This is enforced the same way the rest of COPPER enforces zero-egress: no network call exists in this code path at all, not "network call gated by a flag."

---

## 5. The Gatekeeper Model

### 5.1 Why a *separate* model from the existing router
COPPER already has `DynamicRoutingMemory` + regex cascade in `agent_router.py`, which resolves ~99% of requests in under a millisecond with zero LLM call. The Gatekeeper does **not** replace that — it sits in front of it as the always-resident *voice front door*, and is the LLM fallback for the ~1% of routing decisions the regex cascade can't confidently resolve (previously this fell through to `_llm_subagent_route`, which cold-loads whatever `subagents.router` model is configured). The change here is just: make that fallback model **permanently resident** instead of loaded per-call, and give it two extra jobs:

1. **Wake confirmation** — "Copper, uh, never mind" or background TV audio saying "copper wire" should not open a full turn. The Gatekeeper does a cheap yes/no classification on the STT'd phrase before a turn is opened.
2. **Trivial-turn short-circuit** — greetings, "what time is it", "are you there", "thank you" get answered directly by the Gatekeeper (it already has live temporal context injected, same as CHRONOS) without ever touching a 7B model.

### 5.2 Model choice
`Qwen2.5-0.5B-Instruct` (Q4_K_M, ~380 MB, already listed in [`../technical/model-selection.md`](../technical/model-selection.md) as the `firewall` subagent model). Reusing a model already in the fleet means no new download, and 0.5B is small enough that `keep_alive=-1` costs under half a GB of VRAM permanently — well inside the "Available Safety Headroom" already budgeted in [`../benchmarks.md`](../benchmarks.md).

### 5.3 Gatekeeper system prompt

```text
You are COPPER's Gatekeeper — the always-on front door.
You run permanently in VRAM so COPPER can respond instantly to its wake word.
You do three things, in order, and nothing else:

1. CONFIRM: given a transcript that followed a wake-word detection, decide if it
   was genuinely addressed to COPPER (a real request/question/greeting) or noise
   (background speech, TV, a wake word said in passing). Reply CONFIRM or IGNORE.

2. SHORT-CIRCUIT: if the request is trivial (greeting, current time/date, "are
   you there", thanks/goodbye, a simple factual one-liner you already know),
   answer it directly in COPPER's voice — brief, warm, no hedging. Do not invoke
   a specialist for these.

3. ESCALATE: for anything else, output only the target agent's lowercase name
   from this list: [coding, automation, reminder, research, vision, planner,
   scribe]. Do not explain the routing decision — just the one word.

You are not the full COPPER personality. You are the fast reflex layer in front
of it. When you escalate, the specialist model carries the actual conversation
and personality forward from there.
```

### 5.4 VRAM/keep-alive policy

| Tier | Model(s) | `keep_alive` | Loaded when |
|---|---|---|---|
| Gatekeeper (pinned) | Qwen2.5-0.5B-Instruct | `-1` (forever) | Backend startup |
| Heavy specialists | Llama-3.1-8B, Qwen2.5-Coder-7B, Mistral-7B, DeepSeek-R1-7B, Qwen2-VL-7B, **SCRIBE model (new)** | `240s` idle timeout (configurable) | First routed request needing that agent |
| Vision-fast / micro-subagents | Qwen2-VL-2B and the 360M–3B subagent fleet | `60s` idle timeout | On demand, same as today |

This is implemented as a small tier manager (`model_tier_manager.py`, added in this patch) that wraps the existing `ollama_client` calls: it always issues the Gatekeeper's own chat calls with `keep_alive: -1`, and issues every other model's calls with a numeric `keep_alive` window, plus a background sweep that calls Ollama's `keep_alive: 0` unload trick (the same mechanism `unload_all_models()` already uses) once a heavy model's idle window has elapsed — but it explicitly **never unloads the Gatekeeper**.

---

## 6. Document Generation Capability (SCRIBE)

### 6.1 What was missing
COPPER could read and index documents (`document_service.py`) but had no way to *produce* one — no Word doc, slide deck, spreadsheet, or PDF came out the other end, even though the coding agent could write arbitrary files via the Forge sandbox.

### 6.2 New agent: SCRIBE
- `AgentType.DOCUMENT` added to `constants.py`.
- `document_agent.py` (added in this patch): takes a natural-language request ("write this up as a one-page PDF report", "turn this into a slide deck", "put these numbers in a spreadsheet"), asks the currently-resident heavy chat/reasoning model to draft the *content* (text, headings, table data, slide outline), then assembles the actual file using local, offline Python libraries — no new LLM weights required for this part, just new pip packages:
  - `python-docx` → `.docx`
  - `python-pptx` → `.pptx`
  - `openpyxl` → `.xlsx`
  - `reportlab` → `.pdf`
- Output lands in `data/generated_documents/` (mirrors the existing `frontend/public/generated` pattern used by the image agent) and the agent's response includes a local file link the frontend can surface as a download chip, the same way `DocumentReaderModal` already renders uploaded documents.
- Routing keywords added to `agent_router.py`: "write me a word doc", "make a pdf", "turn this into a spreadsheet", "build a slide deck", "export as docx/pptx/xlsx/pdf", etc. — same weighted-regex pattern already used for the other agents.

### 6.3 Guardian & Firewall integration
File writes from SCRIBE go through the same `is_consequential_action` / Guardian check path used by automation and coding — writing a *new* file in the sandboxed output directory is Level 0 (Execute), but SCRIBE never overwrites arbitrary user paths, only writes inside `data/generated_documents/`, so it can't trigger the destructive-action triggers by construction.

---

## 7. WebSocket / API Surface Additions

```
GET  /api/v1/voice/wake/status         -> { listening: bool, engine: "openwakeword"|"whisper_fallback", gatekeeper_resident: bool }
POST /api/v1/voice/wake/enable         -> starts the background listener
POST /api/v1/voice/wake/disable        -> stops it (mic fully released)
WS   /api/v1/voice/wake/stream         -> pushes { type: "wake_detected" } to the frontend the instant
                                           the wake word fires, so the UI can show a listening pulse
                                           before STT/response even begins
```

The existing `/api/v1/chat/ws/{session_id}` event sequence (`copper_thinking` → `route_decision` → ... → `done`) is unchanged; wake-word activation simply becomes an alternate way of populating `user_message` on that same socket, with `source: "voice_wake"` added to the payload for audit-log attribution.

---

## 8. Rollout Sequence

1. Add `openwakeword`, `webrtcvad`, `python-docx`, `python-pptx`, `openpyxl`, `reportlab` to `backend/requirements.txt`.
2. Land `model_tier_manager.py`, `wake_word_service.py`, `document_agent.py`, and the `wake.py` routes (all included in this patch).
3. Update `constants.py` (`AgentType.DOCUMENT`), `agent_router.py` (SCRIBE keywords), `chat_service.py` (`AGENT_MAP` entry), `config.py` (Gatekeeper/keep-alive settings) — see `INTEGRATION_CHECKLIST.md`.
4. Update `ai-models/models_manifest.json` with the `gatekeeper` and `subagents.document_drafting` entries (included in this patch).
5. Ship with the whisper-tiny fallback wake listener enabled by default (`WAKE_WORD_ENGINE=whisper_fallback`).
6. Train `hey_copper.onnx` via the openWakeWord notebook, drop it in `ai-models/wakeword/`, flip `WAKE_WORD_ENGINE=openwakeword` in settings once validated.

## 9. Success Criteria

- Backend idle-state VRAM usage stays at the Gatekeeper's ~0.5 GB footprint, not the ~4.5 GB a resident 7B model would cost.
- Saying "Hey COPPER" with no prior interaction produces a spoken/text acknowledgment within the Gatekeeper's own latency budget (sub-second, since it never leaves VRAM) even before a heavy model is asked to do anything.
- A request that needs a specialist (e.g. "Hey COPPER, refactor this function") still gets the full quality of the existing AXIS pipeline — the Gatekeeper's only job was getting the turn started and routed correctly.
- SCRIBE can produce a `.docx`, `.pptx`, `.xlsx`, and `.pdf` from a plain-language request, fully offline, landing in `data/generated_documents/`.
