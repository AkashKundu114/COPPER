"""
COPPER Fine-Tune Script — QLoRA / SFT
======================================
Trains any causal-LM available on HuggingFace on the COPPER orchestrator dataset
using QLoRA (4-bit quantisation + LoRA adapters) via the TRL SFTTrainer.

Quick-start on a rented GPU (RunPod / Lambda / Vast.ai):
  pip install -r requirements_finetune.txt
  python copper_dataset_gen.py --size 1000 --outdir ./data
  python finetune_copper.py --model mistralai/Mistral-7B-Instruct-v0.3 \
                             --train_file ./data/copper_train.jsonl \
                             --val_file   ./data/copper_val.jsonl \
                             --output_dir ./copper-lora

After training, merge LoRA weights and push to Hub:
  python finetune_copper.py --merge_and_push --output_dir ./copper-lora \
                             --hub_repo your-org/copper-7b
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ── CLI ──────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="QLoRA fine-tuning for the COPPER orchestrator model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ── Data ──
    data = p.add_argument_group("Data")
    data.add_argument("--train_file",  type=str, default="./data/copper_train.jsonl")
    data.add_argument("--val_file",    type=str, default="./data/copper_val.jsonl")
    data.add_argument("--max_seq_len", type=int, default=1024,
                      help="Maximum token length; longer examples are truncated")

    # ── Model ──
    model = p.add_argument_group("Model")
    model.add_argument("--model", type=str, default="mistralai/Mistral-7B-Instruct-v0.3",
                       help="HuggingFace model ID or local path")
    model.add_argument("--output_dir", type=str, default="./copper-lora",
                       help="Directory to save checkpoints and final adapter")

    # ── LoRA ──
    lora = p.add_argument_group("LoRA")
    lora.add_argument("--lora_r",       type=int,   default=64)
    lora.add_argument("--lora_alpha",   type=int,   default=128)
    lora.add_argument("--lora_dropout", type=float, default=0.05)
    lora.add_argument("--lora_targets", type=str,
                      default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj",
                      help="Comma-separated LoRA target module names")

    # ── Training ──
    train = p.add_argument_group("Training")
    train.add_argument("--epochs",         type=int,   default=3)
    train.add_argument("--batch_size",     type=int,   default=2,
                       help="Per-device train batch size")
    train.add_argument("--grad_accum",     type=int,   default=8,
                       help="Gradient accumulation steps (effective batch = batch_size × grad_accum × gpus)")
    train.add_argument("--lr",             type=float, default=2e-4)
    train.add_argument("--warmup_ratio",   type=float, default=0.05)
    train.add_argument("--weight_decay",   type=float, default=0.01)
    train.add_argument("--lr_scheduler",   type=str,   default="cosine",
                       choices=["cosine", "linear", "constant", "constant_with_warmup"])
    train.add_argument("--fp16",           action="store_true",
                       help="Use fp16 (for V100 / older GPUs)")
    train.add_argument("--bf16",           action="store_true", default=True,
                       help="Use bf16 (for A10G, A100, H100 — recommended)")
    train.add_argument("--save_steps",     type=int,   default=100)
    train.add_argument("--eval_steps",     type=int,   default=100)
    train.add_argument("--logging_steps",  type=int,   default=25)
    train.add_argument("--save_total_limit", type=int, default=3)
    train.add_argument("--seed",           type=int,   default=42)
    train.add_argument("--packing",        action="store_true", default=False,
                       help="Pack multiple short samples into one sequence for efficiency")

    # ── 4-bit quantisation ──
    quant = p.add_argument_group("Quantisation (QLoRA)")
    quant.add_argument("--no_4bit", action="store_true",
                       help="Disable 4-bit quantisation (uses full precision LoRA instead)")
    quant.add_argument("--bnb_4bit_quant_type", type=str, default="nf4",
                       choices=["nf4", "fp4"])
    quant.add_argument("--bnb_4bit_compute_dtype", type=str, default="bfloat16",
                       choices=["bfloat16", "float16", "float32"])

    # ── Logging ──
    log = p.add_argument_group("Logging")
    log.add_argument("--wandb_project", type=str, default="",
                     help="W&B project name (leave empty to disable)")
    log.add_argument("--run_name",      type=str, default="copper-lora")

    # ── Post-training ──
    post = p.add_argument_group("Post-training")
    post.add_argument("--merge_and_push", action="store_true",
                      help="After training, merge LoRA into base model and push to Hub")
    post.add_argument("--hub_repo", type=str, default="",
                      help="HuggingFace Hub repo to push merged model (e.g. org/model-name)")

    return p.parse_args()


# ── Dataset Helpers ──────────────────────────────────────────────────────────
def load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"⚠️  Skipping malformed line {line_no} in {path}: {e}")
    print(f"  Loaded {len(records)} records from {path}")
    return records


def make_hf_dataset(records: list[dict]):
    """Convert list-of-message-dicts to a HuggingFace Dataset."""
    from datasets import Dataset
    return Dataset.from_list(records)


def get_formatting_func(tokenizer):
    """
    Returns a function that applies the model's chat template to a batch.
    Falls back to a manual ChatML format if the tokenizer has no template.
    """
    has_template = (
        getattr(tokenizer, "chat_template", None) is not None
    )

    def _chatML_format(messages: list[dict]) -> str:
        parts = []
        for m in messages:
            role    = m["role"]
            content = m["content"]
            parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
        parts.append("<|im_start|>assistant\n")  # generation prompt
        return "\n".join(parts)

    def formatting_func(example: dict) -> list[str]:
        msgs = example["messages"]
        if has_template:
            try:
                return [tokenizer.apply_chat_template(
                    msgs, tokenize=False, add_generation_prompt=False
                )]
            except Exception:
                pass
        return [_chatML_format(msgs)]

    return formatting_func


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    # ── Lazy imports (so the script can be inspected without GPU deps) ────────
    try:
        import torch
        from datasets import Dataset
        from peft import (
            LoraConfig,
            TaskType,
            get_peft_model,
            prepare_model_for_kbit_training,
        )
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            TrainingArguments,
        )
        from trl import SFTTrainer
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("   Run:  pip install -r requirements_finetune.txt")
        sys.exit(1)

    # ── W&B ──────────────────────────────────────────────────────────────────
    if args.wandb_project:
        os.environ.setdefault("WANDB_PROJECT", args.wandb_project)
        report_to = "wandb"
    else:
        os.environ["WANDB_DISABLED"] = "true"
        report_to = "none"

    # ── Device info ───────────────────────────────────────────────────────────
    if not torch.cuda.is_available():
        print("⚠️  No CUDA GPU detected — training will be very slow on CPU.")
    else:
        n_gpu   = torch.cuda.device_count()
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"🖥  {n_gpu} GPU(s) detected — {gpu_mem:.1f} GB VRAM (device 0)")

    # ── Load tokenizer ────────────────────────────────────────────────────────
    print(f"\n📦 Loading tokenizer: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
        padding_side="right",      # required for SFT loss masking
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── Load model ────────────────────────────────────────────────────────────
    print(f"📦 Loading model: {args.model}")
    compute_dtype = {
        "bfloat16": torch.bfloat16,
        "float16":  torch.float16,
        "float32":  torch.float32,
    }[args.bnb_4bit_compute_dtype]

    if not args.no_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type=args.bnb_4bit_quant_type,
            bnb_4bit_compute_dtype=compute_dtype,
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(
            model, use_gradient_checkpointing=True
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=compute_dtype,
            device_map="auto",
            trust_remote_code=True,
        )
        model.enable_input_require_grads()

    model.config.use_cache = False     # required for gradient checkpointing

    # ── LoRA ─────────────────────────────────────────────────────────────────
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=args.lora_targets.split(","),
        bias="none",
        inference_mode=False,
    )

    trainable, total = 0, 0
    for _, param in model.named_parameters():
        total += param.numel()
        if param.requires_grad:
            trainable += param.numel()
    print(f"🔧 Trainable parameters: {trainable:,} / {total:,}  "
          f"({100 * trainable / total:.2f}%)")

    # ── Dataset ───────────────────────────────────────────────────────────────
    print("\n📂 Loading datasets …")
    train_records = load_jsonl(args.train_file)
    val_records   = load_jsonl(args.val_file)

    train_dataset = make_hf_dataset(train_records)
    val_dataset   = make_hf_dataset(val_records)

    formatting_func = get_formatting_func(tokenizer)

    # ── TrainingArguments ─────────────────────────────────────────────────────
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # bf16/fp16 safety: prefer bf16 unless explicitly requested fp16
    use_bf16 = args.bf16 and not args.fp16
    use_fp16 = args.fp16 and not args.bf16

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        run_name=args.run_name,

        # epochs / steps
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},

        # optimiser
        learning_rate=args.lr,
        warmup_ratio=args.warmup_ratio,
        weight_decay=args.weight_decay,
        lr_scheduler_type=args.lr_scheduler,
        optim="paged_adamw_8bit" if not args.no_4bit else "adamw_torch",

        # precision
        bf16=use_bf16,
        fp16=use_fp16,

        # logging / saving
        logging_dir=str(output_dir / "logs"),
        logging_steps=args.logging_steps,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to=report_to,

        # misc
        seed=args.seed,
        dataloader_num_workers=4,
        remove_unused_columns=False,
        group_by_length=not args.packing,
    )

    # ── Trainer ───────────────────────────────────────────────────────────────
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        peft_config=lora_config,
        formatting_func=formatting_func,
        max_seq_length=args.max_seq_len,
        packing=args.packing,
        tokenizer=tokenizer,
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    print("\n🚀 Training …\n")
    trainer.train()

    # ── Save adapter ──────────────────────────────────────────────────────────
    final_adapter_dir = output_dir / "final_adapter"
    trainer.save_model(str(final_adapter_dir))
    tokenizer.save_pretrained(str(final_adapter_dir))
    print(f"\n💾 LoRA adapter saved → {final_adapter_dir}")

    # ── Optional: merge + push ────────────────────────────────────────────────
    if args.merge_and_push:
        print("\n🔀 Merging LoRA weights into base model …")
        from peft import PeftModel

        base_model = AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        merged_model = PeftModel.from_pretrained(base_model, str(final_adapter_dir))
        merged_model = merged_model.merge_and_unload()

        merged_dir = output_dir / "merged_model"
        merged_model.save_pretrained(str(merged_dir), safe_serialization=True)
        tokenizer.save_pretrained(str(merged_dir))
        print(f"💾 Merged model saved → {merged_dir}")

        if args.hub_repo:
            print(f"☁️  Pushing to HuggingFace Hub: {args.hub_repo}")
            merged_model.push_to_hub(args.hub_repo, safe_serialization=True)
            tokenizer.push_to_hub(args.hub_repo)
            print("✅ Pushed to Hub.")

    print("\n🎉 Fine-tuning complete.")


if __name__ == "__main__":
    main()
