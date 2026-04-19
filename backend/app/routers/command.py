"""
Command Center router — business profile, financials, social metrics, AI next steps.
GET  /command/overview
POST /command/profile
POST /command/financial
GET  /command/financial
POST /command/social
GET  /command/social
POST /command/generate-next-steps  (SSE)
PATCH /command/next-steps/{id}/status
"""
from __future__ import annotations
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional

from app.database import get_db, AsyncSessionLocal
from app.models.command import BusinessProfile, FinancialRecord, SocialMetric, NextStepRecommendation
from app.models.team import TeamMemory
from app.utils.anthropic_client import get_anthropic_client

router = APIRouter()

MODEL = "claude-sonnet-4-6"
CACHE_BETA = "prompt-caching-2024-07-31"
GOAL_ILS = 100_000_000  # ₪100M


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ProfileIn(BaseModel):
    business_name: str = "גבר ללא מגבלות"
    vision: Optional[str] = None
    goals: Optional[list[str]] = None
    current_phase: Optional[str] = None
    founded_year: Optional[int] = None


class FinancialIn(BaseModel):
    month: str  # "2026-04"
    revenue_ils: float = 0
    expenses_ils: float = 0
    mrr_ils: float = 0
    active_students: int = 0
    new_customers: int = 0
    avg_order_value: float = 0
    notes: Optional[str] = None


class SocialIn(BaseModel):
    platform: str
    followers: int = 0
    posts_count: int = 0
    avg_engagement_rate: float = 0
    monthly_reach: int = 0


class NextStepStatusIn(BaseModel):
    status: str  # done|skipped|active


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create_profile(db: AsyncSession) -> BusinessProfile:
    result = await db.execute(select(BusinessProfile).limit(1))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = BusinessProfile(id=str(uuid.uuid4()))
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Full business snapshot for Command Center."""
    profile = await _get_or_create_profile(db)

    fin_result = await db.execute(
        select(FinancialRecord).order_by(desc(FinancialRecord.recorded_at)).limit(1)
    )
    latest_fin = fin_result.scalar_one_or_none()

    social_result = await db.execute(
        select(SocialMetric).order_by(desc(SocialMetric.recorded_at))
    )
    all_social = social_result.scalars().all()
    # Keep only latest per platform
    seen = {}
    social_latest = []
    for s in all_social:
        if s.platform not in seen:
            seen[s.platform] = True
            social_latest.append(s)

    steps_result = await db.execute(
        select(NextStepRecommendation)
        .where(NextStepRecommendation.status == "active")
        .order_by(desc(NextStepRecommendation.generated_at))
        .limit(1)
    )
    latest_steps = steps_result.scalar_one_or_none()

    mrr = latest_fin.mrr_ils if latest_fin else 0
    arr = mrr * 12
    progress_pct = round((arr / GOAL_ILS) * 100, 2) if arr > 0 else 0

    return {
        "profile": {
            "business_name": profile.business_name,
            "vision": profile.vision,
            "goals": json.loads(profile.goals_json) if profile.goals_json else [],
            "current_phase": profile.current_phase,
            "founded_year": profile.founded_year,
        },
        "financials": {
            "month": latest_fin.month if latest_fin else None,
            "mrr_ils": mrr,
            "arr_ils": arr,
            "revenue_ils": latest_fin.revenue_ils if latest_fin else 0,
            "expenses_ils": latest_fin.expenses_ils if latest_fin else 0,
            "net_profit_ils": latest_fin.net_profit_ils if latest_fin else 0,
            "active_students": latest_fin.active_students if latest_fin else 0,
            "new_customers": latest_fin.new_customers if latest_fin else 0,
            "avg_order_value": latest_fin.avg_order_value if latest_fin else 0,
        },
        "social": [
            {
                "platform": s.platform,
                "followers": s.followers,
                "posts_count": s.posts_count,
                "avg_engagement_rate": s.avg_engagement_rate,
                "monthly_reach": s.monthly_reach,
                "recorded_at": s.recorded_at.isoformat(),
            }
            for s in social_latest
        ],
        "next_steps": {
            "id": latest_steps.id if latest_steps else None,
            "content": latest_steps.content if latest_steps else None,
            "generated_at": latest_steps.generated_at.isoformat() if latest_steps else None,
        },
        "goal_ils": GOAL_ILS,
        "progress_pct": progress_pct,
    }


@router.post("/profile")
async def save_profile(req: ProfileIn, db: AsyncSession = Depends(get_db)):
    profile = await _get_or_create_profile(db)
    profile.business_name = req.business_name
    if req.vision is not None:
        profile.vision = req.vision
    if req.goals is not None:
        profile.goals_json = json.dumps(req.goals, ensure_ascii=False)
    if req.current_phase is not None:
        profile.current_phase = req.current_phase
    if req.founded_year is not None:
        profile.founded_year = req.founded_year
    await db.commit()
    return {"status": "saved"}


@router.post("/financial")
async def record_financial(req: FinancialIn, db: AsyncSession = Depends(get_db)):
    rec = FinancialRecord(
        id=str(uuid.uuid4()),
        month=req.month,
        revenue_ils=req.revenue_ils,
        expenses_ils=req.expenses_ils,
        net_profit_ils=req.revenue_ils - req.expenses_ils,
        mrr_ils=req.mrr_ils,
        active_students=req.active_students,
        new_customers=req.new_customers,
        avg_order_value=req.avg_order_value,
        notes=req.notes,
    )
    db.add(rec)
    await db.commit()
    return {"id": rec.id, "month": rec.month}


@router.get("/financial")
async def list_financials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FinancialRecord).order_by(desc(FinancialRecord.recorded_at)).limit(24)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "month": r.month,
            "mrr_ils": r.mrr_ils,
            "arr_ils": r.mrr_ils * 12,
            "revenue_ils": r.revenue_ils,
            "expenses_ils": r.expenses_ils,
            "net_profit_ils": r.net_profit_ils,
            "active_students": r.active_students,
            "new_customers": r.new_customers,
            "avg_order_value": r.avg_order_value,
        }
        for r in records
    ]


@router.post("/social")
async def update_social(req: SocialIn, db: AsyncSession = Depends(get_db)):
    rec = SocialMetric(
        id=str(uuid.uuid4()),
        platform=req.platform,
        followers=req.followers,
        posts_count=req.posts_count,
        avg_engagement_rate=req.avg_engagement_rate,
        monthly_reach=req.monthly_reach,
    )
    db.add(rec)
    await db.commit()
    return {"id": rec.id, "platform": rec.platform}


@router.get("/social")
async def get_social(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SocialMetric).order_by(desc(SocialMetric.recorded_at))
    )
    all_social = result.scalars().all()
    seen: dict[str, SocialMetric] = {}
    for s in all_social:
        if s.platform not in seen:
            seen[s.platform] = s
    return [
        {
            "platform": s.platform,
            "followers": s.followers,
            "posts_count": s.posts_count,
            "avg_engagement_rate": s.avg_engagement_rate,
            "monthly_reach": s.monthly_reach,
        }
        for s in seen.values()
    ]


@router.post("/generate-next-steps")
async def generate_next_steps(db: AsyncSession = Depends(get_db)):
    """Stream AI-generated weekly action plan based on full business snapshot."""
    overview_data = await get_overview(db)

    # Load recent team memory for context
    mem_result = await db.execute(
        select(TeamMemory).order_by(desc(TeamMemory.approved_at)).limit(3)
    )
    memories = mem_result.scalars().all()
    memory_text = ""
    if memories:
        parts = [f"- Goal: {m.goal}\n  Decision: {m.consensus[:200]}..." for m in memories]
        memory_text = "RECENT ADVISORY DECISIONS:\n" + "\n".join(parts)

    profile = overview_data["profile"]
    fin = overview_data["financials"]
    social = overview_data["social"]
    progress = overview_data["progress_pct"]

    snapshot = f"""BUSINESS: {profile['business_name']}
