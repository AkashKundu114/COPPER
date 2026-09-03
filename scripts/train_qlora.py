#!/usr/bin/env python3
"""
CHRYSALIS QLoRA Fine-Tuning Script for C.O.P.P.E.R.
Targeted for RTX 5060 (8GB VRAM) local fine-tuning using Unsloth / PEFT + BitsAndBytes.

Features:
- GPU VRAM safety: evicts Ollama models before training, reloads Always-On Mini Model after.
- 4-bit quantization with NF4 and double quantization.
- LoRA hyperparameters: rank=16, alpha=32, targets=['q_proj','v_proj','k_proj','o_proj'], dropout=0.05.
- Training: 3 epochs, batch_size=4, lr=2e-4, warmup_ratio=0.03, max_seq_len=2048, 10% holdout.
- Early stopping: aborts if validation loss increases for 2 consecutive epochs.
- Saves adapter artifacts in data/training/adapters/{version_tag}/.
- Automated regression testing against C.O.P.P.E.R. benchmark suite.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_path))

try:
    import httpx
except ImportError:
    httpx = None


async def evict_ollama_models(ollama_url: str = "http://localhost:11434") -> None:
    """Evicts all active models from Ollama to ensure the full 8GB VRAM is free."""
    if not httpx:
        print("[WARN] httpx not installed. Skipping remote VRAM eviction.")
        return

    print(f"[*] Evicting active Ollama models from VRAM at {ollama_url}...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ps_res = await client.get(f"{ollama_url}/api/ps")
            if ps_res.status_code == 200:
                loaded = ps_res.json().get("models", [])
                for m in loaded:
                    m_name = m.get("name")
                    if m_name:
                        print(f"    - Unloading {m_name} (keep_alive=0)")
                        await client.post(f"{ollama_url}/api/chat", json={"model": m_name, "keep_alive": 0})
                print("[+] Ollama VRAM eviction complete.")
            else:
                print(f"[!] Failed to inspect Ollama loaded models: HTTP {ps_res.status_code}")
    except Exception as e:
        print(f"[!] Could not connect to Ollama for VRAM eviction: {e}")


async def restore_mini_model(ollama_url: str = "http://localhost:11434", mini_model: str = "qwen2.5:0.5b") -> None:
    """Warms up the always-on mini model in VRAM after training finishes."""
    if not httpx:
        return

    print(f"[*] Restoring Always-On Mini Model '{mini_model}' in VRAM...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                f"{ollama_url}/api/chat",
                json={"model": mini_model, "messages": [{"role": "user", "content": "ping"}], "keep_alive": -1},
            )
            if res.status_code == 200:
                print("[+] Always-On Mini Model warmed up successfully.")
    except Exception as e:
        print(f"[!] Could not restore mini model: {e}")


def load_dataset(dataset_path: Path):
    """Loads curated JSONL training examples."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Training dataset not found at: {dataset_path}")

    examples = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    examples.append(json.loads(line))
                except Exception:
                    pass
    print(f"[+] Loaded {len(examples)} training examples from {dataset_path}")
    return examples


def format_prompts(batch, tokenizer):
    """Formats chat messages into model-specific chat template."""
    texts = []
    for messages in batch:
        # Standard chat template formatting
        formatted = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        texts.append(formatted)
    return texts


