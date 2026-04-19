from __future__ import annotations
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base


class TeamSession(Base):
    __tablename__ = "team_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_name = Column(String, default="גבר ללא מגבלות")
    goal = Column(Text, nullable=False)
    user_answers = Column(Text, nullable=True)  # JSON
    status = Column(String, default="questioning")  # questioning|discussing|consensus|approved
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("TeamMessage", back_populates="session", cascade="all, delete-orphan")


class TeamMessage(Base):
    __tablename__ = "team_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("team_sessions.id"), nullable=False)
    advisor = Column(String, nullable=False)  # hormozi|bwnc|walker|manager|user
    content = Column(Text, nullable=False)
    round_number = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("TeamSession", back_populates="messages")


class TeamMemory(Base):
    __tablename__ = "team_memory"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_name = Column(String, nullable=False)
    goal = Column(Text, nullable=False)
    consensus = Column(Text, nullable=False)
    user_correction = Column(Text, nullable=True)
    approved_at = Column(DateTime, default=datetime.utcnow)
