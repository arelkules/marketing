"""
NotebookLM sync router.
POST /notebooklm/list    — list all notebooks (requires cookies)
POST /notebooklm/sync    — sync selected notebooks into knowledge base
GET  /notebooklm/status  — get sync status
"""
from __future__ import annotations
import asyncio
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import KnowledgeDocument, DocumentChunk
from app.services.ingest.chunker import chunk_text
from app.services.ingest.embedder import embed_chunks
from app.scripts.notebooklm_scraper import list_notebooks, full_sync, Notebook

router = APIRouter()

# In-memory sync status store (per session)
_sync_status: dict[str, list[str]] = {}


class CookiesRequest(BaseModel):
    cookies: list[dict]


class SyncRequest(BaseModel):
    cookies: list[dict]
    notebook_ids: list[str] | None = None  # None = sync all


@router.post("/list")
async def list_notebooks_endpoint(req: CookiesRequest):
    """List all NotebookLM notebooks for the provided cookies."""
    try:
        notebooks = await list_notebooks(req.cookies)
        if notebooks and "error" in notebooks[0]:
            raise HTTPException(401, notebooks[0]["message"])
        return {"notebooks": notebooks}
    except ValueError as e:
        raise HTTPException(401, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to connect to NotebookLM: {e}")


@router.post("/sync")
async def sync_notebooks(req: SyncRequest, db: AsyncSession = Depends(get_db)):
    """Stream sync progress as SSE. Ingests each notebook into the knowledge base."""
    sync_id = str(uuid.uuid4())
    messages = []
    _sync_status[sync_id] = messages

    async def run_sync():
        notebooks: list[Notebook] = []
        errors = []

        def on_progress(msg: str):
            messages.append(msg)

        try:
            notebooks = await full_sync(req.cookies, req.notebook_ids, on_progress)
        except Exception as e:
            messages.append(f"ERROR: {e}")
            return

        # Ingest each notebook into knowledge base
        for notebook in notebooks:
            try:
                full_text = notebook.to_text()
                if not full_text.strip():
                    messages.append(f"⚠ {notebook.title} — no content to ingest")
                    continue

                # Create document record
                doc_id = str(uuid.uuid4())
                filename = f"notebooklm_{notebook.title.replace(' ', '_')}.txt"

                from app.database import AsyncSessionLocal
                async with AsyncSessionLocal() as save_db:
                    doc = KnowledgeDocument(
                        id=doc_id,
                        filename=filename,
                        file_type="txt",
                        file_size=len(full_text.encode()),
                        status="processing",
                    )
                    save_db.add(doc)
                    await save_db.commit()

                    # Chunk + embed
                    chunks = chunk_text(full_text)
                    embed_chunks(chunks, doc_id, filename, "txt")

                    # Save chunk records
                    chunk_records = [
                        DocumentChunk(
                            id=f"{doc_id}_{c.index}",
                            document_id=doc_id,
                            chunk_index=c.index,
                            text_preview=c.text[:200],
                            token_count=c.token_estimate,
                            topic_tag=c.topic_tag,
                        )
                        for c in chunks
                    ]
                    save_db.add_all(chunk_records)
                    doc.status = "completed"
                    doc.chunk_count = len(chunks)
                    await save_db.commit()

                messages.append(f"✅ Ingested '{notebook.title}' — {len(chunks)} chunks added to knowledge base")

            except Exception as e:
                messages.append(f"✗ Failed to ingest {notebook.title}: {e}")

        messages.append(f"DONE:{sync_id}")

    asyncio.create_task(run_sync())

    async def event_stream():
        import asyncio
        sent = 0
        while True:
            while sent < len(_sync_status.get(sync_id, [])):
                msg = _sync_status[sync_id][sent]
                yield f"data: {json.dumps({'message': msg})}\n\n"
                sent += 1
                if msg.startswith("DONE:"):
                    del _sync_status[sync_id]
                    return
            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/cookie-help")
async def cookie_help():
    return {
        "instructions": [
            "1. Open Chrome and go to notebooklm.google.com",
            "2. Make sure you are logged in with your Google account",
            "3. Install the 'EditThisCookie' Chrome extension",
            "4. Click the extension icon while on NotebookLM",
            "5. Click 'Export' (the arrow icon) — copies JSON to clipboard",
            "6. Paste the JSON into the Cookie field in this dashboard",
            "7. Click 'Connect' — your notebooks will appear automatically",
        ],
        "alternative": "You can also use the 'Cookie-Editor' extension and export as JSON"
    }
