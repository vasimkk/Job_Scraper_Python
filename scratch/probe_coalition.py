import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from scraper_agent.classifiers.location_parser import parse_location, is_usa_location

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="msedge")
    page = browser.new_page()
    page.goto("https://boards.greenhouse.io/coalition", timeout=20000)
    page.wait_for_timeout(2000)
    
    openings = page.query_selector_all(".opening")
    print(f"Total openings on coalition: {len(openings)}")
    for op in openings[:10]:
        a = op.query_selector("a")
        loc_el = op.query_selector(".location")
        title = a.inner_text().strip() if a else ""
        loc = loc_el.inner_text().strip() if loc_el else ""
        href = a.get_attribute("href") if a else ""
        
        city, state, country, remote_type = parse_location(loc, title)
        is_us = is_usa_location(loc, title, city=city, state=state, country=country)
        print(f"Job: '{title}' | Loc: '{loc}' -> Parsed: (City={city}, State={state}, Country={country}) -> is_usa={is_us}")
    browser.close()
