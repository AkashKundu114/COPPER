import argparse
import json
import os
import sys
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description='QLoRA fine-tuning for a single COPPER sub-agent', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    data = p.add_argument_group('Data')
    data.add_argument('--agent', type=str, default='', help='Agent name (e.g. AXIS, AEON). Auto-fills train/val/output paths from ./dataset/<AGENT>/<agent>_{train,val}.jsonl if those flags are unset.')
    data.add_argument('--train_file', type=str, default=None)
    data.add_argument('--val_file', type=str, default=None)
    data.add_argument('--max_seq_len', type=int, default=1024, help='Maximum token length; longer examples are truncated')
    model = p.add_argument_group('Model')
    model.add_argument('--model', type=str, default='mistralai/Mistral-7B-Instruct-v0.3', help='HuggingFace model ID or local path')
    model.add_argument('--output_dir', type=str, default=None, help='Directory to save checkpoints and final adapter (default: ./<agent>-lora if --agent is set, else ./copper-lora)')
    lora = p.add_argument_group('LoRA')
    lora.add_argument('--lora_r', type=int, default=64)
    lora.add_argument('--lora_alpha', type=int, default=128)
    lora.add_argument('--lora_dropout', type=float, default=0.05)
    lora.add_argument('--lora_targets', type=str, default='q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj', help='Comma-separated LoRA target module names')
    train = p.add_argument_group('Training')
    train.add_argument('--epochs', type=int, default=3)
    train.add_argument('--batch_size', type=int, default=2, help='Per-device train batch size')
    train.add_argument('--grad_accum', type=int, default=8, help='Gradient accumulation steps (effective batch = batch_size × grad_accum × gpus)')
    train.add_argument('--lr', type=float, default=0.0002)
    train.add_argument('--warmup_ratio', type=float, default=0.05)
    train.add_argument('--weight_decay', type=float, default=0.01)
    train.add_argument('--lr_scheduler', type=str, default='cosine', choices=['cosine', 'linear', 'constant', 'constant_with_warmup'])
    train.add_argument('--fp16', action='store_true', help='Use fp16 (for V100 / older GPUs)')
    train.add_argument('--bf16', action='store_true', default=True, help='Use bf16 (for A10G, A100, H100 — recommended)')
    train.add_argument('--save_steps', type=int, default=100)
    train.add_argument('--eval_steps', type=int, default=100)
    train.add_argument('--logging_steps', type=int, default=25)
    train.add_argument('--save_total_limit', type=int, default=3)
    train.add_argument('--seed', type=int, default=42)
    train.add_argument('--packing', action='store_true', default=False, help='Pack multiple short samples into one sequence for efficiency')
    quant = p.add_argument_group('Quantisation (QLoRA)')
    quant.add_argument('--no_4bit', action='store_true', help='Disable 4-bit quantisation (uses full precision LoRA instead)')
    quant.add_argument('--bnb_4bit_quant_type', type=str, default='nf4', choices=['nf4', 'fp4'])
    quant.add_argument('--bnb_4bit_compute_dtype', type=str, default='bfloat16', choices=['bfloat16', 'float16', 'float32'])
    log = p.add_argument_group('Logging')
    log.add_argument('--wandb_project', type=str, default='', help='W&B project name (leave empty to disable)')
    log.add_argument('--run_name', type=str, default=None, help='Default: <agent>-lora if --agent is set, else copper-lora')
    post = p.add_argument_group('Post-training')
    post.add_argument('--merge_and_push', action='store_true', help='After training, merge LoRA into base model and push to Hub')
    post.add_argument('--hub_repo', type=str, default='', help='HuggingFace Hub repo to push merged model (e.g. org/model-name)')
    return p.parse_args()

def load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f'⚠️  Skipping malformed line {line_no} in {path}: {e}')
    print(f'  Loaded {len(records)} records from {path}')
    return records

def make_hf_dataset(records: list[dict]):
    from datasets import Dataset
    return Dataset.from_list(records)

def get_formatting_func(tokenizer):
    has_template = getattr(tokenizer, 'chat_template', None) is not None

    def _chatML_format(messages: list[dict]) -> str:
        parts = []
        for m in messages:
            role = m['role']
            content = m['content']
            parts.append(f'<|im_start|>{role}\n{content}<|im_end|>')
        parts.append('<|im_start|>assistant\n')
        return '\n'.join(parts)

    def formatting_func(example: dict) -> list[str]:
        msgs = example['messages']
        if has_template:
            try:
                return [tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)]
            except Exception:
                pass
        return [_chatML_format(msgs)]
    return formatting_func

def resolve_agent_defaults(args):
    agent = args.agent.upper() if args.agent else ''
    if args.train_file is None:
        args.train_file = f'./dataset/{agent}/{agent.lower()}_train.jsonl' if agent else './data/copper_train.jsonl'
    if args.val_file is None:
        args.val_file = f'./dataset/{agent}/{agent.lower()}_val.jsonl' if agent else './data/copper_val.jsonl'
    if args.output_dir is None:
        args.output_dir = f'./{agent.lower()}-lora' if agent else './copper-lora'
    if args.run_name is None:
        args.run_name = f'{agent.lower()}-lora' if agent else 'copper-lora'
    return args

