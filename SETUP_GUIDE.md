# Setup Guide — How to Run This

Everything you need to go from a fresh checkout to trained per-agent LoRA
adapters. For renting and configuring a GPU specifically, see
[`CLOUD_GPU_TRAINING_GUIDE.md`](./CLOUD_GPU_TRAINING_GUIDE.md) — this guide
covers the pipeline itself.

## 0. What's in this framework

```
agent_configs.py                     30 agents' system prompts, intents, dialogue, payload schemas
shared_vocab.py                      shared placeholder banks used by all agents' intent templates
generate_agent_dataset.py            generate ONE agent's dataset
generate_all_agents.py               generate ALL 30 agents' datasets in one call
copper_orchestrator_dataset_gen.py   generate COPPER's own (orchestrator) dataset
finetune_agent.py                    QLoRA/SFT fine-tune, generic across agents (and COPPER)
launch_finetune_all.sh               generate + fine-tune everything, one command
requirements_finetune.txt            training dependencies
dataset/                             generated output lands here
```

## 1. Prerequisites

- **Python 3.10+** for dataset generation (no GPU needed for this part).
- **A CUDA GPU** for the fine-tuning step (see the cloud guide if you don't
  have one locally) — 16 GB+ VRAM minimum for the smallest preset.
- **pip** and (recommended) a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```

## 2. Generate the datasets (no GPU required)

This step is pure Python/CPU and takes seconds to a couple of minutes.

**Everything at once** (30 agents + COPPER):

```bash
python generate_all_agents.py --size 1500 --outdir ./dataset
python copper_orchestrator_dataset_gen.py --size 2500 --outdir ./dataset/COPPER
```

This writes, per agent, `dataset/<AGENT>/<agent>_{train,val,test}.jsonl` and
a manifest, plus `dataset/COPPER/copper_{train,val,test}.jsonl` and
`dataset/all_agents_manifest.json` summarizing record counts across every
agent.

**Just one agent**, e.g. while iterating on a new agent config:

```bash
python generate_agent_dataset.py --agent AXIS --size 1500 --outdir ./dataset/AXIS
```

**Just a subset**, via `generate_all_agents.py --agents`:

```bash
python generate_all_agents.py --agents AXIS,AEON,VAULT --size 1500 --outdir ./dataset
```

### Sanity-check the output

```bash
python3 -c "
import json, glob
total = bad = 0
for path in glob.glob('dataset/*/*.jsonl'):
    for line in open(path):
        total += 1
        try:
            r = json.loads(line)
            assert 'messages' in r
        except Exception:
            bad += 1
print(f'{total} records checked, {bad} malformed')
"
```

Or just eyeball a few records:

```bash
head -n 2 dataset/AXIS/axis_train.jsonl | python3 -m json.tool
```

## 3. Install training dependencies (GPU step)

Only needed once you're ready to fine-tune — do this on whatever machine
has the GPU (local box or a rented cloud instance):

```bash
pip install -r requirements_finetune.txt
```

If you're on a specific CUDA version, check the comment block at the top of
`requirements_finetune.txt` for the right `torch` install command first.

## 4. Fine-tune

### One agent

```bash
python finetune_agent.py --agent AXIS --model mistralai/Mistral-7B-Instruct-v0.3
```

`--agent` auto-fills `--train_file`, `--val_file`, `--output_dir`
(`./axis-lora`), and `--run_name` from the naming convention that
`generate_agent_dataset.py` uses — you only need to override those flags if
your files live somewhere non-standard.

### COPPER (the orchestrator)

```bash
python finetune_agent.py --agent COPPER --model mistralai/Mistral-7B-Instruct-v0.3
```

### Everything — all 30 agents + COPPER, one command

```bash
bash launch_finetune_all.sh 24gb
```

The first argument picks a GPU-tier preset (`24gb` / `40gb` / `80gb`) that
sets sane batch size, gradient accumulation, and LoRA rank for that amount
of VRAM — see the table in the cloud guide. It generates any missing
dataset automatically, then fine-tunes each agent in turn, finishing with
COPPER.

To run just a few agents instead of all 30:

```bash
bash launch_finetune_all.sh 40gb AXIS,AEON,VAULT
```

(COPPER still runs at the end regardless of the agent subset — remove that
step from the script if you don't want it every time.)

### What you get

Each run produces `./<agent>-lora/final_adapter/` — a LoRA adapter you can
load on top of the base model with `peft`:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3", device_map="auto")
model = PeftModel.from_pretrained(base, "./axis-lora/final_adapter")
tokenizer = AutoTokenizer.from_pretrained("./axis-lora/final_adapter")
```

