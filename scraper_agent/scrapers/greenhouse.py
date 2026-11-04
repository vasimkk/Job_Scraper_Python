import logging
from datetime import datetime
from typing import List, Optional
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.models.job import RawJobPost
from scraper_agent.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class GreenhouseScraper(BaseScraper):
    """
    Scraper for Greenhouse ATS Boards API.
    Endpoint: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true
    """

    def fetch_jobs(self, source_url: str) -> List[RawJobPost]:
        url = source_url
        if "content=true" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}content=true"

        logger.info(f"Fetching Greenhouse jobs from: {url}")
        resp = self.session.get(url, timeout=SCRAPER_CONFIG.request_timeout)
        resp.raise_for_status()

        data = resp.json()
        raw_jobs = data.get("jobs", [])
        logger.info(f"Greenhouse returned {len(raw_jobs)} total listings.")

        job_posts: List[RawJobPost] = []
        for item in raw_jobs:
            job_id = str(item.get("id"))
            title = (item.get("title") or "").strip()
            raw_content = item.get("content") or ""
            description = self.clean_html(raw_content)

            loc_obj = item.get("location") or {}
            raw_location = (loc_obj.get("name") or "").strip()

            job_url = item.get("absolute_url") or ""
            app_url = job_url  # Greenhouse job page includes application form

            # Parse updated_at
            updated_at_str = item.get("updated_at")
            source_updated_at = self._parse_iso_date(updated_at_str)

            # Metadata
            departments = [d.get("name") for d in item.get("departments", []) if d.get("name")]
            offices = [o.get("name") for o in item.get("offices", []) if o.get("name")]

            job_posts.append(
                RawJobPost(
                    external_job_id=job_id,
                    title=title,
                    raw_description=description,
                    raw_location=raw_location,
                    job_url=job_url,
                    application_url=app_url,
                    posted_at=source_updated_at,
                    source_updated_at=source_updated_at,
                    metadata={
                        "departments": departments,
                        "offices": offices,
                        "raw_html": raw_content,
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

