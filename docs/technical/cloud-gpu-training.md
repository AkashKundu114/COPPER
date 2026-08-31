# Cloud GPU Training Guide

How to rent a GPU and run the COPPER / sub-agent fine-tunes on it, end to
end. Pricing below was checked in **July 2026** — GPU rental rates move
often, so treat these as ballpark figures and re-check the provider's
pricing page before committing to a long run.

---

## 1. Do you actually need a cloud GPU?

`generate_agent_dataset.py`, `generate_all_agents.py`, and
`copper_orchestrator_dataset_gen.py` are pure CPU/Python — run those
anywhere, including this sandbox or your laptop, for free. You only need a
rented GPU for the `finetune_agent.py` step.

**VRAM you need**, using the default `mistralai/Mistral-7B-Instruct-v0.3`
base model with QLoRA (4-bit):

| Config | Min VRAM | Notes |
|---|---|---|
| QLoRA 4-bit, batch=2, seq_len=1024 (`24gb` preset) | ~16-20 GB | Fits on a 24 GB card with headroom |
| QLoRA 4-bit, batch=4, seq_len=2048 (`40gb` preset) | ~32-36 GB | Needs a 40 GB+ card |
| QLoRA 4-bit, batch=8, seq_len=2048, packing (`80gb` preset) | ~55-65 GB | Needs a 80 GB card |

If you swap in a larger base model (13B, 34B, 70B), scale up a tier or two.

---

## 2. Picking a provider

Three providers cover almost everyone's needs. All three work fine with
this pipeline — pick based on budget vs. reliability.

| Provider | RTX 4090 (24GB) | A100 80GB | H100 80GB | Notes |
|---|---|---|---|---|
| **RunPod** | ~$0.34-0.69/hr | ~$1.39-1.49/hr | ~$2.89-3.29/hr | Per-second billing, free egress, Community (cheaper, best-effort) vs Secure Cloud (SLA-backed) tiers |
| **Vast.ai** | ~$0.34-0.46/hr | ~$0.90-1.60/hr (verified hosts) | ~$1.87-2.50/hr | Marketplace — rates fluctuate with demand; pick "verified" hosts for reliability |
| **Lambda Labs** | — (not offered) | ~$1.29-2.06/hr | ~$2.49-3.29/hr | Fixed self-serve pricing, historically better driver/CUDA stability, but frequent capacity shortages on popular GPUs |

Rough cost to fine-tune **one agent** (1,500 records, 3 epochs, 24gb
preset, ~20-40 min): **$0.15-$0.50** on RunPod/Vast.ai.

Rough cost to fine-tune **all 30 agents + COPPER** sequentially via
`launch_finetune_all.sh` (31 runs × ~25 min average): **~13 GPU-hours**, or
roughly **$4.50-$9** on a 24gb-tier RTX 4090, **$18-$20** on an A100 80GB.
Running agents in parallel across multiple pods cuts wall-clock time
proportionally (cost stays about the same, since you're paying for the same
total GPU-hours either way).

---

## 3. Walkthrough: RunPod (recommended default)

1. **Create an account** at runpod.io and add a payment method.
2. **Deploy a Pod**:
   - Choose **Community Cloud** for cheapest rates (fine for this — the
     dataset already lives in your repo, no persistent SLA needed for a
     single training run).
   - GPU: RTX 4090 24GB for the `24gb` preset, or A100 80GB for `80gb`.
   - Template: pick a **PyTorch** template (e.g. "RunPod PyTorch 2.x") so
     CUDA/cuDNN are already installed.
   - Disk: 30-50 GB container disk is plenty for one model + adapters; more
     if you're training many agents and keeping every checkpoint.
3. **Connect** via the web terminal, or `ssh` using the connection details
   RunPod shows once the pod is running.
4. **Get the code onto the pod.** Simplest options:
   - `git clone` if you've pushed this framework to a repo, or
   - zip it locally and upload through RunPod's file browser / `scp`.
5. **Install dependencies and run:**
   ```bash
   cd copper_agents
   pip install -q -r requirements_finetune.txt

   # generate data (fast, CPU-only)
   python generate_all_agents.py --size 1500 --outdir ./dataset
   python copper_orchestrator_dataset_gen.py --size 2500 --outdir ./dataset/COPPER

   # fine-tune everything
   bash launch_finetune_all.sh 24gb
   ```
6. **Persist your results before the pod is destroyed.** RunPod's container
   disk is ephemeral once you terminate the pod — either:
   - attach a **Network Volume** and point `--output_dir` at it, or
   - `scp`/download the `*-lora/final_adapter` folders off the pod, or
   - use `--merge_and_push --hub_repo your-org/axis-7b` to push straight to
     the HuggingFace Hub (requires `huggingface-cli login` on the pod first).
