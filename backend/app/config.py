from __future__ import annotations
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    anthropic_api_key: str = "sk-ant-placeholder"
    database_url: str = "sqlite+aiosqlite:///./data/sqlite/marketing.db"
    chroma_persist_dir: str = "./data/chroma_db"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 50
    embedding_model: str = "all-MiniLM-L6-v2"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
