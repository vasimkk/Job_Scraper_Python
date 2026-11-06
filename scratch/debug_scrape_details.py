import sys
sys.path.insert(0, ".")
from scraper_agent.db.repository import JobRepository
from scraper_agent.agent.scraper_agent import ScraperAgent
from scraper_agent.classifiers.location_parser import parse_location, is_usa_location

repo = JobRepository()
agent = ScraperAgent(filter_tech_only=True, enforce_date_window=True)

url = "https://stryker.wd1.myworkdayjobs.com/StrykerCareers"
company = repo.get_or_create_company("Stryker", domain="stryker.com", career_url=url, industry="Healthcare")
source = repo.get_or_create_job_source(company.id, source_url=url, scraper_type="playwright")

raw_jobs = agent.discovery.playwright_scraper.scrape_career_page(url, max_jobs=50)
tech_jobs, _ = agent.filter_jobs_by_technology_nature(raw_jobs)
db_existing = repo.check_existing_jobs(company.id, [j.external_job_id for j, _ in tech_jobs])

for j, kw in tech_jobs:
    is_new = j.external_job_id not in db_existing
    if is_new:
        print(f"\nNew job: {j.title}")
        print(f"  external_job_id: {j.external_job_id}")
        print(f"  raw_loc: '{j.raw_location}'")
        city, state, country, remote_type = parse_location(j.raw_location)
        print(f"  parsed: city={city}, state={state}, country={country}, remote={remote_type}")
        is_us = is_usa_location(raw_location=j.raw_location, title=j.title, city=city, state=state, country=country)
        print(f"  is_usa_location: {is_us}")
        processed = agent.scrape_job_details(company.id, source.id, j, "FULL_TIME", "Software Engineer", kw)
        print(f"  scrape_job_details returned: {processed is not None}")
