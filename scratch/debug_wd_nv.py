import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.classifiers.location_parser import parse_location, is_usa_location

scraper = PlaywrightCareerScraper(headless=True)
url = "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
raw_jobs = scraper.scrape_career_page(url, max_jobs=20)

for j in raw_jobs:
    print(f"\nTitle: {j.title}")
    print(f"Raw location: '{j.raw_location}'")
    print(f"Job URL: {j.job_url}")
    deep = BaseScraper.fetch_job_deep_info(j.job_url)
    print(f"Deep active: {deep.get('is_active')}")
    print(f"Deep location: '{deep.get('location')}'")
    loc_to_check = deep.get('location') or j.raw_location
    parsed = parse_location(loc_to_check)
    is_us = is_usa_location(parsed)
    print(f"Parsed loc: {parsed}, is_usa: {is_us}")

