from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="msedge")
    page = browser.new_page()
    page.goto("https://www.anduril.com/careers", timeout=20000)
    page.wait_for_timeout(2000)
    
    links = page.query_selector_all("a")
    print(f"Total links on anduril careers: {len(links)}")
    for l in links:
        txt = (l.inner_text() or "").strip()
        href = l.get_attribute("href") or ""
        if any(w in txt.lower() or w in href.lower() for w in ["open", "job", "position", "role", "search", "greenhouse", "lever"]):
            print(f"  Anchor: '{txt}' -> {href}")
    browser.close()

