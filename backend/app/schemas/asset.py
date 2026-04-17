from pydantic import BaseModel
from datetime import datetime
import json


class AssetCreate(BaseModel):
    agent_type: str
    title: str
    content: str
    tags: list[str] = []
    pipeline_stage: str = "draft"
    message_id: str | None = None


class AssetUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    pipeline_stage: str | None = None


class AssetOut(BaseModel):
    id: str
    agent_type: str
    title: str
    content: str
    tags: list[str]
    pipeline_stage: str
    word_count: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if hasattr(obj, "tags") and isinstance(obj.tags, str):
            try:
                obj.tags = json.loads(obj.tags)
            except Exception:
                obj.tags = []
        return super().model_validate(obj, *args, **kwargs)
