"""
NotebookLM integration using the notebooklm-py library.
Replaces browser-based Playwright scraping with direct RPC API calls.

Cookies are accepted in EditThisCookie export format (JSON array) and
converted to a Playwright storage-state file so NotebookLMClient.from_storage()
can initialise auth without launching a browser.
"""
from __future__ import annotations

import asyncio
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from notebooklm import NotebookLMClient

# Extraction prompts sent to each notebook's AI chat to pull synthesised insights
EXTRACTION_PROMPTS = [
    "תן לי תמצות מקיף ומפורט של כל הידע, העקרונות, השיטות, הכלים והתובנות החשובות במחברת הזו. כלול הכל.",
    "מה כל ה-frameworks, המתודולוגיות והגישות המרכזיות? פרט כל אחת עם השלבים המלאים ודוגמאות.",
    "מה כל הכלים, תבניות, שאלות, תרגילים ו-frameworks מעשיים שמוזכרים? תן אותם במלואם.",
    "מה כל הדוגמאות, case studies, תוצאות קונקרטיות ומספרים שמוזכרים? כלול הכל.",
    "מה כל ה-insights הייחודיים, האמירות החשובות והרעיונות מרכזיים שחשוב לזכור?",
]

_AUTH_KEYWORDS = ("auth", "login", "expired", "401", "403", "unauthorized", "unauthenticated")


@dataclass
class NotebookNote:
    title: str
    content: str


@dataclass
class NotebookSource:
    title: str
    content: str


@dataclass
class Notebook:
    id: str
    title: str
    notes: list[NotebookNote] = field(default_factory=list)
    sources: list[NotebookSource] = field(default_factory=list)

    def to_text(self) -> str:
        parts = [f"# {self.title}\n"]
        if self.sources:
            parts.append("## Sources\n")
            for s in self.sources:
                parts.append(f"### {s.title}\n{s.content}\n")
        if self.notes:
            parts.append("## Notes\n")
            for n in self.notes:
                parts.append(f"### {n.title}\n{n.content}\n")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _to_storage_state(cookies: list[dict]) -> dict:
    """Convert an EditThisCookie JSON array to Playwright storage-state format."""
    pw_cookies = []
    for c in cookies:
        name = c.get("name", c.get("Name", ""))
        value = c.get("value", c.get("Value", ""))
        if not name or not value:
            continue
        same_site = c.get("sameSite", c.get("SameSite", "Lax"))
        if same_site not in ("Strict", "Lax", "None"):
            same_site = "Lax"
        pw_cookies.append({
            "name": name,
            "value": value,
            "domain": c.get("domain", c.get("Domain", ".google.com")),
            "path": c.get("path", c.get("Path", "/")),
            "secure": bool(c.get("secure", c.get("Secure", False))),
            "httpOnly": bool(c.get("httpOnly", c.get("HttpOnly", False))),
            "sameSite": same_site,
            "expires": int(c.get("expirationDate", -1)),
        })
    return {"cookies": pw_cookies, "origins": []}


async def _make_client(cookies: list[dict]) -> NotebookLMClient:
    """Create a NotebookLMClient from an EditThisCookie array.

    Writes a temporary Playwright storage-state file, initialises the client
    (which fetches CSRF / session tokens via httpx), then deletes the file.
    """
    storage = _to_storage_state(cookies)
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    try:
        json.dump(storage, tmp)
        tmp.close()
        return await NotebookLMClient.from_storage(path=tmp.name)
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def _is_auth_error(exc: Exception) -> bool:
    return any(k in str(exc).lower() for k in _AUTH_KEYWORDS)


def _extract_text(obj: object) -> str:
    """Pull text from a SourceFulltext (or similar) object."""
    for attr in ("text", "content", "fulltext", "body"):
        val = getattr(obj, attr, None)
        if isinstance(val, str) and val:
            return val
    return str(obj)


# ---------------------------------------------------------------------------
# Public API (same interface expected by app/routers/notebooklm.py)
# ---------------------------------------------------------------------------

async def list_notebooks(cookies: list[dict]) -> list[dict]:
    """Return [{id, title}] for all NotebookLM notebooks."""
    try:
        async with await _make_client(cookies) as client:
            notebooks = await client.notebooks.list()
            return [{"id": nb.id, "title": nb.title} for nb in notebooks]
    except Exception as exc:
        if _is_auth_error(exc):
            return [{"error": "not_authenticated", "message": "Cookies expired or invalid. Please re-export cookies."}]
        raise


async def full_sync(
    cookies: list[dict],
    target_notebook_ids: list[str] | None = None,
    on_progress=None,
) -> list[Notebook]:
    """Sync notebooks: fetch source fulltexts and AI-extracted insights.

    Calls on_progress(message) for streaming status updates.
    """
    def progress(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    progress("Connecting to NotebookLM...")

    async with await _make_client(cookies) as client:
        all_notebooks = await client.notebooks.list()

        if target_notebook_ids:
            all_notebooks = [nb for nb in all_notebooks if nb.id in target_notebook_ids]

        progress(f"Found {len(all_notebooks)} notebooks to sync")

        results: list[Notebook] = []
        for nb_info in all_notebooks:
            progress(f"Syncing: {nb_info.title}...")
            notebook = Notebook(id=nb_info.id, title=nb_info.title)
            try:
                # Retrieve indexed source text directly (no browser needed)
                sources = await client.sources.list(nb_info.id)
                for src in sources:
                    try:
                        ft = await client.sources.get_fulltext(nb_info.id, src.id)
                        notebook.sources.append(NotebookSource(
                            title=src.title or "Source",
                            content=_extract_text(ft),
                        ))
                    except Exception as exc:
                        progress(f"  ⚠ Source '{src.title}': {exc}")

                # AI chat extraction for synthesised knowledge
                conv_id: str | None = None
                for i, prompt in enumerate(EXTRACTION_PROMPTS, 1):
                    try:
                        result = await client.chat.ask(
                            nb_info.id, prompt, conversation_id=conv_id
                        )
                        conv_id = getattr(result, "conversation_id", conv_id)
                        answer = getattr(result, "answer", "") or ""
                        if answer:
                            notebook.notes.append(NotebookNote(
                                title=f"Extract {i}",
                                content=answer,
                            ))
                        await asyncio.sleep(1)  # avoid hitting rate limits
                    except Exception as exc:
                        progress(f"  ⚠ Extract Q{i}: {exc}")

                results.append(notebook)
                progress(
                    f"✓ {nb_info.title} — {len(notebook.sources)} sources, "
                    f"{len(notebook.notes)} extracts"
                )

            except Exception as exc:
                progress(f"✗ {nb_info.title}: {exc}")

    return results
