from pydantic import BaseModel
from typing import Literal


AgentType = Literal["copy", "email", "video", "strategy", "ads"]


class AgentChatRequest(BaseModel):
    message: str
    agent_type: AgentType | None = None
    conversation_id: str | None = None


class AgentChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    content: str
    agent_type: AgentType
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_tokens: int | None = None
    estimated_cost_usd: float | None = None


class ConversationOut(BaseModel):
    id: str
    agent_type: str
    title: str | None

    class Config:
        from_attributes = True
