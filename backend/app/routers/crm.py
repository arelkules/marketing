"""
CRM router.
GET/POST   /crm/contacts
GET/PATCH/DELETE /crm/contacts/{id}
POST       /crm/contacts/{id}/activity
POST       /crm/contacts/{id}/ai-action  (SSE)
GET/POST   /crm/deals
PATCH      /crm/deals/{id}/stage
GET        /crm/stats
"""
from __future__ import annotations
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime

from app.database import get_db, AsyncSessionLocal
from app.models.crm import Contact, Deal, Activity
from app.utils.anthropic_client import get_anthropic_client

router = APIRouter()

MODEL = "claude-sonnet-4-6"
CACHE_BETA = "prompt-caching-2024-07-31"


# ── Schemas ───────────────────────────────────────────────────────────────────

class ContactIn(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    type: str = "lead"
    status: str = "new"
    source: Optional[str] = None
    tags: list[str] = []
    notes: Optional[str] = None
    total_paid_ils: float = 0
    lead_score: int = 0


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None
    total_paid_ils: Optional[float] = None
    lead_score: Optional[int] = None


class ActivityIn(BaseModel):
    type: str = "note"
    content: str


class DealIn(BaseModel):
    contact_id: str
    title: str
    amount_ils: float = 0
    stage: str = "new"
    product: str = "course"
    expected_close: Optional[str] = None
    notes: Optional[str] = None


class DealStageIn(BaseModel):
    stage: str


# ── Contacts ──────────────────────────────────────────────────────────────────

@router.get("/contacts")
async def list_contacts(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(Contact).order_by(desc(Contact.created_at))
    result = await db.execute(q)
    contacts = result.scalars().all()

    out = []
    for c in contacts:
        if type and c.type != type:
            continue
        if status and c.status != status:
            continue
        if search:
            s = search.lower()
            if s not in (c.name or "").lower() and s not in (c.email or "").lower() and s not in (c.phone or "").lower():
                continue
        out.append(_contact_summary(c))
    return out


@router.post("/contacts")
async def create_contact(req: ContactIn, db: AsyncSession = Depends(get_db)):
    c = Contact(
        id=str(uuid.uuid4()),
        name=req.name,
        phone=req.phone,
        email=req.email,
        type=req.type,
        status=req.status,
        source=req.source,
        tags=json.dumps(req.tags, ensure_ascii=False),
        notes=req.notes,
        total_paid_ils=req.total_paid_ils,
        lead_score=req.lead_score,
    )
    db.add(c)
    await db.commit()
    return {"id": c.id}


@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Contact not found")

    deals_result = await db.execute(select(Deal).where(Deal.contact_id == contact_id).order_by(desc(Deal.created_at)))
    deals = deals_result.scalars().all()

    acts_result = await db.execute(select(Activity).where(Activity.contact_id == contact_id).order_by(desc(Activity.created_at)))
    activities = acts_result.scalars().all()

    return {
        **_contact_summary(c),
        "notes": c.notes,
        "deals": [_deal_out(d) for d in deals],
        "activities": [_activity_out(a) for a in activities],
    }


@router.patch("/contacts/{contact_id}")
async def update_contact(contact_id: str, req: ContactUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Contact not found")
    if req.name is not None: c.name = req.name
    if req.phone is not None: c.phone = req.phone
    if req.email is not None: c.email = req.email
    if req.type is not None: c.type = req.type
    if req.status is not None: c.status = req.status
    if req.source is not None: c.source = req.source
    if req.tags is not None: c.tags = json.dumps(req.tags, ensure_ascii=False)
    if req.notes is not None: c.notes = req.notes
    if req.total_paid_ils is not None: c.total_paid_ils = req.total_paid_ils
    if req.lead_score is not None: c.lead_score = req.lead_score
    await db.commit()
    return {"status": "updated"}


@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Contact not found")
    await db.delete(c)
    await db.commit()
    return {"status": "deleted"}


@router.post("/contacts/{contact_id}/activity")
async def log_activity(contact_id: str, req: ActivityIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Contact not found")
    a = Activity(
        id=str(uuid.uuid4()),
        contact_id=contact_id,
        type=req.type,
        content=req.content,
    )
    db.add(a)
    await db.commit()
    return {"id": a.id}


@router.post("/contacts/{contact_id}/ai-action")
async def ai_action_suggestion(contact_id: str, db: AsyncSession = Depends(get_db)):
    """Stream an AI-suggested next action for this contact."""
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Contact not found")

    acts_result = await db.execute(
        select(Activity).where(Activity.contact_id == contact_id).order_by(desc(Activity.created_at)).limit(5)
    )
    recent_activities = acts_result.scalars().all()

    deals_result = await db.execute(select(Deal).where(Deal.contact_id == contact_id))
    deals = deals_result.scalars().all()

    tags = json.loads(c.tags) if c.tags else []
    activity_log = "\n".join(f"- [{a.type}] {a.content} ({a.created_at.strftime('%Y-%m-%d')})" for a in recent_activities) or "No activity yet"
    deals_log = "\n".join(f"- {d.title}: ₪{d.amount_ils:,.0f} ({d.stage})" for d in deals) or "No deals yet"

    prompt = f"""Contact: {c.name}
Type: {c.type} | Status: {c.status} | Score: {c.lead_score}/100
Source: {c.source or 'unknown'} | Total paid: ₪{c.total_paid_ils:,.0f}
Tags: {', '.join(tags) or 'none'}

Recent activities:
{activity_log}

Deals:
{deals_log}

Notes: {c.notes or 'none'}

Based on this contact's profile and history, suggest the single best next action to take RIGHT NOW. Be specific — exact message to send, content to share, or call approach. 2-3 sentences max."""

    client = get_anthropic_client()

    async def stream():
        async with client.messages.stream(
            model=MODEL,
            max_tokens=256,
            system=[{"type": "text", "text": "You are a CRM strategist for an Israeli online course and coaching business. Your job is to suggest the highest-converting next action for each contact.", "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": prompt}],
            extra_headers={"anthropic-beta": CACHE_BETA},
        ) as s:
            async for text in s.text_stream:
                yield f"data: {json.dumps({'text': text})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


# ── Deals ─────────────────────────────────────────────────────────────────────

@router.get("/deals")
async def list_deals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deal).order_by(desc(Deal.created_at)))
    deals = result.scalars().all()
    # Group by stage
    stages = ["new", "qualified", "proposal", "negotiation", "won", "lost"]
    grouped: dict[str, list] = {s: [] for s in stages}
    for d in deals:
        if d.stage in grouped:
            grouped[d.stage].append(_deal_out(d))
    return grouped


@router.post("/deals")
async def create_deal(req: DealIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Contact).where(Contact.id == req.contact_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Contact not found")
    expected = datetime.fromisoformat(req.expected_close) if req.expected_close else None
    d = Deal(
        id=str(uuid.uuid4()),
        contact_id=req.contact_id,
        title=req.title,
        amount_ils=req.amount_ils,
        stage=req.stage,
        product=req.product,
        expected_close=expected,
        notes=req.notes,
    )
    db.add(d)
    await db.commit()
    return {"id": d.id}


@router.patch("/deals/{deal_id}/stage")
async def move_deal_stage(deal_id: str, req: DealStageIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Deal not found")
    d.stage = req.stage
    # If deal won, update contact total_paid
    if req.stage == "won":
        c_result = await db.execute(select(Contact).where(Contact.id == d.contact_id))
        contact = c_result.scalar_one_or_none()
        if contact:
            contact.total_paid_ils = (contact.total_paid_ils or 0) + d.amount_ils
            contact.status = "won"
    await db.commit()
    return {"status": "updated"}


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def crm_stats(db: AsyncSession = Depends(get_db)):
    contacts_result = await db.execute(select(Contact))
    all_contacts = contacts_result.scalars().all()

    deals_result = await db.execute(select(Deal))
    all_deals = deals_result.scalars().all()

    total_by_type = {"lead": 0, "student": 0, "client": 0, "affiliate": 0}
    for c in all_contacts:
        if c.type in total_by_type:
            total_by_type[c.type] += 1

    won_deals = [d for d in all_deals if d.stage == "won"]
    total_revenue = sum(d.amount_ils for d in won_deals)
    avg_deal = total_revenue / len(won_deals) if won_deals else 0

    leads = total_by_type["lead"]
    converted = len([c for c in all_contacts if c.type == "student" or c.status == "won"])
    conversion_rate = round((converted / leads * 100), 1) if leads > 0 else 0

    return {
        "total_contacts": len(all_contacts),
        "by_type": total_by_type,
        "total_deals": len(all_deals),
        "won_deals": len(won_deals),
        "total_revenue_ils": total_revenue,
        "avg_deal_size_ils": avg_deal,
        "conversion_rate_pct": conversion_rate,
    }


# ── Serializers ───────────────────────────────────────────────────────────────

def _contact_summary(c: Contact) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "phone": c.phone,
        "email": c.email,
        "type": c.type,
        "status": c.status,
        "source": c.source,
        "tags": json.loads(c.tags) if c.tags else [],
        "total_paid_ils": c.total_paid_ils,
        "lead_score": c.lead_score,
        "created_at": c.created_at.isoformat(),
    }


def _deal_out(d: Deal) -> dict:
    return {
        "id": d.id,
        "contact_id": d.contact_id,
        "title": d.title,
        "amount_ils": d.amount_ils,
        "stage": d.stage,
        "product": d.product,
        "expected_close": d.expected_close.isoformat() if d.expected_close else None,
        "notes": d.notes,
        "created_at": d.created_at.isoformat(),
    }


def _activity_out(a: Activity) -> dict:
    return {
        "id": a.id,
        "type": a.type,
        "content": a.content,
        "created_at": a.created_at.isoformat(),
    }
