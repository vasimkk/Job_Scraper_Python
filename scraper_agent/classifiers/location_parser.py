import re
from typing import Tuple, Optional

US_STATE_CODES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
}

REMOTE_KEYWORDS = [r"\bremote\b", r"\bwork from home\b", r"\bwfh\b", r"\banywhere\b", r"\bvirtual\b"]
HYBRID_KEYWORDS = [r"\bhybrid\b", r"\bflexible\b"]
ON_SITE_KEYWORDS = [r"\bon-site\b", r"\bonsite\b", r"\bin-office\b"]

REMOTE_RX = [re.compile(p, re.IGNORECASE) for p in REMOTE_KEYWORDS]
HYBRID_RX = [re.compile(p, re.IGNORECASE) for p in HYBRID_KEYWORDS]
ON_SITE_RX = [re.compile(p, re.IGNORECASE) for p in ON_SITE_KEYWORDS]


def parse_location(raw_location: str, title: str = "", description: str = "") -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    """
    Parses a raw location string into (city, state, country, remote_type).
    remote_type will be one of: 'REMOTE', 'HYBRID', 'ON_SITE', 'UNKNOWN'
    """
    if not raw_location:
        raw_location = ""

    combined_text = f"{raw_location} {title}".strip()
    remote_type = "UNKNOWN"

    # Determine remote type
    if any(rx.search(combined_text) for rx in HYBRID_RX):
        remote_type = "HYBRID"
    elif any(rx.search(combined_text) for rx in REMOTE_RX):
        remote_type = "REMOTE"
    elif any(rx.search(combined_text) for rx in ON_SITE_RX):
        remote_type = "ON_SITE"
    else:
        # Default to REMOTE if raw_location mentions Remote, else ON_SITE if a specific physical location is given
        if "remote" in raw_location.lower():
            remote_type = "REMOTE"
        elif raw_location:
            remote_type = "ON_SITE"

    # Clean location text for city / state / country parsing
    clean_loc = re.sub(r"\(.*?\)", "", raw_location)
    clean_loc = re.sub(r"(?i)\b(remote|hybrid|onsite|on-site|office)\b", "", clean_loc)
    clean_loc = clean_loc.replace("-", ",").strip(" ,")

    parts = [p.strip() for p in clean_loc.split(",") if p.strip()]

    city = None
    state = None
    country = None

    if len(parts) == 1:
        part = parts[0]
        if part.upper() in ("USA", "US", "UNITED STATES"):
            country = "United States"
        elif part.upper() in US_STATE_CODES:
            state = part.upper()
            country = "United States"
        else:
            city = part
    elif len(parts) == 2:
        city = parts[0]
        second = parts[1].upper()
        if second in US_STATE_CODES:
            state = second
            country = "United States"
        else:
            country = parts[1]
    elif len(parts) >= 3:
        city = parts[0]
        second = parts[1].upper()
        if second in US_STATE_CODES:
            state = second
        else:
            state = parts[1]
        country = parts[2]

    # Global United States detection
    if not country and state and state.upper() in US_STATE_CODES:
        country = "United States"

    return city, state, country, remote_type

