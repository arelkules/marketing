from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.utils.chroma_client import get_collection
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    await init_db()
    get_collection()  # warm up ChromaDB connection
    # Embedding model loaded lazily on first ingest call
    yield


app = FastAPI(title="Marketing AI Agent System", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import ingest, agents, assets, metrics, pipeline, notebooklm, team, command, crm  # noqa

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(pipeline.router, prefix="/pipeline", tags=["pipeline"])
app.include_router(notebooklm.router, prefix="/notebooklm", tags=["notebooklm"])
app.include_router(team.router, prefix="/team", tags=["team"])
app.include_router(command.router, prefix="/command", tags=["command"])
app.include_router(crm.router, prefix="/crm", tags=["crm"])


from fastapi.responses import PlainTextResponse
import pathlib

@app.get("/download/notebooklm-sync", response_class=PlainTextResponse)
async def download_sync_script():
    """Serve the notebooklm_sync.py script for local download."""
    script_path = pathlib.Path(__file__).parent.parent.parent.parent / "notebooklm_sync.py"
    if not script_path.exists():
        from fastapi import HTTPException
        raise HTTPException(404, "Script not found")
    return PlainTextResponse(
        content=script_path.read_text(encoding="utf-8"),
        headers={"Content-Disposition": "attachment; filename=notebooklm_sync.py"},
        media_type="text/x-python",
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
