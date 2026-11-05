from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="msedge")
    page = browser.new_page()
    page.goto("https://www.anduril.com/open-roles", timeout=20000)
    page.wait_for_timeout(3000)
    
    # Query job cards/anchors
    anchors = page.query_selector_all("a[href*='/open-roles/'], a[href*='/job/'], a[href*='greenhouse'], a[href*='lever']")
    print(f"Jobs anchors on /open-roles: {len(anchors)}")
    for a in anchors[:15]:
        print(f"  {(a.inner_text() or '').strip()} -> {a.get_attribute('href')}")
    browser.close()

