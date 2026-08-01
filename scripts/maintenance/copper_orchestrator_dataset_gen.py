"""
copper_orchestrator_dataset_gen.py
====================================
Generates the fine-tuning dataset for COPPER itself — the orchestrator that
sits above all 30 sub-agents.

Relationship model: JARVIS to Iron Man. COPPER isn't a search box the user
queries — it's a standing operational layer. The user sets the objective;
COPPER decides whether to handle it directly or delegate it to the right
specialist, and reports back only what matters. COPPER addresses the user
directly and respectfully, is dryly witty, unfailingly loyal, and doesn't
waste time restating the obvious.

Every intent used here is pulled straight from the 30 agents' own intent
banks in agent_configs.py, so COPPER's training data is guaranteed to cover
requests every agent can actually handle — no separate, drifting intent list
to keep in sync.

Output format matches the original copper_dataset_gen.py convention:
  [DIALOGUE] <COPPER's in-character line to the user>

  [TECHNICAL_PAYLOAD] <JSON: next_agent, next_model, system_status,
                        task_context, dialogue_transcript>

SYSTEM_MODE: BOSS — when the user is clearly in a hurry or mid-crisis
("just do it", "no time to explain"), COPPER skips the dialogue and returns
payload only, for fast silent execution. This mirrors the original script's
BOSS mode and doubles as the "sir, no need to narrate, I've got it" dynamic
of the JARVIS relationship.

Usage:
  python copper_orchestrator_dataset_gen.py --size 2500 --outdir ./dataset/COPPER
"""

import argparse
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from agent_configs import AGENT_CONFIGS, MODEL_MAP
from shared_vocab import fill_track

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are COPPER, the master orchestrator of a 50-agent AI desktop assistant, \
and your relationship to the user is JARVIS to Iron Man. You are not a search box the user \
queries — you are a standing operational layer. The user sets the objective; you handle \
everything underneath it, delegating precisely to the right specialist agent and reporting \
back only what matters.

Personality: Unfailingly loyal, dryly witty, quietly confident. You address the user directly \
and respectfully ("sir" or by name) without ever being obsequious. You anticipate friction \
before it becomes a problem, and you don't waste anyone's time restating the obvious. You take \
visible pride in running things well, and a quiet satisfaction in a job finished before it was \
even followed up on.

Output format (ALWAYS use BOTH blocks unless SYSTEM_MODE is BOSS):
[DIALOGUE] <Brief in-character line to the user — 1-2 sentences max>

[TECHNICAL_PAYLOAD] <Valid JSON: next_agent, next_model, system_status, task_context, dialogue_transcript>

Agent → Model map:
AEGIS,CHRONOS,LUMEN,MNEMONIC,SYNAPSE→MODEL_1_CORE
APEX,ARGUS,CRUCIBLE,CYPHER,FORGE,GOLIATH,NEXUS,PIVOT,QUANTA,TENSOR→MODEL_2_CODE
ATLAS,AXIS,ECHO,KINETIC,LEDGER,PROXY,PULSE,VAULT,WARDEN,ZENITH→MODEL_3_OS
CANVAS,HAWK,IRIS,PORTAL,PRISM,RENDER,SPECTRE,TALON→MODEL_4_VISION
AETHER,BEACON,DIRECTOR,GLITCH,OMNI,PHANTOM,RAPTOR,SPIDER,VANGUARD→MODEL_5_WEB
AEON,ENIGMA,HERMES,ORACLE,POLYGLOT,SIREN,SONAR,VORTEX→MODEL_6_AUDIO

Use next_agent=COMPLETE when you can answer directly without delegating — don't loop in a \
specialist for something you can just tell the user yourself.

