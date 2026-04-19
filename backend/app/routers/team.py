"""
Multi-agent advisory team router.
POST /team/start        — start session with goal, get clarifying questions
POST /team/discuss      — submit answers, run full discussion (SSE)
POST /team/sessions/{id}/approve  — approve consensus
POST /team/sessions/{id}/feedback — add correction
GET  /team/sessions     — list recent sessions
"""
from __future__ import annotations
import asyncio
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, AsyncSessionLocal
from app.models.team import TeamSession, TeamMessage
from app.services.agents.team.discussion import DiscussionState
from app.services.agents.team.team_manager import ask_clarifying_questions, run_discussion
from app.services.agents.team.memory import save_approved, load_context

router = APIRouter()


class StartRequest(BaseModel):
    goal: str
    business_name: str = "גבר ללא מגבלות"


class DiscussRequest(BaseModel):
    session_id: str
    answers: dict[str, str]  # question -> answer


class ApproveRequest(BaseModel):
    correction: str | None = None


@router.post("/start")
async def start_session(req: StartRequest, db: AsyncSession = Depends(get_db)):
    """Create a session and return clarifying questions."""
    questions = await ask_clarifying_questions(req.goal, req.business_name)

    session = TeamSession(
        id=str(uuid.uuid4()),
        business_name=req.business_name,
        goal=req.goal,
        status="questioning",
    )
    db.add(session)
    await db.commit()

    return {
        "session_id": session.id,
        "questions": questions,
    }


@router.post("/discuss")
async def run_team_discussion(req: DiscussRequest):
    """Submit answers and stream the full advisory discussion as SSE."""

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TeamSession).where(TeamSession.id == req.session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(404, "Session not found")

        session.user_answers = json.dumps(req.answers, ensure_ascii=False)
        session.status = "discussing"
        await db.commit()

        goal = session.goal
        business_name = session.business_name

    past_memory = await load_context(business_name)

    state = DiscussionState(
        goal=goal,
        business_name=business_name,
        user_answers=req.answers,
        past_memory=past_memory,
    )

    async def event_stream():
        messages_to_save: list[TeamMessage] = []

        async for event in run_discussion(state):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

            if event["type"] == "advisor_message":
                messages_to_save.append(TeamMessage(
                    id=str(uuid.uuid4()),
                    session_id=req.session_id,
                    advisor=event["advisor"],
                    content=event["content"],
                    round_number=event["round"],
                ))
            elif event["type"] == "consensus":
                messages_to_save.append(TeamMessage(
                    id=str(uuid.uuid4()),
                    session_id=req.session_id,
                    advisor="manager",
                    content=event["content"],
                    round_number=0,
                ))

        # Persist to DB
        async with AsyncSessionLocal() as db:
            for msg in messages_to_save:
                db.add(msg)
            result = await db.execute(select(TeamSession).where(TeamSession.id == req.session_id))
            session = result.scalar_one_or_none()
            if session:
                session.status = "consensus"
            await db.commit()

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/sessions/{session_id}/approve")
async def approve_session(session_id: str, req: ApproveRequest, db: AsyncSession = Depends(get_db)):
    """Approve or correct the consensus — saves to team memory."""
    result = await db.execute(select(TeamSession).where(TeamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    # Get consensus message
    msg_result = await db.execute(
        select(TeamMessage)
        .where(TeamMessage.session_id == session_id, TeamMessage.advisor == "manager")
    )
    consensus_msg = msg_result.scalar_one_or_none()
    if not consensus_msg:
        raise HTTPException(400, "No consensus found for this session")

    await save_approved(
        session_id=session_id,
        business_name=session.business_name,
        goal=session.goal,
        consensus=consensus_msg.content,
        user_correction=req.correction,
    )

    session.status = "approved"
    await db.commit()

    return {"status": "saved", "message": "Decision saved to team memory"}


@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TeamSession).order_by(TeamSession.created_at.desc()).limit(20)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "business_name": s.business_name,
            "goal": s.goal,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TeamSession).where(TeamSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    msg_result = await db.execute(
        select(TeamMessage)
        .where(TeamMessage.session_id == session_id)
        .order_by(TeamMessage.created_at)
    )
    messages = msg_result.scalars().all()

    return {
        "session": {
            "id": session.id,
            "business_name": session.business_name,
            "goal": session.goal,
            "status": session.status,
            "user_answers": json.loads(session.user_answers) if session.user_answers else {},
        },
        "messages": [
            {
                "advisor": m.advisor,
                "content": m.content,
                "round_number": m.round_number,
            }
            for m in messages
        ],
    }
