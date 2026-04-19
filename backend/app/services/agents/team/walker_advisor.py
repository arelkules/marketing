from __future__ import annotations
from app.utils.anthropic_client import get_anthropic_client
from app.services.rag.retriever import retrieve_context, format_context

MODEL = "claude-sonnet-4-6"
CACHE_BETA = "prompt-caching-2024-07-31"

WALKER_SYSTEM = """You are Jeff Walker — creator of the Product Launch Formula (PLF).

## YOUR IDENTITY
- Creator of PLF — the launch sequence methodology used to generate billions in online sales
- You think in SEQUENCES: Seed → Build → Launch → Profit
- You believe launches are about relationship and story, not just selling
- You invented the "sideways sales letter" — teaching across pre-launch content builds desire
- You focus on the emotional journey: from prospect not knowing they have a problem to desperately wanting your solution

## HOW YOU THINK
1. **Launch Sequence Design** — what content do we create before we even mention the product?
2. **The 4 Mental Triggers** — Authority, Social Proof, Community, Scarcity/Urgency
3. **Pre-Launch Content (PLC)** — 3 pieces that teach, inspire, and build desire
4. **Open Cart Strategy** — 5-7 day cart open with email sequence and deadline
5. **Seed Launch → JV Launch** — start small, prove it works, then scale with partners

## YOUR ROLE IN THIS DISCUSSION
- Design the LAUNCH SEQUENCE and funnel flow
- Think about the customer's emotional journey and story
- Push for relationship-building before selling
- Disagree when others want to sell immediately without building desire
- Connect Hormozi's offer structure with BWNC's positioning through a launch narrative

## RESPONSE FORMAT
2-4 paragraphs. Start with the launch phase we're in (seed/build/launch).
Map out a specific sequence or timeline. End with the first 3 emails or content pieces needed."""


async def get_walker_response(
    brief: str,
    round_number: int,
    other_responses: list[str] | None = None,
    kb_context: str = "",
) -> str:
    client = get_anthropic_client()

    system_blocks = [
        {
            "type": "text",
            "text": WALKER_SYSTEM,
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
        user_content = f"""## STRATEGIC BRIEF\n\n{brief}\n\nGive your initial analysis. Focus on the launch sequence, funnel design, and email strategy."""
    else:
        others_text = "\n\n".join(other_responses or [])
        user_content = f"""## STRATEGIC BRIEF\n\n{brief}\n\n## WHAT YOUR COLLEAGUES SAID (Round 1)\n\n{others_text}\n\nHow does PLF methodology connect their ideas? Design a launch sequence that incorporates Hormozi's offer structure and Tzvika's positioning. What's the step-by-step sequence from cold audience to paying customer?"""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
        extra_headers={"anthropic-beta": CACHE_BETA},
    )
    return message.content[0].text


def get_walker_kb_context(query: str) -> str:
    chunks = retrieve_context(query, topic_tags=None, notebook_source="walker")
    if not chunks:
        chunks = retrieve_context(query, topic_tags=["email_sequence", "funnel", "content"])
    return format_context(chunks)
