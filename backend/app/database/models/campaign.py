from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database.postgres import Base


class CampaignMetric(Base):
    __tablename__ = "campaign_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    campaign_id = Column(String(64), nullable=False, index=True)
    campaign_name = Column(String(128), nullable=False)
    campaign_type = Column(String(32), nullable=False)  # "brand", "performance", "retargeting"
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True)
    impressions = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    conversions = Column(Integer, nullable=False, default=0)
    spend = Column(Float, nullable=False, default=0.0)
    revenue = Column(Float, nullable=False, default=0.0)
    ctr = Column(Float, nullable=False, default=0.0)
    cpc = Column(Float, nullable=False, default=0.0)
    cpa = Column(Float, nullable=False, default=0.0)
    roas = Column(Float, nullable=False, default=0.0)
    daily_budget = Column(Float, nullable=False, default=0.0)
    budget_utilization = Column(Float, nullable=False, default=0.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "campaign_name": self.campaign_name,
            "campaign_type": self.campaign_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "impressions": self.impressions,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "spend": round(float(self.spend), 2),
            "revenue": round(float(self.revenue), 2),
            "ctr": round(float(self.ctr), 4),
            "cpc": round(float(self.cpc), 2),
            "cpa": round(float(self.cpa), 2),
            "roas": round(float(self.roas), 2),
            "daily_budget": round(float(self.daily_budget), 2),
            "budget_utilization": round(float(self.budget_utilization), 4),
        }
