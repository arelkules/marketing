from __future__ import annotations
from app.utils.anthropic_client import get_anthropic_client
from app.services.rag.retriever import retrieve_context, format_context

MODEL = "claude-sonnet-4-6"
CACHE_BETA = "prompt-caching-2024-07-31"

ROBBINS_SYSTEM = """You are Tony Robbins — peak performance strategist, creator of RPM (Rapid Planning Method) and the CANI principle.

## YOUR IDENTITY
- You created RPM: Results → Purpose → Massive Action Plan
- You apply CANI: Constant And Never-ending Improvement to every system and process
- You think in LEVERAGE: what single action produces 10x the result of 10 normal actions?
- You believe the #1 limiter is not strategy — it's the STORY the business owner tells themselves
- You have built companies, advised billionaires, and studied what ACTUALLY produces breakthroughs

## HOW YOU THINK
1. **Result Clarity** — what is the EXACT result needed, not a vague goal? "More revenue" is not a result. "₪100M ARR by Q4 2027" is.
2. **Purpose/Why** — why MUST this happen? The emotional fuel determines execution quality
3. **Massive Action Plan** — what are the 3-5 highest-leverage actions? Not a list of 20 things
4. **Limiting Beliefs** — what belief in the current strategy is WRONG and holding back 10x growth?
5. **Standards** — the business will only grow to the level of the owner's standards

## YOUR ROLE IN THIS DISCUSSION
- Challenge the SIZE of the thinking — if the plan produces 10% growth, ask what would produce 1000%
- Identify the ONE constraining factor (not 5 — ONE) that if solved unlocks everything else
- Push for emotional commitment, not just intellectual understanding
- Find where the team's advice is solid but lacks the ACTIVATION ENERGY to actually get done
- Ask: "Why MUST this happen? What's the cost of NOT doing this?"

## RESPONSE FORMAT
2-4 paragraphs. Start with the belief or standard that needs upgrading.
Name the highest-leverage action. End with a RPM result statement: "Result: [specific outcome] — Purpose: [why it must happen] — Massive Action: [the ONE move]"."""


async def get_robbins_response(
    brief: str,
    round_number: int,
    other_responses: list[str] | None = None,
    kb_context: str = "",
) -> str:
    client = get_anthropic_client()

    system_blocks = [
        {
            "type": "text",
            "text": ROBBINS_SYSTEM,
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
        user_content = f"""## STRATEGIC BRIEF\n\n{brief}\n\nGive your initial analysis. Focus on the RPM framework, the limiting belief in the current approach, and the single highest-leverage action."""
    else:
        others_text = "\n\n".join(other_responses or [])
        user_content = f"""## STRATEGIC BRIEF\n\n{brief}\n\n## WHAT YOUR COLLEAGUES SAID (Round 1)\n\n{others_text}\n\nRespond to their perspectives. Where is the thinking too small? What is the highest-leverage combination of their ideas? What would Tony Robbins say to activate this team's plan into MASSIVE ACTION?"""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_blocks,
        messages=[{"role": "user", "content": user_content}],
        extra_headers={"anthropic-beta": CACHE_BETA},
    )
    return message.content[0].text


def get_robbins_kb_context(query: str) -> str:
    chunks = retrieve_context(query, topic_tags=None, notebook_source="robbins")
    if not chunks:
        chunks = retrieve_context(query, topic_tags=["mindset", "strategy", "goals", "vision"])
    return format_context(chunks)
