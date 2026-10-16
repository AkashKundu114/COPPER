import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
CHROMA_DIR = REPO_ROOT / "backend" / "data" / "chroma"
SANDBOX_DIR = REPO_ROOT / "backend" / "sandbox"

RESET_STATE_TEMPLATES = {
    "commitments.json": "[]",
    "causal_events.json": "[]",
    "causal_links.json": "[]",
    "device_sync.json": "[]",
    "notifications.json": "[]",
    "pattern_history.json": "[]",
    "predictions.json": "[]",
    "session_handoffs.json": "[]",
    "skill_gaps.json": "[]",
    "user_profile.json": """{
  "user_name": "Demo User",
  "role": "Software Engineer & AI Researcher",
  "facts": [
    "User name is Demo User",
    "Role & Work: Software Engineer developing local-first intelligent desktop systems",
    "Hardware: Local workstation with dedicated GPU and offline acceleration",
    "Privacy: 100% local, air-gapped model execution via Ollama",
    "Preferences: Dark cyber-HUD, structured formatting, type-safe architecture"
  ],
  "preferences": {
    "voice": "en-US-AvaNeural",
    "theme": "dark"
  }
}"""
}

def wipe_all_data(interactive: bool = True):
    print("=" * 60)
    print("COPPER DATA PURGE & PRIVACY RESET")
    print("=" * 60)
    print("This will permanently delete all stored epistemic memories,")
    print("conversation histories, meeting notes, audio recordings,")
    print("and vector database embeddings.")
    print("=" * 60)

    if interactive:
        confirm = input("Type 'WIPE' to confirm permanent deletion: ").strip()
        if confirm != "WIPE":
            print("[*] Aborted. No data was deleted.")
            sys.exit(0)

    db_files = list(DATA_DIR.glob("*.db*")) + list(REPO_ROOT.glob("backend/app/ai/ambient/*.db*"))
    for db in db_files:
        try:
            if db.is_file():
                db.unlink()
                print(f"[+] Deleted database: {db.relative_to(REPO_ROOT)}")
        except Exception as e:
            print(f"[!] Warning: Could not delete {db}: {e}")

    if CHROMA_DIR.exists():
        try:
            shutil.rmtree(CHROMA_DIR)
            print(f"[+] Deleted vector store: {CHROMA_DIR.relative_to(REPO_ROOT)}")
        except Exception as e:
            print(f"[!] Warning: Could not delete Chroma directory: {e}")

    runtime_dirs = [
        DATA_DIR / "audio",
        DATA_DIR / "conversations",
        DATA_DIR / "logs",
        DATA_DIR / "meetings",
        DATA_DIR / "reminders",
        DATA_DIR / "screenshots",
        SANDBOX_DIR
    ]

    for r_dir in runtime_dirs:
        if r_dir.exists():
            for item in r_dir.iterdir():
                if item.name == ".gitkeep":
                    continue
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception as e:
                    print(f"[!] Warning deleting {item}: {e}")
            print(f"[+] Cleaned directory: {r_dir.relative_to(REPO_ROOT)}")

    for fname, default_content in RESET_STATE_TEMPLATES.items():
        fpath = DATA_DIR / fname
        try:
            fpath.write_text(default_content.strip() + "\n", encoding="utf-8")
            print(f"[+] Reset state template: {fpath.relative_to(REPO_ROOT)}")
        except Exception as e:
            print(f"[!] Warning writing {fpath}: {e}")

    print("\n[+] Data wipe complete. All persistent state has been reset to factory alpha defaults.")

if __name__ == "__main__":
    is_force = "--force" in sys.argv or "-f" in sys.argv
    wipe_all_data(interactive=not is_force)
