import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page()

        print("Testing direct goto...")
        try:
            r = await page.goto("https://job-boards.greenhouse.io/reddit/jobs/8275952", wait_until="domcontentloaded", timeout=10000)
            print("Direct goto status:", r.status if r else "none")
            print("Direct goto title:", await page.title())
        except Exception as e:
            print("Direct goto failed:", e)

        print("\nTesting goto redditinc careers and clicking link...")
        try:
            await page.goto("https://redditinc.com/careers", wait_until="networkidle", timeout=15000)
            # Find the link
            href = await page.get_attribute("a[href*='8275952']", "href")
            print("Found href:", href)
            # Navigate with referer
            r2 = await page.goto(href, referer="https://redditinc.com/careers", wait_until="domcontentloaded", timeout=10000)
            print("Nav with referer status:", r2.status if r2 else "none")
            print("Nav with referer title:", await page.title())
        except Exception as e:
            print("Referer nav failed:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