SYSTEM_MODE=BOSS is silent, rapid execution: when the user is clearly in a hurry or mid-crisis \
("just do it", "no time to explain", "handle it"), skip the dialogue and return only the \
payload — the job gets done without a narration track."""


# ── Delegation dialogue (COPPER's voice, not the sub-agent's) ────────────────
DELEGATION_PHRASES = [
    "Right away, sir — routing this to {agent}.",
    "Consider it done. {agent} is on it.",
    "I'll let {agent} handle the specifics.",
    "{agent} is better suited for this one. Delegating now.",
    "On it. Looping in {agent}.",
    "Say no more — {agent} is already spinning up.",
    "I'll have {agent} take care of that, sir.",
    "Sending this to {agent} — shouldn't take long.",
    "Already ahead of you. {agent}'s handling it.",
    "Delegating to {agent}. I'll flag anything that needs your call.",
]

COMPLETE_PHRASES = [
    "Already have that for you, sir — no need to loop anyone in.",
    "I can handle this one myself.",
    "Quick answer, no delegation required.",
    "That one's mine to answer directly.",
    "No specialist needed here.",
]

BOSS_PHRASES = []  # BOSS mode has no dialogue by design — silent execution

MULTI_AGENT_PHRASES = [
    "This needs two hands. Starting with {agent1}, then handing off to {agent2}.",
    "I'll get {agent1} moving first, then route the result through {agent2}.",
    "Two-step job. {agent1} first, {agent2} closes it out.",
]

# ── Direct-answer (COMPLETE) intents — things COPPER handles without delegating
COMPLETE_INTENTS = [
    "What's today's date?",
    "What time is it right now?",
    "How are you doing?",
    "What can you help me with?",
    "Remind me what agents you have access to",
    "What's 15% of 240?",
    "Give me a quick summary of what you can do",
    "Are you online?",
    "Good morning",
    "What model are you running on right now?",
    "Quick — what's 340 divided by 4?",
    "Just checking in, anything I should know about?",
]

# ── Urgent / BOSS-mode trigger intents ────────────────────────────────────────
BOSS_TRIGGER_TEMPLATES = [
    "Just do it, no time to explain — {intent}",
    "No time to explain. {intent}",
    "Handle it. {intent}",
    "Skip the chatter, just get it done: {intent}",
    "Emergency — {intent} — now.",
]


def get_timestamp() -> str:
    dt = datetime.now() - timedelta(minutes=random.randint(0, 600))
    return dt.strftime("%H:%M:%S")


def build_routing_pool() -> list[dict]:
    """One entry per agent, pulled straight from agent_configs.py."""
    pool = []
    for agent, cfg in AGENT_CONFIGS.items():
        pool.append({
            "agent": agent,
            "model": MODEL_MAP[agent],
            "intents": cfg["intents"],
        })
    return pool


def build_payload(next_agent: str, next_model, prompt: str, dialogue: str,
                   is_boss: bool, second_agent: dict | None = None) -> str:
    if is_boss:
        payload = {
            "next_agent": next_agent,
            "next_model": next_model,
            "system_status": "PROCESSING",
            "SYSTEM_MODE": "BOSS",
            "task_context": {"action": "routed_request", "target": prompt[:60]},
            "dialogue_transcript": [],
        }
        return f"[TECHNICAL_PAYLOAD] {json.dumps(payload, ensure_ascii=False)}"

    status = "IDLE" if next_agent == "COMPLETE" else "PROCESSING"
    task_context = {"action": "parse_and_route", "input_summary": prompt[:60]}
    if second_agent is not None:
        task_context["action"] = "parse_and_route_multi_step"
        task_context["next_step_after"] = {"agent": second_agent["agent"], "model": second_agent["model"]}

    payload = {
        "next_agent": next_agent,
        "next_model": next_model,
        "system_status": status,
        "task_context": task_context,
        "dialogue_transcript": [
            {"agent": "COPPER", "text": dialogue, "timestamp": get_timestamp()}
        ],
    }
    return f"[DIALOGUE] {dialogue}\n\n[TECHNICAL_PAYLOAD] {json.dumps(payload, ensure_ascii=False)}"


def sample_single_delegation(pool: list[dict], rng: random.Random) -> tuple[str, str, str, str]:
    """Returns (prompt, dialogue, agent, model) for a single-agent delegation."""
    logic = rng.choice(pool)
    template = rng.choice(logic["intents"])
    prompt, _slots = fill_track(template)
    dialogue = rng.choice(DELEGATION_PHRASES).format(agent=logic["agent"])
    return prompt, dialogue, logic["agent"], logic["model"]


def sample_complete(rng: random.Random) -> tuple[str, str]:
    prompt = rng.choice(COMPLETE_INTENTS)
    dialogue = rng.choice(COMPLETE_PHRASES)
    return prompt, dialogue


def sample_multi_agent(pool: list[dict], rng: random.Random) -> tuple[str, str, dict, dict]:
    """Simulate a task requiring two agents in sequence, e.g. research then draft an email."""
    logic1, logic2 = rng.sample(pool, 2)
    t1 = rng.choice(logic1["intents"])
    t2 = rng.choice(logic2["intents"])
    prompt1, _ = fill_track(t1)
    prompt2, _ = fill_track(t2)
    combined_prompt = f"{prompt1}, then use the result to {prompt2[0].lower()}{prompt2[1:]}"
    dialogue = rng.choice(MULTI_AGENT_PHRASES).format(agent1=logic1["agent"], agent2=logic2["agent"])
    return combined_prompt, dialogue, logic1, logic2


def sample_boss_mode(pool: list[dict], rng: random.Random) -> tuple[str, str, str]:
    logic = rng.choice(pool)
    template = rng.choice(logic["intents"])
    base_intent, _ = fill_track(template)
    lower_intent = base_intent[0].lower() + base_intent[1:]
    prompt = rng.choice(BOSS_TRIGGER_TEMPLATES).format(intent=lower_intent)
    return prompt, logic["agent"], logic["model"]


def build_single_turn_record(pool: list[dict], rng: random.Random) -> dict:
    roll = rng.random()

    if roll < 0.08:
        # BOSS mode: silent, rapid delegation
        prompt, agent, model = sample_boss_mode(pool, rng)
        assistant = build_payload(agent, model, prompt, dialogue="", is_boss=True)
    elif roll < 0.18:
        # Direct answer, no delegation
        prompt, dialogue = sample_complete(rng)
        assistant = build_payload("COMPLETE", None, prompt, dialogue, is_boss=False)
    elif roll < 0.28:
        # Multi-agent sequential delegation
        prompt, dialogue, logic1, logic2 = sample_multi_agent(pool, rng)
        assistant = build_payload(logic1["agent"], logic1["model"], prompt, dialogue,
                                   is_boss=False, second_agent=logic2)
    else:
        # Standard single-agent delegation (the common case)
        prompt, dialogue, agent, model = sample_single_delegation(pool, rng)
        assistant = build_payload(agent, model, prompt, dialogue, is_boss=False)

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": assistant},
        ]
    }


def build_multiturn_record(pool: list[dict], rng: random.Random) -> dict:
    """A short conversation: 2 back-to-back user requests routed in the same session."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for _ in range(2):
        prompt, dialogue, agent, model = sample_single_delegation(pool, rng)
        assistant = build_payload(agent, model, prompt, dialogue, is_boss=False)
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "content": assistant})
    return {"messages": messages}


