"""
NotebookLM → Agent Brain Sync
==============================
Run this on YOUR local machine. It will:
1. Open NotebookLM with your Google session
2. Extract all content from your notebooks (using AI chat)
3. Auto-upload everything directly to the backend → agents get instant access

Setup (one time):
    pip install playwright requests
    python -m playwright install chromium

Run:
    python notebooklm_sync.py
"""
import asyncio
import io
import json
import re
import sys
import time
from pathlib import Path
import requests

# ── CONFIG ──────────────────────────────────────────────────────────────────
BACKEND_URL = "http://localhost:8000"   # change if backend runs elsewhere

COOKIES = [
    {"name": "__Secure-1PSID", "value": "g.a0008QjLGUz1Wm93AAtWlKs2wO516CjlXDLXNzRRWvpMt8TLRAHuDHd2RoSBLFyz4KJx6FHB3gACgYKAYYSARISFQHGX2Mi7nS8e5xieDdKJiK59Hra2RoVAUF8yKoLmz8MMWSeWugZjI1eAN5v0076", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
    {"name": "__Secure-3PSID", "value": "g.a0008QjLGUz1Wm93AAtWlKs2wO516CjlXDLXNzRRWvpMt8TLRAHu-SR-XzJHeWWoFlb16AG_KgACgYKASkSARISFQHGX2Mi_ctGk3QzdAKvTMcLEkkKYBoVAUF8yKqdeYie3oBZCLumnHM9h-yL0076", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "None"},
    {"name": "SID", "value": "g.a0008QjLGUz1Wm93AAtWlKs2wO516CjlXDLXNzRRWvpMt8TLRAHuumgLD_rMqbMCVjvIWFi7kwACgYKASASARISFQHGX2MiAbVgrRvpARpXplqK6CI7IRoVAUF8yKq7WFHIAEBCA-4zNz-fcWe70076", "domain": ".google.com", "path": "/", "secure": False, "httpOnly": True, "sameSite": "Lax"},
    {"name": "HSID", "value": "AaDwxmcoDiYIyB92v", "domain": ".google.com", "path": "/", "secure": False, "httpOnly": True, "sameSite": "Lax"},
    {"name": "SSID", "value": "ASwdCeya6k4btdDVX", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
    {"name": "APISID", "value": "chGOUasGymS8Qxt0/AKPH_PS5n08EHHwIV", "domain": ".google.com", "path": "/", "secure": False, "httpOnly": False, "sameSite": "Lax"},
    {"name": "SAPISID", "value": "zb-Evff7gKVp8NLH/A8rdAojYbRyf7g0Bc", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": False, "sameSite": "Lax"},
    {"name": "SIDCC", "value": "AKEyXzWQ4c_y0TiXchaQfuwmLi0t-1f3MsSE3XF33yz3J_o-MEcoFdEJd5O1XNPm4_jxV7C08bU", "domain": ".google.com", "path": "/", "secure": False, "httpOnly": False, "sameSite": "Lax"},
    {"name": "__Secure-1PSIDCC", "value": "AKEyXzVHPGtiY6Qsk62LBkCoF7e9QXT1QXozzEkNLPOSYd7zRKyTMMMeff7Os0kr5CAxll8C1tY", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
    {"name": "__Secure-3PSIDCC", "value": "AKEyXzXMKnVDe5_4JkTOt0LTSejykoHq4SEwKj_yNHa8J4Vg71FZXjhyU7LVr4yBRDV3YGksS2gd", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "None"},
    {"name": "__Secure-OSID", "value": "g.a0008gjLGU2A9VlrgoNBw_CLtlzPwvKMBhos1a3BTegiauVGfPxyCm5hAT8YJYRcwQ3NqnN_TgACgYKAVESARISFQHGX2MiK_FHXv-4WAvk6TwlGurUChoVAUF8yKo9hkCwnhPegY5iTbOF2amG0076", "domain": "notebooklm.google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
    {"name": "OSID", "value": "g.a0008gjLGU2A9VlrgoNBw_CLtlzPwvKMBhos1a3BTegiauVGfPxydj4mxmYNLV6kMSitw-wzYwACgYKAbQSARISFQHGX2MirFwpvNOSjL_PP3EvfCsJHBoVAUF8yKq9xcGJvWByDm1UhDhOP2KN0076", "domain": "notebooklm.google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
]

# Notebooks to sync — names (partial match OK). Set to [] for ALL notebooks.
TARGET_NOTEBOOKS = [
    "גבר ללא מגבלות",
    "Alex Hormozi",
    "עסק ללא מתחרים",
    "Jeff Walker",
    "PLF",
    "Product Launch Formula",
    "Tony Robbins",
    "טוני רובינס",
]

# Deep extraction prompts — sent to each notebook's AI chat
EXTRACTION_PROMPTS = [
    "תן לי תמצות מקיף ומפורט של כל הידע, העקרונות, השיטות, הכלים והתובנות החשובות במחברת הזו. כלול הכל.",
    "מה כל ה-frameworks, המתודולוגיות והגישות המרכזיות? פרט כל אחת עם השלבים המלאים ודוגמאות.",
    "מה כל הכלים, תבניות, שאלות, תרגילים ו-frameworks מעשיים שמוזכרים? תן אותם במלואם.",
    "מה כל הדוגמאות, case studies, תוצאות קונקרטיות ומספרים שמוזכרים? כלול הכל.",
    "מה כל ה-insights הייחודיים, האמירות החשובות והרעיונות מרכזיים שחשוב לזכור?",
]
# ────────────────────────────────────────────────────────────────────────────


def log(msg: str, emoji: str = ""):
    prefix = f"{emoji} " if emoji else "  "
    print(f"{prefix}{msg}", flush=True)


async def get_notebooks(page) -> list[dict]:
    log("Loading NotebookLM...", "🔄")
    await page.goto("https://notebooklm.google.com", wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)

    if "accounts.google.com" in page.url or "signin" in page.url.lower():
        log("Not logged in — cookies may have expired!", "❌")
        sys.exit(1)

    log(f"Logged in ✓ | Title: {await page.title()}", "✅")

    # Strategy 1: find links with /notebook/ in href
    notebooks = []
    seen_ids = set()
    links = await page.query_selector_all("a[href*='notebook']")
    for link in links:
        href = await link.get_attribute("href") or ""
        text = (await link.inner_text()).strip()
        match = re.search(r"/notebook/([a-zA-Z0-9_-]+)", href)
        if match and text and match.group(1) not in seen_ids:
            seen_ids.add(match.group(1))
            notebooks.append({"id": match.group(1), "title": text})

    # Strategy 2: scan page source for notebook IDs + titles
    if not notebooks:
        html = await page.content()
        for m in re.finditer(r'"notebookId"\s*:\s*"([^"]+)"[^}]*?"title"\s*:\s*"([^"]+)"', html):
            nb_id, title = m.group(1), m.group(2)
            if nb_id not in seen_ids:
                seen_ids.add(nb_id)
                notebooks.append({"id": nb_id, "title": title})

    # Strategy 3: scroll and click — get URLs from navigation
    if not notebooks:
        log("Auto-detect failed. Scanning via navigation...", "⚠")
        # Try clicking notebook cards
        cards = await page.query_selector_all("[class*='notebook'], [class*='card']")
        for card in cards[:20]:
            try:
                await card.click()
                await page.wait_for_timeout(1500)
                url = page.url
                match = re.search(r"/notebook/([a-zA-Z0-9_-]+)", url)
                title_el = await page.query_selector("h1, [class*='title']")
                title = (await title_el.inner_text()).strip() if title_el else url
                if match and match.group(1) not in seen_ids:
                    seen_ids.add(match.group(1))
                    notebooks.append({"id": match.group(1), "title": title})
                await page.go_back()
                await page.wait_for_timeout(1000)
            except Exception:
                continue

    return notebooks


async def ask_notebook(page, nb_id: str, nb_title: str) -> str:
    """Navigate to notebook and ask all extraction prompts via AI chat."""
    log(f"Opening: {nb_title}", "📖")
    await page.goto(f"https://notebooklm.google.com/notebook/{nb_id}", wait_until="networkidle", timeout=40000)
    await page.wait_for_timeout(4000)

    all_parts = [f"# {nb_title}\n", f"Extracted from NotebookLM on {time.strftime('%Y-%m-%d')}\n", "=" * 60 + "\n"]

    # Find chat input
    chat_input = await _find_chat_input(page)
    if not chat_input:
        log("No chat input found — grabbing page text instead", "⚠")
        body = await page.evaluate("document.body.innerText")
        all_parts.append(body[:15000])
        return "\n".join(all_parts)

    # Ask each prompt
    for i, prompt in enumerate(EXTRACTION_PROMPTS, 1):
        log(f"  Question {i}/{len(EXTRACTION_PROMPTS)}: {prompt[:60]}...", "💬")
        try:
            await chat_input.click()
            await page.keyboard.press("Control+a")
            await chat_input.fill(prompt)
            await page.wait_for_timeout(300)
            await page.keyboard.press("Enter")

            # Wait for response to complete (watch for loading indicator to disappear)
            await page.wait_for_timeout(3000)
            await _wait_for_response(page)

            response = await _capture_response(page)
            if response:
                all_parts.append(f"\n## שאלה {i}: {prompt}\n\n{response}\n\n{'—' * 40}\n")
                log(f"  Got {len(response):,} chars ✓", "")
            else:
                log(f"  No response captured", "⚠")

            await page.wait_for_timeout(1500)
            chat_input = await _find_chat_input(page)  # re-find after response

        except Exception as e:
            log(f"  Error on Q{i}: {e}", "✗")

    return "\n".join(all_parts)


async def _find_chat_input(page):
    for selector in [
        "textarea[placeholder]",
        "textarea",
        "[contenteditable='true'][role='textbox']",
        "[contenteditable='true']",
    ]:
        try:
            el = await page.wait_for_selector(selector, timeout=4000)
            if el:
                return el
        except Exception:
            continue
    return None


async def _wait_for_response(page, max_wait: int = 25):
    """Wait until the AI stops generating (no loading spinner visible)."""
    for _ in range(max_wait * 2):
        await asyncio.sleep(0.5)
        # Look for loading/generating indicators
        loading = await page.query_selector("[class*='loading'], [class*='generating'], [class*='spinner'], [aria-label*='Loading']")
        if not loading:
            break
    await asyncio.sleep(1)


async def _capture_response(page) -> str:
    """Capture the latest AI response from the page."""
    # Try common response container patterns
    selectors = [
        "[data-message-author-role='model']",
        "[class*='model-response']",
        "[class*='assistant-message']",
        "[class*='response-text']",
        "[class*='chat-message']:last-child",
    ]
    for sel in selectors:
        try:
            els = await page.query_selector_all(sel)
            if els:
                last = els[-1]
                text = (await last.inner_text()).strip()
                if len(text) > 100:
                    return text
        except Exception:
            continue

    # Fallback: JS evaluation to find long text blocks added recently
    try:
        return await page.evaluate("""
            () => {
                const all = Array.from(document.querySelectorAll('p, div, span'))
                    .filter(el => {
                        const t = el.innerText?.trim() || '';
                        return t.length > 150 && !el.querySelector('p') && !el.querySelector('div');
                    })
                    .map(el => el.innerText.trim());
                // Return last 5 unique blocks joined
                const unique = [...new Set(all)].slice(-8);
                return unique.join('\\n\\n');
            }
        """)
    except Exception:
        return ""


def upload_to_backend(content: str, filename: str) -> bool:
    """Upload extracted text directly to the backend knowledge base."""
    try:
        file_bytes = content.encode("utf-8")
        resp = requests.post(
            f"{BACKEND_URL}/ingest/upload",
            files={"file": (filename, io.BytesIO(file_bytes), "text/plain")},
            timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json()
            log(f"Uploaded '{filename}' → document ID: {data.get('id', '?')}", "✅")
            return True
        else:
            log(f"Upload failed: {resp.status_code} {resp.text[:200]}", "❌")
            return False
    except requests.ConnectionError:
        log(f"Cannot reach backend at {BACKEND_URL} — saving file locally instead", "⚠")
        return False
    except Exception as e:
        log(f"Upload error: {e}", "❌")
        return False


async def main():
    print("\n" + "=" * 60)
    print("  NotebookLM → Agent Brain Sync")
    print("=" * 60 + "\n")

    # Check backend connectivity
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if r.status_code == 200:
            log(f"Backend connected at {BACKEND_URL} ✓", "🟢")
        else:
            log(f"Backend responded with {r.status_code}", "⚠")
    except Exception:
        log(f"Backend not reachable at {BACKEND_URL} — will save files locally", "🟡")

    output_dir = Path("notebooklm_export")
    output_dir.mkdir(exist_ok=True)

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # visible so you can see it working
            args=["--no-sandbox", "--start-maximized"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        await context.add_cookies(COOKIES)
        page = await context.new_page()

        # Get all notebooks
        notebooks = await get_notebooks(page)

        if not notebooks:
            log("Could not auto-detect notebooks. Opening browser — navigate to a notebook manually.", "⚠")
            print("\nPress ENTER after you open a notebook...")
            input()
            url = page.url
            m = re.search(r"/notebook/([a-zA-Z0-9_-]+)", url)
            name = input("Notebook name: ").strip() or "notebook"
            if m:
                notebooks = [{"id": m.group(1), "title": name}]

        log(f"Found {len(notebooks)} notebooks:", "📚")
        for nb in notebooks:
            print(f"    • {nb['title']}")

        # Filter to targets
        if TARGET_NOTEBOOKS:
            filtered = [
                nb for nb in notebooks
                if any(t.lower() in nb["title"].lower() for t in TARGET_NOTEBOOKS)
            ]
            if filtered:
                notebooks = filtered
                log(f"Syncing {len(notebooks)} target notebooks", "🎯")

        # Extract + upload each notebook
        results = []
        for nb in notebooks:
            print()
            content = await ask_notebook(page, nb["id"], nb["title"])
            safe = re.sub(r"[^\w\s-]", "", nb["title"]).strip().replace(" ", "_")
            filename = f"notebooklm_{safe}.txt"

            # Try upload to backend
            uploaded = upload_to_backend(content, filename)

            # Always save locally too
            local_path = output_dir / filename
            local_path.write_text(content, encoding="utf-8")

            results.append({
                "notebook": nb["title"],
                "chars": len(content),
                "uploaded": uploaded,
                "local": str(local_path),
            })

        await context.close()

    # Summary
    print("\n" + "=" * 60)
    log("SYNC COMPLETE", "🎉")
    print("=" * 60)
    for r in results:
        status = "✅ Uploaded to agents" if r["uploaded"] else f"📁 Saved locally: {r['local']}"
        print(f"  {r['notebook']}: {r['chars']:,} chars — {status}")

    if any(not r["uploaded"] for r in results):
        print(f"\n  ⬆ Upload these files manually to /knowledge in the dashboard:")
        for r in results:
            if not r["uploaded"]:
                print(f"     {r['local']}")

    print("\n  💬 Agents now have full access to your notebooks!")
    print(f"     Go to /agents and ask anything.\n")


if __name__ == "__main__":
    asyncio.run(main())
