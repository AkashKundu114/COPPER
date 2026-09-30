"""
Automated Campaign Executive Reporting Bridge.

Modeled on DeltaX Intelligent Automation & Reporting:
Synthesizes campaign health, budget optimization decisions, and creative fatigue
into structured executive briefings and PDF documentation via SCRIBE.
"""

from datetime import datetime, timezone
from typing import Any


class CampaignReportGenerator:
    """
    Generates structured ad-tech briefings and executive reports.
    """

    @staticmethod
    def generate_markdown_briefing(
        portfolio_summary: dict[str, Any],
        anomalies: list[dict[str, Any]],
        optimizations: dict[str, Any] | None = None,
        fatigue_alerts: list[dict[str, Any]] | None = None,
    ) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        lines = [
            f"# C.O.P.P.E.R. Campaign Intelligence Executive Briefing",
            f"**Generated:** {date_str} | **Engine:** DELTA Ad-Tech Suite (DeltaX Architecture)",
            "",
            "## 1. Portfolio Performance Snapshot",
            f"- **Daily Run-Rate Spend:** ${portfolio_summary.get('total_spend', 0.0):,.2f}",
            f"- **Projected Daily Conversions:** {portfolio_summary.get('total_conversions', 0):,}",
            f"- **Portfolio ROAS:** {portfolio_summary.get('overall_roas', 0.0):.2f}x",
            f"- **Average CTR:** {portfolio_summary.get('avg_ctr', 0.0) * 100:.2f}%",
            f"- **Average CPC:** ${portfolio_summary.get('avg_cpc', 0.0):.2f}",
            "",
            "## 2. Active Anomaly & Risk Alerts",
        ]

        if not anomalies and not fatigue_alerts:
            lines.append("All campaigns are currently operating within nominal baseline parameters.")
        else:
            for a in anomalies:
                sev = a.get("severity", "warning").upper()
                lines.append(
                    f"- **[{sev}] {a.get('campaign_name', 'Campaign')}**: {a.get('metric_name', 'Metric')} "
                    f"deviation ({a.get('deviation_percent', 0.0):.1f}%). *Recommendation:* {a.get('recommendation', 'Inspect campaign.')}"
                )
            if fatigue_alerts:
                for f in fatigue_alerts:
                    lines.append(
                        f"- **[CREATIVE FATIGUE] {f.get('creative_id', 'Creative')}**: Frequency {f.get('frequency', 1.0)}x, "
                        f"Decay {f.get('ctr_decay_percent', 0.0):.1f}%. *Action:* {f.get('recommendation', '')}"
                    )

        if optimizations:
            lines.extend(
                [
                    "",
                    "## 3. Algorithmic Budget Optimization (SLSQP)",
                    f"- **Recommended Total Allocation:** ${optimizations.get('total_budget', 0.0):,.2f}",
                    f"- **Projected Efficiency Lift:** +{optimizations.get('improvement_percent', 0.0):.1f}% Conversions",
                    "",
                    "### Actionable Reallocation Directives:",
                ]
            )
            for r in optimizations.get("reasoning", []):
                lines.append(f"- {r}")

        lines.extend(
            [
                "",
                "---",
                "*Sovereign ad-tech intelligence executed 100% on host GPU with zero external cloud telemetry.*",
            ]
        )

        return "\n".join(lines)


campaign_report_generator = CampaignReportGenerator()
