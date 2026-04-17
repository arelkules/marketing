from sqlalchemy import Column, String, Float, DateTime, Text
from datetime import datetime
import uuid
from app.database import Base


class RevenueSnapshot(Base):
    __tablename__ = "revenue_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    mrr_usd = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class BusinessMetric(Base):
    __tablename__ = "business_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
