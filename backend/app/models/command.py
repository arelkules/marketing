from __future__ import annotations
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from datetime import datetime
import uuid
from app.database import Base


class BusinessProfile(Base):
    __tablename__ = "business_profile"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_name = Column(String, default="גבר ללא מגבלות")
    vision = Column(Text, nullable=True)
    goals_json = Column(Text, nullable=True)  # JSON array of strings
    current_phase = Column(String, default="build")  # seed|build|launch|scale|dominate
    founded_year = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    month = Column(String, nullable=False)       # "2026-04"
    revenue_ils = Column(Float, default=0)
    expenses_ils = Column(Float, default=0)
    net_profit_ils = Column(Float, default=0)
    mrr_ils = Column(Float, default=0)
    active_students = Column(Integer, default=0)
    new_customers = Column(Integer, default=0)
    avg_order_value = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class SocialMetric(Base):
    __tablename__ = "social_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String, nullable=False)    # instagram|facebook|youtube|tiktok|linkedin
    followers = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    avg_engagement_rate = Column(Float, default=0)
    monthly_reach = Column(Integer, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class NextStepRecommendation(Base):
    __tablename__ = "next_step_recommendations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    context_snapshot = Column(Text, nullable=True)  # JSON
    generated_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")  # active|done|skipped
