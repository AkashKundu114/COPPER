"""GPU-Accelerated Semantic Intent Router & Embedding Escalation Layer.

Provides fast neural semantic intent classification using PyTorch on CUDA/CPU.
Escalates ambiguous, perturbed, or low-margin queries from Stage 1 pattern matching
to prevent accuracy collapse on out-of-distribution prompts.
"""

import json
from pathlib import Path
from typing import Any

import joblib
import torch
import torch.nn as nn

from app.core.constants import AgentType
from app.core.logger import logger

MODEL_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = MODEL_DIR / "semantic_router_weights.pt"
VECTORIZER_PATH = MODEL_DIR / "semantic_vectorizer.pkl"
METADATA_PATH = MODEL_DIR / "semantic_router_metadata.json"

OOD_CLASS = "unsupported_ood"


class SemanticRouterNet(nn.Module):
    def __init__(self, vocab_size: int, hidden_dim: int, num_classes: int):
        super().__init__()
        self.fc1 = nn.Linear(vocab_size, hidden_dim)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.15)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        h = self.dropout(self.relu(self.fc1(x)))
        return self.fc2(h)


class GPUSemanticRouter:
    """Production GPU Semantic Classifier with CPU Fallback."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: SemanticRouterNet | None = None
        self.vectorizer = None
        self.classes: list[str] = []
        self._is_loaded = False
        self._load_model()

    def _load_model(self):
        if not (WEIGHTS_PATH.exists() and VECTORIZER_PATH.exists() and METADATA_PATH.exists()):
            logger.info("Semantic router model artifacts not found; semantic escalation disabled.")
            return

        try:
            with open(METADATA_PATH, encoding="utf-8") as f:
                meta = json.load(f)
            self.classes = meta["classes"]
            vocab_size = meta["vocab_size"]
            hidden_dim = meta.get("hidden_dim", 256)
            num_classes = meta["num_classes"]

            self.vectorizer = joblib.load(VECTORIZER_PATH)

            self.model = SemanticRouterNet(
                vocab_size=vocab_size,
                hidden_dim=hidden_dim,
                num_classes=num_classes,
            )
            state_dict = torch.load(WEIGHTS_PATH, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            self._is_loaded = True
            logger.info(f"GPU Semantic Router initialized on {self.device} ({len(self.classes)} classes).")
        except Exception as e:
            logger.warning(f"Failed to load semantic router artifacts: {e}")
            self._is_loaded = False

    @property
    def is_available(self) -> bool:
        return self._is_loaded and self.model is not None and self.vectorizer is not None

    def classify(self, text: str) -> tuple[str, float, dict[str, float], bool]:
        """Classify a prompt using the GPU-accelerated semantic model.

        Returns:
            (predicted_class, confidence, probabilities_dict, is_ood)
        """
        if not self.is_available:
            return "chat", 0.50, {}, False

        try:
            x_sparse = self.vectorizer.transform([text])
            x_dense = torch.from_numpy(x_sparse.toarray()).float().to(self.device)

            with torch.no_grad():
                logits = self.model(x_dense)
                probs = torch.softmax(logits, dim=-1).squeeze(0)

            top_prob, top_idx = torch.max(probs, dim=-1)
            pred_class = self.classes[top_idx.item()]
            confidence = round(float(top_prob.item()), 4)

            prob_dict = {
                cls_name: round(float(probs[i].item()), 4)
                for i, cls_name in enumerate(self.classes)
            }

            is_ood = pred_class == OOD_CLASS or confidence < 0.35
            return pred_class, confidence, prob_dict, is_ood
        except Exception as e:
            logger.warning(f"Semantic inference error: {e}")
            return "chat", 0.50, {}, False


gpu_semantic_router = GPUSemanticRouter()
