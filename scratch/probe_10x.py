from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="msedge")
    page = browser.new_page()
    page.goto("https://www.10xgenomics.com/careers", timeout=20000)
    page.wait_for_timeout(2000)
    
    anchors = page.query_selector_all("a")
    print(f"Total anchors on 10xgenomics: {len(anchors)}")
    for a in anchors:
        txt = (a.inner_text() or "").strip()
        href = a.get_attribute("href") or ""
        if any(w in txt.lower() or w in href.lower() for w in ["job", "role", "position", "career", "greenhouse", "lever", "workday", "open"]):
            print(f"  '{txt}' -> {href}")
    browser.close()