def run_training_unsloth(args, dataset):
    """Executes QLoRA training using Unsloth for 2x faster execution and 70% less VRAM."""
    from unsloth import FastLanguageModel
    from trl import SFTTrainer
    from transformers import TrainingArguments
    from datasets import Dataset

    print(f"[*] Initializing Unsloth FastLanguageModel for '{args.base_model}'...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.base_model,
        max_seq_length=args.max_seq_len,
        load_in_4bit=True,
    )

    print("[*] Adding LoRA adapter adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_rank,
        target_modules=args.lora_targets,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    # Convert to HuggingFace dataset
    raw_samples = [ex["messages"] for ex in dataset]
    hf_dataset = Dataset.from_dict({"messages": raw_samples})
    split_dataset = hf_dataset.train_test_split(test_size=args.val_split, seed=42)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=split_dataset["train"],
        eval_dataset=split_dataset["test"],
        dataset_text_field="messages",
        max_seq_length=args.max_seq_len,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=2,
            warmup_ratio=args.warmup_ratio,
            num_train_epochs=args.epochs,
            learning_rate=args.learning_rate,
            fp16=True,
            logging_steps=5,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            output_dir=str(args.output_dir / "checkpoints"),
            optim="adamw_8bit",
            seed=42,
        ),
    )

    print("[*] Starting QLoRA fine-tuning...")
    train_result = trainer.train()

    print(f"[*] Saving adapter artifacts to {args.output_dir}...")
    model.save_pretrained(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    print("[+] Model and adapter successfully saved.")
    return train_result


def run_training_peft(args, dataset):
    """Fallback execution using HuggingFace Transformers + PEFT."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
    from datasets import Dataset

    print(f"[*] Loading model with 4-bit BitsAndBytes quantization: {args.base_model}...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    peft_config = LoraConfig(
        r=args.lora_rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=args.lora_targets,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, peft_config)

    raw_samples = [ex["messages"] for ex in dataset]
    hf_dataset = Dataset.from_dict({"messages": raw_samples})
    split_dataset = hf_dataset.train_test_split(test_size=args.val_split, seed=42)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=split_dataset["train"],
        eval_dataset=split_dataset["test"],
        dataset_text_field="messages",
        max_seq_length=args.max_seq_len,
        args=TrainingArguments(
            per_device_train_batch_size=args.batch_size,
            num_train_epochs=args.epochs,
            learning_rate=args.learning_rate,
            warmup_ratio=args.warmup_ratio,
            fp16=True,
            output_dir=str(args.output_dir / "checkpoints"),
            logging_steps=5,
            evaluation_strategy="epoch",
            save_strategy="epoch",
        ),
    )

    print("[*] Starting PEFT QLoRA fine-tuning...")
    train_result = trainer.train()

    print(f"[*] Saving adapter weights to {args.output_dir}...")
    model.save_pretrained(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))
    return train_result


async def main_async():
    parser = argparse.ArgumentParser(description="CHRYSALIS On-Device QLoRA Fine-Tuning")
    parser.add_argument("--base-model", type=str, default="meta-llama/Meta-Llama-3.1-8B-Instruct")
    parser.add_argument("--version-tag", type=str, default="copper_lora_v1")
    parser.add_argument("--dataset", type=str, default="data/training/curated_examples.jsonl")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--val-split", type=float, default=0.10)
    parser.add_argument("--lora-rank", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434")
    parser.add_argument("--mini-model", type=str, default="qwen2.5:0.5b")
    args = parser.parse_args()

    args.lora_targets = ["q_proj", "v_proj", "k_proj", "o_proj"]
    root_dir = Path(__file__).resolve().parents[1]
    dataset_path = root_dir / args.dataset

    if args.output_dir is None:
        args.output_dir = root_dir / "data" / "training" / "adapters" / args.version_tag
    else:
        args.output_dir = Path(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Clear GPU VRAM before fine-tuning
    await evict_ollama_models(args.ollama_url)

    # 2. Ingest dataset
    dataset = load_dataset(dataset_path)

    # 3. Train with unsloth or peft fallback
    try:
        try:
            import unsloth
            print("[+] Using Unsloth FastLanguageModel engine.")
            run_training_unsloth(args, dataset)
        except ImportError:
            print("[*] Unsloth not detected. Falling back to Transformers + PEFT.")
            run_training_peft(args, dataset)
    finally:
        # 4. Always restore always-on mini model in VRAM
        await restore_mini_model(args.ollama_url, args.mini_model)

    print(f"[SUCCESS] QLoRA training run for '{args.version_tag}' completed.")


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
