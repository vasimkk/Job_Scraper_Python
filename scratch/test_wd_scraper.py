import sys
sys.path.insert(0, ".")
from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper

scraper = PlaywrightCareerScraper(headless=True)
url = "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
jobs = scraper.scrape_career_page(url, max_jobs=60)
print(f"Scraped {len(jobs)} jobs for NVIDIA!")
