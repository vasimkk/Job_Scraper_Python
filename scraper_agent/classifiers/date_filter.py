from datetime import datetime, timezone
from typing import Optional, Tuple


def get_freshness_cutoff() -> datetime:
    """
    Computes the cutoff datetime for the start of the previous month.
    For example:
      If today is 2026-11-04, the previous month is October 2026.
      Cutoff is 2026-10-01 00:00:00 UTC.
      Jobs posted in the current month (Nov 2026) or previous month (Oct 2026) are accepted.
      Jobs posted earlier (Sep 2026 or before) are filtered out as stale.
    """
    now = datetime.now(timezone.utc)
    if now.month == 1:
        prev_month = 12
        prev_year = now.year - 1
    else:
        prev_month = now.month - 1
        prev_year = now.year
    return datetime(prev_year, prev_month, 1, 0, 0, 0, tzinfo=timezone.utc)


def is_job_in_date_window(
    posted_at: Optional[datetime],
    cutoff: Optional[datetime] = None,
) -> Tuple[bool, datetime]:
    """
    Checks if a job's posted date falls within the current or previous month.
    Returns:
        (is_valid: bool, cutoff_date: datetime)
    """
    threshold = cutoff or get_freshness_cutoff()

    if posted_at is None:
        # If job posting has no explicit post date (e.g. some generic pages),
        # accept it as currently active
        return True, threshold

    # Ensure tz-aware comparison
    if posted_at.tzinfo is None:
        dt = posted_at.replace(tzinfo=timezone.utc)
    else:
        dt = posted_at.astimezone(timezone.utc)

    return dt >= threshold, threshold


def format_freshness_window_description() -> str:
    """Returns a readable string describing the active freshness window."""
    cutoff = get_freshness_cutoff()
    now = datetime.now(timezone.utc)
    return f"{cutoff.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')} (Current & Previous Month)"

