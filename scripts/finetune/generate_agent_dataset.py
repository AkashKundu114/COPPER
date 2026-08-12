import argparse
import json
import random
from pathlib import Path
from agent_configs import AGENT_CONFIGS, MODEL_MAP, _sys
from shared_vocab import fill_track, random_timestamp
FOLLOWUP_TEMPLATES = ['Actually, can you also double check {noun}?', 'Wait — what if {noun} changes?', 'Can you show me the raw output for that?', 'Good. Now do the same thing but faster.', 'One more thing — can you undo that if needed?', 'Thanks. Can you confirm that actually succeeded?']

def build_record(agent: str, cfg: dict, rng: random.Random) -> dict:
    system_prompt = _sys(agent, cfg['role'], cfg['personality'], cfg['payload_fields'])
    intent_template = rng.choice(cfg['intents'])
    extra_vocab = cfg.get('extra_vocab', {})
    user_text, slots = fill_track(intent_template, extra_vocab)
    dialogue = rng.choice(cfg['dialogue'])
    try:
        dialogue = dialogue.format(**slots)
    except (KeyError, IndexError):
        pass
    payload = cfg['payload_fn'](slots, user_text, rng)
    assistant_text = f'[DIALOGUE] {dialogue}\n\n[TECHNICAL_PAYLOAD] {json.dumps(payload, ensure_ascii=False)}'
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_text}, {'role': 'assistant', 'content': assistant_text}]
    if rng.random() < 0.0:
        pass
    return {'messages': messages, '_meta': {'agent': agent, 'model_tier': MODEL_MAP.get(agent, 'UNKNOWN'), 'timestamp': random_timestamp()}}

def maybe_add_followup(record: dict, cfg: dict, rng: random.Random) -> dict:
    noun = rng.choice(['that', 'the result', 'the timing', 'the output', 'the target'])
    followup_user = rng.choice(FOLLOWUP_TEMPLATES).format(noun=noun)
    dialogue = rng.choice(cfg['dialogue'])
    payload = cfg['payload_fn']({}, followup_user, rng)
    followup_assistant = f'[DIALOGUE] {dialogue}\n\n[TECHNICAL_PAYLOAD] {json.dumps(payload, ensure_ascii=False)}'
    record['messages'].append({'role': 'user', 'content': followup_user})
    record['messages'].append({'role': 'assistant', 'content': followup_assistant})
    return record

def generate_dataset(agent: str, size: int, seed: int=42, multiturn_pct: float=0.12) -> list[dict]:
    if agent not in AGENT_CONFIGS:
        raise ValueError(f"Unknown agent '{agent}'. Known agents: {sorted(AGENT_CONFIGS)}")
    cfg = AGENT_CONFIGS[agent]
    rng = random.Random(seed)
    records = []
    seen_user_texts = set()
    attempts = 0
    while len(records) < size and attempts < size * 20:
        attempts += 1
        record = build_record(agent, cfg, rng)
        user_text = record['messages'][1]['content']
        if user_text in seen_user_texts and rng.random() < 0.85:
            continue
        if rng.random() < multiturn_pct:
            record = maybe_add_followup(record, cfg, rng)
        seen_user_texts.add(user_text)
        records.append(record)
    return records

def split_records(records: list[dict], seed: int=42) -> tuple[list, list, list]:
    rng = random.Random(seed)
    shuffled = records[:]
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * 0.8)
    n_val = int(n * 0.1)
    train = shuffled[:n_train]
    val = shuffled[n_train:n_train + n_val]
    test = shuffled[n_train + n_val:]
    return (train, val, test)

def write_jsonl(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for r in records:
            clean = {'messages': r['messages']}
            f.write(json.dumps(clean, ensure_ascii=False) + '\n')

def write_manifest(agent: str, outdir: Path, train: list, val: list, test: list) -> None:
    manifest = {'agent': agent, 'model_tier': MODEL_MAP.get(agent, 'UNKNOWN'), 'total_records': len(train) + len(val) + len(test), 'splits': {'train': {'file': f'{agent.lower()}_train.jsonl', 'count': len(train)}, 'val': {'file': f'{agent.lower()}_val.jsonl', 'count': len(val)}, 'test': {'file': f'{agent.lower()}_test.jsonl', 'count': len(test)}}}
    with open(outdir / f'{agent.lower()}_dataset_manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

def main():
    p = argparse.ArgumentParser(description='Generate a fine-tuning dataset for one COPPER sub-agent')
    p.add_argument('--agent', type=str, required=True, help=f'Agent name. One of: {sorted(AGENT_CONFIGS)}')
    p.add_argument('--size', type=int, default=1500, help='Total records across train/val/test (1000-2000 recommended)')
    p.add_argument('--outdir', type=str, default=None, help='Output directory (default: ./dataset/<AGENT>)')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--multiturn_pct', type=float, default=0.12, help='Fraction of records with a follow-up turn')
    args = p.parse_args()
    agent = args.agent.upper()
    outdir = Path(args.outdir) if args.outdir else Path(f'./dataset/{agent}')
    records = generate_dataset(agent, args.size, seed=args.seed, multiturn_pct=args.multiturn_pct)
    train, val, test = split_records(records, seed=args.seed)
    write_jsonl(train, outdir / f'{agent.lower()}_train.jsonl')
    write_jsonl(val, outdir / f'{agent.lower()}_val.jsonl')
    write_jsonl(test, outdir / f'{agent.lower()}_test.jsonl')
    write_manifest(agent, outdir, train, val, test)
    print(f'✅ {agent}: {len(records)} records → {outdir} (train={len(train)}, val={len(val)}, test={len(test)})')
if __name__ == '__main__':
    main()