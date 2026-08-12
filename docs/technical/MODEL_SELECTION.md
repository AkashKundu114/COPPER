# C.O.P.P.E.R. Model Selection & Fine-Tuning Strategy

---

## 1. Model Selection Criteria & Matrix

C.O.P.P.E.R. operates with a hybrid dual-engine architecture:
- **Local Engine (Default):** Ensures zero data egress, offline availability, low cost, and minimal latency.
- **Cloud Engine (Fallback):** Provides high-reasoning fallback for complex multi-file architectural refactoring or multimodal analysis.

```
                          +-------------------------------+
                          |   Incoming Prompt / Request   |
                          +---------------+---------------+
                                          |
                                 [Evaluate Complexity]
                                          |
                 +------------------------+------------------------+
                 | (Standard Task)                                 | (High-Reasoning Task)
                 v                                                 v
  +------------------------------+                  +------------------------------+
  | Ollama Local Engine          |                  | Cloud Engine via Firewall    |
  | (Llama 3 / Mistral / Qwen)   |                  | (OpenAI / Claude / Gemini)   |
  +------------------------------+                  +------------------------------+
```

---

## 2. Supported Models Specification

| Model Name | Provider | Deployment | Quantization | Context Window | Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Llama 3.1 8B Instruct** | Meta / Ollama | Local GPU / CPU | `Q4_K_M` | 128k | Default general reasoning & agent routing. |
| **Qwen 2.5 Coder 7B/14B** | Alibaba / Ollama| Local GPU | `Q4_K_M` / `Q8_0` | 32k | Code generation, refactoring, bash tool execution. |
| **Mistral 7B Instruct v0.3**| Mistral / Ollama| Local GPU | `Q4_K_M` | 32k | Fast tool routing & Guardian level evaluation. |
| **GPT-4o / GPT-4o-mini** | OpenAI | Cloud API | N/A | 128k | High-complexity fallback (via Data Firewall). |
| **Claude 3.5 Sonnet** | Anthropic | Cloud API | N/A | 200k | Deep document analysis & long-context research. |

---

## 3. Fine-Tuning Strategy & Custom Models

To maximize local accuracy for Guardian Level classification and Epistemic Memory extraction, C.O.P.P.E.R. supports custom LoRA (Low-Rank Adaptation) fine-tuning.

### 3.1 Training Dataset Generation
Training datasets are generated from anonymized user interaction logs and curated synthetic samples:
- `dataset/guardian_level_classification.jsonl`: 10,000 paired prompts and Guardian Level (0–3) decisions.
- `dataset/epistemic_fact_extraction.jsonl`: 5,000 dialogue snippets and extracted (Fact, Confidence, Category) tuples.

### 3.2 Fine-Tuning Execution Pipeline (Cloud GPU / Unsloth)
Fine-tuning scripts are located in `scripts/finetune/` utilizing Unsloth / PyTorch for accelerated training:

```bash
# Launch LoRA fine-tuning run on 24GB VRAM GPU (e.g. RTX 4090 or A10G)
python scripts/finetune/train_copper_guardian.py \
    --base_model "unsloth/llama-3-8b-Instruct-bnb-4bit" \
    --dataset "dataset/guardian_level_classification.jsonl" \
    --output_dir "ai-models/copper-guardian-lora" \
    --epochs 3 \
    --learning_rate 2e-4
```

### 3.3 Exporting & Quantizing for Ollama
After training, weights are merged and exported to GGUF format:

```bash
# Convert PyTorch model to GGUF
python llama.cpp/convert_hf_to_gguf.py ai-models/copper-guardian-merged --outfile ai-models/copper-guardian.gguf --outtype q4_k_m

# Create Ollama Modelfile and build local model
echo "FROM ./ai-models/copper-guardian.gguf" > Modelfile
ollama create copper-guardian -f Modelfile
```
