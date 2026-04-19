from __future__ import annotations
from datetime import datetime, timezone
from app.services.ingest.chunker import Chunk
from app.utils.chroma_client import get_collection

_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        from app.config import settings
        _embedding_model = SentenceTransformer(settings.embedding_model)
    return _embedding_model


def _detect_notebook_source(filename: str) -> str:
    """Derive which NotebookLM notebook a file came from based on filename."""
    name = filename.lower()
    if "hormozi" in name or "alex" in name or "100m" in name:
        return "hormozi"
    if "מתחרים" in name or "bwnc" in name or "עסק_ללא" in name or "business_without" in name:
        return "bwnc"
    if "walker" in name or "plf" in name or "product_launch" in name:
        return "walker"
    if "robbins" in name or "tony" in name or "טוני" in name:
        return "robbins"
    if "גבר" in name or "ללא_מגבלות" in name or "man_without" in name:
        return "business"
    if name.startswith("notebooklm_"):
        return "business"
    return "general"


def embed_chunks(
    chunks: list[Chunk],
    document_id: str,
    filename: str,
    file_type: str,
) -> list[str]:
    if not chunks:
        return []

    model = _get_embedding_model()
    texts = [c.text for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    collection = get_collection()
    ids = [f"{document_id}_{c.index}" for c in chunks]
    notebook_source = _detect_notebook_source(filename)
    metadatas = [
        {
            "source_filename": filename,
            "document_id": document_id,
            "chunk_index": c.index,
            "topic_tag": c.topic_tag,
            "file_type": file_type,
            "char_count": len(c.text),
            "notebook_source": notebook_source,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
        for c in chunks
    ]

    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return ids


def delete_document_embeddings(document_id: str) -> None:
    collection = get_collection()
    results = collection.get(where={"document_id": document_id})
    if results["ids"]:
        collection.delete(ids=results["ids"])
