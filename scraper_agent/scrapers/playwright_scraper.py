import os
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

# Ensure temporary files stay on D: to prevent disk space exhaustion
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page

from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.models.job import RawJobPost
from scraper_agent.config import SCRAPER_CONFIG

logger = logging.getLogger(__name__)


class PlaywrightCareerScraper(BaseScraper):
    """
    Automated Playwright browser scraper for real company career pages.
    Handles dynamic client-side rendering (React, Vue, Angular, Next.js),
    Workday, Greenhouse, Lever, Ashby, and custom corporate portals.
    """

    def __init__(self, headless: bool = True):
        super().__init__()
        self.headless = headless

    def fetch_jobs(self, source_url: str) -> List[RawJobPost]:
        """Navigates to the real company career URL and extracts live job postings."""
        return self.scrape_career_page(source_url)

    def scrape_career_page(
        self, career_url: str, max_jobs: int = 50
    ) -> List[RawJobPost]:
        """
        Launches Playwright headless Chrome to render and extract jobs from the career page.
        """
        logger.info(f"Opening career page with Playwright: {career_url}")
        job_posts: List[RawJobPost] = []

        try:
            with sync_playwright() as p:
                browser = self._launch_browser(p)
                context = browser.new_context(
                    user_agent=SCRAPER_CONFIG.user_agent,
                    viewport={"width": 1280, "height": 800},
                    ignore_https_errors=True,
                )
                page = context.new_page()

                try:
                    # Navigate to career page with sensible timeout
                    page.goto(career_url, wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(2000)

                    # Trigger lazy-load / scroll safely
                    try:
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                        page.wait_for_timeout(800)
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(1200)
                    except Exception:
                        pass

                    # Check for embedded ATS iframes (e.g. embedded Greenhouse or Lever)
                    try:
                        for frame in page.frames:
                            if "greenhouse.io" in frame.url or "lever.co" in frame.url or "ashbyhq.com" in frame.url:
                                logger.info(f"Detected embedded ATS iframe: {frame.url}")
                                job_posts.extend(self._extract_jobs_from_frame(frame, career_url))
                    except Exception:
                        pass

                    # If not extracted from iframe, extract from main DOM
                    if not job_posts:
                        job_posts = self._extract_jobs_from_page(page, career_url, max_jobs)

                except Exception as nav_exc:
                    logger.warning(f"Unable to scrape career page {career_url}: {nav_exc}")
                finally:
                    try:
                        browser.close()
                    except Exception:
                        pass

        except Exception as exc:
            logger.warning(f"Playwright error initializing for {career_url}: {exc}")

        logger.info(f"Playwright extracted {len(job_posts)} jobs from {career_url}")
        return job_posts

    def _launch_browser(self, playwright_instance) -> Browser:
        """Launches installed Chrome or Edge using Playwright channels."""
        for channel in ["chrome", "msedge"]:
            try:
                return playwright_instance.chromium.launch(
                    channel=channel,
                    headless=self.headless,
                    args=[
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-gpu",
                    ],
                )
            except Exception:
                continue
        # Fallback to default chromium
        return playwright_instance.chromium.launch(headless=self.headless)

    def _extract_jobs_from_page(
        self, page: Page, base_url: str, max_jobs: int = 50
    ) -> List[RawJobPost]:
        """Extracts job elements and links using intelligent selectors."""
        html_content = page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        job_posts: List[RawJobPost] = []
        seen_urls = set()

        # Selector patterns commonly used on modern career pages & ATS systems:
        # Workday: [data-automation-id="jobTitle"], Greenhouse: .opening, Lever: .posting, etc.
        job_elements = page.query_selector_all(
            """
            [data-automation-id="jobTitle"],
            .opening a,
            .posting-title,
            [data-qa="job-card"] a,
            .job-card a,
            .job-listing a,
            a[href*="/job/"],
            a[href*="/jobs/"],
            a[href*="/careers/job/"],
            a[href*="/position/"],
            a[href*="/posting/"],
            a[href*="gh_jid="]
            """
        )

        for elem in job_elements:
            if len(job_posts) >= max_jobs:
                break
            try:
                title = (elem.inner_text() or "").strip()
                if not title or len(title) < 4 or len(title) > 150:
                    continue
                # Skip navigation links like "View all jobs", "Back to careers", etc.
                if any(bad in title.lower() for bad in ["view all", "back to", "search jobs", "apply now", "learn more"]):
                    continue

                href = elem.get_attribute("href") or ""
                job_url = urljoin(base_url, href) if href else base_url
                if job_url in seen_urls:
                    continue
                seen_urls.add(job_url)

                # Try to extract surrounding location and details
                parent = elem.evaluate_handle("el => el.closest('li, div.opening, div.posting, tr, [role=\"listitem\"], article')")
                parent_text = ""
                raw_loc = ""
                if parent:
                    parent_text = parent.as_element().inner_text() if parent.as_element() else ""
                    raw_loc = self._extract_location_from_text(parent_text, title)

                # Generate clean ID
                ext_id = self._generate_job_id(job_url, title)

                job_posts.append(
                    RawJobPost(
                        external_job_id=ext_id,
                        title=title,
                        raw_description=parent_text or title,
                        raw_location=raw_loc or "Remote / Unspecified",
                        job_url=job_url,
                        application_url=job_url,
                        posted_at=datetime.now(timezone.utc),
                        source_updated_at=datetime.now(timezone.utc),
                    )
                )
            except Exception:
                continue

        # If CSS selector found nothing, fallback to parsing soup anchors
        if not job_posts:
            job_posts = self._soup_fallback_extract(soup, base_url, max_jobs)

        return job_posts

    def _extract_jobs_from_frame(self, frame, base_url: str) -> List[RawJobPost]:
        """Extracts job openings from an embedded ATS frame."""
        posts = []
        try:
            links = frame.query_selector_all(".opening a, .posting a, a[href*='/jobs/']")
            for l in links:
                t = (l.inner_text() or "").strip()
                href = l.get_attribute("href") or ""
                if t and href:
                    posts.append(
                        RawJobPost(
                            external_job_id=self._generate_job_id(href, t),
                            title=t,
                            raw_description=t,
                            raw_location="",
                            job_url=urljoin(base_url, href),
                            application_url=urljoin(base_url, href),
                            posted_at=datetime.now(timezone.utc),
                        )
                    )
        except Exception:
            pass
        return posts

    def _soup_fallback_extract(
        self, soup: BeautifulSoup, base_url: str, max_jobs: int = 50
    ) -> List[RawJobPost]:
        """Fallback BeautifulSoup extraction for unusual DOM trees."""
        posts = []
        seen = set()
        for a in soup.find_all("a", href=True):
            if len(posts) >= max_jobs:
                break
            href = a["href"]
            if any(k in href.lower() for k in ["/job", "/career", "gh_jid", "position"]):
                title = a.get_text().strip()
                if 4 < len(title) < 120 and title not in seen:
                    seen.add(title)
                    full_url = urljoin(base_url, href)
                    posts.append(
                        RawJobPost(
                            external_job_id=self._generate_job_id(full_url, title),
                            title=title,
                            raw_description=title,
                            raw_location="",
                            job_url=full_url,
                            application_url=full_url,
                            posted_at=datetime.now(timezone.utc),
                        )
                    )
        return posts

    @staticmethod
    def _extract_location_from_text(block_text: str, title: str) -> str:
        """Extracts location string from card text by stripping out the title."""
        cleaned = block_text.replace(title, "").strip()
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        for line in lines:
            if any(k in line.lower() for k in ["remote", "hybrid", "usa", "san francisco", "new york", "london", "berlin", "austin", "ca", "ny", "tx"]):
                return line
        return lines[0] if lines else ""

    @staticmethod
    def _generate_job_id(job_url: str, title: str) -> str:
        """Generates a stable external ID from the URL or title."""
        parsed = urlparse(job_url)
        path_slug = [p for p in parsed.path.split("/") if p]
        if path_slug:
            last = path_slug[-1]
            if len(last) > 2:
                return re.sub(r"\W+", "_", last)
        return re.sub(r"\W+", "_", f"{parsed.netloc}_{title[:30]}").strip("_")

