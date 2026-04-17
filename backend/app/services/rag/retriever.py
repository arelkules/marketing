from __future__ import annotations
from app.utils.chroma_client import get_collection
from app.services.ingest.embedder import _get_embedding_model

TOP_K = 8


def retrieve_context(query: str, topic_tags: list[str] | None = None) -> list[dict]:
    model = _get_embedding_model()
    query_embedding = model.encode([query]).tolist()[0]
    collection = get_collection()

    where = {"topic_tag": {"$in": topic_tags}} if topic_tags else None

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(TOP_K, collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(TOP_K, max(1, collection.count())),
            include=["documents", "metadatas", "distances"],
        )

    chunks = []
    if results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({
                "text": doc,
                "source": meta.get("source_filename", "unknown"),
                "topic_tag": meta.get("topic_tag", "general"),
                "relevance": round(1 - dist, 3),
            })
    return chunks


def format_context(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    parts = []
    for chunk in chunks:
        parts.append(f"[From: {chunk['source']} | Topic: {chunk['topic_tag']}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)
