import json
import re
from pathlib import Path
from app.core.logger import logger

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
PROFILE_FILE = DATA_DIR / "user_profile.json"
SESSIONS_FILE = DATA_DIR / "sessions_history.json"

DEFAULT_PROFILE = {
  "user_name": "Akash Kundu",
  "facts": [
    "User name is Akash Kundu",
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
                    data = json.load(f)
                    if not data.get("user_name"):
                        data["user_name"] = "Akash Kundu"
                    return data
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
        return self.profile.get("user_name", "Akash Kundu")

    def set_user_name(self, name: str):
        clean_name = name.strip()
        if not clean_name:
            return
        self.profile["user_name"] = clean_name
        fact = f"User name is {clean_name}"
        if fact not in self.profile.get("facts", []):
            self.profile.setdefault("facts", []).append(fact)
        self._save_profile(self.profile)
        logger.info(f"Updated user name in persistent memory to: {clean_name}")

    def add_fact(self, fact: str):
        fact_clean = fact.strip()
        if not fact_clean:
            return
        facts = self.profile.setdefault("facts", [])
        if fact_clean not in facts:
            facts.append(fact_clean)
            self._save_profile(self.profile)
            logger.info(f"Learned persistent fact: {fact_clean}")

    def extract_and_store_facts(self, message: str):
        text = message.strip()
        lower = text.lower()

        # Ignore questions
        if "?" in text or any(lower.startswith(q) for q in ["what", "who", "where", "when", "why", "how", "is", "are", "can", "could", "do", "tell"]):
            return

        # 1. Explicit name patterns
        name_match = (
            re.search(r"(?:my name is|call me|name's|name is)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", text, re.IGNORECASE)
            or re.search(r"^(?:i am|i'm|im)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)", text, re.IGNORECASE)
        )
        if name_match:
            detected = name_match.group(1).strip()
            if detected.lower() not in ["here", "sorry", "asking", "fine", "ready", "thinking", "sure", "testing", "tired", "back", "good", "happy"]:
                self.set_user_name(detected)
                return

        # 2. Direct pure capitalized name (e.g. "Akash Kundu" or "Akash")
        words = text.split()
        if 1 <= len(words) <= 3 and all(w[0].isupper() and w.isalpha() for w in words):
            stop_words = {"yes", "no", "ok", "okay", "hello", "hi", "hey", "help", "sure", "thanks", "clear", "cancel", "stop", "done", "wait"}
            if lower not in stop_words:
                self.set_user_name(text)
                return

        # 3. Explicit memory commands
        remember_match = re.search(r"(?:remember that|note that|don't forget that|keep in mind that)\s+(.*)", text, re.IGNORECASE)
        if remember_match:
            fact = remember_match.group(1).strip()
            self.add_fact(fact)

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        return self.sessions.get(session_id, [])

    def append_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": role, "content": content})
        if len(self.sessions[session_id]) > 50:
            self.sessions[session_id] = self.sessions[session_id][-50:]
        self._save_sessions()

    def get_memory_prompt_snippet(self) -> str:
        user_name = self.get_user_name()
        facts = self.profile.get("facts", [])
        facts_list = "\n".join([f"• {f}" for f in facts])
        return (
            f"[CRITICAL USER IDENTITY & PERSISTENT MEMORY]\n"
            f"• User Name: {user_name}\n"
            f"• Verified Core Facts:\n"
            f"{facts_list}\n"
            f"• CRITICAL INSTRUCTION: You already know the user! Their name is '{user_name}'. When asked 'what is my name', 'who am I', or who you are speaking to, NEVER say you don't know. Always respond directly that their name is {user_name}."
        )

persistent_memory = PersistentMemoryStore()
