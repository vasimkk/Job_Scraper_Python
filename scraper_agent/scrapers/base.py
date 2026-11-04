import hashlib
import html
import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scraper_agent.config import SCRAPER_CONFIG
from scraper_agent.models.job import RawJobPost

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all job scrapers."""

    def __init__(self):
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "User-Agent": SCRAPER_CONFIG.user_agent,
            "Accept": "application/json, text/html, application/xhtml+xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        retries = Retry(
            total=SCRAPER_CONFIG.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @abstractmethod
    def fetch_jobs(self, source_url: str) -> List[RawJobPost]:
        """Fetch and extract raw job postings from the given source URL."""
        pass

    @staticmethod
    def clean_html(raw_html: str) -> str:
        """Strip HTML tags and unescape HTML entities to produce clean plain text."""
        if not raw_html:
            return ""
        # Unescape entities first
        decoded = html.unescape(raw_html)
        soup = BeautifulSoup(decoded, "html.parser")
        text = soup.get_text(separator="\n")
        # Normalize whitespace
        cleaned = re.sub(r"\n\s*\n+", "\n\n", text).strip()
        return cleaned

    @staticmethod
    def compute_content_hash(
        title: str,
        description: str,
        location: str,
        employment_type: str,
    ) -> str:
        """
        Generates SHA-256 hash of core content fields to detect job updates.
        """
        payload = f"{title.strip()}|{description.strip()}|{location.strip()}|{employment_type.strip()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

