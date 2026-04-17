import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.conversation import AgentConversation, AgentMessage
from app.schemas.agent import AgentChatRequest, ConversationOut
from app.services.agents.orchestrator import route_to_agent

router = APIRouter()


@router.post("/chat")
async def chat(request: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    agent = route_to_agent(request.message, request.agent_type)

    if request.conversation_id:
        conv = await db.get(AgentConversation, request.conversation_id)
        if not conv:
            raise HTTPException(404, "Conversation not found")
    else:
        conv = AgentConversation(
            id=str(uuid.uuid4()),
            agent_type=agent.agent_type,
            title=request.message[:60],
        )
        db.add(conv)
        await db.commit()

    history_result = await db.execute(
        select(AgentMessage)
        .where(AgentMessage.conversation_id == conv.id)
        .order_by(AgentMessage.created_at.asc())
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in history_result.scalars().all()
    ]

    user_msg = AgentMessage(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.commit()

    assistant_msg_id = str(uuid.uuid4())

    async def event_stream():
        full_content = []
        usage = None

        yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conv.id, 'message_id': assistant_msg_id, 'agent_type': agent.agent_type})}\n\n"

        async for text, u in agent.stream(request.message, history):
            if u is not None:
                usage = u
            elif text:
                full_content.append(text)
                yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"

        complete_content = "".join(full_content)

        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as save_db:
            asst_msg = AgentMessage(
                id=assistant_msg_id,
                conversation_id=conv.id,
                role="assistant",
                content=complete_content,
                input_tokens=usage.input_tokens if usage else None,
                output_tokens=usage.output_tokens if usage else None,
                cache_read_tokens=usage.cache_read_tokens if usage else None,
                cache_write_tokens=usage.cache_write_tokens if usage else None,
                estimated_cost_usd=usage.cost_usd if usage else None,
            )
            save_db.add(asst_msg)
            await save_db.commit()

        meta = {}
        if usage:
            meta = {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_read_tokens": usage.cache_read_tokens,
                "cost_usd": usage.cost_usd,
            }
        yield f"data: {json.dumps({'type': 'done', **meta})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentConversation).order_by(AgentConversation.updated_at.desc()).limit(50)
    )
    return result.scalars().all()


@router.delete("/conversations/{conv_id}", status_code=204)
async def delete_conversation(conv_id: str, db: AsyncSession = Depends(get_db)):
    conv = await db.get(AgentConversation, conv_id)
    if not conv:
        raise HTTPException(404, "Not found")
    await db.delete(conv)
    await db.commit()
