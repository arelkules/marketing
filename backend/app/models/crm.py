from __future__ import annotations
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    type = Column(String, default="lead")        # lead|student|client|affiliate
    status = Column(String, default="new")       # new|active|churned|won|lost
    source = Column(String, nullable=True)       # instagram|facebook|referral|organic|ads
    tags = Column(Text, default="[]")            # JSON array
    notes = Column(Text, nullable=True)
    total_paid_ils = Column(Float, default=0)
    lead_score = Column(Integer, default=0)      # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deals = relationship("Deal", back_populates="contact", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="contact", cascade="all, delete-orphan", order_by="Activity.created_at.desc()")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    title = Column(String, nullable=False)
    amount_ils = Column(Float, default=0)
    stage = Column(String, default="new")        # new|qualified|proposal|negotiation|won|lost
    product = Column(String, default="course")   # course|coaching|affiliate|other
    expected_close = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contact = relationship("Contact", back_populates="deals")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String, ForeignKey("contacts.id"), nullable=False)
    type = Column(String, default="note")        # note|call|email|meeting|dm|purchase
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    contact = relationship("Contact", back_populates="activities")
