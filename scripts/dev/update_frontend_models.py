from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
AGENTS_TS = ROOT_DIR / "frontend" / "src" / "constants" / "agents.ts"

mapping = [
    ('"llama3.1:8b"', '"qwen2.5:14b"'),
    ('"deepseek-r1:7b"', '"deepseek-r1:14b"'),
    ('"qwen2.5-coder:7b"', '"qwen2.5-coder-abliterated:14b"'),
    ('"mistral:7b"', '"mistral-nemo:12b"'),
    ('"qwen2-vl:7b"', '"qwen2.5-vl:3b"'),
    ('"qwen2.5:7b"', '"phi4:14b"'),
    ('"whisper-base"', '"whisper-large-v3-turbo"'),
    ('"piper-tts"', '"kokoro-tts"'),
]

text = AGENTS_TS.read_text(encoding="utf-8")
for old, new in mapping:
    count = text.count(old)
    text = text.replace(old, new)
    print(f"Replaced {old} -> {new}: {count} occurrences")

AGENTS_TS.write_text(text, encoding="utf-8")
print("\n[+] Successfully synchronized frontend/src/constants/agents.ts!")
