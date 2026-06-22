"""
COPPER Fine-Tuning Pipeline — QLoRA with Unsloth
Trains personality + domain adapters for all 6 model profiles.

Usage:
  python train.py --model 2 --dataset datasets/model2_code_engineering.jsonl
  python train.py --model all   # trains all models sequentially

Requirements:
  pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
  pip install trl peft datasets transformers accelerate bitsandbytes wandb

Hardware:
  Model 1 (14B): A100 40GB+ required
  Model 2-5 (7B): RTX 3090 24GB or better
  Model 3 (3B):   RTX 3080 10GB works
  Model 6:        No fine-tuning — Whisper/Kokoro are pretrained
"""

import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import torch
from datasets import Dataset
from transformers import TrainingArguments
from trl import SFTTrainer, DataCollatorForCompletionOnlyLM
from unsloth import FastLanguageModel, is_bfloat16_supported
from peft import LoraConfig

# ── Model Profiles ────────────────────────────────────────────────────────────

@dataclass
class ModelProfile:
    profile_id: int
    name: str
    base_model: str
    dataset_file: str
    adapter_output: str
    max_seq_len: int = 4096
    # LoRA hyperparameters
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    # Training hyperparameters
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 2
    gradient_accumulation: int = 4
    warmup_ratio: float = 0.05
    # Target modules (Qwen2.5 architecture)
    target_modules: list = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ])


MODEL_REGISTRY: dict[int, ModelProfile] = {
    1: ModelProfile(
        profile_id=1,
        name="core_reasoning",
        base_model="unsloth/Qwen2.5-14B-bnb-4bit",
        dataset_file="datasets/model1_core_reasoning.jsonl",
        adapter_output="adapters/model1_core_reasoning",
        lora_r=32,        # Higher rank for the most important model
        lora_alpha=64,
        batch_size=1,     # 14B needs more conservative batching
        gradient_accumulation=8,
        learning_rate=1e-4,
    ),
    2: ModelProfile(
        profile_id=2,
        name="code_engineering",
        base_model="unsloth/Qwen2.5-Coder-7B-Instruct-bnb-4bit",
        dataset_file="datasets/model2_code_engineering.jsonl",
        adapter_output="adapters/model2_code_engineering",
        lora_r=16,
        lora_alpha=32,
    ),
    3: ModelProfile(
        profile_id=3,
        name="os_executors",
        base_model="unsloth/Qwen2.5-3B-Instruct-bnb-4bit",
        dataset_file="datasets/model3_os_executors.jsonl",
        adapter_output="adapters/model3_os_executors",
        lora_r=16,
        lora_alpha=32,
        batch_size=4,
        gradient_accumulation=2,
        learning_rate=3e-4,
    ),
    4: ModelProfile(
        profile_id=4,
        name="vision_rpa",
        base_model="unsloth/Qwen2-VL-7B-Instruct-bnb-4bit",
        dataset_file="datasets/model4_vision_rpa.jsonl",
        adapter_output="adapters/model4_vision_rpa",
        lora_r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    ),
    5: ModelProfile(
        profile_id=5,
        name="web_streaming",
        base_model="unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
        dataset_file="datasets/model5_web_streaming.jsonl",
        adapter_output="adapters/model5_web_streaming",
        lora_r=16,
        lora_alpha=32,
    ),
    # Model 6 (Whisper + Kokoro) — CPU-only, no fine-tuning via this script
    # See finetune/model6_whisper_notes.md for Whisper fine-tuning approach
}


# ── Dataset Loading ───────────────────────────────────────────────────────────

def load_jsonl_dataset(filepath: str) -> Dataset:
    """Load JSONL in messages format and convert to Unsloth's expected format."""
    records = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            # Support both {"messages": [...]} and flat {"conversations": [...]}
            messages = obj.get("messages") or obj.get("conversations", [])
            records.append({"messages": messages})
    return Dataset.from_list(records)


def format_messages_to_chatml(example: dict, tokenizer) -> dict:
    """Convert messages list to ChatML prompt string."""
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}


# ── Training Function ─────────────────────────────────────────────────────────

