# COPPER Framework — Implementation Guide

> **Documentation set:** [PRD](PRD.md) · [TRD](TRD.md) · [App Flow](APP_FLOW.md) · [UI/UX Brief](UI_UX_BRIEF.md) · [Backend Schema](BACKEND_SCHEMA.md) · [Implementation Guide](IMPLEMENTATION.md)

---

## 13. Project Directory Structure

```
copper_framework/
├── engine.py                  # Main orchestration loop
├── proactive_engine.py        # Morning greeting / check-in generator
├── clock_daemon.py            # Background alarm / reminder watcher
├── kinetic_daemon.py          # Weather & live stream poller
├── screen_diff.py             # Passive vision change detector
├── guardrails.py               # Command whitelist enforcer
│
├── state.json                 # Live active relay baton
├── copper.db                  # SQLite long-term memory
│
├── adapters/                  # LoRA personality adapter files
│   ├── copper_cop_adapter/
│   ├── cypher_dev_adapter/
│   ├── argus_qa_adapter/
│   ├── crucible_debug_adapter/
│   └── ...
│
├── chroma_store/              # ChromaDB vector database (ECHO)
│
├── frontend/                  # React + Tailwind dashboard
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── PulseBadge.jsx
│   │       ├── ActionBanner.jsx
│   │       ├── VRAMGauge.jsx
│   │       ├── DialogueLog.jsx
│   │       └── ConfirmModal.jsx
│   ├── api/
│   │   └── statePoller.js
│   └── tailwind.config.js
│
├── models/                    # Symlinks to Ollama model paths
└── requirements.txt
```

