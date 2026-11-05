from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="msedge")
    page = browser.new_page()
    page.goto("https://www.10xgenomics.com/careers#open-roles", timeout=20000)
    page.wait_for_timeout(3000)
    
    # Check frames
    print(f"Total frames: {len(page.frames)}")
    for f in page.frames:
        print(f"  Frame URL: {f.url}")
        
    # Check iframes in DOM
    iframes = page.query_selector_all("iframe")
    print(f"Total iframes in DOM: {len(iframes)}")
    for ifr in iframes:
        print(f"  src: {ifr.get_attribute('src')}")
        
    browser.close()

