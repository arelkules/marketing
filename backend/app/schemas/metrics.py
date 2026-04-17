from pydantic import BaseModel
from datetime import datetime


class RevenueSnapshotCreate(BaseModel):
    mrr_usd: float
    notes: str | None = None


class RevenueSnapshotOut(BaseModel):
    id: str
    mrr_usd: float
    notes: str | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class BusinessMetricCreate(BaseModel):
    metric_name: str
    metric_value: float


class BusinessMetricOut(BaseModel):
    id: str
    metric_name: str
    metric_value: float
    recorded_at: datetime

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    latest_mrr: float
    arr: float
    months_to_100m_conservative: float | None
    months_to_100m_expected: float | None
    months_to_100m_aggressive: float | None
    total_assets: int
    total_documents: int
