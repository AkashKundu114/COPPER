# COPPER — All-Agent Dataset Generation & Fine-Tuning

Generalizes the original `copper_dataset_gen.py` (orchestrator-only) and
`aeon_dataset_gen.py` (one hand-written agent) into a single data-driven
framework that produces a standalone fine-tuning dataset — and a fine-tuned
LoRA adapter — for **every** COPPER sub-agent, plus COPPER itself.

📖 **Docs:**
[Setup Guide](./docs/SETUP_GUIDE.md) (how to run this, end to end) ·
[Cloud GPU Training Guide](./docs/CLOUD_GPU_TRAINING_GUIDE.md) (renting a
GPU, provider walkthroughs, cost estimates, troubleshooting)

This README covers what the framework contains and how it's put together.
For step-by-step commands, start with the Setup Guide instead.

## Roster: 30 agents + COPPER

The original codebase's routing table named 26 implemented agents plus
`GLITCH` (referenced but never given a dataset generator). This framework
fills that gap and adds 3 more — **MNEMONIC** (memory/recall), **VAULT**
(credentials/secrets), and **POLYGLOT** (translation/localization) — to
reach a literal **30 specialist agents**, plus **COPPER** itself as the
orchestrator sitting above all of them.

| Model tier | Agents |
|---|---|
| MODEL_1_CORE | CHRONOS, MNEMONIC |
| MODEL_2_CODE | CYPHER, CRUCIBLE, FORGE, NEXUS, ARGUS |
| MODEL_3_OS | AXIS, ATLAS, KINETIC, PULSE, ZENITH, LEDGER, VAULT |
| MODEL_4_VISION | HAWK, TALON, PORTAL, IRIS |
| MODEL_5_WEB | RAPTOR, PHANTOM, VANGUARD, AETHER, BEACON, DIRECTOR, GLITCH |
| MODEL_6_AUDIO | SONAR, ORACLE, HERMES, AEON, POLYGLOT |

## COPPER: the orchestrator

COPPER doesn't have intent templates of its own — it draws directly from all
30 agents' intent banks in `agent_configs.py`, so its training data is
guaranteed to only ever route to requests an agent can actually handle.

**Relationship model: JARVIS to Iron Man.** COPPER isn't a query box — it's a
standing operational layer. You set the objective; COPPER decides whether to
answer directly or delegate, and to whom, addressing you directly ("sir")
with dry wit and quiet competence, never restating the obvious.

`copper_orchestrator_dataset_gen.py` generates five kinds of training record:

| Type | Frequency | What it teaches |
|---|---|---|
| Standard delegation | ~72% | Route a request to the one correct specialist agent |
| Direct answer (`next_agent: COMPLETE`) | ~10% | Answer directly without delegating when a specialist isn't needed |
| Multi-agent delegation | ~10% | Chain two agents for a task that needs both (e.g. IRIS extracts data, then TALON clicks it into a form) |
| `SYSTEM_MODE: BOSS` (silent) | ~8% | When the user is clearly in a hurry ("just do it", "no time to explain"), skip the dialogue and execute silently — payload only |
| Multi-turn conversation | ~10% | Two routing decisions back-to-back in one session, for conversational coherence |

```bash
python copper_orchestrator_dataset_gen.py --size 2500 --outdir ./dataset/COPPER
python finetune_agent.py --agent COPPER --model mistralai/Mistral-7B-Instruct-v0.3
```

Sample record (standard delegation):
```json
{"messages": [
  {"role": "system", "content": "You are COPPER, the master orchestrator ... your relationship to the user is JARVIS to Iron Man ..."},
  {"role": "user", "content": "Log into a competitor's product page using Playwright"},
  {"role": "assistant", "content": "[DIALOGUE] Sending this to PHANTOM — shouldn't take long.\n\n[TECHNICAL_PAYLOAD] {\"next_agent\": \"PHANTOM\", \"next_model\": \"MODEL_5_WEB\", \"system_status\": \"PROCESSING\", \"task_context\": {...}, \"dialogue_transcript\": [...]}"}
]}
```

Sample record (BOSS mode — silent execution):
```json
{"messages": [
  {"role": "user", "content": "Emergency — compose a formal email about the search service — now."},
  {"role": "assistant", "content": "[TECHNICAL_PAYLOAD] {\"next_agent\": \"HERMES\", \"next_model\": \"MODEL_6_AUDIO\", \"system_status\": \"PROCESSING\", \"SYSTEM_MODE\": \"BOSS\", \"task_context\": {...}, \"dialogue_transcript\": []}"}
]}
```