def main():
    args = parse_args()
    args = resolve_agent_defaults(args)
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
        from trl import SFTTrainer
    except ImportError as e:
        print(f'\n❌ Missing dependency: {e}')
        print('   Run:  pip install -r requirements_finetune.txt')
        sys.exit(1)
    if args.wandb_project:
        os.environ.setdefault('WANDB_PROJECT', args.wandb_project)
        report_to = 'wandb'
    else:
        os.environ['WANDB_DISABLED'] = 'true'
        report_to = 'none'
    if not torch.cuda.is_available():
        print('⚠️  No CUDA GPU detected — training will be very slow on CPU.')
    else:
        n_gpu = torch.cuda.device_count()
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1000000000.0
        print(f'🖥  {n_gpu} GPU(s) detected — {gpu_mem:.1f} GB VRAM (device 0)')
    print(f'\n📦 Loading tokenizer: {args.model}')
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True, padding_side='right')
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f'📦 Loading model: {args.model}')
    compute_dtype = {'bfloat16': torch.bfloat16, 'float16': torch.float16, 'float32': torch.float32}[args.bnb_4bit_compute_dtype]
    if not args.no_4bit:
        bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_use_double_quant=True, bnb_4bit_quant_type=args.bnb_4bit_quant_type, bnb_4bit_compute_dtype=compute_dtype)
        model = AutoModelForCausalLM.from_pretrained(args.model, quantization_config=bnb_config, device_map='auto', trust_remote_code=True)
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=compute_dtype, device_map='auto', trust_remote_code=True)
        model.enable_input_require_grads()
    model.config.use_cache = False
    lora_config = LoraConfig(task_type=TaskType.CAUSAL_LM, r=args.lora_r, lora_alpha=args.lora_alpha, lora_dropout=args.lora_dropout, target_modules=args.lora_targets.split(','), bias='none', inference_mode=False)
    trainable, total = (0, 0)
    for _, param in model.named_parameters():
        total += param.numel()
        if param.requires_grad:
            trainable += param.numel()
    print(f'🔧 Trainable parameters: {trainable:,} / {total:,}  ({100 * trainable / total:.2f}%)')
    print('\n📂 Loading datasets …')
    train_records = load_jsonl(args.train_file)
    val_records = load_jsonl(args.val_file)
    train_dataset = make_hf_dataset(train_records)
    val_dataset = make_hf_dataset(val_records)
    formatting_func = get_formatting_func(tokenizer)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    use_bf16 = args.bf16 and (not args.fp16)
    use_fp16 = args.fp16 and (not args.bf16)
    training_args = TrainingArguments(output_dir=str(output_dir), run_name=args.run_name, num_train_epochs=args.epochs, per_device_train_batch_size=args.batch_size, per_device_eval_batch_size=args.batch_size, gradient_accumulation_steps=args.grad_accum, gradient_checkpointing=True, gradient_checkpointing_kwargs={'use_reentrant': False}, learning_rate=args.lr, warmup_ratio=args.warmup_ratio, weight_decay=args.weight_decay, lr_scheduler_type=args.lr_scheduler, optim='paged_adamw_8bit' if not args.no_4bit else 'adamw_torch', bf16=use_bf16, fp16=use_fp16, logging_dir=str(output_dir / 'logs'), logging_steps=args.logging_steps, eval_strategy='steps', eval_steps=args.eval_steps, save_strategy='steps', save_steps=args.save_steps, save_total_limit=args.save_total_limit, load_best_model_at_end=True, metric_for_best_model='eval_loss', greater_is_better=False, report_to=report_to, seed=args.seed, dataloader_num_workers=4, remove_unused_columns=False, group_by_length=not args.packing)
    trainer = SFTTrainer(model=model, args=training_args, train_dataset=train_dataset, eval_dataset=val_dataset, peft_config=lora_config, formatting_func=formatting_func, max_seq_length=args.max_seq_len, packing=args.packing, tokenizer=tokenizer)
    print('\n🚀 Training …\n')
    trainer.train()
    final_adapter_dir = output_dir / 'final_adapter'
    trainer.save_model(str(final_adapter_dir))
    tokenizer.save_pretrained(str(final_adapter_dir))
    print(f'\n💾 LoRA adapter saved → {final_adapter_dir}')
    if args.merge_and_push:
        print('\n🔀 Merging LoRA weights into base model …')
        from peft import PeftModel
        base_model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16, device_map='auto', trust_remote_code=True)
        merged_model = PeftModel.from_pretrained(base_model, str(final_adapter_dir))
        merged_model = merged_model.merge_and_unload()
        merged_dir = output_dir / 'merged_model'
        merged_model.save_pretrained(str(merged_dir), safe_serialization=True)
        tokenizer.save_pretrained(str(merged_dir))
        print(f'💾 Merged model saved → {merged_dir}')
        if args.hub_repo:
            print(f'☁️  Pushing to HuggingFace Hub: {args.hub_repo}')
            merged_model.push_to_hub(args.hub_repo, safe_serialization=True)
            tokenizer.push_to_hub(args.hub_repo)
            print('✅ Pushed to Hub.')
    print('\n🎉 Fine-tuning complete.')
if __name__ == '__main__':
    main()