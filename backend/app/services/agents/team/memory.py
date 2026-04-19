from __future__ import annotations
import json
import uuid
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.team import TeamMemory


async def save_approved(
    session_id: str,
    business_name: str,
    goal: str,
    consensus: str,
    user_correction: str | None = None,
) -> None:
    async with AsyncSessionLocal() as db:
        record = TeamMemory(
            id=str(uuid.uuid4()),
            business_name=business_name,
            goal=goal,
            consensus=consensus,
            user_correction=user_correction,
        )
        db.add(record)
        await db.commit()


async def load_context(business_name: str, limit: int = 5) -> str:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TeamMemory)
            .where(TeamMemory.business_name == business_name)
            .order_by(TeamMemory.approved_at.desc())
            .limit(limit)
        )
        records = result.scalars().all()

    if not records:
        return ""

    lines = ["## PREVIOUSLY APPROVED DECISIONS FOR THIS BUSINESS\n"]
    for r in reversed(records):
        label = "✅ Approved" if not r.user_correction else f"✏️ Corrected: {r.user_correction}"
        lines.append(f"**Goal:** {r.goal}\n**Consensus:** {r.consensus}\n**Status:** {label}\n")

    return "\n---\n".join(lines)
