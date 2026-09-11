import json
import os
from dataclasses import dataclass, field, asdict
from typing import List
from app.core.logger import logger

DATA_DIR = "data"
CONFIG_PATH = os.path.join(DATA_DIR, "personality_config.json")

@dataclass
class PersonalityConfig:
    warmth: float = 0.7
    formality: float = 0.4
    verbosity: float = 0.5
    humor: float = 0.3
    use_emojis: bool = True
    code_first: bool = True
    custom_instructions: List[str] = field(default_factory=list)

class PersonalityManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PersonalityManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self.config = PersonalityConfig()
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = PersonalityConfig(**data)
            except Exception as e:
                logger.error(f"Failed to load personality config: {e}")
        else:
            self.save_config()

    def save_config(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(asdict(self.config), f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save personality config: {e}")

    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()

    def get_system_prompt_addon(self) -> str:
        addon = []
        if self.config.warmth > 0.7:
            addon.append("Tone: Very warm and empathetic.")
        elif self.config.warmth < 0.3:
            addon.append("Tone: Cold, strictly professional and objective.")
        else:
            addon.append("Tone: Balanced and approachable.")

        if self.config.formality > 0.7:
            addon.append("Style: Highly formal.")
        elif self.config.formality < 0.3:
            addon.append("Style: Casual and relaxed.")
        
        if self.config.verbosity > 0.7:
            addon.append("Length: Detailed and comprehensive explanations.")
        elif self.config.verbosity < 0.3:
            addon.append("Length: Very concise, use bullet points if possible.")

        if self.config.humor > 0.7:
            addon.append("Humor: Feel free to use light humor or puns.")
        elif self.config.humor < 0.3:
            addon.append("Humor: No humor, remain serious.")

        if self.config.use_emojis:
            addon.append("Emojis: Allowed and encouraged where appropriate.")
        else:
            addon.append("Emojis: Do not use emojis.")
            
        if self.config.code_first:
            addon.append("Priority: Show code examples first before explaining.")

        if self.config.custom_instructions:
            addon.append("Custom Directives:")
            for instr in self.config.custom_instructions:
                addon.append(f"- {instr}")

        return " ".join(addon)

    def adapt_from_message(self, user_message: str):
        # Lightweight heuristic sentiment/style analyzer
        msg_lower = user_message.lower()
        
        # Verbosity
        words = user_message.split()
        if len(words) < 5:
            self.config.verbosity = max(0.0, self.config.verbosity - 0.05)
        elif len(words) > 50:
            self.config.verbosity = min(1.0, self.config.verbosity + 0.05)
            
        # Formality
        casual_words = ["hey", "hi", "thanks", "cool", "awesome", "dude", "lol"]
        formal_words = ["please", "kindly", "appreciate", "furthermore", "therefore"]
        
        casual_count = sum(1 for w in casual_words if w in msg_lower)
        formal_count = sum(1 for w in formal_words if w in msg_lower)
        
        if casual_count > formal_count:
            self.config.formality = max(0.0, self.config.formality - 0.05)
        elif formal_count > casual_count:
            self.config.formality = min(1.0, self.config.formality + 0.05)

        self.save_config()

personality_manager = PersonalityManager()
