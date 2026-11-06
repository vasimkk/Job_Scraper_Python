import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import time
from concurrent.futures import ThreadPoolExecutor
from scraper_agent.db.repository import JobRepository
from scraper_agent.agent.scraper_agent import ScraperAgent
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper

repo = JobRepository()
agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

url = "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
company = repo.get_or_create_company("NVIDIA", domain="nvidia.com", career_url=url, industry="IT, Software & Technology")
source = repo.get_or_create_job_source(company.id, source_url=url, scraper_type="playwright")

scraper = PlaywrightCareerScraper(headless=True)
raw_jobs = scraper.scrape_career_page(url, max_jobs=100)
print(f"Scraped raw jobs: {len(raw_jobs)}")

# Filter US only test
us_jobs = [j for j in raw_jobs if "/job/US-" in j.job_url or "US," in j.raw_location or "United States" in j.raw_location]
print(f"US jobs to deep-fetch: {len(us_jobs)}")

t0 = time.time()
with ThreadPoolExecutor(max_workers=10) as executor:
    deep_infos = list(executor.map(BaseScraper.fetch_job_deep_info, [j.job_url for j in us_jobs]))
dt = time.time() - t0

active_cnt = sum(1 for d in deep_infos if d.get("is_active"))
print(f"Deep-fetched {len(us_jobs)} US jobs in {dt:.2f}s ({active_cnt} active)!")
for j, d in zip(us_jobs[:3], deep_infos[:3]):
    print(f"  {j.title} -> Loc: {d.get('location')}, Desc len: {len(d.get('description') or '')}")