## Files

| File | Purpose |
|---|---|
| `shared_vocab.py` | Shared placeholder banks (tech stacks, errors, dirs, people, etc.) used by every agent's intent templates |
| `agent_configs.py` | The single source of truth: each agent's system prompt, personality, 6-8 intent templates, dialogue lines, and technical-payload schema/builder |
| `generate_agent_dataset.py` | Generic CLI — generates one agent's dataset |
| `generate_all_agents.py` | Runs the above for all 30 agents (or a subset) in one call |
| `copper_orchestrator_dataset_gen.py` | Generates COPPER's own orchestrator dataset (delegation, direct answers, multi-agent chains, BOSS mode) |
| `finetune_agent.py` | Generalized QLoRA/SFT trainer (based on `finetune_copper.py`) — pass `--agent NAME` (including `COPPER`) and it infers train/val paths and output dir |
| `launch_finetune_all.sh` | Loops dataset-gen + fine-tune across all 30 agents plus COPPER, with GPU-tier presets (24gb/40gb/80gb) |
| `requirements_finetune.txt` | Same training deps as the original pipeline |
| `dataset/<AGENT>/` | Generated data per agent: `<agent>_train.jsonl`, `<agent>_val.jsonl`, `<agent>_test.jsonl`, `<agent>_dataset_manifest.json` |
| `dataset/COPPER/` | COPPER's own orchestrator dataset: `copper_{train,val,test}.jsonl`, `copper_dataset_manifest.json` |
| `dataset/all_agents_manifest.json` | Combined record counts across all 30 agents |

## Quick start

Generate every agent's dataset (1500 records each) plus COPPER's own (2500 records):

```bash
python generate_all_agents.py --size 1500 --outdir ./dataset
python copper_orchestrator_dataset_gen.py --size 2500 --outdir ./dataset/COPPER
```

Generate just one agent, or a custom size (1000-2000 recommended):

```bash
python generate_agent_dataset.py --agent AXIS --size 2000 --outdir ./dataset/AXIS
```

Fine-tune one agent (auto-locates its dataset from the convention above):

```bash
pip install -r requirements_finetune.txt
python finetune_agent.py --agent AXIS --model mistralai/Mistral-7B-Instruct-v0.3
python finetune_agent.py --agent COPPER --model mistralai/Mistral-7B-Instruct-v0.3
```

Fine-tune every agent (and COPPER) end-to-end (generates data if missing, then trains, one adapter at a time):

```bash
bash launch_finetune_all.sh 24gb                       # all 30 agents + COPPER
bash launch_finetune_all.sh 80gb AXIS,AEON,CYPHER        # just three agents, bigger GPU profile (COPPER always runs last)
```

This produces **31 separate LoRA adapters** (`./<agent>-lora/final_adapter`
for each of the 30 specialists, plus `./copper-lora/final_adapter` for the
orchestrator) — COPPER learns to route, each specialist learns its own
domain in depth.

## Data format

Identical convention to the original scripts:

```json
{"messages": [
  {"role": "system",    "content": "You are AXIS, the shell and system-administration agent of COPPER. ..."},
  {"role": "user",      "content": "Restart the docker service"},
  {"role": "assistant", "content": "[DIALOGUE] Executing shell commands. Proceeding with caution.\n\n[TECHNICAL_PAYLOAD] {\"action\": \"execute_shell_command\", \"command\": \"systemctl restart docker\", \"working_dir\": \"/opt/service\", \"requires_confirmation\": true}"}
]}
```

About 12% of records (`--multiturn_pct`) include a follow-up user/assistant
turn to teach basic multi-turn coherence, similar to `aeon_dataset_gen.py`'s
conflict-check follow-ups.

## Extending

To add a 31st agent, add one entry to `AGENT_CONFIGS` in `agent_configs.py`:

```python
AGENT_CONFIGS["YOURAGENT"] = {
    "role": "the ... agent of COPPER. You ...",
    "personality": "...",
    "payload_fields": "action, field_a, field_b",
    "intents": ["Do {task} for me", "..."],       # 6-10 templates
    "dialogue": ["In-character reaction 1", "..."], # 5-8 lines
    "payload_fn": lambda slots, text, rng: {"action": "...", "field_a": slots.get("task")},
}
```

and add its model tier to `MODEL_MAP`. Everything else (generation,
splitting, manifest, fine-tuning) works automatically — no other code
changes needed.