> Frontend component naming follows [UI/UX Brief §3](UI_UX_BRIEF.md#3-component-specifications); `tailwind.config.js` should be extended with the design tokens from [UI/UX Brief §2](UI_UX_BRIEF.md#2-design-tokens).

---

## 14. Core Engine Implementation

### 14.1 Main Orchestration Loop

`engine.py` — the core sequential hot-swap loop described in [App Flow §8](APP_FLOW.md#8-primary-execution-flow-state-persistent-hot-swap).

```python
import requests, json, gc, torch, time, sqlite3
from datetime import datetime
from guardrails import validate_command

OLLAMA_URL = "http://localhost:11434/api/chat"
STATE_FILE = "state.json"
DB_PATH = "copper.db"

MODEL_MAP = {
    "MODEL_1_CORE":   "qwen2.5-14b:q4_k_m",
    "MODEL_2_CODE":   "qwen2.5-coder:7b-q4_k_m",
    "MODEL_3_OS":     "qwen2.5:3b-q4_k_m",
    "MODEL_4_VISION": "florence-2:large",
    "MODEL_5_WEB":    "qwen2.5:7b-q4_k_m",
    "MODEL_6_AUDIO":  None  # CPU-bound, no Ollama
}

def flush_vram():
    """Purge all GPU memory between agent transitions."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    # Confirm VRAM is cleared via Ollama
    requests.post("http://localhost:11434/api/generate",
        json={"model": "qwen2.5-coder:7b", "keep_alive": 0, "prompt": ""})

def read_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"next_agent": "COPPER", "execution_logs": [], "dialogue_transcript": []}

def write_state(state: dict):
    """Atomic write to prevent state corruption."""
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    import os; os.replace(tmp, STATE_FILE)

def fetch_agent_profile(agent_id: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT system_role, personality_traits, humor_style, "
              "vocabulary_quirks FROM agent_profiles WHERE agent_id = ?", (agent_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return "You are a helpful AI assistant."
    return (f"CORE IDENTITY: {row[0]}\n"
            f"PERSONALITY: {row[1]}\n"
            f"HUMOR: {row[2]}\n"
            f"SPEECH PATTERNS: {row[3]}\n"
            f"CONSTRAINT: Maintain persona. Do not break character. Be concise.")

def run_agent(agent_id: str, model_key: str, task_context: str, state: dict) -> str:
    model_name = MODEL_MAP.get(model_key)
    if not model_name:
        raise ValueError(f"Unknown model key: {model_key}")

    # Build peer commentary context (unless Boss Mode)
    dialogue_ctx = ""
    if state.get("SYSTEM_MODE") != "BOSS":
        recent = state.get("dialogue_transcript", [])[-3:]
        dialogue_ctx = "\n".join([f"{d['agent']}: '{d['text']}'" for d in recent])

    system_prompt = fetch_agent_profile(agent_id)
    if dialogue_ctx:
        system_prompt += (f"\n\nCOWORKER LOG:\n{dialogue_ctx}\n"
                          f"Start with a brief reaction to your coworkers, "
                          f"then execute your task.")

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_context}
        ],
        "options": {"keep_alive": 0, "num_ctx": 4096}
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=300).json()
    return response["message"]["content"]

def log_execution(session_id, agent, model, task, output, status, ms):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO agent_execution_logs "
        "(session_id, agent_name, model_profile, task_given, task_output,"
        " execution_status, execution_time_ms) VALUES (?,?,?,?,?,?,?)",
        (session_id, agent, model, task, output, status, ms)
    )
    conn.commit(); conn.close()

def update_telemetry(state, agent, action, status="PROCESSING"):
    ts = datetime.now().strftime("%H:%M:%S")
    state["system_status"] = status
    state["telemetry"] = {"active_agent": agent, "current_action": action, "last_update": ts}
    state["execution_logs"].append(f"[{ts}] [{agent}] {action}")
    write_state(state)

# ---- MAIN LOOP ----
def run():
    state = read_state()
    while state.get("next_agent") != "COMPLETE":
        agent = state["next_agent"]
        model = state.get("next_model", "MODEL_1_CORE")

        update_telemetry(state, agent, f"Loading {agent}...")
        t_start = time.time()
        try:
            output = run_agent(agent, model, json.dumps(state.get("task_context", {})), state)
            ms = int((time.time() - t_start) * 1000)
            # Parse output and update state accordingly
            # (JSON parsing logic omitted for brevity)
            log_execution(state.get("session_id", ""), agent, model,
                          str(state.get("task_context")), output, "SUCCESS", ms)
        except Exception as e:
            update_telemetry(state, agent, f"CRASHED: {e}", status="CRASHED")
            log_execution(state.get("session_id", ""), agent, model, "", str(e), "FAILED", 0)
            state["next_agent"] = "COPPER"
        finally:
            flush_vram()
            state = read_state()  # Re-read fresh state after agent update

if __name__ == "__main__":
    run()
```

### 14.2 VRAM Flush Utility

`guardrails.py` — the command safety whitelist used by `validate_command()`, satisfying [TRD §7.6](TRD.md#76-tr-06-security-guardrails-axis--talon).

```python
BLOCKED_PATTERNS = [
    "rm -rf ", "rm -r /", "format ", "del /f", "del /s",
    "dd if=", "mkfs", ":(){:|:&};:", "chmod -R 777 /",
    "sudo rm ", "rmdir /s"
]

def validate_command(cmd: str) -> tuple[bool, str]:
    """Returns (is_safe, reason). Blocks high-risk shell patterns."""
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in cmd.lower():
            return False, f"Blocked: command contains '{pattern}'"
    return True, "OK"
```

### 14.3 Proactive Engine

`proactive_engine.py` — morning greeting synthesizer, supporting [PRD US-03](PRD.md#us-03-proactive-morning-greeting).

```python
import sqlite3
from datetime import datetime

def generate_proactive_context(db_path="copper.db") -> str:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        SELECT category, project_name, summary_details
        FROM episodic_memory
        ORDER BY last_activity_date DESC LIMIT 2
    """)
    projects = c.fetchall()

    c.execute("""
        SELECT task_type, payload, trigger_timestamp
        FROM temporal_tasks
        WHERE trigger_timestamp > ? AND is_completed = 0
        ORDER BY trigger_timestamp ASC LIMIT 1
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    upcoming = c.fetchone()
    conn.close()

    ctx = "SYSTEM CONTEXT FOR GREETING:\n"
    for cat, proj, details in projects:
        ctx += f"- Recent {cat} project '{proj}': {details}\n"
    if upcoming:
        ctx += f"- Upcoming: [{upcoming[0]}] '{upcoming[1]}' at {upcoming[2]}\n"

    ctx += ("\nINSTRUCTION: You are COPPER waking up. "
            "Do NOT say 'How can I help?'. Generate a specific, intelligent greeting "
            "referencing the context above. Ask a targeted question about a real ongoing "
            "project or mention an imminent schedule item naturally.")
    return ctx
```

### 14.4 Clock Daemon

`clock_daemon.py` — SQLite alarm watcher, satisfying [TRD §7.7](TRD.md#77-tr-07-background-daemon-requirements) and the interrupt flow in [App Flow §8.3](APP_FLOW.md#83-interrupt-flow-background-alarm--weather-trigger).

```python
import sqlite3, json, time
from datetime import datetime

STATE_FILE = "state.json"
DB_PATH = "copper.db"

def check_and_fire_alarms():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        SELECT task_id, task_type, payload
        FROM temporal_tasks
        WHERE trigger_timestamp <= ? AND is_completed = 0
    """, (now,))
    due = c.fetchall()

    for task_id, task_type, payload in due:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        state["next_agent"] = "COPPER"
        state["force_interrupt"] = True
        state["interrupt_data"] = f"{task_type}: {payload}"
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        conn.execute("UPDATE temporal_tasks SET is_completed=1 WHERE task_id=?", (task_id,))
        conn.commit()

    conn.close()

if __name__ == "__main__":
    print("[clock_daemon] Running. Polling every 60s.")
    while True:
        check_and_fire_alarms()
        time.sleep(60)
```

---

## 15. Fine-Tuning Pipeline

### 15.1 QLoRA Training with Unsloth

`finetune.py` — personality adapter training, satisfying [TRD §7.5](TRD.md#75-tr-05-lora-adapter-hot-swap) and [Implementation Phases — Phase 8](#17-implementation-phases).

```python
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
import json

# Load base model with 4-bit quantization
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit",
    max_seq_length=4096,
    load_in_4bit=True,
)

# Attach LoRA adapters (lightweight, ~30 MB output)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # LoRA rank
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)

# Training data format
# Each row: {"messages": [{"role": "system", "content": "[AGENT_PROFILE]"},
#                          {"role": "user", "content": "..."},
#                          {"role": "assistant", "content": "[DIALOGUE] ...\n[TECHNICAL_PAYLOAD] {...}"}]}

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,  # Load from JSONL
    dataset_text_field="text",
    max_seq_length=4096,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        lr_scheduler_type="cosine",
        output_dir="./adapters/cypher_dev_adapter",
        save_strategy="epoch",
    ),
)
trainer.train()
model.save_pretrained("./adapters/cypher_dev_adapter")
```

---

## 16. Deployment & Setup

### 16.1 Prerequisites

`requirements.txt`:

```
# Inference
ollama>=0.3.0
torch>=2.1.0
transformers>=4.40.0
accelerate>=0.28.0

# Agents / Automation
pyautogui>=0.9.54
pyperclip>=1.9.0
pygetwindow>=0.0.9
playwright>=1.44.0
opencv-python>=4.9.0
yt-dlp>=2024.5.0
faster-whisper>=1.0.0
kokoro>=0.3.0

# Database
chromadb>=0.5.0

# Backend
requests>=2.31.0
apscheduler>=3.10.0
watchdog>=4.0.0

# Frontend bridge
flask>=3.0.0

# Fine-tuning (cloud GPU only)
unsloth>=2024.6.0
trl>=0.9.0
peft>=0.11.0
```

### 16.2 Initial Setup Commands

`setup.sh`:

```bash
#!/bin/bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull required models
ollama pull qwen2.5-coder:7b-q4_k_m
ollama pull qwen2.5:3b-q4_k_m
ollama pull qwen2.5:7b-q4_k_m

# 3. Initialize SQLite database
python3 -c "
import sqlite3
conn = sqlite3.connect('copper.db')
# (Execute all CREATE TABLE statements from Backend Schema section)
conn.commit(); conn.close()
print('copper.db initialized.')
"

# 4. Install Python dependencies
pip install -r requirements.txt
playwright install chromium

# 5. Start background daemons
python3 clock_daemon.py &
python3 kinetic_daemon.py &

# 6. Start frontend
cd frontend && npm install && npm run dev &

echo 'COPPER Framework initialized. Run: python3 engine.py'
```

> Step 3 should execute the full `CREATE TABLE` and `CREATE INDEX` statements from [Backend Schema §12](BACKEND_SCHEMA.md#12-sqlite-database-schema-copperdb).

### 16.3 Ollama Model Configuration (Modelfile)

Context window cap enforcement, per [TRD §7.2](TRD.md#72-tr-02-context-window-enforcement):

```
FROM qwen2.5-coder:7b-q4_k_m

# Hard-cap context to 4096 tokens to prevent VRAM overflow
PARAMETER num_ctx 4096

# Immediately release VRAM after each inference call
PARAMETER keep_alive 0

# Temperature for balanced creative + technical output
PARAMETER temperature 0.7
```

---

## 17. Implementation Phases

| Phase | Features | Subsystems | RAM Cost |
|---|---|---|---|
| **Phase 1** | Core COPPER loop, `state.json` relay, SQLite setup, basic CLI | `engine.py`, `copper.db` | Baseline |
| **Phase 2** | React dashboard, pulse badge, telemetry stream, clipboard & window sync | `frontend/`, `pyperclip` | < 10 MB |
| **Phase 3** | Agent personalities, LoRA adapters, inter-agent dialogue | `adapters/`, `agent_profiles` table | < 5 MB |
| **Phase 4** | Proactive engine, episodic memory, morning greeting | `proactive_engine.py` | < 5 MB |
| **Phase 5** | Alarms, calendar, weather, interrupt flows | `clock_daemon.py`, `kinetic_daemon.py` | < 20 MB |
| **Phase 6** | Local media transcription, ChromaDB (ECHO), SONAR/AETHER pipeline | `chroma_store/`, faster-whisper | ~500 MB during use |
| **Phase 7** | Passive vision, screen diff, Boss Mode, security guardrails | `screen_diff.py`, `guardrails.py` | ~40 MB continuous |
| **Phase 8** | QLoRA fine-tuning on all 6 model profiles | Cloud GPU (Unsloth) | N/A (cloud) |
| **Phase 9** | 6-model specialist routing, full 30-agent deployment | Deterministic Model-Swap Router | Peak 5.2 GB VRAM |

---

## 18. Known Limitations & Mitigations

| Limitation | Impact | Mitigation |
|---|---|---|
| Sequential only | Slower total task completion | Acceptable; user trades speed for hardware safety |
| 14B model layer offload | Slower token generation | Q3_K_L quantization; accept latency for safety |
| Context window 4,096 tokens | Cannot handle very long documents inline | Pre-compress via ChromaDB RAG; summarize before passing |
| Florence-2 not in Ollama | Requires separate HF inference path | Implement as a separate Python subprocess alongside Ollama |
| LoRA adapter injection | Currently manual via API; hot-swap under 100ms target | Use `llama.cpp` `lora-scale` parameter in inference call |
| No real multi-agent memory | Agents only see last 3 dialogue turns | Episodic memory table compensates for long-term context |
| Whisper-tiny accuracy | Lower accuracy than large model | Acceptable for personal use; upgrade path to small/base |
