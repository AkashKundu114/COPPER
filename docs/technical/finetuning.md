# COPPER Fine-Tuning Guide

Complete instructions for training QLoRA personality + domain adapters for all 6 model profiles using Unsloth + TRL.

---

## Overview

| Model | Base Model | Agents | Dataset | Output |
|---|---|---|---|---|
| 1 — Core Reasoning | Qwen2.5-14B Q4 | COPPER, CHRONOS | `model1_core_reasoning.jsonl` | `adapters/model1_core_reasoning/` |
| 2 — Code Engineering | Qwen2.5-Coder-7B-Instruct Q4 | CYPHER, CRUCIBLE, FORGE, NEXUS, ARGUS | `model2_code_engineering.jsonl` | `adapters/model2_code_engineering/` |
| 3 — OS Executors | Qwen2.5-3B-Instruct Q4 | AXIS, ATLAS, KINETIC, PULSE, ZENITH, LEDGER | `model3_os_executors.jsonl` | `adapters/model3_os_executors/` |
| 4 — Vision & RPA | Qwen2-VL-7B-Instruct Q4 | HAWK, TALON, PORTAL, IRIS | `model4_vision_rpa.jsonl` | `adapters/model4_vision_rpa/` |
| 5 — Web & Streaming | Qwen2.5-7B-Instruct Q4 | RAPTOR, PHANTOM, VANGUARD, AETHER, BEACON, GLITCH, DIRECTOR | `model5_web_streaming.jsonl` | `adapters/model5_web_streaming/` |
| 6 — Audio/Speech | Whisper-tiny + Kokoro-82M | SONAR, ORACLE, HERMES, AEON | `model6_audio_speech.jsonl` | No training needed (pretrained) |

---

## Step 0 — Hardware

### Minimum Requirements Per Model

| Model | Min VRAM | Recommended | Est. Training Time |
|---|---|---|---|
| Model 1 (14B) | 24 GB | A100 40GB | 8-12 hrs (500 examples) |
| Model 2 (7B Coder) | 16 GB | RTX 3090 24GB | 3-5 hrs |
| Model 3 (3B) | 8 GB | RTX 3080 10GB | 1-2 hrs |
| Model 4 (7B Vision) | 16 GB | RTX 3090 24GB | 3-5 hrs |
| Model 5 (7B) | 16 GB | RTX 3090 24GB | 3-5 hrs |
| Model 6 | CPU only | Any | N/A |

### Cloud GPU Options (Cost-Effective)

```bash
# RunPod — recommended for Models 1, 2, 4, 5
# A100 80GB SXM: ~$2.49/hr  →  Model 1 cost ≈ $25-30
# RTX 3090:      ~$0.44/hr  →  Models 2/3/5 cost ≈ $2-4 each

# Lambda Labs
# A100 40GB: ~$1.29/hr (when available)

# Google Colab Pro+
# A100 GPU: ~$10/month subscription, good for Models 2/3/5
# Tip: Use T4 for Model 3 (3B), it fits fine
```

---

## Step 1 — Environment Setup

### Local GPU Setup

```bash
# Create isolated environment
python3 -m venv copper_finetune
source copper_finetune/bin/activate  # Linux/Mac
# copper_finetune\Scripts\activate   # Windows

# Install PyTorch first (adjust CUDA version for your GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Unsloth — choose the right version for your CUDA
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Install remaining dependencies
pip install trl peft datasets transformers accelerate bitsandbytes
pip install wandb  # optional — for training visualization

# Verify GPU is detected
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"
```

### Cloud (RunPod / Colab) Quick Setup

```bash
# All-in-one for cloud GPU instances
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" trl peft datasets wandb
```

---

## Step 2 — Dataset Expansion

The provided datasets have 7-12 examples per model — enough to verify the pipeline works. For production-quality fine-tuning, **expand each dataset to 200-500 examples**.

### Dataset Format (JSONL)

