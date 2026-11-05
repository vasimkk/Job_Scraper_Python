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

DISALLOWED_URL_PATTERNS = [
    r"/(?:product|products|solution|solutions|pricing|features|feature|customers|case-studies|blog|news|docs|documentation|events|webinars|press|legal|privacy|terms|about-us|platform|security|overview|demo)/",
    r"\.(?:pdf|png|jpg|jpeg|gif|svg|zip|mp4)$",
]


def is_valid_job_url(job_url: str) -> bool:
    """Validates that a URL points to an actual job posting and not a product or marketing page."""
    if not job_url or not job_url.startswith("http"):
        return False
    u = job_url.lower()
    # Reject malformed greenhouse company URLs (e.g. boards.greenhouse.io/company/...)
    if "boards.greenhouse.io/company/" in u:
        return False
    for pat in DISALLOWED_URL_PATTERNS:
        if re.search(pat, u):
            return False
    # Known ATS domains are immediately recognized
    if any(ats in u for ats in [
        "greenhouse.io", "lever.co", "myworkdayjobs.com", "ashbyhq.com",
        "icims.com", "taleo.net", "smartrecruiters.com", "bamboohr.com", "jobvite.com"
    ]):
        return True
    # Path contains clear job indicators with identifiers or slugs
    if re.search(r"/(?:job|jobs|position|positions|posting|postings)/\S+", u):
        return True
    if re.search(r"/careers?/[a-z0-9_-]+/[0-9a-z_-]+", u):
        return True
    if "gh_jid=" in u or "job_id=" in u or "jid=" in u:
        return True
    return False


def normalize_job_url(href: str, base_url: str) -> str:
    """
    Normalizes relative job URLs against base URL.
    Fixes malformed relative paths like '/company/careers/...' that accidentally join to boards.greenhouse.io.
    """
    if not href:
        return base_url

    # If href is /company/careers/... and base_url is a Greenhouse board
    if "boards.greenhouse.io/" in base_url and ("/company/careers/" in href or "/company/" in href):
        m = re.search(r"[-=](\d{6,})", href)
        board_m = re.search(r"boards\.greenhouse\.io/([^/?#]+)", base_url)
        if m and board_m and board_m.group(1) != "company":
            return f"https://boards.greenhouse.io/{board_m.group(1)}/jobs/{m.group(1)}"

    # If href already has boards.greenhouse.io/company/
    if "boards.greenhouse.io/company/" in href:
        m = re.search(r"[-=](\d{6,})", href)
        board_m = re.search(r"boards\.greenhouse\.io/([^/?#]+)", base_url)
        if m and board_m and board_m.group(1) != "company":
            return f"https://boards.greenhouse.io/{board_m.group(1)}/jobs/{m.group(1)}"

    return urljoin(base_url, href)


