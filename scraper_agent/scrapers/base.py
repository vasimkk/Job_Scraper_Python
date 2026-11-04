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
    def fetch_job_deep_info(job_url: str) -> dict:
        """
        Deep-fetches job description, location, title, and employment metadata from the job page.
        Returns a dict: {'description': Optional[str], 'location': Optional[str], 'title': Optional[str], 'employment_type': Optional[str]}
        """
        import json
        result = {
            "description": None,
            "location": None,
            "title": None,
            "employment_type": None,
        }
        if not job_url or not job_url.startswith("http"):
            return result
        try:
            resp = requests.get(
                job_url,
                headers={
                    "User-Agent": SCRAPER_CONFIG.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=7,
            )
            if resp.status_code == 200 and resp.text:
                soup = BeautifulSoup(resp.text, "html.parser")

                # 1. Check schema.org JSON-LD
                for s in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(s.string)
                        if isinstance(data, dict):
                            if data.get("@type") == "JobPosting":
                                if data.get("title"):
                                    result["title"] = str(data["title"]).strip()
                                if data.get("employmentType"):
                                    result["employment_type"] = str(data["employmentType"]).strip()
                                job_loc = data.get("jobLocation")
                                if isinstance(job_loc, dict):
                                    addr = job_loc.get("address", {})
                                    if isinstance(addr, dict):
                                        loc_parts = [
                                            addr.get("addressLocality"),
                                            addr.get("addressRegion"),
                                            addr.get("addressCountry"),
                                        ]
                                        valid_locs = [p for p in loc_parts if p and isinstance(p, str)]
                                        if valid_locs:
                                            result["location"] = ", ".join(valid_locs)
                    except Exception:
                        pass

                # 2. Extract Location if not found in JSON-LD
                if not result["location"]:
                    loc_el = soup.select_one(
                        ".location, [class*='location'], [data-automation-id*='location'], "
                        "[data-qa*='location'], [data-testid*='location'], .job-location, "
                        ".posting-categories .location, dd[class*='location']"
                    )
                    if loc_el:
                        loc_text = loc_el.get_text(separator=" ", strip=True)
                        if loc_text and len(loc_text) < 100 and not any(bad in loc_text.lower() for bad in ["unspecified", "not specified"]):
                            result["location"] = loc_text

                # 3. Extract Title if not found in JSON-LD
                if not result["title"]:
                    h1_el = soup.find("h1")
                    if h1_el:
                        h1_text = h1_el.get_text(strip=True)
                        if 4 < len(h1_text) < 150 and not any(bad in h1_text.lower() for bad in ["apply", "welcome", "careers", "job search"]):
                            result["title"] = h1_text

                # 4. Extract Description
                for sel in [
                    "#content",
                    ".content",
                    "#job-description",
                    ".job-description",
                    ".description",
                    "[data-automation-id='jobPostingDescription']",
                    ".posting-page",
                    ".section-page",
                    "main",
                    "article",
                ]:
                    el = soup.select_one(sel)
                    if el:
                        text = el.get_text(separator="\n", strip=True)
                        if len(text) > 120:
                            result["description"] = BaseScraper.clean_html(text)
                            break
                if not result["description"]:
                    body = soup.find("body")
                    if body:
                        text = body.get_text(separator="\n", strip=True)
                        if len(text) > 120:
                            result["description"] = BaseScraper.clean_html(text[:5000])
        except Exception:
            pass
        return result

    @staticmethod
    def fetch_job_page_details(job_url: str) -> Optional[str]:
        """
        Fetches the full job description from the direct job posting page.
        Extracts main content containers (e.g. description, content, posting-page).
        """
        info = BaseScraper.fetch_job_deep_info(job_url)
        return info.get("description")

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

