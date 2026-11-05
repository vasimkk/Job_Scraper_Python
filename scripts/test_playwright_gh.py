import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        
        test_urls = [
            "https://job-boards.greenhouse.io/primemedicine/jobs/6184175004",
            "https://primemedicine.com/career/?gh_jid=6184175004",
            "https://boards.greenhouse.io/reddit/jobs/8211850",
            "https://boards.greenhouse.io/cloudflare/jobs/8331928",
            "https://www.redditinc.com/careers",
        ]
        
        for u in test_urls:
            try:
                resp = await page.goto(u, wait_until="domcontentloaded", timeout=15000)
                status = resp.status if resp else "no_resp"
                title = await page.title()
                print(f"URL: {u}\n  -> Status: {status} | Title: {title}\n")
            except Exception as e:
                print(f"URL: {u}\n  -> FAILED: {e}\n")
        
        await browser.close()

asyncio.run(main())

