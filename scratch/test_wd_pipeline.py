import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scraper_agent.db.repository import JobRepository
from scraper_agent.agent.scraper_agent import ScraperAgent

repo = JobRepository()
agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

url = "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
company = repo.get_or_create_company("NVIDIA", domain="nvidia.com", career_url=url, industry="IT, Software & Technology")
source = repo.get_or_create_job_source(company.id, source_url=url, scraper_type="playwright")

print("Processing company NVIDIA (first 30 jobs test)...")
# Let's scrape only 30 jobs
raw_jobs = agent.discovery.playwright_scraper.scrape_career_page(url, max_jobs=30)
print(f"Scraped raw jobs: {len(raw_jobs)}")
agent._process_single_company_pipeline(company, source, raw_jobs)
print("Done processing pipeline!")

