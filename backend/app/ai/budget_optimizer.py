from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy.optimize import minimize
from sqlalchemy.orm import Session

from app.database.models.campaign import CampaignMetric


@dataclass
class BudgetOptimization:
    total_budget: float
    current_allocation: dict[str, float]  # campaign_id -> current spend
    optimized_allocation: dict[str, float]  # campaign_id -> optimal spend
    projected_current_conversions: float
    projected_optimized_conversions: float
    improvement_percent: float
    reasoning: list[str]  # explain each reallocation decision

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BudgetOptimizer:
    """
    ML-driven budget allocator using diminishing-returns logarithmic response curves:
      Conversions(Spend) = a * ln(Spend) + b
    Solves constrained non-linear optimization with SLSQP to maximize total portfolio conversions.
    """

    @staticmethod
    def fit_response_curve(spends: list[float], conversions: list[float]) -> tuple[float, float]:
        """
        Fits conversions = a * ln(spend) + b.
        Ensures a > 0 to guarantee concave diminishing returns.
        """
        if len(spends) < 2 or len(conversions) < 2:
            return 5.0, 0.0

        x = np.log(np.maximum(np.array(spends, dtype=float), 1.0))
        y = np.array(conversions, dtype=float)

        try:
            # Polyfit on log-transformed spend: y = a * x + b
            a, b = np.polyfit(x, y, deg=1)
            # Ensure strictly positive slope for diminishing returns modeling
            if a <= 0.05:
                # Fallback slope grounded in empirical conversion efficiency
                avg_spend = max(1.0, float(np.mean(spends)))
                avg_conv = max(0.5, float(np.mean(conversions)))
                a = max(0.5, avg_conv / np.log(max(2.0, avg_spend)))
                b = max(0.0, avg_conv - a * np.log(avg_spend))
            return float(a), float(b)
        except Exception:
            return 5.0, 1.0

    @staticmethod
    def predict_conversions(spend: float, a: float, b: float) -> float:
        """Projects conversions for a given spend level using fitted parameters."""
        if spend <= 0:
            return 0.0
        val = a * np.log(max(1.0, spend)) + b
        return float(max(0.0, val))

    def optimize_budget(
        self,
        campaign_historical_data: dict[str, dict[str, Any]],
        total_budget: float,
        min_spend_ratio: float = 0.10,
        max_spend_ratio: float = 2.00,
    ) -> BudgetOptimization:
        """
        Optimizes budget allocation across campaigns.
        campaign_historical_data format:
          {
            "cmp-id": {
              "campaign_name": "...",
              "current_spend": 1200.0,
              "spends": [...],
              "conversions": [...]
            }
          }
        """
        cids = list(campaign_historical_data.keys())
        n = len(cids)
        if n == 0:
            return BudgetOptimization(
                total_budget=total_budget,
                current_allocation={},
                optimized_allocation={},
                projected_current_conversions=0.0,
                projected_optimized_conversions=0.0,
                improvement_percent=0.0,
                reasoning=["No campaigns provided for optimization."],
            )

        # Fit response curves and collect current spends
        curves: dict[str, tuple[float, float]] = {}
        current_alloc: dict[str, float] = {}

        for cid in cids:
            data = campaign_historical_data[cid]
            spends = data.get("spends", [])
            convs = data.get("conversions", [])
            a, b = self.fit_response_curve(spends, convs)
            curves[cid] = (a, b)
            current_alloc[cid] = float(data.get("current_spend", total_budget / n))

        # Define bounds and constraints
        current_sum = sum(current_alloc.values()) or total_budget
        scale_to_budget = total_budget / max(1.0, current_sum)
        x0 = np.array([current_alloc[cid] * scale_to_budget for cid in cids], dtype=float)

        bounds = []
        for cid in cids:
            cur = current_alloc[cid]
            lower = max(10.0, cur * min_spend_ratio)
            upper = max(lower * 2.0, cur * max_spend_ratio, total_budget * 0.85)
            bounds.append((lower, upper))

        # Adjust bounds if unfeasible
        min_total = sum(b[0] for b in bounds)
        max_total = sum(b[1] for b in bounds)
        if total_budget < min_total:
            bounds = [(min(b[0], total_budget / n), b[1]) for b in bounds]
        elif total_budget > max_total:
            bounds = [(b[0], max(b[1], total_budget * 0.95)) for b in bounds]

        # Objective: minimize negative total conversions
        def objective(x: np.ndarray) -> float:
            total_conv = 0.0
            for idx, cid in enumerate(cids):
                a, b = curves[cid]
                total_conv += self.predict_conversions(x[idx], a, b)
            return -total_conv

        constraints = [{"type": "eq", "fun": lambda x: np.sum(x) - total_budget}]

        res = minimize(
            objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 200, "ftol": 1e-6},
        )

        optimized_x = res.x if res.success else x0
        # Re-normalize to guarantee exact sum = total_budget
        opt_sum = np.sum(optimized_x)
        if opt_sum > 0:
            optimized_x = (optimized_x / opt_sum) * total_budget

        optimized_alloc: dict[str, float] = {}
        for idx, cid in enumerate(cids):
            optimized_alloc[cid] = round(float(optimized_x[idx]), 2)

        # Fix minor rounding discrepancy on largest allocation
        diff = total_budget - sum(optimized_alloc.values())
        if abs(diff) > 0.001:
            max_key = max(optimized_alloc, key=optimized_alloc.get)
            optimized_alloc[max_key] = round(optimized_alloc[max_key] + diff, 2)

        # Calculate conversions
        proj_curr = sum(
            self.predict_conversions(current_alloc[cid], curves[cid][0], curves[cid][1]) for cid in cids
        )
        proj_opt = sum(
            self.predict_conversions(optimized_alloc[cid], curves[cid][0], curves[cid][1]) for cid in cids
        )

        imp_pct = round(((proj_opt - proj_curr) / max(0.01, proj_curr)) * 100, 2)

        # Generate intelligent reasoning explanations
        reasoning: list[str] = []
        for cid in cids:
            name = campaign_historical_data[cid].get("campaign_name", cid)
            c_val = current_alloc[cid]
            o_val = optimized_alloc[cid]
            delta = o_val - c_val
            pct = ((delta) / max(1.0, c_val)) * 100
            a_param = curves[cid][0]

            if delta > 10.0:
                reasoning.append(
                    f"Campaign '{name}' ({cid}): Reallocate +${delta:.2f} (+{pct:.1f}%). "
                    f"High marginal conversion elasticity (slope a={a_param:.2f}) indicates untapped growth capacity."
                )
            elif delta < -10.0:
                reasoning.append(
                    f"Campaign '{name}' ({cid}): Trim budget by -${abs(delta):.2f} ({pct:.1f}%). "
                    f"Diminishing returns indicate saturation point exceeded; surplus funds shifted to higher-yield campaigns."
                )
            else:
                reasoning.append(
                    f"Campaign '{name}' ({cid}): Maintain steady budget around ${o_val:.2f} (near-optimal marginal yield)."
                )

        reasoning.append(
            f"Portfolio Total: Projected conversions increase from {proj_curr:.1f} to {proj_opt:.1f} "
            f"(+{imp_pct:.1f}% improvement) at an identical total daily spend of ${total_budget:,.2f}."
        )

        return BudgetOptimization(
            total_budget=round(total_budget, 2),
            current_allocation={k: round(v, 2) for k, v in current_alloc.items()},
            optimized_allocation=optimized_alloc,
            projected_current_conversions=round(proj_curr, 2),
            projected_optimized_conversions=round(proj_opt, 2),
            improvement_percent=imp_pct,
            reasoning=reasoning,
        )

    def optimize_from_db(
        self,
        db: Session,
        total_budget: float | None = None,
        campaign_ids: list[str] | None = None,
        days: int = 14,
    ) -> BudgetOptimization:
        """Loads historical campaign data from database and executes budget optimization."""
        query = db.query(CampaignMetric)
        if campaign_ids:
            query = query.filter(CampaignMetric.campaign_id.in_(campaign_ids))

        all_records = query.all()
        grouped: dict[str, dict[str, Any]] = {}

        for rec in all_records:
            cid = rec.campaign_id
            if cid not in grouped:
                grouped[cid] = {
                    "campaign_name": rec.campaign_name,
                    "current_spend": float(rec.daily_budget),
                    "spends": [],
                    "conversions": [],
                }
            grouped[cid]["spends"].append(float(rec.spend))
            grouped[cid]["conversions"].append(float(rec.conversions))

        calc_budget = total_budget or sum(data["current_spend"] for data in grouped.values())
        return self.optimize_budget(grouped, total_budget=calc_budget)


budget_optimizer = BudgetOptimizer()
