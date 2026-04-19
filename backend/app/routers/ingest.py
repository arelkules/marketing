import asyncio
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.document import KnowledgeDocument, DocumentChunk
from app.schemas.document import KnowledgeDocumentOut, DocumentStatusOut
from app.services.ingest.parser import parse_file
from app.services.ingest.chunker import chunk_text
from app.services.ingest.embedder import embed_chunks, delete_document_embeddings
from app.config import settings

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


async def _process_document(doc_id: str, content: bytes, filename: str, file_type: str):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        doc = await db.get(KnowledgeDocument, doc_id)
        if not doc:
            return
        try:
            doc.status = "processing"
            await db.commit()

            text = parse_file(content, filename)
            chunks = chunk_text(text)

            embed_chunks(chunks, doc_id, filename, file_type)

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
            db.add_all(chunk_records)
            doc.status = "completed"
            doc.chunk_count = len(chunks)
            await db.commit()

        except Exception as e:
            doc.status = "error"
            doc.error_msg = str(e)[:500]
            await db.commit()


@router.post("/upload", response_model=KnowledgeDocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES and not file.filename.endswith((".pdf", ".txt", ".docx")):
        raise HTTPException(400, "Only PDF, TXT, and DOCX files are supported.")

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_size_mb}MB limit.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
    doc_id = str(uuid.uuid4())
    doc = KnowledgeDocument(
        id=doc_id,
        filename=file.filename,
        file_type=ext,
        file_size=len(content),
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(_process_document, doc_id, content, file.filename, ext)
    return doc


@router.get("/documents", response_model=list[KnowledgeDocumentOut])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()))
    return result.scalars().all()


@router.get("/documents/{doc_id}/status", response_model=DocumentStatusOut)
async def document_status(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return DocumentStatusOut(id=doc.id, status=doc.status, chunk_count=doc.chunk_count, error_msg=doc.error_msg)


@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    doc = await db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    delete_document_embeddings(doc_id)
    await db.delete(doc)
    await db.commit()


@router.get("/notebooks")
async def list_notebooks_status(db: AsyncSession = Depends(get_db)):
    """Show which NotebookLM notebooks are loaded and their chunk counts."""
    from app.services.ingest.embedder import _detect_notebook_source
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.filename.like("notebooklm_%"))
        .order_by(KnowledgeDocument.created_at.desc())
    )
    docs = result.scalars().all()

    ADVISOR_MAP = {
        "hormozi": {"name": "Alex Hormozi", "icon": "💪", "advisor": "hormozi"},
        "bwnc":    {"name": "עסק ללא מתחרים", "icon": "🎯", "advisor": "bwnc"},
        "walker":  {"name": "Jeff Walker / PLF", "icon": "🚀", "advisor": "walker"},
        "robbins": {"name": "Tony Robbins", "icon": "🔥", "advisor": "robbins"},
        "business":{"name": "גבר ללא מגבלות", "icon": "🏢", "advisor": "all agents"},
        "general": {"name": "General", "icon": "📄", "advisor": "all agents"},
    }

    seen: dict[str, dict] = {}
    for doc in docs:
        source = _detect_notebook_source(doc.filename)
        if source not in seen:
            info = ADVISOR_MAP.get(source, {"name": source, "icon": "📄", "advisor": "?"})
            seen[source] = {
                **info,
                "notebook_source": source,
                "chunks": 0,
                "status": doc.status,
                "last_synced": doc.created_at.isoformat(),
                "documents": [],
            }
        seen[source]["chunks"] += (doc.chunk_count or 0)
        seen[source]["documents"].append({
            "filename": doc.filename,
            "status": doc.status,
            "chunks": doc.chunk_count or 0,
        })

    # Which advisors are missing
    all_sources = {"hormozi", "bwnc", "walker", "robbins", "business"}
    missing = [
        {**ADVISOR_MAP[s], "notebook_source": s, "chunks": 0, "status": "not_synced", "documents": []}
        for s in all_sources if s not in seen
    ]

    return {
        "loaded": list(seen.values()),
        "missing": missing,
        "total_chunks": sum(v["chunks"] for v in seen.values()),
    }