PHASE: {profile['current_phase']}
VISION: {profile['vision'] or 'Not set'}

FINANCIALS (latest month):
- MRR: ₪{fin['mrr_ils']:,.0f}
- ARR: ₪{fin['arr_ils']:,.0f}
- Revenue: ₪{fin['revenue_ils']:,.0f}
- Net Profit: ₪{fin['net_profit_ils']:,.0f}
- Active Students: {fin['active_students']}
- New Customers this month: {fin['new_customers']}

PROGRESS TO ₪100M ARR: {progress}%

SOCIAL MEDIA:
{chr(10).join(f"- {s['platform'].title()}: {s['followers']:,} followers, {s['avg_engagement_rate']}% engagement" for s in social) or "No data yet"}

{memory_text}"""

    system_prompt = """You are a ₪100M business growth strategist specializing in Israeli online education and consulting businesses.

Given a business snapshot, generate 5 SPECIFIC, numbered actions the owner should do THIS WEEK to accelerate growth toward ₪100M ARR.

Rules:
- Each action must be concrete and doable in 1-3 days
- Include specific numbers, platforms, content angles where relevant
- Prioritize highest-leverage actions (the ones that compound)
- No vague advice like "post more content" — say EXACTLY what to post, where, and why
- Format: numbered list, each item 2-3 sentences max"""

    client = get_anthropic_client()

    async def event_stream():
        full_text = ""
        async with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": f"Generate 5 actions for this week:\n\n{snapshot}"}],
            extra_headers={"anthropic-beta": CACHE_BETA},
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"

        # Save to DB
        async with AsyncSessionLocal() as save_db:
            rec = NextStepRecommendation(
                id=str(uuid.uuid4()),
                content=full_text,
                context_snapshot=json.dumps({"mrr": fin['mrr_ils'], "progress_pct": progress}, ensure_ascii=False),
            )
            save_db.add(rec)
            await save_db.commit()
            yield f"data: {json.dumps({'type': 'done', 'id': rec.id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.patch("/next-steps/{step_id}/status")
async def update_step_status(step_id: str, req: NextStepStatusIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NextStepRecommendation).where(NextStepRecommendation.id == step_id))
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "Not found")
    rec.status = req.status
    await db.commit()
    return {"status": "updated"}
