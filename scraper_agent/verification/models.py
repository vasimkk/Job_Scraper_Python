from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any


class VerificationAction(str, Enum):
    """Action to take in the database based on the 6 Important Database Rules."""
    KEEP_ACTIVE = "KEEP_ACTIVE"        # URL Active + Job Open -> Keep job Active (status = OPEN)
    MARK_CLOSED = "MARK_CLOSED"        # URL Active + Job Closed / Confirmed Closed -> Mark job Closed (status = CLOSED)
    KEEP_STATUS = "KEEP_STATUS"        # URL Active + Status Unclear -> Keep existing status; do not mark Closed
    NO_CHANGE = "NO_CHANGE"            # CAPTCHA / Login / Network Error -> Do not change job status


class VerificationReason(str, Enum):
    """Categorized explanation for verification outcomes."""
    JOB_OPEN = "JOB_OPEN"
    JOB_CLOSED_MESSAGE = "JOB_CLOSED_MESSAGE"
    SCHEMA_EXPIRED = "SCHEMA_EXPIRED"
    REDIRECTED_TO_CAREER_HOME = "REDIRECTED_TO_CAREER_HOME"
    URL_NOT_FOUND_404 = "URL_NOT_FOUND_404"
    URL_GONE_410 = "URL_GONE_410"
    STATUS_UNCLEAR = "STATUS_UNCLEAR"
    CAPTCHA_BLOCKED = "CAPTCHA_BLOCKED"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    NETWORK_ERROR = "NETWORK_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    SERVER_ERROR = "SERVER_ERROR"


@dataclass
class JobVerificationDetails:
    """Detailed audit information collected during verification."""
    url_opens: bool = False
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    is_redirect_to_portal: bool = False
    closed_message_detected: bool = False
    matched_closed_phrase: Optional[str] = None
    job_status_active: bool = False
    apply_button_found: bool = False
    apply_button_enabled: bool = False
    application_form_active: bool = False
    is_captcha: bool = False
    is_login_required: bool = False
    is_network_error: bool = False
    retries_performed: int = 0
    notes: str = ""


@dataclass
class JobVerificationResult:
    """Outcome of verifying a single job posting against the Important Database Rules."""
    job_id: int
    job_url: str
    action: VerificationAction
    reason: VerificationReason
    details: JobVerificationDetails
    title: Optional[str] = None
    company_name: Optional[str] = None
    external_job_id: Optional[str] = None
    verified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def target_db_status(self) -> Optional[str]:
        """
        Database status to set.
        Returns 'CLOSED' only if action is MARK_CLOSED.
        Returns 'OPEN' if KEEP_ACTIVE.
        Returns None if KEEP_STATUS or NO_CHANGE (do not modify status).
        """
        if self.action == VerificationAction.MARK_CLOSED:
            return "CLOSED"
        elif self.action == VerificationAction.KEEP_ACTIVE:
            return "OPEN"
        return None  # KEEP_STATUS or NO_CHANGE -> preserve existing status untouched

