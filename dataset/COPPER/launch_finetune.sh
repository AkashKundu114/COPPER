#!/usr/bin/env bash
# ============================================================
# COPPER Fine-Tune Launch Script
# Covers three common cloud GPU tiers.
# Usage:  bash launch_finetune.sh [tier]
#         tier: 24gb (default) | 40gb | 80gb
# ============================================================
set -euo pipefail

TIER="${1:-24gb}"
MODEL="mistralai/Mistral-7B-Instruct-v0.3"
DATA_DIR="./data"
OUTPUT_DIR="./copper-lora"

# ── Step 1: Generate dataset if not present ──────────────────────────────────
if [ ! -f "$DATA_DIR/copper_train.jsonl" ]; then
  echo "📂 Dataset not found — generating now …"
  python copper_dataset_gen.py --size 1000 --outdir "$DATA_DIR"
fi

# ── Step 2: Install deps ─────────────────────────────────────────────────────
pip install -q -r requirements_finetune.txt

# ── Step 3: Choose config by GPU tier ────────────────────────────────────────
case "$TIER" in

  24gb)
    # RTX 3090 / 4090 / A10G (24 GB VRAM)
    # QLoRA 4-bit, small batch, r=64
    echo "🖥  Config: 24 GB GPU (e.g. RTX 4090 / A10G)"
    python finetune_copper.py \
      --model          "$MODEL"      \
      --train_file     "$DATA_DIR/copper_train.jsonl" \
      --val_file       "$DATA_DIR/copper_val.jsonl"   \
      --output_dir     "$OUTPUT_DIR" \
      --epochs         3             \
      --batch_size     2             \
      --grad_accum     8             \
      --lr             2e-4          \
      --lora_r         64            \
      --lora_alpha     128           \
      --max_seq_len    1024          \
      --bf16
    ;;

  40gb)
    # A100 40 GB / A6000
    # Larger batch, r=128
    echo "🖥  Config: 40 GB GPU (e.g. A100 40 GB)"
    python finetune_copper.py \
      --model          "$MODEL"      \
      --train_file     "$DATA_DIR/copper_train.jsonl" \
      --val_file       "$DATA_DIR/copper_val.jsonl"   \
      --output_dir     "$OUTPUT_DIR" \
      --epochs         3             \
      --batch_size     4             \
      --grad_accum     4             \
      --lr             2e-4          \
      --lora_r         128           \
      --lora_alpha     256           \
      --max_seq_len    2048          \
      --bf16
    ;;

  80gb)
    # A100 80 GB / H100
    # Full batch, r=128, packing on
    echo "🖥  Config: 80 GB GPU (e.g. A100 80 GB / H100)"
    python finetune_copper.py \
      --model          "$MODEL"      \
      --train_file     "$DATA_DIR/copper_train.jsonl" \
      --val_file       "$DATA_DIR/copper_val.jsonl"   \
      --output_dir     "$OUTPUT_DIR" \
      --epochs         3             \
      --batch_size     8             \
      --grad_accum     2             \
      --lr             2e-4          \
      --lora_r         128           \
      --lora_alpha     256           \
      --max_seq_len    2048          \
      --bf16           \
      --packing
    ;;

  *)
    echo "❌ Unknown tier '$TIER'. Choose: 24gb | 40gb | 80gb"
    exit 1
    ;;
esac

echo ""
echo "✅ Training complete. Adapter saved to $OUTPUT_DIR/final_adapter"
echo ""
echo "To merge + push:  python finetune_copper.py --merge_and_push \\"
echo "  --output_dir $OUTPUT_DIR --hub_repo your-org/copper-7b"
