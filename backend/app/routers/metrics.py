import uuid
import math
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.metrics import RevenueSnapshot, BusinessMetric
from app.models.asset import GeneratedAsset
from app.models.document import KnowledgeDocument
from app.schemas.metrics import (
    RevenueSnapshotCreate, RevenueSnapshotOut,
    BusinessMetricCreate, BusinessMetricOut,
    DashboardSummary,
)

router = APIRouter()
TARGET_ARR = 100_000_000


def _months_to_target(current_mrr: float, monthly_growth: float) -> float | None:
    if current_mrr <= 0:
        return None
    target_mrr = TARGET_ARR / 12
    if current_mrr >= target_mrr:
        return 0.0
    if monthly_growth <= 0:
        return None
    try:
        return math.log(target_mrr / current_mrr) / math.log(1 + monthly_growth)
    except Exception:
        return None


@router.post("/revenue", response_model=RevenueSnapshotOut)
async def record_revenue(data: RevenueSnapshotCreate, db: AsyncSession = Depends(get_db)):
    snap = RevenueSnapshot(id=str(uuid.uuid4()), mrr_usd=data.mrr_usd, notes=data.notes)
    db.add(snap)
    await db.commit()
    await db.refresh(snap)
    return snap


@router.get("/revenue", response_model=list[RevenueSnapshotOut])
async def list_revenue(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RevenueSnapshot).order_by(RevenueSnapshot.recorded_at.desc()).limit(100)
    )
    return result.scalars().all()


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    rev_result = await db.execute(
        select(RevenueSnapshot).order_by(RevenueSnapshot.recorded_at.desc()).limit(1)
    )
    latest = rev_result.scalar_one_or_none()
    mrr = latest.mrr_usd if latest else 0.0

    asset_count = await db.scalar(select(func.count()).select_from(GeneratedAsset))
    doc_count = await db.scalar(select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.status == "completed"))

    return DashboardSummary(
        latest_mrr=mrr,
        arr=mrr * 12,
        months_to_100m_conservative=_months_to_target(mrr, 0.20),
        months_to_100m_expected=_months_to_target(mrr, 0.35),
        months_to_100m_aggressive=_months_to_target(mrr, 0.50),
        total_assets=asset_count or 0,
        total_documents=doc_count or 0,
    )


@router.post("/business", response_model=BusinessMetricOut)
async def record_metric(data: BusinessMetricCreate, db: AsyncSession = Depends(get_db)):
    metric = BusinessMetric(id=str(uuid.uuid4()), metric_name=data.metric_name, metric_value=data.metric_value)
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


@router.get("/business", response_model=list[BusinessMetricOut])
async def list_metrics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BusinessMetric).order_by(BusinessMetric.recorded_at.desc()))
    return result.scalars().all()
