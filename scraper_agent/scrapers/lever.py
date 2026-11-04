import logging
from datetime import datetime, timezone
from typing import List, Optional
from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.models.job import RawJobPost
from scraper_agent.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class LeverScraper(BaseScraper):
    """
    Scraper for Lever ATS API.
    Endpoint: https://api.lever.co/v0/postings/{company}?mode=json
    """

    def fetch_jobs(self, source_url: str) -> List[RawJobPost]:
        url = source_url
        if "mode=json" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}mode=json"

        logger.info(f"Fetching Lever jobs from: {url}")
        resp = self.session.get(url, timeout=SCRAPER_CONFIG.request_timeout)
        resp.raise_for_status()

        data = resp.json()
        if isinstance(data, dict) and "postings" in data:
            data = data["postings"]
        elif not isinstance(data, list):
            data = []

        logger.info(f"Lever returned {len(data)} total listings.")
        job_posts: List[RawJobPost] = []

        for item in data:
            job_id = str(item.get("id"))
            title = (item.get("text") or "").strip()

            raw_desc = item.get("descriptionPlain") or item.get("description") or ""
            desc = self.clean_html(raw_desc)
            additional = item.get("additionalPlain") or item.get("additional") or ""
            if additional:
                desc = f"{desc}\n\n{self.clean_html(additional)}"

            categories = item.get("categories") or {}
            raw_location = categories.get("location") or ""
            commitment = categories.get("commitment") or ""
            team = categories.get("team") or categories.get("department") or ""

            job_url = item.get("hostedUrl") or ""
            app_url = item.get("applyUrl") or job_url

            # Created timestamp in milliseconds
            created_at_ms = item.get("createdAt")
            posted_at = None
            if created_at_ms:
                try:
                    posted_at = datetime.fromtimestamp(created_at_ms / 1000.0, tz=timezone.utc)
                except Exception:
                    pass

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
                        "commitment": commitment,
                        "team": team,
                        "categories": categories,
                    },
                )
            )

        return job_posts

