import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page()

        test_cases = [
            ("Prime Medicine (job-boards)", "https://job-boards.greenhouse.io/primemedicine/jobs/6184175004"),
            ("Prime Medicine (website)", "https://primemedicine.com/career/?gh_jid=6184175004"),
            ("Reddit", "https://job-boards.greenhouse.io/reddit/jobs/8275952"),
            ("Cloudflare", "https://boards.greenhouse.io/cloudflare/jobs/8331928"),
            ("Figma (boards)", "https://boards.greenhouse.io/figma/jobs/5711913004"),
            ("Figma (website)", "https://www.figma.com/careers/?gh_jid=5711913004"),
            ("Scale AI (job-boards)", "https://job-boards.greenhouse.io/scaleai/jobs/4720422005"),
            ("Scale AI (website)", "https://scale.com/careers?gh_jid=4720422005"),
            ("Affirm (job-boards)", "https://job-boards.greenhouse.io/affirm/jobs/8016833003"),
            ("Affirm (website)", "https://www.affirm.com/careers?gh_jid=8016833003"),
            ("Vercel (job-boards)", "https://job-boards.greenhouse.io/vercel/jobs/5798406004"),
            ("Vercel (website)", "https://vercel.com/careers?gh_jid=5798406004"),
        ]

        for label, url in test_cases:
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=12000)
                status = resp.status if resp else "none"
                title = await page.title()
                print(f"[{label}] -> Status: {status} | Title: {title}")
            except Exception as e:
                print(f"[{label}] -> ERROR: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

