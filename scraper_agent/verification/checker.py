import html
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

from scraper_agent.config import SCRAPER_CONFIG
from scraper_agent.verification.models import (
    VerificationAction,
    VerificationReason,
    JobVerificationDetails,
    JobVerificationResult,
)

logger = logging.getLogger(__name__)

# Explicit, unambiguous closed phrases
CLOSED_PHRASES = [
    r"\bjob\s+closed\b",
    r"\bjob\s+is\s+closed\b",
    r"\bthis\s+job\s+is\s+closed\b",
    r"\bposition\s+closed\b",
    r"\bthis\s+position\s+is\s+closed\b",
    r"\bposition\s+is\s+closed\b",
    r"\brequisition\s+closed\b",
    r"\bvacancy\s+is\s+closed\b",
    r"\bno\s+longer\s+accepting\s+applications\b",
    r"\bwe\s+are\s+no\s+longer\s+accepting\s+applications\b",
    r"\bnot\s+accepting\s+applications\b",
    r"\bapplications\s+(?:are|now)\s+closed\b",
    r"\bapplications\s+for\s+this\s+position\s+are\s+closed\b",
    r"\bapplications\s+are\s+no\s+longer\s+being\s+accepted\b",
    r"\bposition\s+filled\b",
    r"\bthis\s+position\s+has\s+been\s+filled\b",
    r"\bthis\s+role\s+has\s+been\s+filled\b",
    r"\bthe\s+position\s+has\s+been\s+filled\b",
    r"\bposition\s+is\s+filled\b",
    r"\brole\s+has\s+been\s+filled\b",
    r"\bposting\s+has\s+expired\b",
    r"\bthis\s+posting\s+has\s+expired\b",
    r"\bthis\s+job\s+has\s+expired\b",
    r"\bjob\s+has\s+expired\b",
    r"\blisting\s+has\s+expired\b",
    r"\bjob\s+vacancy\s+has\s+expired\b",
    r"\bjob\s+is\s+no\s+longer\s+available\b",
    r"\bthis\s+job\s+is\s+no\s+longer\s+available\b",
    r"\bthis\s+position\s+is\s+no\s+longer\s+available\b",
    r"\bposting\s+is\s+no\s+longer\s+available\b",
    r"\bno\s+longer\s+available\b",
    r"\bsorry,\s+but\s+we\s+can't\s+find\s+that\s+page\b",
    r"\bpage\s+not\s+found\b",
    r"\b404\s+not\s+found\b",
    r"\bthis\s+listing\s+has\s+been\s+archived\b",
    r"\bjob\s+requisition\s+is\s+no\s+longer\s+active\b",
    r"\bthis\s+job\s+is\s+not\s+active\b",
]

# Paths for general career portals where removed jobs redirect
CAREER_HOMEPAGE_PATHS = [
    r"^/?$",
    r"^/(?:en|us|careers|jobs|career|job|join-us|work-with-us|openings|search-jobs|search|opportunities)/?$",
    r"^/(?:en|us)/(?:careers|jobs|career|openings)/?$",
]

# Bot defense / CAPTCHA signatures
CAPTCHA_SIGNATURES = [
    "attention required! | cloudflare",
    "just a moment...",
    "cf-chl-bypass",
    "challenges.cloudflare.com",
    "turnstile",
    "cf-turnstile",
    "hcaptcha.com",
    "h-captcha",
    "google.com/recaptcha",
    "g-recaptcha",
    "datadome",
    "perimeterx",
    "kasada",
    "incapsula",
    "verify you are human",
    "please verify you are human",
    "security check to access",
    "checking your browser before accessing",
    "enable javascript and cookies to continue",
]

# Login wall path signatures
LOGIN_PATH_PATTERNS = [
    r"/(?:login|signin|sign-in|log-in|auth|authenticate|sso|saml)/?",
]

# Login text signatures
LOGIN_TEXT_SIGNATURES = [
    "please log in to continue",
    "sign in to apply",
    "please sign in to apply",
    "login required to view this position",
    "authentication required",
    "employee login required",
    "internal candidate sign in",
]

