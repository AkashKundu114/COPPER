import json
import os
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime

from app.core.logger import logger

@dataclass
class PrivacyBudget:
    epsilon: float = 1.0  # Privacy parameter (lower = more private, range 0.1-10.0)
    delta: float = 1e-5   # Probability of privacy failure
    total_epsilon_spent: float = 0.0
    total_queries: int = 0
    budget_limit: float = 10.0  # Max cumulative epsilon before reset required
    last_reset: datetime = field(default_factory=datetime.utcnow)

class DifferentialPrivacyEngine:
    def __init__(self):
        self.budget = PrivacyBudget()
        self._config_path = "data/dp_config.json"
        self._load_config()

    def add_noise_to_embedding(self, embedding: list[float], sensitivity: float = 1.0) -> list[float]:
        epsilon = max(self.budget.epsilon, 1e-6)
        delta = self.budget.delta
        # Gaussian noise: sigma = sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
        noise = np.random.normal(0, sigma, len(embedding))
        noised_embedding = np.array(embedding) + noise
        return noised_embedding.tolist()

    def add_noise_to_query_results(self, results: list[dict], epsilon_per_query: float | None = None) -> list[dict]:
        eps = epsilon_per_query if epsilon_per_query is not None else self.budget.epsilon
        eps = max(eps, 1e-6)
        sensitivity = 1.0
        scale = sensitivity / eps
        
        noised_results = []
        for res in results:
            new_res = dict(res)
            if "distance" in new_res:
                noise = np.random.laplace(0, scale)
                new_res["distance"] = new_res["distance"] + noise
            noised_results.append(new_res)
        return noised_results

    def spend_budget(self, epsilon_cost: float) -> bool:
        if self.budget.total_epsilon_spent + epsilon_cost > self.budget.budget_limit:
            return False
        self.budget.total_epsilon_spent += epsilon_cost
        self.budget.total_queries += 1
        self._save_config()
        return True

    def get_budget_status(self) -> dict:
        spent = self.budget.total_epsilon_spent
        limit = self.budget.budget_limit
        rem = max(0.0, limit - spent)
        pct = (spent / limit * 100.0) if limit > 0 else 100.0
        return {
            "epsilon": self.budget.epsilon,
            "delta": self.budget.delta,
            "total_spent": spent,
            "remaining": rem,
            "pct_used": pct,
            "queries": self.budget.total_queries,
            "needs_reset": spent >= limit
        }

    def reset_budget(self):
        self.budget.total_epsilon_spent = 0.0
        self.budget.total_queries = 0
        self.budget.last_reset = datetime.utcnow()
        self._save_config()
        logger.info("Privacy budget reset.")

    def configure(self, epsilon: float, delta: float, budget_limit: float):
        self.budget.epsilon = max(0.1, min(10.0, epsilon))
        self.budget.delta = max(1e-10, min(1e-2, delta))
        self.budget.budget_limit = max(1.0, budget_limit)
        self._save_config()
        logger.info(f"DP Engine configured: epsilon={self.budget.epsilon}, delta={self.budget.delta}, limit={self.budget.budget_limit}")

    def get_privacy_guarantee(self) -> str:
        return f"This memory store satisfies (ε={self.budget.epsilon}, δ={self.budget.delta})-differential privacy. After {self.budget.total_queries} queries, cumulative privacy loss is ε_total={self.budget.total_epsilon_spent}."

    def _load_config(self):
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r") as f:
                    data = json.load(f)
                self.budget.epsilon = data.get("epsilon", self.budget.epsilon)
                self.budget.delta = data.get("delta", self.budget.delta)
                self.budget.total_epsilon_spent = data.get("total_epsilon_spent", self.budget.total_epsilon_spent)
                self.budget.total_queries = data.get("total_queries", self.budget.total_queries)
                self.budget.budget_limit = data.get("budget_limit", self.budget.budget_limit)
            except Exception as e:
                logger.error(f"Failed to load DP config: {e}")

    def _save_config(self):
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            with open(self._config_path, "w") as f:
                json.dump({
                    "epsilon": self.budget.epsilon,
                    "delta": self.budget.delta,
                    "total_epsilon_spent": self.budget.total_epsilon_spent,
                    "total_queries": self.budget.total_queries,
                    "budget_limit": self.budget.budget_limit,
                    "last_reset": self.budget.last_reset.isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save DP config: {e}")

dp_engine = DifferentialPrivacyEngine()
