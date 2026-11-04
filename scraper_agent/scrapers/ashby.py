import logging
from datetime import datetime
from typing import List, Optional
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.models.job import RawJobPost
from scraper_agent.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class AshbyScraper(BaseScraper):
    """
    Scraper for Ashby Job Board API.
    Endpoint: https://api.ashbyhq.com/posting-api/job-board/{organization}
    """

    def fetch_jobs(self, source_url: str) -> List[RawJobPost]:
        logger.info(f"Fetching Ashby jobs from: {source_url}")
        resp = self.session.get(source_url, timeout=SCRAPER_CONFIG.request_timeout)
        resp.raise_for_status()

        data = resp.json()
        raw_jobs = data.get("jobs", [])
        logger.info(f"Ashby returned {len(raw_jobs)} total listings.")

        job_posts: List[RawJobPost] = []
        for item in raw_jobs:
            job_id = str(item.get("id"))
            title = (item.get("title") or "").strip()

            raw_desc = item.get("descriptionHtml") or item.get("descriptionPlain") or ""
            desc = self.clean_html(raw_desc)

            raw_location = (item.get("location") or "").strip()
            job_url = item.get("jobUrl") or ""
            app_url = item.get("applyUrl") or job_url

            published_at_str = item.get("publishedAt")
            posted_at = self._parse_iso_date(published_at_str)

            employment_type = item.get("employmentType") or ""
            department = item.get("department") or ""

            job_posts.append(
                RawJobPost(
                    external_job_id=job_id,
                    title=title,
                    raw_description=desc,
                    raw_location=raw_location,
                    job_url=job_url,
                    application_url=app_url,
                    posted_at=posted_at,
                    source_updated_at=posted_at,
                    metadata={
                        "employment_type": employment_type,
                        "department": department,
                        "is_remote": item.get("isRemote", False),
                    },
                )
            )

        return job_posts

    @staticmethod
    def _parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None

