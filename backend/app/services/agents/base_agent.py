from __future__ import annotations
from typing import AsyncIterator
from app.utils.anthropic_client import get_anthropic_client
from app.utils.token_counter import calculate_cost
from app.services.rag.retriever import retrieve_context, format_context

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
CACHE_BETA = "prompt-caching-2024-07-31"


class TokenUsage:
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0
        self.cache_write_tokens = 0
        self.cost_usd = 0.0


class BaseMarketingAgent:
    agent_type: str = "base"
    topic_tags: list[str] | None = None

    def get_system_prompt(self) -> str:
        raise NotImplementedError

    async def stream(
        self,
        user_message: str,
        history: list[dict],
    ) -> AsyncIterator[tuple[str, TokenUsage | None]]:
        client = get_anthropic_client()
        # Prefer the business notebook; fall back to all sources
        context_chunks = retrieve_context(user_message, self.topic_tags, notebook_source="business")
        if not context_chunks:
            context_chunks = retrieve_context(user_message, self.topic_tags)
        kb_context = format_context(context_chunks)

        system = [
            {
                "type": "text",
                "text": self.get_system_prompt(),
                "cache_control": {"type": "ephemeral"},
            }
        ]
        if kb_context:
            system.append({
                "type": "text",
                "text": f"## YOUR BUSINESS KNOWLEDGE BASE\n\nThe following is retrieved from your specific business strategy sessions. Always reference relevant specifics:\n\n{kb_context}",
                "cache_control": {"type": "ephemeral"},
            })

        messages = self._build_messages(history, user_message)
        usage = TokenUsage()

        async with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
            extra_headers={"anthropic-beta": CACHE_BETA},
        ) as stream:
            async for text in stream.text_stream:
                yield text, None

            final = await stream.get_final_message()
            u = final.usage
            usage.input_tokens = u.input_tokens
            usage.output_tokens = u.output_tokens
            usage.cache_read_tokens = getattr(u, "cache_read_input_tokens", 0) or 0
            usage.cache_write_tokens = getattr(u, "cache_creation_input_tokens", 0) or 0
            usage.cost_usd = calculate_cost(
                usage.input_tokens,
                usage.output_tokens,
                usage.cache_write_tokens,
                usage.cache_read_tokens,
            )
            yield "", usage

    def _build_messages(self, history: list[dict], user_message: str) -> list[dict]:
        messages = []
        for i, msg in enumerate(history[-10:]):  # keep last 10 turns
            content = msg["content"]
            is_last_assistant = (
                msg["role"] == "assistant"
                and i == len(history[-10:]) - 1
            )
            if is_last_assistant:
                content = [{"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}]
            messages.append({"role": msg["role"], "content": content})
        messages.append({"role": "user", "content": user_message})
        return messages
