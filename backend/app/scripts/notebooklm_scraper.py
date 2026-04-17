"""
NotebookLM scraper using Playwright.
Uses browser cookies for authentication — no password needed.
"""
from __future__ import annotations
import asyncio
import json
import re
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, BrowserContext, Page

NOTEBOOKLM_URL = "https://notebooklm.google.com"


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


async def _make_context(playwright, cookies: list[dict]) -> BrowserContext:
    browser = await playwright.chromium.launch(
        headless=True,
        executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 900},
    )
    # Set cookies for Google auth
    google_cookies = []
    for c in cookies:
        cookie = {
            "name": c.get("name", c.get("Name", "")),
            "value": c.get("value", c.get("Value", "")),
            "domain": c.get("domain", c.get("Domain", ".google.com")),
            "path": c.get("path", c.get("Path", "/")),
        }
        if cookie["name"] and cookie["value"]:
            google_cookies.append(cookie)
    await context.add_cookies(google_cookies)
    return context


async def list_notebooks(cookies: list[dict]) -> list[dict]:
    """Return list of {id, title} for all notebooks."""
    async with async_playwright() as p:
        context = await _make_context(p, cookies)
        page = await context.new_page()

        await page.goto(NOTEBOOKLM_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)

        # Check if logged in
        if "accounts.google.com" in page.url or "signin" in page.url.lower():
            await context.close()
            return [{"error": "not_authenticated", "message": "Cookies expired or invalid. Please re-export cookies."}]

        notebooks = []
        # NotebookLM lists notebooks as cards
        cards = await page.query_selector_all("[data-notebook-id], .notebook-card, [data-id]")

        if not cards:
            # Try to find notebooks via text content patterns
            await page.wait_for_timeout(2000)
            # Get all notebook titles from the page
            all_links = await page.query_selector_all("a[href*='notebook']")
            for link in all_links:
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if href and text.strip():
                    nb_id = _extract_notebook_id(href)
                    if nb_id:
                        notebooks.append({"id": nb_id, "title": text.strip()})

        if not notebooks:
            # Fallback: scrape page source for notebook data
            content = await page.content()
            notebooks = _parse_notebooks_from_html(content)

        await context.close()
        return notebooks


async def scrape_notebook(cookies: list[dict], notebook_id: str, notebook_title: str = "") -> Notebook:
    """Scrape all notes and sources from a specific notebook."""
    async with async_playwright() as p:
        context = await _make_context(p, cookies)
        page = await context.new_page()

        url = f"{NOTEBOOKLM_URL}/notebook/{notebook_id}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(4000)

        if "accounts.google.com" in page.url:
            await context.close()
            raise ValueError("Authentication failed — cookies expired")

        notebook = Notebook(id=notebook_id, title=notebook_title or notebook_id)

        # --- Extract Notes ---
        notebook.notes = await _extract_notes(page)

        # --- Extract Sources ---
        notebook.sources = await _extract_sources(page)

        # --- Try AI chat to get summary if notes are empty ---
        if not notebook.notes and not notebook.sources:
            summary = await _ask_notebook_ai(page, "תן לי סיכום מקיף של כל המידע במחברת הזו, כולל כל העקרונות, שיטות, כלים ותובנות חשובות.")
            if summary:
                notebook.notes.append(NotebookNote(title="AI Summary", content=summary))

        await context.close()
        return notebook


async def _extract_notes(page: Page) -> list[NotebookNote]:
    notes = []
    await page.wait_for_timeout(1000)

    # Look for notes panel
    note_elements = await page.query_selector_all("[data-note-id], .note-item, [class*='note']")
    for el in note_elements:
        try:
            title_el = await el.query_selector("[class*='title'], h3, h4")
            content_el = await el.query_selector("[class*='content'], [class*='body'], p")
            title = (await title_el.inner_text()).strip() if title_el else "Note"
            content = (await content_el.inner_text()).strip() if content_el else ""
            if content:
                notes.append(NotebookNote(title=title, content=content))
        except Exception:
            continue

    return notes


async def _extract_sources(page: Page) -> list[NotebookSource]:
    sources = []

    source_elements = await page.query_selector_all("[data-source-id], .source-item, [class*='source']")
    for el in source_elements:
        try:
            title_el = await el.query_selector("[class*='title'], span, p")
            title = (await title_el.inner_text()).strip() if title_el else "Source"
            if title:
                sources.append(NotebookSource(title=title, content=""))
        except Exception:
            continue

    return sources


async def _ask_notebook_ai(page: Page, question: str) -> str:
    """Send a message to NotebookLM's AI chat and get the response."""
    try:
        # Find the chat input
        chat_input = await page.wait_for_selector(
            "textarea, [contenteditable='true'], input[type='text'][placeholder*='Ask']",
            timeout=5000
        )
        if not chat_input:
            return ""

        await chat_input.click()
        await chat_input.fill(question)
        await page.wait_for_timeout(500)

        # Submit
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(8000)  # Wait for AI response

        # Get the latest response
        response_els = await page.query_selector_all("[class*='response'], [class*='answer'], [class*='message']")
        if response_els:
            last = response_els[-1]
            return (await last.inner_text()).strip()

    except Exception:
        pass
    return ""


def _extract_notebook_id(href: str) -> str | None:
    match = re.search(r"/notebook/([a-zA-Z0-9_-]+)", href)
    return match.group(1) if match else None


def _parse_notebooks_from_html(html: str) -> list[dict]:
    notebooks = []
    ids = re.findall(r'"notebookId"\s*:\s*"([^"]+)"', html)
    titles = re.findall(r'"title"\s*:\s*"([^"]+)"', html)
    for i, nb_id in enumerate(ids):
        title = titles[i] if i < len(titles) else f"Notebook {i+1}"
        notebooks.append({"id": nb_id, "title": title})
    return notebooks


async def full_sync(
    cookies: list[dict],
    target_notebook_ids: list[str] | None = None,
    on_progress=None,
) -> list[Notebook]:
    """
    Full sync: list all notebooks, scrape the specified ones (or all if None).
    Calls on_progress(message) for status updates.
    """
    def progress(msg: str):
        if on_progress:
            on_progress(msg)

    progress("Connecting to NotebookLM...")
    notebooks_list = await list_notebooks(cookies)

    if notebooks_list and "error" in notebooks_list[0]:
        raise ValueError(notebooks_list[0]["message"])

    if target_notebook_ids:
        notebooks_list = [n for n in notebooks_list if n["id"] in target_notebook_ids]

    progress(f"Found {len(notebooks_list)} notebooks to sync")

    results = []
    for nb_info in notebooks_list:
        progress(f"Scraping: {nb_info['title']}...")
        try:
            notebook = await scrape_notebook(cookies, nb_info["id"], nb_info["title"])
            results.append(notebook)
            progress(f"✓ {nb_info['title']} — {len(notebook.notes)} notes, {len(notebook.sources)} sources")
        except Exception as e:
            progress(f"✗ {nb_info['title']} — Error: {e}")

    return results
