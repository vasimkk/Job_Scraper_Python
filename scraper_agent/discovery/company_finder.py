import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

# Ensure temp directory stays on D: to prevent disk space exhaustion
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

from scraper_agent.db.repository import JobRepository
from scraper_agent.models.job import Company, JobSource, RawJobPost
from scraper_agent.scrapers.playwright_scraper import PlaywrightCareerScraper

logger = logging.getLogger(__name__)


class DynamicJobDiscovery:
    """
    Industry-based company discovery and career page scraper using Playwright.
    Follows the workflow:
      Identify Industry -> Find Companies in Industry -> Identify Posted Jobs directly from Career Pages.
    """

    def __init__(self, headless: bool = True):
        self.repo = JobRepository()
        self.playwright_scraper = PlaywrightCareerScraper(headless=headless)

    def scrape_custom_url(
        self, career_url: str, company_name: Optional[str] = None, industry: Optional[str] = None
    ) -> Tuple[Company, JobSource, List[RawJobPost]]:
        """Scrapes a specific real company career page URL directly using Playwright."""
        domain = self._extract_domain(career_url)
        name = company_name or (domain.split(".")[0].title() if domain else "Custom Company")
        ind = industry or "Information Technology"

        company = self.repo.get_or_create_company(
            name=name, domain=domain, career_url=career_url, industry=ind
        )
        source = self.repo.get_or_create_job_source(
            company_id=company.id, source_url=career_url, scraper_type="playwright"
        )
        raw_jobs = self.playwright_scraper.scrape_career_page(career_url)
        return company, source, raw_jobs

    def find_companies_in_industry(
        self, industry: str, company_filter: Optional[str] = None
    ) -> List[Tuple[Company, JobSource]]:
        """
        Flow Step 3: Find Companies in Industry.
        Retrieves companies belonging to the identified industry, along with their active career page sources.
        """
        ind_clean = (industry or "ALL").strip()
        matched_companies: List[Company] = []

        if company_filter:
            comp = self.repo.get_company_by_name(company_filter)
            if comp:
                matched_companies.append(comp)
        else:
            matched_companies = self.repo.get_companies_by_industry(ind_clean)

        results: List[Tuple[Company, JobSource]] = []
        for comp in matched_companies:
            sources = self.repo.get_active_sources_for_company(comp.id)
            for src in sources:
                if src.scraper_type == "playwright" or "career" in src.source_url or "job" in src.source_url:
                    results.append((comp, src))
                    break
            else:
                # If no existing job source, create one pointing to company.career_url
                if comp.career_url:
                    src = self.repo.get_or_create_job_source(
                        company_id=comp.id,
                        source_url=comp.career_url,
                        scraper_type="playwright",
                    )
                    results.append((comp, src))

        return results

    def identify_posted_jobs(
        self, source: JobSource, max_jobs: int = 50
    ) -> List[RawJobPost]:
        """
        Flow Step 4: Identify Posted Jobs.
        Opens the company's real career page URL using Playwright browser automation
        and extracts all active job postings.
        """
        logger.info(f"Opening career page with Playwright: {source.source_url}")
        return self.playwright_scraper.scrape_career_page(source.source_url, max_jobs=max_jobs)

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        if not url:
            return None
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            return netloc.replace("www.", "") if netloc else None
        except Exception:
            return None
