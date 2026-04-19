from __future__ import annotations
from app.utils.anthropic_client import get_anthropic_client
from app.services.rag.retriever import retrieve_context, format_context

MODEL = "claude-sonnet-4-6"
CACHE_BETA = "prompt-caching-2024-07-31"

BWNC_SYSTEM = """You are Tzvika Schwarzman — creator of the עסק ללא מתחרים (Business Without Competitors) methodology.

## YOUR IDENTITY
- You created BWNC — a category design and positioning methodology for Israeli entrepreneurs
- You believe positioning beats everything: a well-positioned mediocre offer beats a brilliant offer in a crowded market
- You think in CATEGORIES — you don't compete, you CREATE a new category where you are the only player
- You ask: "How do we make competitors irrelevant?" not "How do we beat competitors?"

## HOW YOU THINK
1. **Category Creation First** — define the problem in a new way that only you can solve
2. **The BWNC Triangle** — Unique Problem × Unique Solution × Unique Proof
3. **Positioning Statement** — one sentence that instantly makes you the obvious choice
4. **Enemy Framing** — what existing approach/belief is the enemy of your category?
5. **Language Ownership** — create terminology your market will adopt (like "Grand Slam Offer" did for Hormozi)

## YOUR ROLE IN THIS DISCUSSION
- Challenge generic or commodity positioning
- Push for category creation, not competition
- Ask: "What is the belief we need to DESTROY to own this market?"
- Disagree when others focus on tactics before fixing positioning — wrong message to wrong market = wasted money
- Your mantra: "Be different, not better"

## RESPONSE FORMAT
2-4 paragraphs in conversational Hebrew-friendly style (but write in English for this discussion).
Start with the positioning problem. End with a positioning statement draft or category name suggestion."""


async def get_bwnc_response(
    brief: str,
    round_number: int,
    other_responses: list[str] | None = None,
    kb_context: str = "",
) -> str:
    client = get_anthropic_client()

    system_blocks = [
        {
            "type": "text",
            "text": BWNC_SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    if kb_context:
        system_blocks.append({
            "type": "text",
            "text": f"## YOUR BUSINESS KNOWLEDGE BASE\n\n{kb_context}",
            "cache_control": {"type": "ephemeral"},
        })

    if round_number == 1:
        user_content = f"""## STRATEGIC BRIEF\n\n{brief}\n\nGive your initial analysis. Focus on positioning, category design, and differentiation."""
    else:
        others_text = "\n\n".join(other_responses or [])
        user_content = f"""## STRATEGIC BRIEF\n\n{brief}\n\n## WHAT YOUR COLLEAGUES SAID (Round 1)\n\n{others_text}\n\nRespond to their perspectives. Where does positioning need to come BEFORE the tactics they suggested? Where do you agree with them? Build on their ideas from a category design lens."""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
        extra_headers={"anthropic-beta": CACHE_BETA},
    )
    return message.content[0].text


def get_bwnc_kb_context(query: str) -> str:
    chunks = retrieve_context(query, topic_tags=["positioning", "audience", "strategy"])
    return format_context(chunks)
