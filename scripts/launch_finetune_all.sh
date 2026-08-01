#!/usr/bin/env bash
# ============================================================
# COPPER — Launch Fine-Tune for All Sub-Agents
# Generates each agent's dataset (if missing) and runs QLoRA
# fine-tuning for it, sequentially, one adapter per agent.
#
# Usage:
#   bash launch_finetune_all.sh [tier] [agent1,agent2,...]
#     tier:   24gb (default) | 40gb | 80gb   — GPU config profile
#     agents: comma-separated list (default: all 27 agents)
#
# Examples:
#   bash launch_finetune_all.sh                    # all 27 agents, 24gb profile
#   bash launch_finetune_all.sh 80gb                # all 27 agents, 80gb profile
#   bash launch_finetune_all.sh 24gb AXIS,AEON,CYPHER  # just three agents
#
# Each agent gets its own dataset at ./dataset/<AGENT>/ and its own LoRA
# adapter at ./<agent-lowercase>-lora/final_adapter — this is 27 separate
# fine-tunes of the base model, not one shared model. If you instead want a
# single model that routes across all agents (like the original COPPER
# orchestrator), use copper_dataset_gen.py + finetune_copper.py directly.
# ============================================================
set -euo pipefail

TIER="${1:-24gb}"
AGENTS_ARG="${2:-}"
MODEL="mistralai/Mistral-7B-Instruct-v0.3"
DATA_ROOT="./dataset"
SIZE_PER_AGENT=1500

ALL_AGENTS="AEGIS,AEON,AETHER,APEX,ARGUS,ATLAS,AXIS,BEACON,CANVAS,CHRONOS,CRUCIBLE,CYPHER,DIRECTOR,ECHO,ENIGMA,FORGE,GLITCH,GOLIATH,HAWK,HERMES,IRIS,KINETIC,LEDGER,LUMEN,MNEMONIC,NEXUS,OMNI,ORACLE,PHANTOM,PIVOT,POLYGLOT,PORTAL,PRISM,PROXY,PULSE,QUANTA,RAPTOR,RENDER,SIREN,SONAR,SPECTRE,SPIDER,SYNAPSE,TALON,TENSOR,VANGUARD,VAULT,VORTEX,WARDEN,ZENITH"
AGENTS="${AGENTS_ARG:-$ALL_AGENTS}"

# Note: COPPER itself (the orchestrator) is NOT in this loop — it has its own
# generator (copper_orchestrator_dataset_gen.py) and needs a separate
# finetune_agent.py --agent COPPER call since its dataset lives at
# ./dataset/COPPER/copper_{train,val,test}.jsonl, one level up from the
# per-agent convention. See the "Fine-tune COPPER" section at the bottom.

echo "📦 Installing dependencies …"
pip install -q -r requirements_finetune.txt

case "$TIER" in
  24gb) BATCH=2; GRAD_ACCUM=8; LORA_R=64;  LORA_ALPHA=128; MAX_SEQ=1024; EXTRA_FLAGS="" ;;
  40gb) BATCH=4; GRAD_ACCUM=4; LORA_R=128; LORA_ALPHA=256; MAX_SEQ=2048; EXTRA_FLAGS="" ;;
  80gb) BATCH=8; GRAD_ACCUM=2; LORA_R=128; LORA_ALPHA=256; MAX_SEQ=2048; EXTRA_FLAGS="--packing" ;;
  *) echo "❌ Unknown tier '$TIER'. Choose: 24gb | 40gb | 80gb"; exit 1 ;;
esac
echo "🖥  GPU profile: $TIER  (batch=$BATCH, grad_accum=$GRAD_ACCUM, lora_r=$LORA_R)"

IFS=',' read -ra AGENT_LIST <<< "$AGENTS"
TOTAL=${#AGENT_LIST[@]}
i=0

for AGENT in "${AGENT_LIST[@]}"; do
  i=$((i+1))
  AGENT_LOWER=$(echo "$AGENT" | tr '[:upper:]' '[:lower:]')
  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "[$i/$TOTAL] $AGENT"
  echo "════════════════════════════════════════════════════════"

  # ── Step 1: Generate dataset if not present ──
  if [ ! -f "$DATA_ROOT/$AGENT/${AGENT_LOWER}_train.jsonl" ]; then
    echo "📂 Dataset not found — generating $SIZE_PER_AGENT records …"
    python generate_agent_dataset.py --agent "$AGENT" --size "$SIZE_PER_AGENT" --outdir "$DATA_ROOT/$AGENT"
  else
    echo "📂 Dataset already exists at $DATA_ROOT/$AGENT — skipping generation."
  fi

  # ── Step 2: Fine-tune ──
  python finetune_agent.py \
    --agent          "$AGENT"       \
    --model          "$MODEL"       \
    --epochs         3              \
    --batch_size     "$BATCH"       \
    --grad_accum     "$GRAD_ACCUM"  \
    --lr             2e-4           \
    --lora_r         "$LORA_R"      \
    --lora_alpha     "$LORA_ALPHA"  \
    --max_seq_len    "$MAX_SEQ"     \
    --bf16 $EXTRA_FLAGS

  echo "✅ $AGENT adapter saved → ./${AGENT_LOWER}-lora/final_adapter"
done

echo ""
echo "🎉 All $TOTAL agent(s) fine-tuned."
echo "   Adapters are at ./<agent>-lora/final_adapter for each agent."
echo "   To merge + push one:  python finetune_agent.py --agent AXIS --merge_and_push --hub_repo your-org/axis-7b"

# ── Fine-tune COPPER (the orchestrator itself) ──
echo ""
echo "════════════════════════════════════════════════════════"
echo "COPPER (orchestrator)"
echo "════════════════════════════════════════════════════════"
if [ ! -f "$DATA_ROOT/COPPER/copper_train.jsonl" ]; then
  echo "📂 COPPER dataset not found — generating 2500 records …"
  python copper_orchestrator_dataset_gen.py --size 2500 --outdir "$DATA_ROOT/COPPER"
else
  echo "📂 COPPER dataset already exists — skipping generation."
fi

python finetune_agent.py \
  --agent          "COPPER"       \
  --model          "$MODEL"       \
  --epochs         3              \
  --batch_size     "$BATCH"       \
  --grad_accum     "$GRAD_ACCUM"  \
  --lr             2e-4           \
  --lora_r         "$LORA_R"      \
  --lora_alpha     "$LORA_ALPHA"  \
  --max_seq_len    "$MAX_SEQ"     \
  --bf16 $EXTRA_FLAGS

echo "✅ COPPER adapter saved → ./copper-lora/final_adapter"
