import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page()

        async def log_request(route, request):
            if "greenhouse.io" in request.url:
                print("Request URL:", request.url)
                print("Headers:", request.headers)
            await route.continue_()

        await page.route("**/*", log_request)
        resp = await page.goto("https://job-boards.greenhouse.io/primemedicine/jobs/6184175004")
        print("Status:", resp.status)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