Or merge into a standalone model and optionally push to the Hub:

```bash
python finetune_agent.py --agent AXIS --merge_and_push \
  --output_dir ./axis-lora --hub_repo your-org/axis-7b
```

## 5. Quick smoke test after training

Before trusting a fine-tuned adapter, sanity-check it on a held-out example
from that agent's own `_test.jsonl`:

```python
import json
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

test_record = json.loads(open("dataset/AXIS/axis_test.jsonl").readline())
system_msg, user_msg = test_record["messages"][0], test_record["messages"][1]

base = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3", device_map="auto")
model = PeftModel.from_pretrained(base, "./axis-lora/final_adapter")
tokenizer = AutoTokenizer.from_pretrained("./axis-lora/final_adapter")

prompt = tokenizer.apply_chat_template(
    [system_msg, user_msg], tokenize=False, add_generation_prompt=True
)
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
out = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(out[0], skip_special_tokens=True))
```

Check the output actually contains a well-formed `[DIALOGUE]` /
`[TECHNICAL_PAYLOAD]` pair matching that agent's schema.

## 6. Extending the roster

Adding a 31st agent (or your own custom one) is a single dict entry — no
changes needed anywhere else:

```python
# in agent_configs.py
AGENT_CONFIGS["YOURAGENT"] = {
    "role": "the ... agent of COPPER. You ...",
    "personality": "...",
    "payload_fields": "action, field_a, field_b",
    "intents": ["Do {task} for me", "..."],        # 6-10 templates
    "dialogue": ["In-character reaction 1", "..."],  # 5-8 lines
    "payload_fn": lambda slots, text, rng: {"action": "...", "field_a": slots.get("task")},
}
# and add it to MODEL_MAP with its tier
```

Then:

```bash
python generate_agent_dataset.py --agent YOURAGENT --size 1500 --outdir ./dataset/YOURAGENT
python finetune_agent.py --agent YOURAGENT
```

COPPER's orchestrator dataset picks up new agents automatically the next
time you regenerate it (`copper_orchestrator_dataset_gen.py` reads straight
from `AGENT_CONFIGS`), so regenerate that too if you add agents:

```bash
python copper_orchestrator_dataset_gen.py --size 2500 --outdir ./dataset/COPPER
```

## 7. FAQ

**Do I need a GPU to generate the datasets?**
No — `generate_agent_dataset.py`, `generate_all_agents.py`, and
`copper_orchestrator_dataset_gen.py` are pure Python/CPU. Only
`finetune_agent.py` needs a GPU.

**Can I use a different base model?**
Yes — pass `--model` to `finetune_agent.py` with any causal LM on
HuggingFace. Larger models need more VRAM; adjust the GPU tier accordingly.

**How big should `--size` be?**
1,000-2,000 per agent is the recommended range — enough variety without
excessive duplicate near-misses given each agent has ~6-10 intent
templates. COPPER's own dataset benefits from being larger (2,000-3,000)
since it needs to cover routing decisions across all 30 agents plus direct
answers, multi-agent chains, and BOSS mode.

**Why do some agents have more records in COPPER's `agent_distribution`
than others?**
COPPER samples uniformly across the 30 agents, so counts should be close
to even — small differences are just random variation from the seed. If
you want it exactly balanced, that's a straightforward tweak to
`sample_single_delegation` in `copper_orchestrator_dataset_gen.py` (round-
robin instead of `rng.choice`).

**Where do I go next if training fails or I need cloud GPU setup help?**
See [`CLOUD_GPU_TRAINING_GUIDE.md`](./CLOUD_GPU_TRAINING_GUIDE.md) —
provider walkthroughs (RunPod / Vast.ai / Lambda Labs), cost estimates, and
a troubleshooting table for common CUDA/OOM/auth errors.
