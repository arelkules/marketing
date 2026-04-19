from __future__ import annotations
from app.utils.chroma_client import get_collection
from app.services.ingest.embedder import _get_embedding_model

TOP_K = 8


def retrieve_context(
    query: str,
    topic_tags: list[str] | None = None,
    notebook_source: str | None = None,
) -> list[dict]:
    model = _get_embedding_model()
    query_embedding = model.encode([query]).tolist()[0]
    collection = get_collection()

    total = collection.count()
    if total == 0:
        return []
    n_results = min(TOP_K, total)

    # Build where clause
    where = _build_where(topic_tags, notebook_source)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # Fallback: no filter (empty knowledge base edge case)
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

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
                "notebook_source": meta.get("notebook_source", "general"),
                "relevance": round(1 - dist, 3),
            })
    return chunks


def _build_where(
    topic_tags: list[str] | None,
    notebook_source: str | None,
) -> dict | None:
    conditions = []
    if notebook_source:
        conditions.append({"notebook_source": {"$eq": notebook_source}})
    if topic_tags:
        conditions.append({"topic_tag": {"$in": topic_tags}})

    if len(conditions) == 0:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def format_context(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    parts = []
    for chunk in chunks:
        parts.append(f"[From: {chunk['source']} | Topic: {chunk['topic_tag']}]\n{chunk['text']}")
    return "\n\n---\n\n".join(parts)
