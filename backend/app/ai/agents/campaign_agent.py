from collections.abc import AsyncGenerator
from datetime import datetime
import json
import re
from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.budget_optimizer import budget_optimizer
from app.ai.campaign_anomaly_detector import campaign_anomaly_detector
from app.ai.llm.model_manager import model_manager
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger
from app.database.models.campaign import CampaignMetric
from app.database.postgres import SessionLocal
from app.services.campaign_simulator import ensure_simulated_campaign_data


class CampaignIntelligenceAgent(BaseAgent):
    """
    Campaign Intelligence Agent modeled on DeltaX Assistant:
    Monitors advertising campaign metrics, detects statistical/trend/budget anomalies,
    optimizes cross-campaign budget allocation, and provides actionable recommendations.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.CAMPAIGN_INTELLIGENCE,
            name="DELTA (Campaign Intelligence Agent)",
            description=(
                "Advertising technology specialist that monitors simulated advertising campaign metrics, "
                "detects anomalies using Z-score, trend moving-average crossovers, and burn rate projections, "
                "optimizes budget allocations, and generates actionable ad-tech alerts."
            ),
            tools=[],
            max_tool_steps=3,
        )

    def get_target_model(self) -> str:
        return model_manager.get_model("core_agents.reasoning", "deepseek-r1:14b")

    def _get_active_campaign_metrics(self) -> list[CampaignMetric]:
        db = SessionLocal()
        try:
            ensure_simulated_campaign_data(db)
            # Fetch latest 168 hours of metrics for analysis
            metrics = (
                db.query(CampaignMetric)
                .order_by(CampaignMetric.timestamp.desc())
                .limit(5 * 168)
                .all()
            )
            return list(reversed(metrics))
        finally:
            db.close()

    def analyze_intent(self, message: str) -> str:
        msg = message.lower()
        if any(k in msg for k in ["optimize", "reallocate", "allocation", "budget optimizer", "maximize conversions"]):
            return "optimize_budget"
        if any(k in msg for k in ["underperform", "worst", "failing", "losing", "drop", "decay"]):
            return "underperforming"
        if any(k in msg for k in ["ctr", "click through", "click-through", "clicks dropped"]):
            return "ctr_analysis"
        if any(k in msg for k in ["alert", "problem", "issue", "anomaly", "anomalies", "warn", "warning"]):
            return "alerts"
        return "performance_summary"

    def execute_intelligence(self, intent: str, user_query: str) -> dict[str, Any]:
        """Core analytical engine generating structured response JSON for campaign queries."""
        metrics = self._get_active_campaign_metrics()
        db = SessionLocal()
        try:
            # Group metrics by campaign
            campaigns: dict[str, list[CampaignMetric]] = {}
            for m in metrics:
                campaigns.setdefault(m.campaign_id, []).append(m)

            # Compute portfolio aggregate stats from latest hour
            latest_per_cmp = [cmp_list[-1] for cmp_list in campaigns.values() if cmp_list]
            total_spend = sum(float(m.spend) for m in latest_per_cmp) * 24.0  # Daily run-rate
            total_conversions = sum(int(m.conversions) for m in latest_per_cmp) * 24
            total_revenue = sum(float(m.revenue) for m in latest_per_cmp) * 24.0
            avg_ctr = (
                float(sum(m.ctr for m in latest_per_cmp) / len(latest_per_cmp))
                if latest_per_cmp
                else 0.03
            )
            avg_cpc = (
                float(sum(m.cpc for m in latest_per_cmp) / len(latest_per_cmp))
                if latest_per_cmp
                else 1.80
            )
            overall_roas = (
                round(total_revenue / max(1.0, total_spend), 2) if total_spend > 0 else 0.0
            )

            # Run anomaly detection
            anomalies = campaign_anomaly_detector.scan_all_campaigns(db, hours=168)
            anom_dicts = [a.to_dict() for a in anomalies]

            # Prepare charts data (aggregate timeline for frontend visualizer)
            timeline_map: dict[str, dict[str, Any]] = {}
            for m in metrics[-120:]:  # last 24 hours of 5 campaigns
                ts_key = m.timestamp.strftime("%Y-%m-%d %H:00") if m.timestamp else ""
                if ts_key not in timeline_map:
                    timeline_map[ts_key] = {"timestamp": ts_key, "spend": 0.0, "conversions": 0, "clicks": 0, "impressions": 0}
                timeline_map[ts_key]["spend"] += float(m.spend)
                timeline_map[ts_key]["conversions"] += int(m.conversions)
                timeline_map[ts_key]["clicks"] += int(m.clicks)
                timeline_map[ts_key]["impressions"] += int(m.impressions)

            charts_data = {
                "timeline": list(timeline_map.values()),
                "campaigns": [
                    {
                        "campaign_id": m.campaign_id,
                        "campaign_name": m.campaign_name,
                        "campaign_type": m.campaign_type,
                        "spend": round(float(m.spend), 2),
                        "ctr": round(float(m.ctr), 4),
                        "cpc": round(float(m.cpc), 2),
                        "roas": round(float(m.roas), 2),
                        "conversions": int(m.conversions),
                    }
                    for m in latest_per_cmp
                ],
            }

            # Response dispatch based on specific ad-tech intent
            if intent == "optimize_budget":
                opt_result = budget_optimizer.optimize_from_db(db)
                return {
                    "summary": (
                        f"Budget optimization complete. Reallocating your ${opt_result.total_budget:,.2f} daily budget "
                        f"is projected to improve portfolio conversions by +{opt_result.improvement_percent:.1f}% "
                        f"({opt_result.projected_current_conversions:.1f} -> {opt_result.projected_optimized_conversions:.1f} conversions)."
                    ),
                    "metrics": {
                        "total_daily_budget": opt_result.total_budget,
                        "projected_current_conversions": opt_result.projected_current_conversions,
                        "projected_optimized_conversions": opt_result.projected_optimized_conversions,
                        "improvement_percent": opt_result.improvement_percent,
                    },
                    "anomalies": anom_dicts,
                    "recommendations": opt_result.reasoning,
                    "charts_data": {
                        **charts_data,
                        "budget_optimization": opt_result.to_dict(),
                    },
                }

            if intent == "underperforming":
                flagged = [a for a in anomalies if a.severity in ("critical", "warning")]
                summary = (
                    f"Identified {len(flagged)} underperforming campaign issues. "
                    + (
                        f"Primary bottleneck: {flagged[0].campaign_name} ({flagged[0].metric_name} deviation: {flagged[0].deviation_percent}%)."
                        if flagged
                        else "All campaigns are currently operating within nominal baseline parameters."
                    )
                )
                recommendations = [f"{a.campaign_name}: {a.recommendation}" for a in flagged]
                if not recommendations:
                    recommendations.append("Continue monitoring current bidding strategies and creative performance.")

                return {
                    "summary": summary,
                    "metrics": {
                        "flagged_campaign_count": len(set(a.campaign_id for a in flagged)),
                        "total_active_anomalies": len(flagged),
                        "portfolio_roas": overall_roas,
                    },
                    "anomalies": [a.to_dict() for a in flagged],
                    "recommendations": recommendations,
                    "charts_data": charts_data,
                }

            if intent == "ctr_analysis":
                ctr_anomalies = [a for a in anomalies if "ctr" in a.anomaly_type.lower() or a.metric_name == "CTR"]
                if ctr_anomalies:
                    top_anom = ctr_anomalies[0]
                    summary = (
                        f"CTR analysis detected a {top_anom.deviation_percent:.1f}% drop on {top_anom.campaign_name} "
                        f"(current: {top_anom.current_value * 100:.2f}% vs expected: {top_anom.expected_value * 100:.2f}%). "
                        "This indicates audience saturation or ad fatigue."
                    )
                    recommendations = [top_anom.recommendation]
                else:
                    summary = f"Overall portfolio CTR is healthy at {avg_ctr * 100:.2f}%. No critical CTR decay detected across active ad sets."
                    recommendations = ["Maintain current creative rotations and bid pacing."]

                return {
                    "summary": summary,
                    "metrics": {
                        "average_portfolio_ctr": round(avg_ctr, 4),
                        "active_campaigns": len(latest_per_cmp),
                    },
                    "anomalies": [a.to_dict() for a in ctr_anomalies],
                    "recommendations": recommendations,
                    "charts_data": charts_data,
                }

            if intent == "alerts":
                crit_count = sum(1 for a in anomalies if a.severity == "critical")
                warn_count = sum(1 for a in anomalies if a.severity == "warning")
                summary = (
                    f"Full anomaly scan completed: {len(anomalies)} active campaign alerts "
                    f"({crit_count} critical, {warn_count} warnings)."
                )
                recs = [f"[{a.severity.upper()}] {a.campaign_name}: {a.recommendation}" for a in anomalies]
                return {
                    "summary": summary,
                    "metrics": {
                        "total_alerts": len(anomalies),
                        "critical_alerts": crit_count,
                        "warning_alerts": warn_count,
                    },
                    "anomalies": anom_dicts,
                    "recommendations": recs or ["All systems nominal."],
                    "charts_data": charts_data,
                }

            # Default: performance_summary
            summary = (
                f"Portfolio Performance Overview: 5 active campaigns running at ${total_spend:,.2f}/day run-rate, "
                f"generating {total_conversions:,} conversions with a blended ROAS of {overall_roas:.2f}x (CTR: {avg_ctr * 100:.2f}%, CPC: ${avg_cpc:.2f})."
            )
            recs = [a.recommendation for a in anomalies[:3]] if anomalies else [
                "Portfolio running efficiently. Test new creative variants on top performers."
            ]

            return {
                "summary": summary,
                "metrics": {
                    "daily_spend_run_rate": round(total_spend, 2),
                    "daily_conversions": total_conversions,
                    "overall_roas": overall_roas,
                    "average_ctr": round(avg_ctr, 4),
                    "average_cpc": round(avg_cpc, 2),
                    "active_campaigns": len(latest_per_cmp),
                },
                "anomalies": anom_dicts[:5],
                "recommendations": recs,
                "charts_data": charts_data,
            }
        finally:
            db.close()

    async def synthesize_with_perspective_model(
        self, user_query: str, intelligence_result: dict[str, Any]
    ) -> str:
        """
        Uses the perspective model (deepseek-r1:14b) via Ollama to generate an authoritative
        ad-tech domain synthesis grounded in the calculated telemetry and anomalies.
        """
        try:
            from app.ai.llm.ollama_client import ollama_client

            if not await ollama_client.is_available():
                return intelligence_result["summary"]

            target_model = self.get_target_model()
            anom_summary = [
                f"- {a['campaign_name']}: {a['anomaly_type']} ({a['metric_name']} dev: {a['deviation_percent']}%, severity: {a['severity']})"
                for a in intelligence_result.get("anomalies", [])[:3]
            ]
            anom_str = "\n".join(anom_summary) if anom_summary else "No critical anomalies."

            prompt = (
                f"You are DELTA, an AI advertising intelligence specialist for DeltaX.\n"
                f"User query: '{user_query}'\n\n"
                f"Calculated Ad-Tech Telemetry Context:\n"
                f"- Baseline Telemetry: {intelligence_result.get('summary')}\n"
                f"- Metrics: {json.dumps(intelligence_result.get('metrics', {}))}\n"
                f"- Detected Anomalies:\n{anom_str}\n\n"
                f"Provide a concise, professional 2-3 sentence executive briefing and diagnosis "
                f"from your perspective as DELTA."
            )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are DELTA, the Campaign Intelligence Agent within C.O.P.P.E.R. "
                        "specializing in DeltaX advertising technology and ad performance optimization."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            llm_resp = await ollama_client.chat(messages, model=target_model, agent_type=self.agent_type)
            clean_resp = re.sub(r"<think>.*?</think>", "", llm_resp, flags=re.DOTALL).strip()
            if clean_resp:
                return clean_resp
            return intelligence_result["summary"]
        except Exception as e:
            logger.debug(f"Perspective model synthesis fallback: {e}")
            return intelligence_result["summary"]

    async def run(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        use_llm: bool = True,
        *args,
        **kwargs,
    ) -> str:
        intent = self.analyze_intent(message)
        result = self.execute_intelligence(intent, message)
        if use_llm:
            result["summary"] = await self.synthesize_with_perspective_model(message, result)
        return json.dumps(result, indent=2)

    async def stream(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        metrics_collector: dict | None = None,
        session_id: str | None = None,
        use_llm: bool = True,
        *args,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        intent = self.analyze_intent(message)
        result = self.execute_intelligence(intent, message)
        if use_llm:
            result["summary"] = await self.synthesize_with_perspective_model(message, result)
        formatted_json = json.dumps(result, indent=2)
        yield formatted_json


campaign_agent = CampaignIntelligenceAgent()