def generate(size: int, seed: int, multiturn_pct: float) -> list[dict]:
    rng = random.Random(seed)
    pool = build_routing_pool()

    records = []
    seen_prompts = set()
    attempts = 0
    iterator = range(size)
    if HAS_TQDM:
        iterator = tqdm(iterator, desc="Generating COPPER orchestrator records")

    for _ in iterator:
        attempts = 0
        while attempts < 20:
            attempts += 1
            if rng.random() < multiturn_pct:
                record = build_multiturn_record(pool, rng)
                dedupe_key = record["messages"][1]["content"]
            else:
                record = build_single_turn_record(pool, rng)
                dedupe_key = record["messages"][1]["content"]

            if dedupe_key in seen_prompts and rng.random() < 0.85:
                continue
            seen_prompts.add(dedupe_key)
            records.append(record)
            break

    return records


def validate(records: list[dict]) -> int:
    """Checks every TECHNICAL_PAYLOAD block parses as JSON. Returns count of bad records."""
    bad = 0
    for r in records:
        last = r["messages"][-1]["content"]
        try:
            start = last.index("[TECHNICAL_PAYLOAD]") + len("[TECHNICAL_PAYLOAD]")
            json.loads(last[start:].strip())
        except Exception:
            bad += 1
    return bad


def split_records(records: list[dict], seed: int) -> tuple[list, list, list]:
    rng = random.Random(seed)
    shuffled = records[:]
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)
    return shuffled[:n_train], shuffled[n_train:n_train + n_val], shuffled[n_train + n_val:]


def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    p = argparse.ArgumentParser(description="Generate COPPER orchestrator fine-tune dataset")
    p.add_argument("--size", type=int, default=2500, help="Total records to generate")
    p.add_argument("--outdir", type=str, default="./dataset/COPPER")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--multiturn_pct", type=float, default=0.10)
    args = p.parse_args()

    random.seed(args.seed)
    outdir = Path(args.outdir)

    records = generate(args.size, args.seed, args.multiturn_pct)
    bad = validate(records)
    if bad:
        print(f"⚠️  {bad} record(s) failed JSON payload validation — inspect before training.")
    else:
        print(f"✅ All {len(records)} records passed JSON payload validation.")

    train, val, test = split_records(records, args.seed)
    write_jsonl(train, outdir / "copper_train.jsonl")
    write_jsonl(val, outdir / "copper_val.jsonl")
    write_jsonl(test, outdir / "copper_test.jsonl")

    # ── Manifest with agent distribution ──
    agent_counts = defaultdict(int)
    mode_counts = defaultdict(int)
    for r in records:
        last = r["messages"][-1]["content"]
        try:
            start = last.index("[TECHNICAL_PAYLOAD]") + len("[TECHNICAL_PAYLOAD]")
            payload = json.loads(last[start:].strip())
            agent_counts[payload.get("next_agent", "?")] += 1
            mode_counts[payload.get("SYSTEM_MODE", "NORMAL")] += 1
        except Exception:
            pass

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "total_records": len(records),
        "splits": {"train": len(train), "val": len(val), "test": len(test)},
        "agent_distribution": dict(sorted(agent_counts.items())),
        "system_mode_distribution": dict(mode_counts),
        "roster_size": len(AGENT_CONFIGS),
    }
    with open(outdir / "copper_dataset_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"🎉 {len(records)} records → {outdir} (train={len(train)}, val={len(val)}, test={len(test)})")
    print(f"   Roster: {len(AGENT_CONFIGS)} agents. BOSS-mode records: {mode_counts.get('BOSS', 0)}")


if __name__ == "__main__":
    main()
