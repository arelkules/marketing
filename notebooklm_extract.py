"""
NotebookLM Local Extractor
Run this script on YOUR machine (not the server).
It will extract all your notebooks and save them as text files.

Usage:
    pip install playwright
    python playwright install chromium
    python notebooklm_extract.py
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path

COOKIES = [
    {"name": "__Secure-1PSID", "value": "g.a0008QjLGUz1Wm93AAtWlKs2wO516CjlXDLXNzRRWvpMt8TLRAHuDHd2RoSBLFyz4KJx6FHB3gACgYKAYYSARISFQHGX2Mi7nS8e5xieDdKJiK59Hra2RoVAUF8yKoLmz8MMWSeWugZjI1eAN5v0076", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
    {"name": "__Secure-3PSID", "value": "g.a0008QjLGUz1Wm93AAtWlKs2wO516CjlXDLXNzRRWvpMt8TLRAHu-SR-XzJHeWWoFlb16AG_KgACgYKASkSARISFQHGX2Mi_ctGk3QzdAKvTMcLEkkKYBoVAUF8yKqdeYie3oBZCLumnHM9h-yL0076", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "None"},
    {"name": "SID", "value": "g.a0008QjLGUz1Wm93AAtWlKs2wO516CjlXDLXNzRRWvpMt8TLRAHuumgLD_rMqbMCVjvIWFi7kwACgYKASASARISFQHGX2MiAbVgrRvpARpXplqK6CI7IRoVAUF8yKq7WFHIAEBCA-4zNz-fcWe70076", "domain": ".google.com", "path": "/", "secure": False, "httpOnly": True, "sameSite": "Lax"},
    {"name": "HSID", "value": "AaDwxmcoDiYIyB92v", "domain": ".google.com", "path": "/", "secure": False, "httpOnly": True, "sameSite": "Lax"},
    {"name": "SSID", "value": "ASwdCeya6k4btdDVX", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
    {"name": "APISID", "value": "chGOUasGymS8Qxt0/AKPH_PS5n08EHHwIV", "domain": ".google.com", "path": "/", "secure": False, "httpOnly": False, "sameSite": "Lax"},
    {"name": "SAPISID", "value": "zb-Evff7gKVp8NLH/A8rdAojYbRyf7g0Bc", "domain": ".google.com", "path": "/", "secure": True, "httpOnly": False, "sameSite": "Lax"},
    {"name": "SIDCC", "value": "AKEyXzWQ4c_y0TiXchaQfuwmLi0t-1f3MsSE3XF33yz3J_o-MEcoFdEJd5O1XNPm4_jxV7C08bU", "domain": ".google.com", "path": "/", "secure": False, "httpOnly": False, "sameSite": "Lax"},
    {"name": "__Secure-OSID", "value": "g.a0008gjLGU2A9VlrgoNBw_CLtlzPwvKMBhos1a3BTegiauVGfPxyCm5hAT8YJYRcwQ3NqnN_TgACgYKAVESARISFQHGX2MiK_FHXv-4WAvk6TwlGurUChoVAUF8yKo9hkCwnhPegY5iTbOF2amG0076", "domain": "notebooklm.google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
    {"name": "OSID", "value": "g.a0008gjLGU2A9VlrgoNBw_CLtlzPwvKMBhos1a3BTegiauVGfPxydj4mxmYNLV6kMSitw-wzYwACgYKAbQSARISFQHGX2MirFwpvNOSjL_PP3EvfCsJHBoVAUF8yKq9xcGJvWByDm1UhDhOP2KN0076", "domain": "notebooklm.google.com", "path": "/", "secure": True, "httpOnly": True, "sameSite": "Lax"},
]

# Which notebooks to extract (None = all)
TARGET_NOTEBOOKS = [
    "גבר ללא מגבלות",
    "Alex Hormozi",
    "עסק ללא מתחרים",
]

OUTPUT_DIR = Path("notebooklm_export")

EXTRACTION_PROMPTS = [
    "תן לי תמצות מקיף ומפורט של כל הידע, העקרונות, השיטות, הכלים והתובנות החשובות במחברת הזו. כלול כל מה שיכול לעזור לבניית אסטרטגיה שיווקית.",
    "מה כל ה-frameworks וה-methodologies המרכזיות שנידונות במחברת הזו? פרט כל אחת עם השלבים המלאים.",
    "מה כל הדוגמאות, case studies ותוצאות קונקרטיות שמוזכרות? כלול מספרים ספציפיים.",
    "מה כל הכלים, תבניות, שאלות ו-exercises שמוזכרים? תן אותם במלואם.",
]


async def extract_notebook(page, notebook_id: str, notebook_title: str) -> str:
    print(f"\n📖 Extracting: {notebook_title}")
    url = f"https://notebooklm.google.com/notebook/{notebook_id}"
    await page.goto(url, wait_until="networkidle", timeout=40000)
    await page.wait_for_timeout(3000)

    all_content = [f"# {notebook_title}\n"]
    all_content.append(f"Source: NotebookLM notebook {notebook_id}\n")
    all_content.append("=" * 60 + "\n")

    # Find the chat input
    chat_input = None
    for selector in [
        "textarea[placeholder]",
        "[contenteditable='true']",
        "textarea",
        "input[type='text']",
    ]:
        try:
            el = await page.wait_for_selector(selector, timeout=5000)
            if el:
                chat_input = el
                break
        except Exception:
            continue

    if not chat_input:
        print(f"  ⚠ Could not find chat input for {notebook_title}")
        # Try to get whatever text is on the page
        body = await page.evaluate("document.body.innerText")
        all_content.append(body[:10000])
        return "\n".join(all_content)

    # Ask each extraction prompt
    for i, prompt in enumerate(EXTRACTION_PROMPTS, 1):
        print(f"  Asking question {i}/{len(EXTRACTION_PROMPTS)}...")
        try:
            await chat_input.click()
            await chat_input.fill(prompt)
            await page.wait_for_timeout(500)
            await page.keyboard.press("Enter")

            # Wait for response (up to 30s)
            await page.wait_for_timeout(15000)

            # Get the latest AI response
            response_text = await _get_latest_response(page)
            if response_text:
                all_content.append(f"\n## Q{i}: {prompt[:80]}...\n")
                all_content.append(response_text)
                all_content.append("\n" + "-" * 40 + "\n")
                print(f"  ✓ Got {len(response_text)} chars")
            else:
                print(f"  ⚠ No response captured for Q{i}")

            await page.wait_for_timeout(2000)

        except Exception as e:
            print(f"  ✗ Error on Q{i}: {e}")

    return "\n".join(all_content)


async def _get_latest_response(page) -> str:
    """Try multiple selectors to get the latest AI response."""
    selectors = [
        # NotebookLM response containers
        ".response-content",
        "[data-response]",
        ".chat-response",
        ".message-content:last-child",
        # Generic last paragraph blocks
        "p:last-of-type",
    ]
    for sel in selectors:
        try:
            els = await page.query_selector_all(sel)
            if els:
                texts = []
                for el in els[-3:]:  # last 3 elements
                    t = (await el.inner_text()).strip()
                    if len(t) > 100:
                        texts.append(t)
                if texts:
                    return "\n\n".join(texts)
        except Exception:
            continue

    # Fallback: get all visible text blocks longer than 200 chars
    try:
        result = await page.evaluate("""
            () => {
                const blocks = [];
                document.querySelectorAll('p, div, span').forEach(el => {
                    const text = el.innerText?.trim();
                    if (text && text.length > 200 && !el.querySelector('p, div')) {
                        blocks.push(text);
                    }
                });
                return blocks.slice(-5).join('\\n\\n');
            }
        """)
        return result
    except Exception:
        return ""


async def list_all_notebooks(page) -> list[dict]:
    print("📋 Loading notebook list...")
    await page.goto("https://notebooklm.google.com", wait_until="networkidle", timeout=30000)
    await page.wait_for_timeout(3000)

    if "accounts.google.com" in page.url or "signin" in page.url.lower():
        print("❌ Not logged in! Cookies may have expired.")
        return []

    print(f"✅ Logged in. Page: {await page.title()}")

    # Take screenshot for debugging
    await page.screenshot(path=str(OUTPUT_DIR / "homepage.png"))

    # Extract notebook links from page
    notebooks = []
    links = await page.query_selector_all("a[href*='notebook']")
    for link in links:
        href = await link.get_attribute("href") or ""
        text = (await link.inner_text()).strip()
        match = re.search(r"/notebook/([a-zA-Z0-9_-]+)", href)
        if match and text:
            nb_id = match.group(1)
            if not any(n["id"] == nb_id for n in notebooks):
                notebooks.append({"id": nb_id, "title": text})

    # Also try to find notebook IDs from page source
    content = await page.content()
    ids_in_source = re.findall(r'"([a-f0-9]{20,})"', content)
    titles_in_source = re.findall(r'"title"\s*:\s*"([^"]{3,60})"', content)

    if not notebooks:
        print("⚠ Could not auto-detect notebooks from links. Saving page source...")
        with open(OUTPUT_DIR / "page_source.html", "w") as f:
            f.write(content)
        print(f"  Saved to {OUTPUT_DIR}/page_source.html — inspect to find notebook IDs")

    return notebooks


async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    print("🚀 NotebookLM Extractor starting...")
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}\n")

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Visible so you can see what's happening
            args=["--no-sandbox"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        await context.add_cookies(COOKIES)
        page = await context.new_page()

        # List all notebooks
        notebooks = await list_all_notebooks(page)

        if not notebooks:
            print("\n⚠ No notebooks found automatically.")
            print("Opening browser so you can navigate manually...")
            print("Press ENTER when you're on a notebook page to extract it.")
            input()
            title = input("Enter notebook name: ").strip() or "notebook"
            current_url = page.url
            match = re.search(r"/notebook/([a-zA-Z0-9_-]+)", current_url)
            if match:
                notebooks = [{"id": match.group(1), "title": title}]

        print(f"\nFound {len(notebooks)} notebooks:")
        for nb in notebooks:
            print(f"  • {nb['title']} (id: {nb['id'][:20]}...)")

        # Filter to target notebooks if specified
        if TARGET_NOTEBOOKS:
            filtered = [nb for nb in notebooks if any(t.lower() in nb["title"].lower() for t in TARGET_NOTEBOOKS)]
            if filtered:
                notebooks = filtered
                print(f"\nFiltered to {len(notebooks)} target notebooks")

        # Extract each notebook
        for nb in notebooks:
            content = await extract_notebook(page, nb["id"], nb["title"])
            safe_name = re.sub(r'[^\w\s-]', '', nb["title"]).strip().replace(" ", "_")
            filepath = OUTPUT_DIR / f"{safe_name}.txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"\n✅ Saved: {filepath} ({len(content):,} chars)")

        await context.close()

    print(f"\n🎉 Done! Files saved to: {OUTPUT_DIR.absolute()}")
    print("\nNext step: Upload all .txt files from the output folder to your dashboard at /knowledge")


if __name__ == "__main__":
    asyncio.run(main())
