import json
import re
from pathlib import Path
from app.core.logger import logger

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
PROFILE_FILE = DATA_DIR / "user_profile.json"
SESSIONS_FILE = DATA_DIR / "sessions_history.json"

DEFAULT_PROFILE = {
  "user_name": "Akash",
  "facts": [
    "User name is Akash",
    "Hardware: Windows 11 with NVIDIA RTX 5060 Laptop GPU (8GB VRAM) and AMD Ryzen 9 8940HX",
    "Privacy: 100% local, air-gapped model execution via Ollama",
    "Preferences: Dark cyber-HUD, structured formatting, type-safe architecture"
  ],
  "preferences": {
    "voice": "en_US-amy-medium",
    "theme": "dark"
  }
}

class PersistentMemoryStore:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.profile = self._load_profile()
        self.sessions = self._load_sessions()

    def _load_profile(self) -> dict:
        try:
            if PROFILE_FILE.exists():
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading user_profile.json: {e}")
        self._save_profile(DEFAULT_PROFILE)
        return DEFAULT_PROFILE

    def _save_profile(self, data: dict):
        try:
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving user_profile.json: {e}")

    def _load_sessions(self) -> dict[str, list[dict[str, str]]]:
        try:
            if SESSIONS_FILE.exists():
                with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading sessions_history.json: {e}")
        return {}

    def _save_sessions(self):
        try:
            with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sessions_history.json: {e}")

    def get_user_name(self) -> str:
        return self.profile.get("user_name", "Akash")

    def set_user_name(self, name: str):
        self.profile["user_name"] = name
        # Add fact if not already present
        fact = f"User name is {name}"
        if fact not in self.profile.get("facts", []):
            self.profile.setdefault("facts", []).append(fact)
        self._save_profile(self.profile)

    def add_fact(self, fact: str):
        fact_clean = fact.strip()
        if not fact_clean:
            return
        facts = self.profile.setdefault("facts", [])
        if fact_clean not in facts:
            facts.append(fact_clean)
            self._save_profile(self.profile)

    def extract_and_store_facts(self, message: str):
        msg_lower = message.lower().strip()
        
        # Name detection patterns
        name_match = (
            re.search(r"(?:my name is|i am|call me|name's)\s+([a-zA-Z]+)", message, re.IGNORECASE)
            or re.search(r"^(?:i'm|im)\s+([a-zA-Z]+)", message, re.IGNORECASE)
        )
        if name_match:
            detected_name = name_match.group(1).capitalize()
            if detected_name.lower() not in ["here", "sorry", "asking", "fine", "ready", "thinking", "sure"]:
                self.set_user_name(detected_name)
                logger.info(f"Learned user name: {detected_name}")

        # Explicit remember pattern
        remember_match = re.search(r"(?:remember that|note that|don't forget that|keep in mind that)\s+(.*)", message, re.IGNORECASE)
        if remember_match:
            fact = remember_match.group(1).strip()
            self.add_fact(fact)
            logger.info(f"Learned persistent fact: {fact}")

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        return self.sessions.get(session_id, [])

    def append_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": role, "content": content})
        # Keep last 50 messages per session
        if len(self.sessions[session_id]) > 50:
            self.sessions[session_id] = self.sessions[session_id][-50:]
        self._save_sessions()

    def get_memory_prompt_snippet(self) -> str:
        user_name = self.get_user_name()
        facts = self.profile.get("facts", [])
        facts_list = "\n".join([f"- {f}" for f in facts[-8:]])
        return (
            f"[PERSISTENT USER PROFILE & LONG-TERM MEMORY]\n"
            f"• User Name: {user_name}\n"
            f"• Verified Core Facts & Context:\n"
            f"{facts_list}"
        )

persistent_memory = PersistentMemoryStore()
