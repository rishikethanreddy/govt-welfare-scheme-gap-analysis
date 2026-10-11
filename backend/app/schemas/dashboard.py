"""
Dashboard schemas — overview metrics and trends.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class OverviewMetrics(BaseModel):
    total_records: int = 0
    schemes_analyzed: int = 0
    states_covered: int = 0
    districts_covered: int = 0
    awareness_gap_signals: int = 0
    gap_rate: float = 0.0
    active_sources: int = 0
    total_sources: int = 0
    latest_collection: Optional[datetime] = None


class TrendDataPoint(BaseModel):
    period: str  # e.g., "2026-01", "2026-W12", "2026-01-15"
    total: int = 0
    gap_signals: int = 0
    gap_rate: float = 0.0


class TrendResponse(BaseModel):
    data: list[TrendDataPoint] = []
    granularity: str = "monthly"  # daily / weekly / monthly / yearly


class SchemeDistributionItem(BaseModel):
    scheme: str
    total_records: int = 0
    gap_signals: int = 0
    gap_rate: float = 0.0


class IntentDistributionItem(BaseModel):
    intent: str
    count: int = 0
    percentage: float = 0.0


class GapTypeDistributionItem(BaseModel):
    gap_type: str
    count: int = 0
    percentage: float = 0.0


class RecurringIssue(BaseModel):
    text: str
    scheme: Optional[str] = None
    intent: Optional[str] = None
    gap_type: Optional[str] = None
    count: int = 1
    states: list[str] = Field(default_factory=list)


class RecentActivity(BaseModel):
    source_name: str
    action: str
    records: int = 0
    timestamp: Optional[datetime] = None
    status: str = "completed"


class DashboardResponse(BaseModel):
    overview: OverviewMetrics
    scheme_distribution: list[SchemeDistributionItem] = []
    intent_distribution: list[IntentDistributionItem] = []
    gap_type_distribution: list[GapTypeDistributionItem] = []
    recurring_issues: list[RecurringIssue] = []
    recent_activity: list[RecentActivity] = []
