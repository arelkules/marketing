from pydantic import BaseModel
from datetime import datetime


class DocumentChunkOut(BaseModel):
    id: str
    chunk_index: int
    text_preview: str
    token_count: int | None
    topic_tag: str | None

    class Config:
        from_attributes = True


class KnowledgeDocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_msg: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusOut(BaseModel):
    id: str
    status: str
    chunk_count: int
    error_msg: str | None