def train_model(profile: ModelProfile, resume_from: Optional[str] = None, dry_run: bool = False):
    print(f"\n{'='*60}")
    print(f"Training MODEL {profile.profile_id}: {profile.name}")
    print(f"Base: {profile.base_model}")
    print(f"Dataset: {profile.dataset_file}")
    print(f"Output: {profile.adapter_output}")
    print(f"{'='*60}\n")

    if not Path(profile.dataset_file).exists():
        raise FileNotFoundError(f"Dataset not found: {profile.dataset_file}")

    # ── Load Model ────────────────────────────────────────────────────────────
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=profile.base_model,
        max_seq_length=profile.max_seq_len,
        load_in_4bit=True,
        dtype=None,  # auto: bf16 on Ampere+, fp16 on older
    )

    # ── Attach LoRA ───────────────────────────────────────────────────────────
    model = FastLanguageModel.get_peft_model(
        model,
        r=profile.lora_r,
        target_modules=profile.target_modules,
        lora_alpha=profile.lora_alpha,
        lora_dropout=profile.lora_dropout,
        bias="none",
        use_gradient_checkpointing="unsloth",  # 30% VRAM reduction
        random_state=42,
    )

    print(f"Trainable parameters: {model.num_parameters(only_trainable=True):,}")

    # ── Load & Format Dataset ─────────────────────────────────────────────────
    raw_dataset = load_jsonl_dataset(profile.dataset_file)
    print(f"Dataset size: {len(raw_dataset)} examples")

    dataset = raw_dataset.map(
        lambda ex: format_messages_to_chatml(ex, tokenizer),
        batched=False,
    )

    if dry_run:
        print("DRY RUN — showing first example:")
        print(dataset[0]["text"][:500])
        print("...\nExiting dry run.")
        return

    # ── Training Arguments ────────────────────────────────────────────────────
    training_args = TrainingArguments(
        output_dir=profile.adapter_output,
        per_device_train_batch_size=profile.batch_size,
        gradient_accumulation_steps=profile.gradient_accumulation,
        num_train_epochs=profile.num_epochs,
        learning_rate=profile.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=profile.warmup_ratio,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        optim="adamw_8bit",
        seed=42,
        report_to="wandb" if _wandb_available() else "none",
        run_name=f"copper-model{profile.profile_id}-{profile.name}",
        dataloader_num_workers=0,  # avoid multiprocess issues in most setups
    )

    # ── Trainer ───────────────────────────────────────────────────────────────
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=profile.max_seq_len,
        dataset_num_proc=1,
        args=training_args,
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    print(f"\nStarting training...")
    trainer_stats = trainer.train(resume_from_checkpoint=resume_from)

    # ── Save Adapter ──────────────────────────────────────────────────────────
    output_path = Path(profile.adapter_output)
    output_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    print(f"\n✓ Adapter saved to: {output_path}")
    print(f"  Training loss: {trainer_stats.training_loss:.4f}")
    print(f"  Total steps:   {trainer_stats.global_step}")

    # ── Save GGUF for Ollama ──────────────────────────────────────────────────
    gguf_path = str(output_path) + "_gguf"
    print(f"\nSaving GGUF (Q4_K_M) for Ollama to: {gguf_path}")
    model.save_pretrained_gguf(
        gguf_path,
        tokenizer,
        quantization_method="q4_k_m",
    )
    print(f"✓ GGUF saved.")

    return trainer_stats


def _wandb_available() -> bool:
    try:
        import wandb
        return True
    except ImportError:
        return False


# ── Evaluation Helper ─────────────────────────────────────────────────────────

def evaluate_model(profile: ModelProfile, test_prompts: list[str]):
    """Run inference with the fine-tuned adapter for quick sanity checking."""
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=profile.adapter_output,
        max_seq_length=profile.max_seq_len,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)

    for prompt in test_prompts:
        messages = [{"role": "user", "content": prompt}]
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to("cuda")

        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        print(f"\nPrompt: {prompt[:80]}...")
        print(f"Response: {response[:500]}...")


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="COPPER Fine-Tuning Pipeline")
    parser.add_argument(
        "--model",
        type=str,
        default="2",
        help="Model profile ID (1-5) or 'all' to train all",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Override dataset path",
    )
    parser.add_argument(
        "--resume",
        type=str,
        default=None,
        help="Resume from checkpoint path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load model and dataset but don't train",
    )
    parser.add_argument(
        "--eval-only",
        action="store_true",
        help="Run evaluation on trained adapter",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.model == "all":
        profile_ids = list(MODEL_REGISTRY.keys())
        print(f"Training ALL models: {profile_ids}")
    else:
        profile_ids = [int(args.model)]

    for pid in profile_ids:
        if pid not in MODEL_REGISTRY:
            print(f"Unknown model profile: {pid}. Available: {list(MODEL_REGISTRY.keys())}")
            continue

        profile = MODEL_REGISTRY[pid]
        if args.dataset:
            profile.dataset_file = args.dataset

        if args.eval_only:
            test_prompts = [
                "Write a FastAPI endpoint that accepts a file upload",
                "Debug this Python error: AttributeError: 'NoneType' object has no attribute 'split'",
            ]
            evaluate_model(profile, test_prompts)
        else:
            train_model(profile, resume_from=args.resume, dry_run=args.dry_run)

        # Free VRAM between models when training 'all'
        if len(profile_ids) > 1:
            import gc
            gc.collect()
            torch.cuda.empty_cache()
            print(f"\nVRAM cleared. Moving to next model.\n")


if __name__ == "__main__":
    main()