Every line must be a valid JSON object with this structure:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are CYPHER, the caffeine-deprived full-stack developer..."
    },
    {
      "role": "user",
      "content": "Write a FastAPI endpoint for user login"
    },
    {
      "role": "assistant",
      "content": "[DIALOGUE] Login endpoint. JWT, bcrypt, the whole package.\n\n[TECHNICAL_PAYLOAD] {\"language\": \"python\", \"code\": \"...\"}"
    }
  ]
}
```

### How to Expand Datasets

**Option A — Manual (best quality)**

Write examples covering every task your agent will encounter:
- Every code pattern CYPHER should write
- Every error type CRUCIBLE should debug
- Both BOSS MODE and normal mode variants
- Edge cases and error recovery scenarios

**Option B — GPT-4 / Claude augmentation (faster)**

Use a strong model to generate additional examples, then review each one:

```python
# Example prompt for generating more COPPER routing examples:
GENERATION_PROMPT = """
Generate 10 more training examples for the COPPER orchestrator agent.
Each example must:
1. Have a realistic user request
2. Include [DIALOGUE] (1-2 sentences of COPPER's dry wit)
3. Include [TECHNICAL_PAYLOAD] with valid JSON routing to the correct agent
4. Cover different scenarios: code tasks, automation, research, direct answers

Format: one JSON object per line (JSONL format).
Agent roster: CYPHER (code), CRUCIBLE (debug), HAWK (vision), TALON (click), 
              ATLAS (files), AXIS (shell), VANGUARD (research), NEXUS (git)
"""
```

**Option C — Self-play (advanced)**

Run the untrained base model on real tasks, collect its outputs, manually correct them, then add to dataset. Iterative but produces domain-relevant data.

### Dataset Quality Checklist

Before training, validate your dataset:

```python
import json

issues = []
with open("datasets/model2_code_engineering.jsonl") as f:
    for i, line in enumerate(f):
        try:
            obj = json.loads(line.strip())
            msgs = obj.get("messages", [])
            if len(msgs) < 2:
                issues.append(f"Line {i + 1}: Less than 2 messages")
            assistant_msgs = [m for m in msgs if m["role"] == "assistant"]
            for msg in assistant_msgs:
                if (
                    "[DIALOGUE]" not in msg["content"]
                    and "[TECHNICAL_PAYLOAD]" not in msg["content"]
                ):
                    issues.append(f"Line {i + 1}: Missing output format blocks")
        except json.JSONDecodeError as e:
            issues.append(f"Line {i + 1}: Invalid JSON — {e}")

if issues:
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("Dataset validation passed")
```

---

## Step 3 — Training

### Train a Single Model

```bash
# Start with Model 2 (7B) — best balance of capability vs training cost
python train.py --model 2

# Model 3 (3B) — fastest, good for testing the pipeline first
python train.py --model 3

# Full run — train all models sequentially (long GPU session)
python train.py --model all

# Dry run — loads model, shows first example, exits without training
python train.py --model 2 --dry-run

# Resume from checkpoint (if interrupted)
python train.py --model 2 --resume adapters/model2_code_engineering/checkpoint-150
```

### Training Metrics to Watch

```
Step  10: loss=2.41  — normal at start
Step  50: loss=1.82  — should be dropping
Step 100: loss=1.23  — good convergence
Step 150: loss=0.94  — excellent
Step 200: loss=0.87  — nearly converged

If loss plateaus above 1.5 → reduce learning rate by 50%
If loss < 0.5 too early → possible overfitting, check dataset diversity
```

### WandB Monitoring (Optional but Recommended)

```bash
wandb login  # paste your API key from wandb.ai
# Training will auto-log metrics, loss curves, GPU utilization
```

---

## Step 4 — Evaluate the Adapter

After training, run the evaluation mode to verify behavior:

```bash
python train.py --model 2 --eval-only
```

Manual evaluation checklist:
- [ ] Does the model output `[DIALOGUE]` blocks with the right personality?
- [ ] Does the `[TECHNICAL_PAYLOAD]` contain valid JSON?
- [ ] Does BOSS MODE suppress `[DIALOGUE]` when `SYSTEM_MODE: BOSS`?
- [ ] Does the agent stay in character across different task types?
- [ ] Are code outputs (Model 2) syntactically correct?

---

## Step 5 — Register Adapter with Ollama

The training script saves a GGUF file. Create a Modelfile and register with Ollama:

```bash
# Create Modelfile for Model 2 adapter
cat > Modelfile_model2 << 'EOF'
FROM ./adapters/model2_code_engineering_gguf/model-q4_k_m.gguf

PARAMETER num_ctx 4096
PARAMETER keep_alive 0
PARAMETER temperature 0.7

SYSTEM """You are CYPHER, CRUCIBLE, FORGE, NEXUS, or ARGUS depending on the system prompt injected at runtime. You are one of the code engineering specialists of the COPPER system. Always output [DIALOGUE] followed by [TECHNICAL_PAYLOAD] unless SYSTEM_MODE is BOSS."""
EOF

