import logging
import re
from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.models.job import RawJobPost
from scraper_agent.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class GenericHtmlScraper(BaseScraper):
    """
    Fallback scraper for standard career webpages using BeautifulSoup HTML parsing.
    Extracts job cards, headings, links, and text.
    """

    def fetch_jobs(self, source_url: str) -> List[RawJobPost]:
        logger.info(f"Fetching Generic HTML career page from: {source_url}")
        resp = self.session.get(source_url, timeout=SCRAPER_CONFIG.request_timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        job_posts: List[RawJobPost] = []

        # Find job listings via common CSS classes or tags
        candidates = soup.find_all(
            ["div", "li", "tr", "article"],
            class_=re.compile(r"(?i)(job|posting|career|position|vacancy)"),
        )

        for idx, elem in enumerate(candidates):
            # Look for link inside candidate
            link_tag = elem.find("a", href=True)
            if not link_tag:
                continue

            title = (link_tag.get_text() or "").strip()
            if not title or len(title) < 3 or len(title) > 200:
                continue

            href = link_tag["href"]
            job_url = urljoin(source_url, href)
            external_job_id = re.sub(r"\W+", "_", f"job_{idx}_{title[:30]}").strip("_")

            # Try to find location inside element
            loc_tag = elem.find(
                class_=re.compile(r"(?i)(location|city|country|workplace)")
            )
            raw_location = loc_tag.get_text().strip() if loc_tag else ""

            raw_desc = self.clean_html(elem.get_text(separator=" "))

            job_posts.append(
                RawJobPost(
                    external_job_id=external_job_id,
                    title=title,
                    raw_description=raw_desc,
                    raw_location=raw_location,
                    job_url=job_url,
                    application_url=job_url,
                )
            )

        logger.info(f"Generic HTML scraper extracted {len(job_posts)} listings.")
        return job_posts

