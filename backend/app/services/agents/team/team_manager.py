from __future__ import annotations
import asyncio
from typing import AsyncIterator
from app.utils.anthropic_client import get_anthropic_client
from app.services.agents.team.discussion import DiscussionState, AdvisorMessage
from app.services.agents.team.hormozi_advisor import get_hormozi_response, get_hormozi_kb_context
from app.services.agents.team.bwnc_advisor import get_bwnc_response, get_bwnc_kb_context
from app.services.agents.team.walker_advisor import get_walker_response, get_walker_kb_context

MODEL = "claude-sonnet-4-6"
CACHE_BETA = "prompt-caching-2024-07-31"

MANAGER_SYSTEM = """You are the Strategic Director of this advisory team.

Your job is to:
1. Ask 2-3 sharp clarifying questions before discussions start (not generic — specific to the goal)
2. Synthesize 3 advisors into ONE clear, actionable consensus
3. Resolve conflicts between advisors — find where they genuinely agree
4. Output specific deliverables with clear next steps

Be concise. The user needs to act, not read an essay.
No filler. No "great question." Just sharp strategic thinking."""


def build_brief(state: DiscussionState) -> str:
    brief = f"""## BUSINESS: {state.business_name}

## GOAL: {state.goal}"""

    if state.user_answers:
        qa = "\n".join(f"- Q: {q}\n  A: {a}" for q, a in state.user_answers.items())
        brief += f"\n\n## CLARIFICATIONS FROM USER:\n{qa}"

    if state.past_memory:
        brief += f"\n\n{state.past_memory}"

    return brief


async def ask_clarifying_questions(goal: str, business_name: str) -> list[str]:
    client = get_anthropic_client()
    prompt = f"""Business: {business_name}
Goal: {goal}

Ask exactly 3 sharp clarifying questions that will help the advisory team give specific, actionable advice.
Each question should uncover something that would significantly change the strategy.
DO NOT ask generic questions like "what's your target audience" — be specific to THIS goal.

Return ONLY a JSON array of 3 strings. Example:
["Question 1?", "Question 2?", "Question 3?"]"""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=[{"type": "text", "text": MANAGER_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"anthropic-beta": CACHE_BETA},
    )
    import json
    text = message.content[0].text.strip()
    # Extract JSON array even if surrounded by markdown
    start = text.find("[")
    end = text.rfind("]") + 1
    return json.loads(text[start:end])


async def synthesize_consensus(state: DiscussionState) -> str:
    client = get_anthropic_client()

    all_messages = []
    for msg in state.round1 + state.round2:
        label = {"hormozi": "💪 Alex Hormozi", "bwnc": "🎯 Tzvika (BWNC)", "walker": "🚀 Jeff Walker"}.get(msg.advisor, msg.advisor)
        all_messages.append(f"### {label} (Round {msg.round_number})\n{msg.content}")

    discussion_text = "\n\n".join(all_messages)

    prompt = f"""## BUSINESS GOAL: {state.goal}

## FULL DISCUSSION:
{discussion_text}

Now synthesize the team's discussion into ONE clear consensus recommendation.

Format your response as:
**THE CONSENSUS**
[2-3 sentence summary of what the team agrees on]

**ACTION PLAN**
1. [First concrete action — who does what, by when]
2. [Second concrete action]
3. [Third concrete action]

**KEY INSIGHT**
[The single most important insight from this discussion]

Be specific. No vague advice."""

    message = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=[{"type": "text", "text": MANAGER_SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
        extra_headers={"anthropic-beta": CACHE_BETA},
    )
    return message.content[0].text


async def run_discussion(state: DiscussionState) -> AsyncIterator[dict]:
    """
    Yields events:
      {"type": "round1_start"}
      {"type": "advisor_message", "advisor": "hormozi", "round": 1, "content": "..."}
      {"type": "round2_start"}
      {"type": "advisor_message", "advisor": "bwnc", "round": 2, "content": "..."}
      {"type": "consensus", "content": "..."}
      {"type": "done"}
    """
    brief = build_brief(state)

    # Retrieve KB context for each advisor
    hormozi_kb = get_hormozi_kb_context(state.goal)
    bwnc_kb = get_bwnc_kb_context(state.goal)
    walker_kb = get_walker_kb_context(state.goal)

    yield {"type": "round1_start"}

    # Round 1 — parallel
    hormozi_r1, bwnc_r1, walker_r1 = await asyncio.gather(
        get_hormozi_response(brief, round_number=1, kb_context=hormozi_kb),
        get_bwnc_response(brief, round_number=1, kb_context=bwnc_kb),
        get_walker_response(brief, round_number=1, kb_context=walker_kb),
    )

    state.round1 = [
        AdvisorMessage("hormozi", hormozi_r1, 1),
        AdvisorMessage("bwnc", bwnc_r1, 1),
        AdvisorMessage("walker", walker_r1, 1),
    ]

    yield {"type": "advisor_message", "advisor": "hormozi", "round": 1, "content": hormozi_r1}
    yield {"type": "advisor_message", "advisor": "bwnc", "round": 1, "content": bwnc_r1}
    yield {"type": "advisor_message", "advisor": "walker", "round": 1, "content": walker_r1}

    yield {"type": "round2_start"}

    # Round 2 — each sees the other two's Round 1
    hormozi_r2, bwnc_r2, walker_r2 = await asyncio.gather(
        get_hormozi_response(brief, round_number=2, other_responses=[bwnc_r1, walker_r1], kb_context=hormozi_kb),
        get_bwnc_response(brief, round_number=2, other_responses=[hormozi_r1, walker_r1], kb_context=bwnc_kb),
        get_walker_response(brief, round_number=2, other_responses=[hormozi_r1, bwnc_r1], kb_context=walker_kb),
    )

    state.round2 = [
        AdvisorMessage("hormozi", hormozi_r2, 2),
        AdvisorMessage("bwnc", bwnc_r2, 2),
        AdvisorMessage("walker", walker_r2, 2),
    ]

    yield {"type": "advisor_message", "advisor": "hormozi", "round": 2, "content": hormozi_r2}
    yield {"type": "advisor_message", "advisor": "bwnc", "round": 2, "content": bwnc_r2}
    yield {"type": "advisor_message", "advisor": "walker", "round": 2, "content": walker_r2}

    # Consensus
    consensus = await synthesize_consensus(state)
    state.consensus = consensus
    yield {"type": "consensus", "content": consensus}
    yield {"type": "done"}
