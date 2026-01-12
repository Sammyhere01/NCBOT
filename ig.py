# ===============================
#        Sammy - IG GC Renamer
# ===============================

import argparse
import asyncio
import json
import random
import re
from playwright.async_api import async_playwright

INVISIBLE_CHARS = ["\u200B", "\u200C", "\u200D", "\u2060"]

async def apply_anti_detection(page):
    await page.evaluate("""() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
        window.chrome = { runtime: {} };
    }""")

async def main():
    parser = argparse.ArgumentParser("Sammy IG GC Renamer")
    parser.add_argument("--thread-url", required=True)
    parser.add_argument("--names", required=True)
    parser.add_argument("--storage-state", required=True)
    parser.add_argument("--delay", default="3")
    parser.add_argument("--headless", default="true")
    args = parser.parse_args()

    delay = float(args.delay)
    headless = args.headless.lower() == "true"
    names_list = [n.strip() for n in re.split(r"[,\n]", args.names) if n.strip()]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(storage_state=args.storage_state)
        page = await context.new_page()
        await apply_anti_detection(page)

        await page.goto(args.thread_url, timeout=60000)

        await page.wait_for_selector(
            "div[aria-label='Open the details pane of the chat']",
            timeout=60000
        )
        await page.click("div[aria-label='Open the details pane of the chat']")

        i = 0
        while True:
            base = names_list[i % len(names_list)]
            invis = "".join(
                random.choice(INVISIBLE_CHARS)
                for _ in range(random.randint(1, 3))
            )
            pos = random.randint(0, len(base))
            new_name = base[:pos] + invis + base[pos:]

            try:
                await page.click("div[aria-label='Change group name']")
                inp = page.locator("input[aria-label='Group name']")
                await inp.fill(new_name)
                await page.click("div:has-text('Save')")
                print(f"[Sammy] Renamed → {base}")
            except Exception as e:
                print("[Sammy ERROR]", e)

            i += 1
            await asyncio.sleep(delay)

if __name__ == "__main__":
    asyncio.run(main())
