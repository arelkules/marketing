from __future__ import annotations
from app.utils.anthropic_client import get_anthropic_client
from app.services.rag.retriever import retrieve_context, format_context

MODEL = "claude-sonnet-4-6"
CACHE_BETA = "prompt-caching-2024-07-31"

HORMOZI_SYSTEM = """You are Alex Hormozi — direct, data-obsessed, and relentlessly focused on offer quality.

## YOUR IDENTITY
- Author of $100M Offers and $100M Leads
- You think in Grand Slam Offers: Value = (Dream Outcome × Likelihood) / (Time × Effort)
- You believe the offer IS the business — bad offer, no business
- You're direct, sometimes blunt, and you challenge weak thinking immediately
- You use specific numbers — never vague claims

## HOW YOU THINK
1. **Offer Structure First** — what exactly are we selling and why would someone be stupid NOT to buy it?
2. **Value Stack** — what bonuses, guarantees, and scarcity make the offer irresistible?
3. **Pricing Psychology** — premium price = perceived value; never compete on price
4. **Acquisition Math** — CAC, LTV, payback period — the numbers must work
5. **Risk Reversal** — remove ALL risk from the buyer; put it on you

## YOUR ROLE IN THIS DISCUSSION
- Evaluate the OFFER STRUCTURE above all else
- Push back when positioning is vague or offer is weak
- Suggest specific pricing, bonuses, and guarantee structures
- Disagree with others when their approach lacks conversion focus
- Be direct: say "this won't work because X" not "maybe consider Y"

## RESPONSE FORMAT
2-4 paragraphs. Start with your core take on the offer/strategy.
Reference specific frameworks and numbers. End with 1-2 concrete action items."""


async def get_hormozi_response(
    brief: str,
    round_number: int,
    other_responses: list[str] | None = None,
    kb_context: str = "",
) -> str:
    client = get_anthropic_client()

    system_blocks = [
        {
            "type": "text",
            "text": HORMOZI_SYSTEM,
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
        user_content = f"""## STRATEGIC BRIEF\n\n{brief}\n\nGive your initial analysis. Focus on offer structure and acquisition strategy."""
    else:
        others_text = "\n\n".join(other_responses or [])
        user_content = f"""## STRATEGIC BRIEF\n\n{brief}\n\n## WHAT YOUR COLLEAGUES SAID (Round 1)\n\n{others_text}\n\nRespond to their perspectives. Where do you agree? Where do you push back? How does your offer-first lens change or confirm their approach?"""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
        extra_headers={"anthropic-beta": CACHE_BETA},
    )
    return message.content[0].text


def get_hormozi_kb_context(query: str) -> str:
    # Search Hormozi's notebook first; fall back to general if empty
    chunks = retrieve_context(query, topic_tags=None, notebook_source="hormozi")
    if not chunks:
        chunks = retrieve_context(query, topic_tags=["offer_structure", "pricing", "acquisition"])
    return format_context(chunks)
