import sys
sys.path.insert(0, ".")
from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper
from scraper_agent.scrapers.base import BaseScraper

scraper = PlaywrightCareerScraper(headless=True)
jobs = scraper.scrape_career_page("https://stryker.wd1.myworkdayjobs.com/StrykerCareers", max_jobs=5)
print(f"Scraped {len(jobs)} jobs for Stryker")
for j in jobs:
    print(f"\nTitle: {j.title}")
    print(f"URL: {j.job_url}")
    deep = BaseScraper.fetch_job_deep_info(j.job_url)
    print(f"is_active: {deep.get('is_active')}, loc: {deep.get('location')}, desc len: {len(deep.get('description') or '')}")

