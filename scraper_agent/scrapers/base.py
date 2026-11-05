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

    DEAD_JOB_INDICATORS = [
        "sorry, but we can't find that page",
        "can't find that page",
        "page not found",
        "404 not found",
        "this job is no longer available",
        "job is no longer available",
        "posting has expired",
        "this position has been filled",
        "no longer accepting applications",
    ]

    @staticmethod
    def is_url_active(job_url: str) -> bool:
        """
        Validates that a job URL is live, accessible, and not a 404 or expired posting.
        Returns False if server returns 4xx/5xx, is malformed, or page contains dead-job error text.
        """
        if not job_url or not job_url.startswith("http"):
            return False
        # Malformed greenhouse company URLs are immediately invalid
        if "boards.greenhouse.io/company/" in job_url:
            return False

        # Fast Greenhouse API check (handles both greenhouse.io and custom domains with gh_jid=)
        if "greenhouse.io/" in job_url:
            gh_m = re.search(r"greenhouse\.io/(?:job-boards/)?([a-zA-Z0-9_-]+)/jobs/(\d+)", job_url)
            if gh_m:
                slug, jid = gh_m.group(1), gh_m.group(2)
                if slug != "company":
                    try:
                        api_u = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{jid}"
                        r = requests.get(api_u, headers={"User-Agent": SCRAPER_CONFIG.user_agent}, timeout=5)
                        return r.status_code == 200
                    except Exception:
                        return False
        elif "gh_jid=" in job_url:
            gh_jid_m = re.search(r"gh_jid=(\d+)", job_url)
            domain_m = re.search(r"https?://(?:www\.|careers\.)?([a-zA-Z0-9_-]+)\.", job_url)
            if gh_jid_m and domain_m:
                slug, jid = domain_m.group(1), gh_jid_m.group(1)
                try:
                    api_u = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{jid}"
                    r = requests.get(api_u, headers={"User-Agent": SCRAPER_CONFIG.user_agent}, timeout=5)
                    if r.status_code == 200:
                        return True
                except Exception:
                    pass

        try:
            resp = requests.get(
                job_url,
                headers={
                    "User-Agent": SCRAPER_CONFIG.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=SCRAPER_CONFIG.request_timeout,
                allow_redirects=True,
            )
            if resp.status_code != 200:
                return False
            body_lower = resp.text.lower()
            if any(ind in body_lower for ind in BaseScraper.DEAD_JOB_INDICATORS):
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def fetch_job_deep_info(job_url: str) -> dict:
        """
        Deep-fetches job description, location, title, and employment metadata from the job page.
        Returns a dict: {'description': Optional[str], 'location': Optional[str], 'title': Optional[str], 'employment_type': Optional[str], 'is_active': bool}
        """
        import json
        result = {
            "description": None,
            "location": None,
            "title": None,
            "employment_type": None,
            "is_active": False,
        }
        if not job_url or not job_url.startswith("http"):
            return result
        if "boards.greenhouse.io/company/" in job_url:
            return result

        # 1. Official Greenhouse API handler (instant, full JD, 100% active validation)
        if "greenhouse.io/" in job_url:
            gh_m = re.search(r"greenhouse\.io/(?:job-boards/)?([a-zA-Z0-9_-]+)/jobs/(\d+)", job_url)
            if gh_m:
                slug, jid = gh_m.group(1), gh_m.group(2)
                if slug != "company":
                    try:
                        api_u = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{jid}"
                        r = requests.get(api_u, headers={"User-Agent": SCRAPER_CONFIG.user_agent}, timeout=5)
                        if r.status_code == 200:
                            data = r.json()
                            result["is_active"] = True
                            if data.get("title"):
                                result["title"] = data["title"].strip()
                            loc_data = data.get("location")
                            if isinstance(loc_data, dict) and loc_data.get("name"):
                                result["location"] = loc_data["name"].strip()
                            content_html = data.get("content") or ""
                            if content_html:
                                result["description"] = BaseScraper.clean_html(content_html)
                            return result
                        elif r.status_code == 404:
                            result["is_active"] = False
                            return result
                    except Exception:
                        pass
        elif "gh_jid=" in job_url:
            gh_jid_m = re.search(r"gh_jid=(\d+)", job_url)
            domain_m = re.search(r"https?://(?:www\.|careers\.)?([a-zA-Z0-9_-]+)\.", job_url)
            if gh_jid_m and domain_m:
                slug, jid = domain_m.group(1), gh_jid_m.group(1)
                try:
                    api_u = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs/{jid}"
                    r = requests.get(api_u, headers={"User-Agent": SCRAPER_CONFIG.user_agent}, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        result["is_active"] = True
                        if data.get("title"):
                            result["title"] = data["title"].strip()
                        loc_data = data.get("location")
                        if isinstance(loc_data, dict) and loc_data.get("name"):
                            result["location"] = loc_data["name"].strip()
                        content_html = data.get("content") or ""
                        if content_html:
                            result["description"] = BaseScraper.clean_html(content_html)
                        return result
                    elif r.status_code == 404:
                        result["is_active"] = False
                        return result
                except Exception:
                    pass

        try:
            resp = requests.get(
                job_url,
                headers={
                    "User-Agent": SCRAPER_CONFIG.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=SCRAPER_CONFIG.request_timeout,
                allow_redirects=True,
            )
            if resp.status_code == 200 and resp.text:
                body_lower = resp.text.lower()
                if any(ind in body_lower for ind in BaseScraper.DEAD_JOB_INDICATORS):
                    result["is_active"] = False
                    return result

                result["is_active"] = True
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

                # Decompose navigation, headers, and footers so menus/international office links don't pollute JD text
                for tag in soup(["header", "nav", "footer", "noscript", "svg"]):
                    tag.decompose()

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

