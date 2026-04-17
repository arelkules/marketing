from dataclasses import dataclass
import re


TOPIC_KEYWORDS: dict[str, list[str]] = {
    "offer_structure": ["grand slam", "offer", "value stack", "bonus", "guarantee", "price", "pricing", "upsell"],
    "email_copy": ["email", "subject line", "open rate", "sequence", "nurture", "broadcast", "drip"],
    "video_script": ["script", "hook", "youtube", "tiktok", "reels", "shorts", "thumbnail", "cta", "watch time"],
    "business_strategy": ["strategy", "value ladder", "funnel", "revenue", "growth", "scale", "100m", "market"],
    "ad_copy": ["ad", "facebook", "google", "paid traffic", "creative", "roas", "campaign", "targeting"],
    "audience": ["avatar", "audience", "customer", "prospect", "lead", "buyer", "persona"],
    "testimonials": ["testimonial", "case study", "result", "transformation", "success story"],
    "positioning": ["positioning", "competitor", "differentiate", "unique", "blue ocean", "category"],
}

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    text: str
    index: int
    topic_tag: str
    token_estimate: int


def _estimate_tokens(text: str) -> int:
    return len(text) // 4


def _classify_topic(text: str) -> str:
    text_lower = text.lower()
    for tag, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return tag
    return "general"


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break

        # Find the best split point near end
        best_split = end
        for sep in SEPARATORS:
            idx = text.rfind(sep, start + chunk_size // 2, end)
            if idx != -1:
                best_split = idx + len(sep)
                break

        chunks.append(text[start:best_split])
        start = best_split - overlap

    return [c.strip() for c in chunks if c.strip()]


def chunk_text(text: str) -> list[Chunk]:
    raw_chunks = _split_text(text, CHUNK_SIZE * 4, CHUNK_OVERLAP * 4)  # char-based approx
    result = []
    for i, chunk_text in enumerate(raw_chunks):
        token_est = _estimate_tokens(chunk_text)
        result.append(Chunk(
            text=chunk_text,
            index=i,
            topic_tag=_classify_topic(chunk_text),
            token_estimate=token_est,
        ))
    return result
