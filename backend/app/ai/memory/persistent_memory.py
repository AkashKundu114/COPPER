import json
import re
from pathlib import Path

from app.core.logger import logger

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
PROFILES_DIR = DATA_DIR / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
PROFILE_FILE = PROFILES_DIR / "active_user.json"
SESSIONS_FILE = DATA_DIR / "sessions_history.json"

DEFAULT_PROFILE = {
    "user_name": "Akash Kundu",
    "role": "Software Engineer & Full-Stack Developer",
    "facts": [
        "User name is Akash Kundu",
        "Role & Work: Software Engineer & Developer working on Python, TypeScript, and AI operating systems",
        "Hardware: Windows 11 with NVIDIA RTX 5060 Laptop GPU (8GB VRAM) and AMD Ryzen 9 8940HX",
        "Privacy: 100% local, air-gapped model execution via Ollama",
        "Preferences: Dark cyber-HUD, structured formatting, type-safe architecture",
    ],
    "preferences": {"voice": "en-US-AvaNeural", "theme": "dark"},
}


class PersistentMemoryStore:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.profile = self._load_profile()
        self.sessions = self._load_sessions()

    def _load_profile(self) -> dict:
        try:
            if PROFILE_FILE.exists():
                with open(PROFILE_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                    name = data.get("user_name", "")
                    if (
                        not name
                        or len(name) < 3
                        or name.lower() in ["f", "who am i", "whats my name", "dude", "clear vram"]
                    ):
                        data["user_name"] = "Akash Kundu"
                    data.setdefault("role", "Software Engineer & Full-Stack Developer")
                    data["facts"] = [
                        f
                        for f in data.get("facts", [])
                        if not any(
                            bad in f.lower()
                            for bad in [
                                "who am i",
                                "whats my name",
                                "user name is f",
                                "user name is dude",
                                "user name is clear",
                            ]
                        )
                    ]
                    if "User name is Akash Kundu" not in data["facts"]:
                        data["facts"].insert(0, "User name is Akash Kundu")
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
                with open(SESSIONS_FILE, encoding="utf-8") as f:
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
        if not clean_name or len(clean_name) < 2:
            return
        # Block single chars or commands from becoming names
        if len(clean_name) <= 2 or clean_name.lower() in [
            "f",
            "gf",
            "who am i",
            "whats my name",
            "what do i do",
            "how to",
            "dude",
            "clear",
            "clear vram",
            "unload",
        ]:
            return

        self.profile["user_name"] = clean_name
        fact = f"User name is {clean_name}"
        if fact not in self.profile.get("facts", []):
            self.profile.setdefault("facts", []).append(fact)
        self._save_profile(self.profile)
        logger.info(f"User name updated in persistent memory: {clean_name}")

    def add_fact(self, fact: str):
        fact_clean = fact.strip()
        if not fact_clean or len(fact_clean) < 3:
            return
        facts = self.profile.setdefault("facts", [])
        if fact_clean not in facts:
            facts.append(fact_clean)
            self._save_profile(self.profile)
            logger.info(f"Learned persistent fact: {fact_clean}")

    def extract_and_store_facts(self, message: str):
        text = message.strip()
        lower = text.lower()

        # Strict ignore for questions, single letters, short words, commands
        if (
            "?" in text
            or len(text) < 4
            or any(
                lower.startswith(q)
                for q in [
                    "what",
                    "who",
                    "where",
                    "when",
                    "why",
                    "how",
                    "is",
                    "are",
                    "can",
                    "could",
                    "do",
                    "tell",
                    "i mean",
                    "did i",
                ]
            )
        ):
            return

        # ONLY recognize explicit name introductions (e.g. "My name is Akash", "Call me Akash Kundu")
        name_match = re.search(
            r"\b(?:my name is|call me|name's|name is)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\b", text
        ) or re.search(r"^(?:I am|I'm)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)$", text)
        if name_match:
            detected = name_match.group(1).strip()
            blacklist = {
                "here",
                "sorry",
                "asking",
                "fine",
                "ready",
                "thinking",
                "sure",
                "testing",
                "tired",
                "back",
                "good",
                "happy",
                "dude",
                "clear",
            }
            if detected.lower() not in blacklist and len(detected) >= 3:
                self.set_user_name(detected)
                return

        # Explicit memory commands (e.g. "remember that I prefer dark mode")
        remember_match = re.search(
            r"\b(?:remember that|note that|don't forget that|keep in mind that)\s+(.*)", text, re.IGNORECASE
        )
        if remember_match:
            fact = remember_match.group(1).strip()
            self.add_fact(fact)

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        raw = self.sessions.get(session_id, [])
        clean = []
        for m in raw:
            content = m.get("content", "")
            if any(
                content.startswith(err)
                for err in [
                    "Ollama returned status",
                    "Cannot reach local Ollama",
                    "Cannot reach the local Ollama",
                    "Ollama model '",
                ]
            ):
                continue
            clean.append(m)
        return clean

    def append_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append({"role": role, "content": content})
        if len(self.sessions[session_id]) > 50:
            self.sessions[session_id] = self.sessions[session_id][-50:]
        self._save_sessions()

    def get_memory_prompt_snippet(self) -> str:
        user_name = self.get_user_name()
        role = self.profile.get("role", "Software Engineer & Full-Stack Developer")
        facts = self.profile.get("facts", [])
        facts_list = "\n".join([f"• {f}" for f in facts])
        return (
            f"[CRITICAL USER IDENTITY & PERSISTENT MEMORY]\n"
            f"• User Name: {user_name}\n"
            f"• Occupation / Role: {role}\n"
            f"• Verified Core Facts:\n"
            f"{facts_list}\n"
            f"• CRITICAL INSTRUCTIONS:\n"
            f"  1. The user's name is '{user_name}'. When asked 'who am I' or 'what is my name', ALWAYS answer directly that they are {user_name}.\n"
            f"  2. When asked 'what do I do' or about their profession, refer to their role as {role} and their engineering/software work on C.O.P.P.E.R.\n"
            f"  3. NEVER refer to the user as single letters or commands like 'f' or 'clear vram'."
        )


persistent_memory = PersistentMemoryStore()
