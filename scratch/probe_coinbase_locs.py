import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from scraper_agent.classifiers.location_parser import parse_location, is_usa_location

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="msedge")
    page = browser.new_page()
    page.goto("https://boards.greenhouse.io/coinbase", timeout=20000)
    page.wait_for_timeout(2000)
    
    anchors = page.query_selector_all("a[href*='/jobs/']")
    print(f"Total Coinbase jobs: {len(anchors)}")
    for a in anchors[:15]:
        t = (a.inner_text() or "").strip()
        loc = a.evaluate("""el => {
            const card = el.closest('div.opening, tr, li, div');
            const l = card ? card.querySelector('.location') : null;
            return l ? l.innerText.trim() : '';
        }""")
        c, s, co, r = parse_location(loc, t)
        is_us = is_usa_location(loc, t, city=c, state=s, country=co)
        print(f"'{t}' | Loc: '{loc}' -> (City={c}, State={s}, Country={co}) -> is_usa={is_us}")
    browser.close()

