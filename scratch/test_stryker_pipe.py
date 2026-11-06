import sys
sys.path.insert(0, ".")
from scraper_agent.db.repository import JobRepository
from scraper_agent.agent.scraper_agent import ScraperAgent

repo = JobRepository()
agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

url = "https://stryker.wd1.myworkdayjobs.com/StrykerCareers"
company = repo.get_or_create_company("Stryker", domain="stryker.com", career_url=url, industry="Healthcare")
source = repo.get_or_create_job_source(company.id, source_url=url, scraper_type="playwright")

raw_jobs = agent.discovery.playwright_scraper.scrape_career_page(url, max_jobs=50)
print(f"Scraped raw: {len(raw_jobs)}")
agent._process_single_company_pipeline(company, source, raw_jobs)