# Apply button patterns
APPLY_BUTTON_PATTERNS = [
    r"(?i)\bapply\b",
    r"(?i)\bapply\s+now\b",
    r"(?i)\bapply\s+for\s+this\s+(?:job|position|role)\b",
    r"(?i)\bstart\s+application\b",
    r"(?i)\bsubmit\s+application\b",
    r"(?i)\bapply\s+with\s+(?:linkedin|indeed)\b",
    r"(?i)\beasy\s+apply\b",
]

# Form field signatures
FORM_FIELD_SIGNATURES = [
    "resume", "cv", "first_name", "firstname", "last_name", "lastname",
    "email", "phone", "attachments", "cover_letter", "portfolio",
]


class JobAvailabilityChecker:
    """
    Evaluates job listings against the 6 Important Database Rules:
      1. URL Active + Job Open -> Keep job Active.
      2. URL Active + Job Closed -> Mark job Closed.
      3. URL Active + Status Unclear -> Keep existing status; do not mark Closed.
      4. URL Inaccessible -> Retry verification before changing status.
      5. CAPTCHA / Login / Network Error -> Do not change job status.
      6. Confirmed Closed -> Update the database to Closed.
    """

    def __init__(
        self,
        request_timeout: Optional[int] = None,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        user_agent: Optional[str] = None,
    ):
        self.request_timeout = request_timeout or SCRAPER_CONFIG.request_timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.user_agent = user_agent or SCRAPER_CONFIG.user_agent

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        })

    # =========================================================================
    # Rule 4: URL Inaccessible & Retry Mechanism
    # =========================================================================
    def fetch_with_retry(
        self,
        url: str,
        allow_redirects: bool = True,
    ) -> Tuple[Optional[requests.Response], int, Optional[Exception]]:
        """
        Executes HTTP request with automatic retries for transient errors (429, 5xx, timeouts).
        Returns: (response, retries_count, last_exception)
        """
        retries = 0
        last_exception = None

        while retries <= self.max_retries:
            try:
                resp = self.session.get(
                    url,
                    timeout=self.request_timeout,
                    allow_redirects=allow_redirects,
                )

                # Retry on rate limiting (429) or transient server errors (500, 502, 503, 504)
                if resp.status_code in (429, 500, 502, 503, 504) and retries < self.max_retries:
                    wait_time = self.backoff_seconds * (2 ** retries)
                    logger.debug(f"Transient HTTP {resp.status_code} for {url}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    retries += 1
                    continue

                return resp, retries, None

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
                last_exception = e
                if retries < self.max_retries:
                    wait_time = self.backoff_seconds * (2 ** retries)
                    logger.debug(f"Network error ({type(e).__name__}) for {url}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    retries += 1
                    continue
                else:
                    return None, retries, last_exception

        return None, retries, last_exception

    # =========================================================================
    # Rule 5: CAPTCHA / Login / Network Error Detection
    # =========================================================================
    @staticmethod
    def detect_captcha(resp: requests.Response) -> bool:
        """Detects if response is blocked by CAPTCHA, Turnstile, Cloudflare, or Bot Protection."""
        text = (resp.text or "").lower()
        if resp.status_code in (403, 503, 429):
            if any(sig in text for sig in CAPTCHA_SIGNATURES):
                return True
            # Check for Cloudflare specific block code
            if "error code: 1015" in text or "you are being rate limited" in text:
                return True
            if "access denied" in text and "cloudflare" in text:
                return True

        if "challenges.cloudflare.com" in text or "cf-turnstile" in text:
            if "verify you are human" in text or "security check" in text:
                return True

        if "just a moment..." in text and "cloudflare" in text:
            return True

        return False

    @staticmethod
    def detect_login_requirement(resp: requests.Response) -> bool:
        """Detects if response requires user authentication or was redirected to a login page."""
        if resp.status_code == 401:
            return True

        final_url = resp.url.lower()
        parsed = urlparse(final_url)
        for pattern in LOGIN_PATH_PATTERNS:
            if re.search(pattern, parsed.path):
                return True

        text = (resp.text or "").lower()
        if resp.status_code == 403 and any(sig in text for sig in LOGIN_TEXT_SIGNATURES):
            return True

        if "please log in to continue" in text or "login required to view this position" in text:
            return True

        return False

    @staticmethod
    def is_redirect_to_career_home(original_url: str, final_url: str) -> bool:
        """
        Detects if a deep job URL redirected away to a generic career homepage/portal,
        which indicates the job requisition was closed and removed.
        """
        orig_parsed = urlparse(original_url)
        final_parsed = urlparse(final_url)

        if orig_parsed.path == final_parsed.path:
            return False

        final_path = final_parsed.path.rstrip("/")
        if not final_path:
            final_path = "/"

        for pattern in CAREER_HOMEPAGE_PATHS:
            if re.match(pattern, final_path, re.IGNORECASE):
                # Ensure the original URL was an actual deep job post (at least 2 path segments)
                orig_parts = [p for p in orig_parsed.path.split("/") if p]
                if len(orig_parts) >= 2:
                    return True

        # Check for redirect to queryless /careers#open-roles
        if "/careers" in final_parsed.path.lower() and ("open-roles" in final_parsed.fragment or not final_parsed.path.strip("/").endswith(orig_parsed.path.strip("/").split("/")[-1])):
            orig_parts = [p for p in orig_parsed.path.split("/") if p]
            if len(orig_parts) >= 2 and any(p in orig_parsed.path.lower() for p in ["job", "jobs", "position", "posting"]):
                if not any(p in final_parsed.path.lower() for p in ["job", "jobs", "position", "posting"]):
                    return True

        return False

    # =========================================================================
    # Rule 2: Explicit Closed Message & Schema Check
    # =========================================================================
    @staticmethod
    def check_closed_message(soup: BeautifulSoup) -> Tuple[bool, Optional[str]]:
        """
        Scans visible page text (with scripts and styles stripped) for explicit closed messages:
        'Job Closed', 'No Longer Accepting Applications', 'Position Filled', etc.
        """
        # Create a clean text representation without <script>, <style>, <svg>, <noscript>
        # This prevents JavaScript router code or i18n dictionary objects from triggering false matches
        text_soup = BeautifulSoup(str(soup), "html.parser")
        for tag in text_soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            tag.decompose()

        clean_text = text_soup.get_text(separator=" ").lower()
        clean_text = re.sub(r"\s+", " ", clean_text)

        for pattern in CLOSED_PHRASES:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match:
                return True, match.group(0).strip()

        # Also inspect explicit alert/banner containers
        alert_elements = soup.find_all(
            ["div", "p", "span", "h1", "h2", "h3", "h4"],
            class_=re.compile(r"(?:alert|notice|closed|banner|warning|status|badge|expired)", re.I),
        )
        for elem in alert_elements:
            elem_text = elem.get_text(separator=" ").strip().lower()
            for pattern in CLOSED_PHRASES:
                if re.search(pattern, elem_text, re.IGNORECASE):
                    return True, elem_text[:100]

        return False, None

    @staticmethod
    def check_schema_expiration(soup: BeautifulSoup) -> Tuple[bool, Optional[str]]:
        """Checks Schema.org JobPosting metadata for an expired validThrough timestamp."""
        now = datetime.now(timezone.utc)
        scripts = soup.find_all("script", type=re.compile(r"ld\+json", re.I))
        for script in scripts:
            try:
                if not script.string:
                    continue
                data = json.loads(script.string.strip())
                postings = []
                if isinstance(data, dict):
                    if data.get("@graph"):
                        postings.extend([item for item in data["@graph"] if isinstance(item, dict)])
                    else:
                        postings.append(data)
                elif isinstance(data, list):
                    postings.extend([item for item in data if isinstance(item, dict)])

                for post in postings:
                    p_type = post.get("@type", "")
                    if isinstance(p_type, list):
                        p_type = " ".join(p_type)
                    if "jobposting" in p_type.lower():
                        valid_through = post.get("validThrough")
                        if valid_through:
                            try:
                                dt = datetime.fromisoformat(valid_through.replace("Z", "+00:00"))
                                if dt.tzinfo is None:
                                    dt = dt.replace(tzinfo=timezone.utc)
                                if dt < now:
                                    return True, f"Schema.org validThrough expired: {valid_through}"
                            except Exception:
                                pass
            except Exception:
                continue
        return False, None

    # =========================================================================
    # Rule 1 & 3: Active Indicators & Unclear Status Check
    # =========================================================================
    @staticmethod
    def check_apply_elements(soup: BeautifulSoup) -> Tuple[bool, bool, Optional[str]]:
        """
        Searches for an Apply button, apply link, or application form.
        Returns: (apply_found, apply_enabled, apply_text)
        """
        # Look for buttons or links
        candidates = soup.find_all(
            ["a", "button", "input"],
            attrs={"data-automation-id": re.compile(r"apply", re.I)},
        )
        if not candidates:
            candidates = soup.find_all(["a", "button", "input"])

        for elem in candidates:
            tag = elem.name.lower()
            text = ""
            if tag == "input":
                text = elem.get("value", "") or elem.get("placeholder", "") or elem.get("aria-label", "")
            else:
                text = elem.get_text(separator=" ").strip() or elem.get("aria-label", "") or elem.get("title", "")

            is_apply = False
            for pat in APPLY_BUTTON_PATTERNS:
                if re.search(pat, text):
                    is_apply = True
                    break

            elem_id = elem.get("id", "")
            elem_class = " ".join(elem.get("class", [])) if isinstance(elem.get("class"), list) else str(elem.get("class", ""))
            elem_href = elem.get("href", "")

            if not is_apply:
                if re.search(r"\bapply\b", elem_id, re.I) or re.search(r"\b(?:btn-apply|apply-button|apply-btn)\b", elem_class, re.I):
                    is_apply = True
                elif re.search(r"/(?:apply|application)(?:/|\?|$)", elem_href, re.I):
                    is_apply = True

            if is_apply:
                is_disabled = (
                    elem.has_attr("disabled")
                    or elem.get("aria-disabled") == "true"
                    or "disabled" in elem_class.lower()
                    or "is-disabled" in elem_class.lower()
                )
                return True, not is_disabled, text.strip()[:60]

        # Check for direct embedded application form
        forms = soup.find_all("form")
        for form in forms:
            f_inputs = " ".join([
                (inp.get("name") or "") + " " + (inp.get("id") or "") + " " + (inp.get("type") or "")
                for inp in form.find_all(["input", "textarea"])
            ]).lower()
            matches = sum(1 for sig in FORM_FIELD_SIGNATURES if sig in f_inputs)
            if matches >= 2:
                return True, True, "Embedded Application Form"

        return False, False, None

    # =========================================================================
    # Master Decision Engine: Strict 6 Database Rules
    # =========================================================================
    def verify_job(
        self,
        job_url: str,
        job_id: int = 0,
        title: Optional[str] = None,
        company_name: Optional[str] = None,
        external_job_id: Optional[str] = None,
    ) -> JobVerificationResult:
        """
        Executes verification strictly enforcing the user's database rules:
          - URL Active + Job Open: Keep job Active.
          - URL Active + Job Closed: Mark job Closed.
          - URL Active + Status Unclear: Keep existing status; do not mark Closed.
          - URL Inaccessible: Retry verification before changing status.
          - CAPTCHA/Login/Network Error: Do not change job status.
          - Confirmed Closed: Update the database to Closed.
        """
        details = JobVerificationDetails()

        # Sanitize URL
        if not job_url or not job_url.startswith("http"):
            details.notes = "Invalid or malformed URL string"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url or "",
                action=VerificationAction.MARK_CLOSED,
                reason=VerificationReason.URL_NOT_FOUND_404,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # Rule 4: URL Inaccessible -> Retry verification before changing status
        resp, retries, exc = self.fetch_with_retry(job_url)
        details.retries_performed = retries

        # Rule 5: Network Error after retries -> Do not change job status
        if exc is not None or resp is None:
            details.is_network_error = True
            details.notes = f"Network connection failed after {retries} retries: {exc}"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.NO_CHANGE,
                reason=VerificationReason.NETWORK_ERROR,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        details.status_code = resp.status_code
        details.final_url = resp.url

        # Rule 5: CAPTCHA / Bot Defense -> Do not change job status
        if self.detect_captcha(resp):
            details.is_captcha = True
            details.notes = "Blocked by CAPTCHA / Bot challenge (status untouched)"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.NO_CHANGE,
                reason=VerificationReason.CAPTCHA_BLOCKED,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # Rule 5: Login Requirement -> Do not change job status
        if self.detect_login_requirement(resp):
            details.is_login_required = True
            details.notes = "Requires authentication / login (status untouched)"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.NO_CHANGE,
                reason=VerificationReason.LOGIN_REQUIRED,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # Rule 5: Transient Server Error (5xx) or Rate Limit (429) -> Do not change job status
        if resp.status_code == 429:
            details.notes = "Rate limited (HTTP 429) after retries (status untouched)"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.NO_CHANGE,
                reason=VerificationReason.RATE_LIMITED,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        if 500 <= resp.status_code < 600:
            details.notes = f"Server error (HTTP {resp.status_code}) after retries (status untouched)"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.NO_CHANGE,
                reason=VerificationReason.SERVER_ERROR,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # Rule 6 / Confirmed Closed: 404 Not Found or 410 Gone after retries
        if resp.status_code == 404:
            details.url_opens = False
            details.notes = "URL returned HTTP 404 Not Found (confirmed closed)"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.MARK_CLOSED,
                reason=VerificationReason.URL_NOT_FOUND_404,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        if resp.status_code == 410:
            details.url_opens = False
            details.notes = "URL returned HTTP 410 Gone (confirmed closed)"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.MARK_CLOSED,
                reason=VerificationReason.URL_GONE_410,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # Any unexpected non-200 code (e.g. 403 without captcha text) -> Safety First: Do not change status
        if resp.status_code != 200:
            details.notes = f"Unexpected HTTP status {resp.status_code} (status untouched)"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.NO_CHANGE,
                reason=VerificationReason.NETWORK_ERROR,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # At this point, URL Active (HTTP 200)
        details.url_opens = True

        # Rule 2 / Confirmed Closed: Redirected away to generic career portal / home
        if self.is_redirect_to_career_home(job_url, resp.url):
            details.is_redirect_to_portal = True
            details.notes = f"Redirected to career homepage: {resp.url} (confirmed closed)"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.MARK_CLOSED,
                reason=VerificationReason.REDIRECTED_TO_CAREER_HOME,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        soup = BeautifulSoup(resp.text, "html.parser")

        # Rule 2 / Confirmed Closed: Explicit closed message on page
        has_closed, closed_text = self.check_closed_message(soup)
        details.closed_message_detected = has_closed
        details.matched_closed_phrase = closed_text
        if has_closed:
            details.notes = f"Confirmed closed message: '{closed_text}'"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.MARK_CLOSED,
                reason=VerificationReason.JOB_CLOSED_MESSAGE,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # Rule 2 / Confirmed Closed: Schema.org validThrough explicitly expired
        schema_expired, schema_msg = self.check_schema_expiration(soup)
        if schema_expired:
            details.notes = schema_msg or "Schema.org expiration"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.MARK_CLOSED,
                reason=VerificationReason.SCHEMA_EXPIRED,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # Check for active apply buttons and forms
        apply_found, apply_enabled, apply_label = self.check_apply_elements(soup)
        details.apply_button_found = apply_found
        details.apply_button_enabled = apply_enabled

        # Rule 1: URL Active + Job Open -> Keep job Active
        if apply_found and apply_enabled:
            details.job_status_active = True
            details.notes = f"URL active (200), apply button active ('{apply_label}')"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.KEEP_ACTIVE,
                reason=VerificationReason.JOB_OPEN,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # If apply button is explicitly found AND disabled -> Rule 2: Job Closed
        if apply_found and not apply_enabled:
            details.notes = f"Apply button is explicitly disabled ('{apply_label}')"
            return JobVerificationResult(
                job_id=job_id,
                job_url=job_url,
                action=VerificationAction.MARK_CLOSED,
                reason=VerificationReason.JOB_CLOSED_MESSAGE,
                details=details,
                title=title,
                company_name=company_name,
                external_job_id=external_job_id,
            )

        # Rule 3: URL Active + Status Unclear -> Keep existing status; do not mark Closed
        # (Page opened 200, no closed message, but dynamic layout or custom client-rendered elements)
        details.notes = "URL opens (200), no closed messages, status unclear (preserving status)"
        return JobVerificationResult(
            job_id=job_id,
            job_url=job_url,
            action=VerificationAction.KEEP_STATUS,
            reason=VerificationReason.STATUS_UNCLEAR,
            details=details,
            title=title,
            company_name=company_name,
            external_job_id=external_job_id,
        )