# Register with Ollama
ollama create copper-model2-code -f Modelfile_model2

# Verify it's registered
ollama list | grep copper

# Test it
ollama run copper-model2-code "Write a Python function to read a JSON file"
```

### Update COPPER's Model Map

In your engine configuration (`state.json` or `config.py`), update the MODEL_MAP:

```python
MODEL_MAP = {
    "MODEL_1_CORE": "copper-model1-core",  # Your fine-tuned model
    "MODEL_2_CODE": "copper-model2-code",  # Your fine-tuned model
    "MODEL_3_OS": "copper-model3-os",  # Your fine-tuned model
    "MODEL_4_VISION": "copper-model4-vision",  # Your fine-tuned model
    "MODEL_5_WEB": "copper-model5-web",  # Your fine-tuned model
    "MODEL_6_AUDIO": None,  # CPU-bound, no Ollama
}
```

---

## Step 6 — Model 6 (Audio) — No Fine-Tuning Required

SONAR (Faster-Whisper) and ORACLE (Kokoro) are pre-trained and require no QLoRA training.

### Install Model 6 Dependencies

```bash
# SONAR — speech-to-text
pip install faster-whisper
# Download model (happens automatically on first use)
# Variants: tiny (fastest/CPU), base (balanced), small (better accuracy)
# COPPER default: base

# ORACLE — text-to-speech  
pip install kokoro>=0.3.0
# Requires espeak-ng on Linux:
sudo apt-get install espeak-ng

# Test SONAR
python -c "
from faster_whisper import WhisperModel
model = WhisperModel('base', device='cpu', compute_type='int8')
segments, info = model.transcribe('test_audio.wav', beam_size=5)
print(' '.join([s.text for s in segments]))
"

# Test Kokoro
python -c "
from kokoro import KPipeline
pipeline = KPipeline(lang_code='a')  # 'a' = American English
audio, sr = pipeline('Hello, I am COPPER.', voice='af_sky')
print(f'Generated {len(audio)/sr:.1f}s of audio')
"
```

---

## Troubleshooting

### OOM (Out of Memory) During Training

```python
# In train.py, reduce batch size and increase gradient accumulation:
profile.batch_size = 1
profile.gradient_accumulation = 16

# Also add to TrainingArguments:
training_args = TrainingArguments(
    ...
    gradient_checkpointing=True,    # Already enabled via Unsloth
    dataloader_num_workers=0,       # Reduce memory from data loading
    fp16=True,                      # Use fp16 instead of bf16 if needed
)
```

### Training Loss Not Decreasing

```python
# Try: lower learning rate, check dataset quality
profile.learning_rate = 5e-5  # From 2e-4

# Or: increase LoRA rank for more capacity
profile.lora_r = 32  # From 16
profile.lora_alpha = 64  # Should be 2x lora_r
```

### Adapter Doesn't Change Model Behavior

This usually means:
1. Training examples are too similar — add more variety to dataset
2. Too few examples — need at least 100 diverse examples
3. Model already knows the behavior — check if base model already outputs correct format

### GGUF Conversion Fails

```bash
# Manual GGUF conversion using llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && pip install -r requirements.txt

# Convert merged model to GGUF
python convert_hf_to_gguf.py adapters/model2_merged/ --outtype q4_k_m
```

---

## Dataset Targets (Production)

For COPPER to behave reliably in production, aim for:

| Model | Min Examples | Recommended | Coverage |
|---|---|---|---|
| Model 1 (COPPER) | 100 | 300+ | All 12+ agent routing combinations |
| Model 1 (CHRONOS) | 50 | 150+ | All project types, various complexities |
| Model 2 (CYPHER) | 80 | 200+ | Python, TypeScript, SQL, React, FastAPI |
| Model 2 (CRUCIBLE) | 60 | 150+ | Common error types across languages |
| Model 2 (FORGE/NEXUS/ARGUS) | 40 each | 100 each | Domain-specific tasks |
| Model 3 (each agent) | 30 | 80+ | Varies by agent scope |
| Model 4 (HAWK/TALON) | 60 | 150+ | Different UI layouts, apps, resolutions |
| Model 5 (each agent) | 40 | 100+ | Different sites, content types |

**Total rough target: 1,500-2,000 examples across all datasets.**