class PlaywrightCareerScraper(BaseScraper):
    """
    Automated Playwright browser scraper for real company career pages.
    Handles dynamic client-side rendering (React, Vue, Angular, Next.js),
    Workday, Greenhouse, Lever, Ashby, and custom corporate portals.
    """

    def __init__(self, headless: bool = True):
        super().__init__()
        self.headless = headless

    def _fetch_greenhouse_api_jobs(self, slug: str, max_jobs: int = 120) -> List[RawJobPost]:
        """Directly fetches jobs from Greenhouse's official public REST API when HTML is challenged or blocked."""
        import urllib.request
        import json
        posts = []
        try:
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
            req = urllib.request.Request(api_url, headers={"User-Agent": SCRAPER_CONFIG.user_agent})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                raw_list = data.get("jobs", [])
                for item in raw_list[:max_jobs]:
                    jid = str(item.get("id"))
                    title = (item.get("title") or "").strip()
                    loc = item.get("location", {}).get("name", "") if isinstance(item.get("location"), dict) else ""
                    # Prefer canonical greenhouse URL so deep detail fetch never 404s on custom SPA domains
                    canonical_gh_url = f"https://boards.greenhouse.io/{slug}/jobs/{jid}"
                    raw_abs_url = item.get("absolute_url") or ""
                    app_url = raw_abs_url if (raw_abs_url and "boards.greenhouse.io/company/" not in raw_abs_url) else canonical_gh_url
                    job_url = canonical_gh_url
                    posts.append(
                        RawJobPost(
                            external_job_id=f"gh_{slug}_{jid}",
                            title=title,
                            raw_description=title,
                            raw_location=loc,
                            job_url=job_url,
                            application_url=app_url,
                            posted_at=datetime.now(timezone.utc),
                        )
                    )
        except Exception as e:
            logger.debug(f"Greenhouse API fallback failed for {slug}: {e}")
        return posts

    def fetch_jobs(self, source_url: str) -> List[RawJobPost]:
        """Navigates to the real company career URL and extracts live job postings."""
        return self.scrape_career_page(source_url, max_jobs=120)

    def scrape_career_page(
        self, career_url: str, max_jobs: int = 120
    ) -> List[RawJobPost]:
        """
        Launches Playwright headless Chrome to render and extract jobs from the career page.
        """
        # Fast, robust Greenhouse API check (bypasses Cloudflare/HTTP 403 on greenhouse boards)
        if "boards.greenhouse.io/" in career_url:
            board_m = re.search(r"boards\.greenhouse\.io/([^/?#]+)", career_url)
            if board_m and board_m.group(1) != "company":
                slug = board_m.group(1)
                api_jobs = self._fetch_greenhouse_api_jobs(slug, max_jobs=max_jobs)
                if api_jobs:
                    logger.info(f"Greenhouse API returned {len(api_jobs)} active jobs for {slug}")
                    return api_jobs

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

                    # If still 0 jobs, look for navigation subpage like "/open-roles", "Open Roles", "View Openings", or ATS link
                    if not job_posts:
                        subpage_link = self._find_openings_subpage(page, career_url)
                        if subpage_link and subpage_link != career_url and not subpage_link.endswith(career_url):
                            logger.info(f"Navigating to openings subpage: {subpage_link}")
                            try:
                                page.goto(subpage_link, wait_until="domcontentloaded", timeout=20000)
                                page.wait_for_timeout(2500)
                                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                                page.wait_for_timeout(600)
                                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                page.wait_for_timeout(1000)
                                job_posts = self._extract_jobs_from_page(page, subpage_link, max_jobs)
                            except Exception as sub_exc:
                                logger.warning(f"Error navigating to openings subpage {subpage_link}: {sub_exc}")

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

    def _find_openings_subpage(self, page: Page, base_url: str) -> Optional[str]:
        """Looks for links to open jobs, openings, or ATS boards on landing pages."""
        try:
            anchors = page.query_selector_all("a[href]")
            for a in anchors:
                txt = (a.inner_text() or "").strip().lower()
                href = (a.get_attribute("href") or "").strip()
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue
                # Priority 1: direct ATS link
                if any(ats in href for ats in ["greenhouse.io", "lever.co", "ashbyhq.com", "myworkdayjobs.com", "icims.com"]):
                    return urljoin(base_url, href)
                # Priority 2: explicit open roles / jobs button
                if any(phrase in txt for phrase in [
                    "open roles", "explore open roles", "view open roles", "open positions",
                    "view open positions", "current openings", "search jobs", "view jobs",
                    "all openings", "see all roles", "browse jobs", "job openings"
                ]):
                    return urljoin(base_url, href)
                # Priority 3: clear openings path
                if any(p in href.lower() for p in ["/open-roles", "/openings", "/jobs/search", "/careers/jobs"]):
                    return urljoin(base_url, href)
        except Exception:
            pass
        return None

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
                if not title:
                    continue

                # Check if anchor is an action button (e.g. "Apply", "View Job", "Read More")
                # and retrieve the actual job title from the enclosing card heading
                if any(bad in title.lower() for bad in ["view all", "back to", "search jobs", "all jobs"]):
                    continue

                if title.lower() in ["apply", "apply now", "view", "view job", "details", "read more", "learn more"] or len(title) < 4:
                    heading = elem.evaluate("""el => {
                        let cur = el;
                        for (let i = 0; i < 5 && cur && cur.parentElement && cur.tagName !== 'BODY'; i++) {
                            cur = cur.parentElement;
                            const h = cur.querySelector('h1, h2, h3, h4, h5, [class*="title"], [class*="heading"]');
                            if (h && h.innerText.trim().length >= 4) {
                                return h.innerText.trim();
                            }
                        }
                        return null;
                    }""")
                    if heading and len(heading) >= 4:
                        title = heading
                    else:
                        continue

                if len(title) < 4 or len(title) > 150:
                    continue

                href = elem.get_attribute("href") or ""
                job_url = normalize_job_url(href, base_url) if href else base_url
                if not is_valid_job_url(job_url):
                    continue
                if job_url in seen_urls:
                    continue
                seen_urls.add(job_url)

                # Try to extract surrounding location and details
                raw_loc = elem.evaluate("""el => {
                    const card = el.closest('li, div.opening, div.posting, tr, [role="listitem"], article, div[class*="layout"]');
                    if (!card) return null;
                    const loc = card.querySelector('.location, [class*="location"], [data-automation-id*="location"], [data-qa*="location"], .posting-categories .location, span.sort-by-location');
                    return loc ? loc.innerText.trim() : null;
                }""") or ""

                parent = elem.evaluate_handle("el => el.closest('li, div.opening, div.posting, tr, [role=\"listitem\"], article, div[class*=\"layout\"]')")
                parent_text = ""
                if parent and parent.as_element():
                    parent_text = parent.as_element().inner_text() or ""
                    if not raw_loc:
                        raw_loc = self._extract_location_from_text(parent_text, title)

                # Generate clean ID
                ext_id = self._generate_job_id(job_url, title)

                job_posts.append(
                    RawJobPost(
                        external_job_id=ext_id,
                        title=title,
                        raw_description=parent_text or title,
                        raw_location=raw_loc or "",
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
                            job_url=normalize_job_url(href, base_url),
                            application_url=normalize_job_url(href, base_url),
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
            full_url = normalize_job_url(href, base_url)
            if not is_valid_job_url(full_url):
                continue
            title = a.get_text().strip()
            if 4 < len(title) < 120 and title not in seen:
                seen.add(title)
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
            line_lower = line.lower()
            if any(k in line_lower for k in [
                "remote", "hybrid", "on-site", "onsite", "usa", "united states",
                "san francisco", "new york", "austin", "seattle", "boston", "denver",
                "los angeles", "chicago", "hawthorne", "el segundo", "sunnyvale",
                ", ca", ", tx", ", ny", ", wa", ", ma", ", co", ", fl", ", va"
            ]):
                return line
        return ""

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

