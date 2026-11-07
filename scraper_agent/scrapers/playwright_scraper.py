import os
import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse, quote_plus

# Ensure temporary files stay on D: to prevent disk space exhaustion
os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page

from scraper_agent.scrapers.base import BaseScraper
from scraper_agent.models.job import RawJobPost
from scraper_agent.config import SCRAPER_CONFIG
from scraper_agent.classifiers.location_parser import US_STATE_NAMES_TO_CODE

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
        "icims.com", "taleo.net", "smartrecruiters.com", "bamboohr.com", "jobvite.com",
        "dice.com"
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

    def _fetch_greenhouse_api_jobs(self, slug: str, max_jobs: int = 1000) -> List[RawJobPost]:
        """Directly fetches jobs from Greenhouse's official public REST API with full content."""
        import urllib.request
        import json
        posts = []
        try:
            # ?content=true includes full clean HTML description for all jobs in 1 call
            api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            req = urllib.request.Request(api_url, headers={"User-Agent": SCRAPER_CONFIG.user_agent})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                raw_list = data.get("jobs", [])
                for item in raw_list[:max_jobs]:
                    jid = str(item.get("id"))
                    title = (item.get("title") or "").strip()
                    loc = item.get("location", {}).get("name", "") if isinstance(item.get("location"), dict) else ""
                    canonical_gh_url = f"https://boards.greenhouse.io/{slug}/jobs/{jid}"
                    raw_abs_url = item.get("absolute_url") or ""
                    app_url = raw_abs_url if (raw_abs_url and "boards.greenhouse.io/company/" not in raw_abs_url) else canonical_gh_url
                    job_url = canonical_gh_url

                    content_html = item.get("content") or ""
                    raw_desc = BaseScraper.clean_html(content_html) if content_html else title

                    posted_dt = datetime.now(timezone.utc)
                    updated_at_str = item.get("updated_at")
                    if updated_at_str:
                        try:
                            posted_dt = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                        except Exception:
                            pass

                    posts.append(
                        RawJobPost(
                            external_job_id=f"gh_{slug}_{jid}",
                            title=title,
                            raw_description=raw_desc,
                            raw_location=loc,
                            job_url=job_url,
                            application_url=app_url,
                            posted_at=posted_dt,
                            metadata={"ats": "greenhouse", "slug": slug},
                        )
                    )
        except Exception as e:
            logger.debug(f"Greenhouse API fetch failed for {slug}: {e}")
        return posts

    def _fetch_lever_api_jobs(self, slug: str, max_jobs: int = 1000) -> List[RawJobPost]:
        """Directly fetches jobs from Lever's official public REST API with full JD and commitment."""
        import urllib.request
        import json
        posts = []
        try:
            api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            req = urllib.request.Request(api_url, headers={"User-Agent": SCRAPER_CONFIG.user_agent})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw_list = json.loads(resp.read().decode())
                if isinstance(raw_list, list):
                    for item in raw_list[:max_jobs]:
                        jid = str(item.get("id"))
                        title = (item.get("text") or "").strip()
                        categories = item.get("categories") or {}
                        loc = categories.get("location") or item.get("workplaceType") or ""
                        job_url = item.get("hostedUrl") or f"https://jobs.lever.co/{slug}/{jid}"
                        app_url = item.get("applyUrl") or job_url
                        posted_ts = item.get("createdAt")
                        posted_dt = datetime.fromtimestamp(posted_ts / 1000.0, tz=timezone.utc) if posted_ts else datetime.now(timezone.utc)

                        desc_plain = item.get("descriptionPlain") or ""
                        desc_html = item.get("description") or ""
                        desc = desc_plain if desc_plain else BaseScraper.clean_html(desc_html)
                        lists = item.get("lists") or []
                        for lst in lists:
                            hdr = lst.get("text") or ""
                            content = BaseScraper.clean_html(lst.get("content") or "")
                            if hdr or content:
                                desc += f"\n\n{hdr}:\n{content}"

                        commitment = categories.get("commitment") or ""

                        posts.append(
                            RawJobPost(
                                external_job_id=f"lever_{slug}_{jid}",
                                title=title,
                                raw_description=desc.strip() if desc.strip() else title,
                                raw_location=loc,
                                job_url=job_url,
                                application_url=app_url,
                                posted_at=posted_dt,
                                metadata={"ats": "lever", "slug": slug, "commitment": commitment},
                            )
                        )
        except Exception as e:
            logger.debug(f"Lever API fetch failed for {slug}: {e}")
        return posts

    def _fetch_ashby_api_jobs(self, slug: str, max_jobs: int = 1000) -> List[RawJobPost]:
        """Directly fetches jobs from Ashby's official public REST API with full JD and employmentType."""
        import urllib.request
        import json
        posts = []
        try:
            api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
            req = urllib.request.Request(api_url, headers={"User-Agent": SCRAPER_CONFIG.user_agent})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                raw_list = data.get("jobs", []) if isinstance(data, dict) else []
                for item in raw_list[:max_jobs]:
                    jid = str(item.get("id"))
                    title = (item.get("title") or "").strip()
                    loc = item.get("locationName") or ""
                    job_url = item.get("jobUrl") or f"https://jobs.ashbyhq.com/{slug}/{jid}"
                    app_url = item.get("applyUrl") or job_url
                    published = item.get("publishedAt")
                    try:
                        posted_dt = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else datetime.now(timezone.utc)
                    except Exception:
                        posted_dt = datetime.now(timezone.utc)

                    desc_plain = item.get("descriptionPlain") or ""
                    desc_html = item.get("descriptionHtml") or ""
                    desc = desc_plain if desc_plain else BaseScraper.clean_html(desc_html)
                    emp_type = item.get("employmentType") or ""

                    posts.append(
                        RawJobPost(
                            external_job_id=f"ashby_{slug}_{jid}",
                            title=title,
                            raw_description=desc.strip() if desc.strip() else title,
                            raw_location=loc,
                            job_url=job_url,
                            application_url=app_url,
                            posted_at=posted_dt,
                            metadata={"ats": "ashby", "slug": slug, "employment_type": emp_type},
                        )
                    )
        except Exception as e:
            logger.debug(f"Ashby API fetch failed for {slug}: {e}")
        return posts

    def _fetch_smartrecruiters_api_jobs(self, slug: str, max_jobs: int = 1000) -> List[RawJobPost]:
        """Directly fetches jobs from SmartRecruiters official public REST API with pagination."""
        import urllib.request
        import json
        posts = []
        try:
            offset = 0
            limit = 100
            while len(posts) < max_jobs:
                api_url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?offset={offset}&limit={limit}"
                req = urllib.request.Request(api_url, headers={"User-Agent": SCRAPER_CONFIG.user_agent})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    content = data.get("content", []) if isinstance(data, dict) else []
                    if not content:
                        break
                    for item in content:
                        if len(posts) >= max_jobs:
                            break
                        jid = str(item.get("id"))
                        title = (item.get("name") or "").strip()
                        loc_dict = item.get("location") or {}
                        loc_parts = [loc_dict.get("city"), loc_dict.get("region"), loc_dict.get("country")]
                        loc = ", ".join([p for p in loc_parts if p])
                        job_url = f"https://jobs.smartrecruiters.com/{slug}/{jid}"
                        posted_str = item.get("releasedDate")
                        try:
                            posted_dt = datetime.fromisoformat(posted_str.replace("Z", "+00:00")) if posted_str else datetime.now(timezone.utc)
                        except Exception:
                            posted_dt = datetime.now(timezone.utc)

                        type_emp = (item.get("typeOfEmployment") or {}).get("label") or ""

                        posts.append(
                            RawJobPost(
                                external_job_id=f"sr_{slug}_{jid}",
                                title=title,
                                raw_description=title,
                                raw_location=loc,
                                job_url=job_url,
                                application_url=job_url,
                                posted_at=posted_dt,
                                metadata={"ats": "smartrecruiters", "slug": slug, "employment_type": type_emp},
                            )
                        )
                    offset += limit
                    total_found = data.get("totalFound", 0)
                    if offset >= total_found:
                        break
        except Exception as e:
            logger.debug(f"SmartRecruiters API fetch failed for {slug}: {e}")
        return posts

    def _fetch_bamboohr_api_jobs(self, company: str, max_jobs: int = 250) -> List[RawJobPost]:
        """Directly fetches jobs from BambooHR public jobs endpoint."""
        import urllib.request
        import json
        posts = []
        try:
            api_url = f"https://{company}.bamboohr.com/careers/list"
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": SCRAPER_CONFIG.user_agent, "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                raw_list = data.get("result", []) if isinstance(data, dict) else []
                for item in raw_list[:max_jobs]:
                    jid = str(item.get("id"))
                    title = (item.get("jobOpeningName") or "").strip()
                    loc_dict = item.get("location") or {}
                    loc = f"{loc_dict.get('city', '')}, {loc_dict.get('state', '')}".strip(", ")
                    job_url = f"https://{company}.bamboohr.com/careers/{jid}"
                    emp_type = item.get("type") or item.get("jobType") or ""
                    posts.append(
                        RawJobPost(
                            external_job_id=f"bamboo_{company}_{jid}",
                            title=title,
                            raw_description=title,
                            raw_location=loc,
                            job_url=job_url,
                            application_url=job_url,
                            posted_at=datetime.now(timezone.utc),
                            metadata={"ats": "bamboohr", "company": company, "employment_type": emp_type},
                        )
                    )
        except Exception as e:
            logger.debug(f"BambooHR API fetch failed for {company}: {e}")
        return posts

    def _fetch_workday_cxs_jobs(self, host: str, tenant: str, board: str, max_jobs: int = 1500) -> List[RawJobPost]:
        """Directly fetches jobs from Workday's official CXS public API with pagination."""
        import urllib.request
        import json
        posts = []
        try:
            offset = 0
            limit = 20
            total_count = None
            while len(posts) < max_jobs:
                api_url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"
                payload = json.dumps({"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""}).encode("utf-8")
                req = urllib.request.Request(
                    api_url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": SCRAPER_CONFIG.user_agent,
                        "Accept": "application/json",
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode())
                    job_list = data.get("jobPostings", [])
                    if not job_list:
                        break
                    for item in job_list:
                        if len(posts) >= max_jobs:
                            break
                        title = (item.get("title") or "").strip()
                        ext_path = item.get("externalPath") or ""
                        loc = (item.get("locationsText") or "").strip()

                        # Extract location from externalPath if loc is empty or generic (e.g. '2 Locations')
                        if not loc or re.match(r"^\d+\s+Locations?$", loc, re.IGNORECASE):
                            m_us = re.search(r"/job/US-([A-Z]{2})-([^/]+)/", ext_path)
                            if m_us:
                                st, city = m_us.group(1), m_us.group(2).replace("-", " ")
                                loc = f"{city}, {st}, United States"
                            elif "/job/" in ext_path:
                                path_parts = ext_path.strip("/").split("/")
                                if len(path_parts) >= 2:
                                    loc_part = path_parts[1]
                                    tokens = [t.lower() for t in loc_part.split("-")]
                                    found_st = None
                                    for t in tokens:
                                        if t in US_STATE_NAMES_TO_CODE:
                                            found_st = US_STATE_NAMES_TO_CODE[t]
                                            break
                                    if found_st:
                                        clean_city = loc_part.replace("-", " ")
                                        loc = f"{clean_city}, {found_st}, United States"
                                    else:
                                        loc = loc_part.replace("-", ", ")

                        job_url = f"https://{host}/{board}{ext_path}" if ext_path else f"https://{host}/{board}"
                        jid = re.sub(r"\W+", "_", ext_path.strip("/")) or title[:20]
                        time_type = item.get("timeType") or ""
                        posts.append(
                            RawJobPost(
                                external_job_id=f"wd_{tenant}_{jid}",
                                title=title,
                                raw_description=title,
                                raw_location=loc,
                                job_url=job_url,
                                application_url=job_url,
                                posted_at=datetime.now(timezone.utc),
                                metadata={"ats": "workday", "tenant": tenant, "board": board, "time_type": time_type},
                            )
                        )
                    if total_count is None and data.get("total"):
                        total_count = data["total"]
                    offset += len(job_list)
                    if (total_count and offset >= total_count) or len(job_list) < limit:
                        break
        except Exception as e:
            logger.debug(f"Workday CXS API fetch failed for {host}/{tenant}/{board}: {e}")
        return posts

    def _fetch_jobvite_jobs(self, url: str, max_jobs: int = 250) -> List[RawJobPost]:
        """Directly fetches jobs from Jobvite career portals using XML feed and HTML parsing."""
        import urllib.request
        from bs4 import BeautifulSoup
        posts = []
        try:
            m = re.search(r"jobs\.jobvite\.com/([a-zA-Z0-9_-]+)", url)
            if not m:
                m = re.search(r"[?&]c=([a-zA-Z0-9_-]+)", url)
            company = m.group(1) if m else None

            # 1. Try Jobvite public XML feed
            if company:
                try:
                    xml_url = f"https://app.jobvite.com/CompanyJobs/Xml.aspx?c={company}"
                    req = urllib.request.Request(xml_url, headers={"User-Agent": SCRAPER_CONFIG.user_agent})
                    with urllib.request.urlopen(req, timeout=6) as r:
                        xml_data = r.read().decode("utf-8", errors="ignore")
                        if "<job>" in xml_data:
                            soup = BeautifulSoup(xml_data, "xml")
                            for j in soup.find_all("job")[:max_jobs]:
                                jid = j.find("id").text if j.find("id") else ""
                                title = j.find("title").text if j.find("title") else ""
                                loc = j.find("location").text if j.find("location") else ""
                                j_url = j.find("detail-url").text if j.find("detail-url") else url
                                desc = j.find("description").text if j.find("description") else title
                                jtype = j.find("job-type").text if j.find("job-type") else ""
                                if title:
                                    posts.append(
                                        RawJobPost(
                                            external_job_id=f"jobvite_{company}_{jid or title[:15]}",
                                            title=title.strip(),
                                            raw_description=BaseScraper.clean_html(desc),
                                            raw_location=loc.strip(),
                                            job_url=j_url.strip(),
                                            application_url=j_url.strip(),
                                            posted_at=datetime.now(timezone.utc),
                                            metadata={"ats": "jobvite", "company": company, "employment_type": jtype},
                                        )
                                    )
                            if posts:
                                logger.info(f"Jobvite XML feed returned {len(posts)} jobs for {company}")
                                return posts
                except Exception:
                    pass

            # 2. HTML parsing of Jobvite jobs table
            target_url = url if "/jobs" in url else (f"https://jobs.jobvite.com/{company}/jobs" if company else url)
            req = urllib.request.Request(target_url, headers={"User-Agent": SCRAPER_CONFIG.user_agent})
            with urllib.request.urlopen(req, timeout=8) as r:
                html_text = r.read().decode("utf-8", errors="ignore")
                soup = BeautifulSoup(html_text, "html.parser")
                job_links = soup.select(".jv-job-list a, .jv-job-card a, a[href*='/job/']")
                seen = set()
                for a in job_links[:max_jobs]:
                    title = a.get_text(strip=True)
                    href = a.get("href") or ""
                    if not title or not href or len(title) < 4:
                        continue
                    full_url = urljoin(target_url, href)
                    if full_url in seen:
                        continue
                    seen.add(full_url)
                    loc = ""
                    parent = a.find_parent("tr") or a.find_parent("div")
                    if parent:
                        loc_el = parent.select_one(".jv-job-list-location, [class*='location']")
                        if loc_el:
                            loc = loc_el.get_text(strip=True)
                    jid_m = re.search(r"/job/([a-zA-Z0-9_-]+)", href)
                    jid = jid_m.group(1) if jid_m else re.sub(r"\W+", "_", title[:20])
                    posts.append(
                        RawJobPost(
                            external_job_id=f"jobvite_{company or 'jv'}_{jid}",
                            title=title,
                            raw_description=title,
                            raw_location=loc,
                            job_url=full_url,
                            application_url=full_url,
                            posted_at=datetime.now(timezone.utc),
                            metadata={"ats": "jobvite", "company": company or ""},
                        )
                    )
        except Exception as e:
            logger.debug(f"Jobvite fetch failed for {url}: {e}")
        return posts

    def _fetch_icims_jobs(self, url: str, max_jobs: int = 250) -> List[RawJobPost]:
        """Directly fetches jobs from iCIMS portal search pages with pagination."""
        import urllib.request
        from bs4 import BeautifulSoup
        posts = []
        try:
            parsed = urlparse(url)
            host = parsed.netloc
            page = 0
            seen = set()
            while len(posts) < max_jobs and page < 10:
                search_url = f"https://{host}/jobs/search?pr={page}&in_iframe=1"
                req = urllib.request.Request(search_url, headers={"User-Agent": SCRAPER_CONFIG.user_agent})
                with urllib.request.urlopen(req, timeout=10) as r:
                    html_text = r.read().decode("utf-8", errors="ignore")
                    soup = BeautifulSoup(html_text, "html.parser")
                    rows = soup.select(".iCIMS_JobsTable .row, .iCIMS_JobHeaderGroup")
                    if not rows:
                        # Try finding any anchor with /jobs/
                        rows = [a.find_parent("div") for a in soup.select("a.iCIMS_Anchor, a[href*='/jobs/']") if a.find_parent("div")]
                    if not rows:
                        break
                    found_in_page = 0
                    for row in rows:
                        if len(posts) >= max_jobs:
                            break
                        a = row.select_one("a.iCIMS_Anchor, a[href*='/jobs/']") or row.find("a", href=True)
                        if not a:
                            continue
                        title = a.get_text(strip=True)
                        href = a.get("href") or ""
                        if not title or not href or len(title) < 4:
                            continue
                        full_url = normalize_job_url(href, f"https://{host}")
                        if full_url in seen:
                            continue
                        seen.add(full_url)
                        found_in_page += 1
                        loc = ""
                        loc_el = row.select_one(".iCIMS_JobHeaderTag, span[itemprop='addressLocality'], [class*='location']")
                        if loc_el:
                            loc = loc_el.get_text(strip=True)
                        jid_m = re.search(r"/jobs/(\d+)/", href)
                        jid = jid_m.group(1) if jid_m else re.sub(r"\W+", "_", title[:20])
                        posts.append(
                            RawJobPost(
                                external_job_id=f"icims_{host}_{jid}",
                                title=title,
                                raw_description=title,
                                raw_location=loc,
                                job_url=full_url,
                                application_url=full_url,
                                posted_at=datetime.now(timezone.utc),
                                metadata={"ats": "icims", "host": host},
                            )
                        )
                    if found_in_page == 0:
                        break
                    page += 1
        except Exception as e:
            logger.debug(f"iCIMS fetch failed for {url}: {e}")
        return posts

    def _fetch_taleo_jobs(self, url: str, max_jobs: int = 250) -> List[RawJobPost]:
        """Fetches jobs from Oracle Taleo career portal using Playwright browser."""
        posts = []
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
                    page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    page.wait_for_timeout(3500)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    page.wait_for_timeout(1000)

                    elements = page.query_selector_all(
                        """
                        span.titlelink a,
                        a[id*="requisitionListInterface.reqTitle"],
                        .multiline-data-container a,
                        .portalContent table tr a[href*="jobdetail"]
                        """
                    )
                    seen = set()
                    for el in elements[:max_jobs]:
                        t = (el.inner_text() or "").strip()
                        href = el.get_attribute("href") or ""
                        if not t or len(t) < 4:
                            continue
                        full_u = urljoin(url, href) if href else url
                        if full_u in seen:
                            continue
                        seen.add(full_u)

                        # Location in table row
                        loc = ""
                        try:
                            loc = el.evaluate("""el => {
                                const row = el.closest('tr, .multiline-data-container');
                                if (!row) return '';
                                const locEl = row.querySelector('[id*="Location"], [id*="reqLocation"], span.location');
                                return locEl ? locEl.innerText.trim() : '';
                            }""") or ""
                        except Exception:
                            pass

                        jid_m = re.search(r"job=(\d+)", href) or re.search(r"requisition=(\d+)", href)
                        jid = jid_m.group(1) if jid_m else re.sub(r"\W+", "_", t[:20])

                        posts.append(
                            RawJobPost(
                                external_job_id=f"taleo_{jid}",
                                title=t,
                                raw_description=t,
                                raw_location=loc,
                                job_url=full_u,
                                application_url=full_u,
                                posted_at=datetime.now(timezone.utc),
                                metadata={"ats": "taleo"},
                            )
                        )
                finally:
                    browser.close()
        except Exception as e:
            logger.debug(f"Taleo scraping failed for {url}: {e}")
        return posts

    def _fetch_dice_jobs(self, url_or_query: str, max_jobs: int = 1000) -> List[RawJobPost]:
        """
        Extracts live job postings from the Dice ATS platform (dice.com).
        Supports search URLs, company profiles, and direct search queries.
        Paginates dynamically across search pages and extracts titles, company names,
        USA locations, employment types (Full-Time, Contract), relative posted dates,
        and job URLs.
        """
        posts: List[RawJobPost] = []
        u = (url_or_query or "").strip()

        # Build search URL
        if u.startswith("http"):
            base_url = u
        else:
            query = quote_plus(u) if u else "software"
            base_url = f"https://www.dice.com/jobs?q={query}"

        # Relative date parser for Dice
        def _parse_dice_relative_date(posted_str: str) -> datetime:
            now = datetime.now(timezone.utc)
            s = (posted_str or "").lower().strip()
            if any(k in s for k in ["today", "just now", "moment"]):
                return now
            if "yesterday" in s:
                return now - timedelta(days=1)
            m_d = re.search(r"(\d+)\s*d", s)
            if m_d:
                return now - timedelta(days=int(m_d.group(1)))
            m_h = re.search(r"(\d+)\s*h", s)
            if m_h:
                return now - timedelta(hours=int(m_h.group(1)))
            m_w = re.search(r"(\d+)\s*w", s)
            if m_w:
                return now - timedelta(weeks=int(m_w.group(1)))
            m_m = re.search(r"(\d+)\s*mo", s)
            if m_m:
                return now - timedelta(days=int(m_m.group(1)) * 30)
            return now

        seen_ids = set()
        page = 1
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        while len(posts) < max_jobs and page <= 50:
            sep = "&" if "?" in base_url else "?"
            target_page_url = f"{base_url}{sep}page={page}"
            try:
                import requests
                resp = requests.get(target_page_url, headers=headers, timeout=10)
                if resp.status_code != 200 or not resp.text:
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                card_anchors = soup.find_all("a", {"data-testid": "job-search-job-card-link"})
                if not card_anchors:
                    break

                page_new_jobs = 0
                for a in card_anchors:
                    if len(posts) >= max_jobs:
                        break
                    card = a.parent
                    href = a.get("href", "")
                    m_id = re.search(r"/job-detail/([a-f0-9-]+)", href)
                    if not m_id:
                        continue
                    job_uuid = m_id.group(1)
                    if job_uuid in seen_ids:
                        continue
                    seen_ids.add(job_uuid)

                    title_el = card.find("a", {"data-testid": "job-search-job-detail-link"})
                    title = title_el.text.strip() if title_el else ""
                    if not title or len(title) < 3:
                        aria_title = a.get("aria-label", "")
                        if "View Details for " in aria_title:
                            title = aria_title.replace("View Details for ", "").split("(")[0].strip()
                    if not title:
                        continue

                    co_el = card.find("p", {"data-testid": "job-card-company-name"})
                    company_name = co_el.text.strip() if co_el else "Dice Employer"

                    loc_p = card.find("p", class_=re.compile(r"text-foreground-light"))
                    loc_text = loc_p.text.strip() if loc_p else ""
                    raw_loc = loc_text
                    posted_at = datetime.now(timezone.utc)
                    if "•" in loc_text:
                        parts = [p.strip() for p in loc_text.split("•") if p.strip()]
                        if len(parts) >= 2:
                            raw_loc = parts[0]
                            posted_at = _parse_dice_relative_date(parts[1])
                        elif len(parts) == 1:
                            raw_loc = parts[0]

                    emp_el = card.find(id="employmentType-label")
                    emp_type = emp_el.text.strip() if emp_el else "Full-time"

                    job_url = f"https://www.dice.com/job-detail/{job_uuid}"
                    desc = f"{title} position at {company_name} located in {raw_loc}. Employment type: {emp_type}. Source: Dice ATS Platform."

                    raw_post = RawJobPost(
                        external_job_id=job_uuid,
                        title=title,
                        raw_description=desc,
                        raw_location=raw_loc,
                        job_url=job_url,
                        application_url=job_url,
                        posted_at=posted_at,
                        metadata={
                            "company_name": company_name,
                            "employment_type": emp_type,
                            "ats": "dice",
                            "source": "Dice",
                        },
                    )
                    posts.append(raw_post)
                    page_new_jobs += 1

                if page_new_jobs == 0:
                    break

                page += 1
            except Exception as e:
                logger.debug(f"Error fetching Dice jobs on page {page}: {e}")
                break

        return posts

    def _route_ats_url(self, url: str, max_jobs: int = 1000) -> Optional[List[RawJobPost]]:
        """Fast router that detects and executes direct ATS API endpoints for known ATS platforms."""
        if not url:
            return None
        u = url.strip()

        # 1. Greenhouse (handles boards.greenhouse.io, job-boards.greenhouse.io, and ?for=slug)
        if "greenhouse.io" in u:
            slug = None
            m_for = re.search(r"[?&]for=([a-zA-Z0-9_-]+)", u)
            if m_for:
                slug = m_for.group(1)
            if not slug:
                m = re.search(r"(?:boards|job-boards)\.greenhouse\.io/([^/?#]+)", u)
                if m and m.group(1) not in ("company", "embed"):
                    slug = m.group(1)
            if slug:
                jobs = self._fetch_greenhouse_api_jobs(slug, max_jobs=max_jobs)
                logger.info(f"Greenhouse API returned {len(jobs)} active jobs for {slug}")
                return jobs

        # 2. Lever
        if "jobs.lever.co/" in u:
            m = re.search(r"jobs\.lever\.co/([^/?#]+)", u)
            if m:
                jobs = self._fetch_lever_api_jobs(m.group(1), max_jobs=max_jobs)
                logger.info(f"Lever API returned {len(jobs)} active jobs for {m.group(1)}")
                return jobs

        # 3. Ashby
        if "jobs.ashbyhq.com/" in u:
            m = re.search(r"jobs\.ashbyhq\.com/([^/?#]+)", u)
            if m:
                jobs = self._fetch_ashby_api_jobs(m.group(1), max_jobs=max_jobs)
                logger.info(f"Ashby API returned {len(jobs)} active jobs for {m.group(1)}")
                return jobs

        # 4. SmartRecruiters
        if "smartrecruiters.com" in u:
            m = re.search(r"(?:careers|jobs)?\.smartrecruiters\.com/([^/?#]+)", u)
            if m:
                jobs = self._fetch_smartrecruiters_api_jobs(m.group(1), max_jobs=max_jobs)
                logger.info(f"SmartRecruiters API returned {len(jobs)} active jobs for {m.group(1)}")
                return jobs

        # 5. Workday CXS
        if "myworkdayjobs.com" in u:
            parsed = urlparse(u)
            host = parsed.netloc
            parts = [p for p in parsed.path.strip("/").split("/") if p]
            tenant = host.split(".")[0]
            board = None
            for p in parts:
                if not re.match(r"^[a-z]{2}(?:-[A-Z]{2})?$", p, re.IGNORECASE) and p not in ("job", "jobs", "wday", "cxs"):
                    board = p
                    break
            if not board and parts:
                board = parts[-1]
            if host and tenant and board:
                jobs = self._fetch_workday_cxs_jobs(host, tenant, board, max_jobs=max_jobs)
                logger.info(f"Workday CXS API returned {len(jobs)} active jobs for {tenant}/{board}")
                return jobs

        # 6. BambooHR
        if "bamboohr.com" in u:
            m = re.search(r"https?://([^.]+)\.bamboohr\.com", u)
            if m:
                jobs = self._fetch_bamboohr_api_jobs(m.group(1), max_jobs=max_jobs)
                logger.info(f"BambooHR API returned {len(jobs)} active jobs for {m.group(1)}")
                return jobs

        # 7. Jobvite
        if "jobvite.com" in u:
            jobs = self._fetch_jobvite_jobs(u, max_jobs=max_jobs)
            if jobs:
                logger.info(f"Jobvite returned {len(jobs)} active jobs for {u}")
                return jobs

        # 8. iCIMS
        if "icims.com" in u:
            jobs = self._fetch_icims_jobs(u, max_jobs=max_jobs)
            if jobs:
                logger.info(f"iCIMS returned {len(jobs)} active jobs for {u}")
                return jobs

        # 9. Oracle Taleo
        if "taleo.net" in u:
            jobs = self._fetch_taleo_jobs(u, max_jobs=max_jobs)
            if jobs:
                logger.info(f"Taleo returned {len(jobs)} active jobs for {u}")
                return jobs

        # 10. Dice Tech ATS Platform
        if "dice.com" in u:
            jobs = self._fetch_dice_jobs(u, max_jobs=max_jobs)
            if jobs:
                logger.info(f"Dice ATS platform returned {len(jobs)} active jobs for {u}")
                return jobs

        return None

    def fetch_jobs(self, source_url: str) -> List[RawJobPost]:
        """Navigates to the real company career URL and extracts live job postings."""
        return self.scrape_career_page(source_url, max_jobs=1000)

    def scrape_career_page(
        self, career_url: str, max_jobs: int = 1000
    ) -> List[RawJobPost]:
        """
        Extracts jobs from career page using fast ATS API routing first,
        falling back to Playwright headless browser for custom landing pages & SPAs.
        """
        # Fast direct ATS routing check
        direct_jobs = self._route_ats_url(career_url, max_jobs=max_jobs)
        if direct_jobs:
            return direct_jobs

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

                    # 1. Check if redirected to a recognized ATS platform
                    if page.url and page.url != career_url:
                        redirect_jobs = self._route_ats_url(page.url, max_jobs=max_jobs)
                        if redirect_jobs:
                            logger.info(f"Page redirected to ATS {page.url} -> {len(redirect_jobs)} jobs")
                            return redirect_jobs

                    # Trigger lazy-load / scroll safely
                    try:
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                        page.wait_for_timeout(800)
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(1200)
                    except Exception:
                        pass

                    # 2. Check for embedded ATS iframes (Greenhouse, Lever, Ashby, Workday, BambooHR, etc.)
                    try:
                        for frame in page.frames:
                            frame_api_jobs = self._route_ats_url(frame.url, max_jobs=max_jobs)
                            if frame_api_jobs:
                                logger.info(f"Extracted {len(frame_api_jobs)} jobs from ATS iframe API: {frame.url}")
                                job_posts.extend(frame_api_jobs)
                                break
                            if any(ats in frame.url for ats in [
                                "greenhouse.io", "lever.co", "ashbyhq.com", "myworkdayjobs.com",
                                "icims.com", "taleo.net", "smartrecruiters.com", "bamboohr.com", "jobvite.com"
                            ]):
                                logger.info(f"Detected embedded ATS iframe: {frame.url}")
                                job_posts.extend(self._extract_jobs_from_frame(frame, career_url))
                    except Exception:
                        pass

                    # 3. Check for prominent direct ATS links on landing page
                    if not job_posts:
                        try:
                            anchors = page.query_selector_all("a[href]")
                            for a in anchors:
                                href = (a.get_attribute("href") or "").strip()
                                if any(ats in href for ats in [
                                    "greenhouse.io", "lever.co", "myworkdayjobs.com", "ashbyhq.com",
                                    "icims.com", "taleo.net", "smartrecruiters.com", "bamboohr.com", "jobvite.com"
                                ]):
                                    full_ats_url = urljoin(career_url, href)
                                    ats_anchor_jobs = self._route_ats_url(full_ats_url, max_jobs=max_jobs)
                                    if ats_anchor_jobs:
                                        logger.info(f"Discovered ATS link on landing page: {full_ats_url} -> {len(ats_anchor_jobs)} jobs")
                                        job_posts.extend(ats_anchor_jobs)
                                        break
                        except Exception:
                            pass

                    # 4. If not extracted from ATS router/iframe, extract from rendered DOM
                    if not job_posts:
                        job_posts = self._extract_jobs_from_page(page, career_url, max_jobs)

                    # 5. If still 0 jobs, navigate to open openings subpage
                    if not job_posts:
                        subpage_link = self._find_openings_subpage(page, career_url)
                        if subpage_link and subpage_link != career_url and not subpage_link.endswith(career_url):
                            # Check if subpage link is an ATS URL
                            sub_ats_jobs = self._route_ats_url(subpage_link, max_jobs=max_jobs)
                            if sub_ats_jobs:
                                job_posts.extend(sub_ats_jobs)
                            else:
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

        logger.info(f"Extracted {len(job_posts)} jobs from {career_url}")
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
                if any(ats in href for ats in [
                    "greenhouse.io", "lever.co", "ashbyhq.com", "myworkdayjobs.com",
                    "icims.com", "taleo.net", "smartrecruiters.com", "bamboohr.com", "jobvite.com"
                ]):
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
        self, page: Page, base_url: str, max_jobs: int = 250
    ) -> List[RawJobPost]:
        """Extracts job elements and links using intelligent selectors."""
        html_content = page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        job_posts: List[RawJobPost] = []
        seen_urls = set()

        # Selector patterns commonly used on modern career pages & ATS systems:
        # Workday, Greenhouse, Lever, Ashby, SmartRecruiters, BambooHR, iCIMS, Taleo, Jobvite
        job_elements = page.query_selector_all(
            """
            [data-automation-id="jobTitle"],
            [data-automation-id="compositeHeader"] a,
            .opening a,
            .posting-title,
            .posting a,
            [data-qa="job-card"] a,
            .job-card a,
            .job-listing a,
            .job-item a,
            .iCIMS_JobsTable a,
            a.iCIMS_Anchor,
            .iCIMS_JobHeaderGroup a,
            span.titlelink a,
            .multiline-data-container a,
            a[id*="requisitionListInterface"],
            .jv-job-list a,
            .jv-job-card a,
            .BambooHR-ATS-Jobs-Item a,
            a[href*="/job/"],
            a[href*="/jobs/"],
            a[href*="/careers/job/"],
            a[href*="/careers/jobs/"],
            a[href*="/position/"],
            a[href*="/posting/"],
            a[href*="smartrecruiters.com"],
            a[href*="bamboohr.com/careers/"],
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
            links = frame.query_selector_all(
                """
                [data-automation-id="jobTitle"],
                .opening a,
                .posting a,
                .job-item a,
                .iCIMS_JobsTable a,
                span.titlelink a,
                .jv-job-list a,
                a[href*='/job/'],
                a[href*='/jobs/'],
                a[href*='/posting/']
                """
            )
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
        self, soup: BeautifulSoup, base_url: str, max_jobs: int = 250
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