7. **Stop or terminate the pod** the moment you're done — billing is
   per-second, but only while the pod is running.

---

## 4. Walkthrough: Vast.ai (cheapest, more hands-on)

1. Create an account, add credit.
2. Under **Search**, filter by GPU type and check "Verified" hosts if this
   is anything beyond a quick experiment (unverified hosts vary a lot in
   reliability and network speed).
3. Pick a template with PyTorch + CUDA preinstalled, or a bare Ubuntu image
   if you don't mind installing the stack yourself.
4. Once the instance is up, `ssh` in using the provided command.
5. Same steps as RunPod from here: clone/upload the code, `pip install -r
   requirements_finetune.txt`, generate data, run `launch_finetune_all.sh`.
6. Vast.ai instances are billed by the minute while running — **stop the
   instance**, don't just close the terminal, when you're done. Vast.ai
   keeps your disk image between stop/start (billed separately, cheaply)
   if you want to pause and resume later; destroy it if you're fully done.

---

## 5. Walkthrough: Lambda Labs (most "it just works", pricier / less available)

1. Create an account, add a payment method.
2. Launch an instance — Lambda's fixed catalog usually has A100/H100
   options; availability is the main constraint (popular GPUs often show
   as "out of capacity").
3. Lambda instances come with PyTorch/CUDA preinstalled via their
   "Lambda Stack" — you can usually skip straight to:
   ```bash
   pip install -q -r requirements_finetune.txt
   ```
4. Same generate → `launch_finetune_all.sh` flow as above.
5. Lambda bills hourly while the instance is running — terminate it from
   the dashboard when done.

---

## 6. Running long jobs safely: use `tmux` or `screen`

Fine-tuning all 31 models is a multi-hour job. If your SSH session drops,
you don't want to lose the run. Start it inside a terminal multiplexer:

```bash
tmux new -s copper-finetune
bash launch_finetune_all.sh 24gb
# detach with Ctrl+B then D — the job keeps running
# reconnect any time with: tmux attach -t copper-finetune
```

(`screen -S copper-finetune` / `screen -r copper-finetune` works the same
way if `tmux` isn't installed.)

---

## 7. Monitoring while it runs

- **GPU utilization / VRAM**: `watch -n 2 nvidia-smi` in a second terminal
  (or a second `tmux` pane).
- **Training loss**: `finetune_agent.py` logs to stdout every
  `--logging_steps` (default 25) and to `<output_dir>/logs` via
  TensorBoard-compatible logs.
- **Weights & Biases** (optional): pass `--wandb_project your-project-name`
  to `finetune_agent.py` (or add it inside `launch_finetune_all.sh`) and
  `pip install wandb` first — useful if you want loss curves and comparisons
  across all 31 agent fine-tunes in one dashboard.

---

## 8. Common issues

| Symptom | Likely cause / fix |
|---|---|
| `CUDA out of memory` | Drop `--batch_size`, raise `--grad_accum` to compensate, or drop `--max_seq_len`. Or move up a GPU tier. |
| `ImportError: bitsandbytes` / CUDA mismatch | `bitsandbytes` needs a CUDA version matching your PyTorch build — reinstall torch for your CUDA version per the comment at the top of `requirements_finetune.txt`, then reinstall `bitsandbytes`. |
| Training loss is `NaN` | Usually fp16 numerical instability — make sure `--bf16` is set (default) and `--fp16` is not, unless you're on an older GPU (V100) that lacks bf16 support. |
| Hangs on "Loading model" for a long time | First run downloads the base model from HuggingFace (~14 GB for a 7B model) — check network, or pre-download with `huggingface-cli download mistralai/Mistral-7B-Instruct-v0.3`. |
| `401 Unauthorized` pulling the base model | Some models (e.g. Llama family) are gated — run `huggingface-cli login` with a token that has accepted the model's license on huggingface.co first. |
| Pod/instance terminated and you lost the adapter | Always copy `*-lora/final_adapter` off-box (or push to the Hub) before stopping a pod — container disks are usually ephemeral. |

---

## 9. After training: merge and share

```bash
python finetune_agent.py --agent AXIS --merge_and_push \
  --output_dir ./axis-lora --hub_repo your-org/axis-7b
```

This merges the LoRA adapter into the base model's weights and pushes the
full merged model to your HuggingFace Hub repo (requires
`huggingface-cli login` first). Repeat per agent, or write a small loop
over `ALL_AGENTS` similar to `launch_finetune_all.sh` if you want to push
all 31 at once.
