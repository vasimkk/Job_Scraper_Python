import re
from typing import Tuple, Optional, Dict, Set

# Comprehensive 50 US States + DC
US_STATE_CODES: Set[str] = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
}

# State name to 2-letter postal code mapping
US_STATE_NAMES_TO_CODE: Dict[str, str] = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC"
}

# Major US Cities and Tech Hubs mapped to their State Code
MAJOR_US_CITIES_TO_STATE: Dict[str, str] = {
    # California
    "san francisco": "CA", "san jose": "CA", "los angeles": "CA", "san diego": "CA",
    "sacramento": "CA", "oakland": "CA", "palo alto": "CA", "mountain view": "CA",
    "sunnyvale": "CA", "santa clara": "CA", "cupertino": "CA", "fremont": "CA",
    "irvine": "CA", "long beach": "CA", "pasadena": "CA", "hawthorne": "CA",
    "el segundo": "CA", "berkeley": "CA", "redwood city": "CA", "menlo park": "CA",
    "san mateo": "CA", "foster city": "CA", "glendale": "CA", "burbank": "CA",
    "santa monica": "CA", "culver city": "CA", "santa barbara": "CA",
    # Texas
    "austin": "TX", "dallas": "TX", "houston": "TX", "san antonio": "TX",
    "fort worth": "TX", "plano": "TX", "irving": "TX", "arlington": "TX",
    "frisco": "TX", "richardson": "TX", "el paso": "TX",
    # Washington
    "seattle": "WA", "bellevue": "WA", "redmond": "WA", "kirkland": "WA",
    "tacoma": "WA", "spokane": "WA",
    # New York
    "new york": "NY", "new york city": "NY", "nyc": "NY", "brooklyn": "NY",
    "manhattan": "NY", "queens": "NY", "albany": "NY", "buffalo": "NY",
    "rochester": "NY", "syracuse": "NY",
    # Massachusetts
    "boston": "MA", "cambridge": "MA", "waltham": "MA", "somerville": "MA",
    "burlington": "MA", "worcester": "MA",
    # Illinois
    "chicago": "IL", "naperville": "IL", "evanston": "IL", "schaumburg": "IL",
    # Colorado
    "denver": "CO", "boulder": "CO", "colorado springs": "CO", "aurora": "CO",
    "fort collins": "CO", "louisville": "CO", "englewood": "CO",
    # Georgia
    "atlanta": "GA", "alpharetta": "GA", "marietta": "GA", "duluth": "GA",
    # Virginia & DC & Maryland
    "washington": "DC", "washington dc": "DC", "reston": "VA", "arlington": "VA",
    "mclean": "VA", "tysons": "VA", "herndon": "VA", "richmond": "VA",
    "alexandria": "VA", "chantilly": "VA", "bethesda": "MD", "rockville": "MD",
    "silver spring": "MD", "baltimore": "MD", "columbia": "MD",
    # North Carolina
    "raleigh": "NC", "durham": "NC", "charlotte": "NC", "cary": "NC",
    "chapel hill": "NC", "greensboro": "NC", "research triangle park": "NC",
    # Arizona
    "phoenix": "AZ", "scottsdale": "AZ", "tempe": "AZ", "chandler": "AZ",
    "mesa": "AZ", "tucson": "AZ",
    # Utah
    "salt lake city": "UT", "lehi": "UT", "provo": "UT", "sandy": "UT",
    "draper": "UT", "ogden": "UT",
    # Minnesota
    "minneapolis": "MN", "st. paul": "MN", "saint paul": "MN", "bloomington": "MN",
    # Pennsylvania
    "philadelphia": "PA", "pittsburgh": "PA", "king of prussia": "PA",
    # Michigan
    "detroit": "MI", "ann arbor": "MI", "grand rapids": "MI",
    # Ohio
    "columbus": "OH", "cleveland": "OH", "cincinnati": "OH", "dayton": "OH",
    # Tennessee
    "nashville": "TN", "memphis": "TN", "knoxville": "TN", "chattanooga": "TN",
    # Florida
    "miami": "FL", "tampa": "FL", "orlando": "FL", "jacksonville": "FL",
    "fort lauderdale": "FL", "st. petersburg": "FL", "boca raton": "FL",
    # Indiana
    "indianapolis": "IN", "carmel": "IN",
    # Oregon
    "portland": "OR", "hillsboro": "OR", "beaverton": "OR", "eugene": "OR",
    # Nevada
    "las vegas": "NV", "reno": "NV", "henderson": "NV",
    # Missouri
    "st. louis": "MO", "saint louis": "MO", "kansas city": "MO",
    # Wisconsin
    "milwaukee": "WI", "madison": "WI",
    # Connecticut
    "hartford": "CT", "stamford": "CT", "new haven": "CT", "greenwich": "CT",
    # New Jersey
    "newark": "NJ", "jersey city": "NJ", "princeton": "NJ", "hoboken": "NJ",
}

# Comprehensive International Countries, Territories, and Non-USA Cities
INTERNATIONAL_LOCATIONS: Dict[str, str] = {
    # India
    "india": "India", "bengaluru": "India", "bangalore": "India", "hyderabad": "India",
    "pune": "India", "mumbai": "India", "delhi": "India", "new delhi": "India",
    "gurgaon": "India", "gurugram": "India", "noida": "India", "chennai": "India",
    "kolkata": "India", "ahmedabad": "India", "karnataka": "India", "telangana": "India",
    "maharashtra": "India", "tamil nadu": "India",
    # United Kingdom
    "united kingdom": "United Kingdom", "uk": "United Kingdom", "england": "United Kingdom",
    "great britain": "United Kingdom", "london": "United Kingdom", "manchester": "United Kingdom",
    "edinburgh": "United Kingdom", "birmingham": "United Kingdom", "bristol": "United Kingdom",
    "scotland": "United Kingdom", "wales": "United Kingdom", "northern ireland": "United Kingdom",
    "cambridge, uk": "United Kingdom", "oxford, uk": "United Kingdom",
    # Canada
    "canada": "Canada", "toronto": "Canada", "vancouver": "Canada", "montreal": "Canada",
    "ottawa": "Canada", "calgary": "Canada", "waterloo": "Canada", "ontario": "Canada",
    "british columbia": "Canada", "quebec": "Canada",
    # Germany
    "germany": "Germany", "berlin": "Germany", "munich": "Germany", "frankfurt": "Germany",
    "hamburg": "Germany", "cologne": "Germany", "stuttgart": "Germany",
    # France
    "france": "France", "paris": "France", "lyon": "France", "marseille": "France", "toulouse": "France",
    # Ireland
    "ireland": "Ireland", "dublin": "Ireland", "cork": "Ireland", "galway": "Ireland",
    # Netherlands
    "netherlands": "Netherlands", "amsterdam": "Netherlands", "rotterdam": "Netherlands", "utrecht": "Netherlands",
    # Switzerland
    "switzerland": "Switzerland", "zurich": "Switzerland", "geneva": "Switzerland", "lausanne": "Switzerland",
    # Japan
    "japan": "Japan", "tokyo": "Japan", "osaka": "Japan", "kyoto": "Japan", "yokohama": "Japan",
    # Singapore
    "singapore": "Singapore",
    # Australia
    "australia": "Australia", "sydney": "Australia", "melbourne": "Australia", "brisbane": "Australia", "perth": "Australia",
    # Israel
    "israel": "Israel", "tel aviv": "Israel", "jerusalem": "Israel", "haifa": "Israel", "herzliya": "Israel",
    # Brazil
    "brazil": "Brazil", "são paulo": "Brazil", "sao paulo": "Brazil", "rio de janeiro": "Brazil",
    # Mexico
    "mexico": "Mexico", "mexico city": "Mexico", "guadalajara": "Mexico", "monterrey": "Mexico",
    # Poland
    "poland": "Poland", "warsaw": "Poland", "krakow": "Poland", "wroclaw": "Poland",
    # Spain
    "spain": "Spain", "madrid": "Spain", "barcelona": "Spain",
    # Italy
    "italy": "Italy", "rome": "Italy", "milan": "Italy",
    # Sweden
    "sweden": "Sweden", "stockholm": "Sweden", "gothenburg": "Sweden",
    # China & Taiwan
    "china": "China", "beijing": "China", "shanghai": "China", "shenzhen": "China",
    "taiwan": "Taiwan", "taipei": "Taiwan",
    # South Korea
    "south korea": "South Korea", "seoul": "South Korea",
    # UAE
    "united arab emirates": "United Arab Emirates", "uae": "United Arab Emirates", "dubai": "United Arab Emirates",
    # Argentina, Colombia, Chile
    "argentina": "Argentina", "buenos aires": "Argentina",
    "colombia": "Colombia", "bogota": "Colombia",
    "chile": "Chile", "santiago": "Chile",
    "costa rica": "Costa Rica",
    # Philippines, Vietnam, Indonesia
    "philippines": "Philippines", "manila": "Philippines",
    "vietnam": "Vietnam", "ho chi minh": "Vietnam",
    "indonesia": "Indonesia", "jakarta": "Indonesia",
    "new zealand": "New Zealand", "auckland": "New Zealand",
}

# Non-USA regional indicators
INTERNATIONAL_REGIONAL_KEYWORDS = {
    "emea", "apac", "latam", "europe", "asia", "latin america", "middle east",
    "in-karnataka", "in-telangana", "in-maharashtra", "in-tamil",
}

REMOTE_KEYWORDS = [r"\bremote\b", r"\bwork from home\b", r"\bwfh\b", r"\banywhere\b", r"\bvirtual\b", r"\btelecommute\b"]
HYBRID_KEYWORDS = [r"\bhybrid\b", r"\bflexible\b"]
ON_SITE_KEYWORDS = [r"\bon-site\b", r"\bonsite\b", r"\bin-office\b", r"\boffice-based\b"]

REMOTE_RX = [re.compile(p, re.IGNORECASE) for p in REMOTE_KEYWORDS]
HYBRID_RX = [re.compile(p, re.IGNORECASE) for p in HYBRID_KEYWORDS]
ON_SITE_RX = [re.compile(p, re.IGNORECASE) for p in ON_SITE_KEYWORDS]

# Words that indicate a placeholder or non-geographic string
NOISE_LOCATION_WORDS = {
    "unspecified", "not specified", "n/a", "none", "unknown",
    "multiple locations", "various", "anywhere", "tbd", "flexible",
    "remote", "hybrid", "onsite", "on-site", "office", "locations",
    "all locations", "multiple", "nationwide", "united states", "usa", "us"
}


def _clean_location_string(raw: str) -> str:
    """Removes parenthetical noise, ATS prefixes, and extra punctuation."""
    if not raw:
        return ""
    # Reject survey/form questions scraped as location
    if "?" in raw or any(q in raw.lower() for q in ["where are you", "what is your", "are you located"]):
        return ""

    # Normalize Workday/ATS patterns like US-CA-Campbell-254 or US-TX-Austin
    m_wd = re.match(r"^(?:US|USA)-([A-Za-z]{2})-([A-Za-z0-9_-]+)$", raw.strip(), re.IGNORECASE)
    if m_wd:
        st = m_wd.group(1).upper()
        city_raw = re.sub(r"-\d+$", "", m_wd.group(2)).replace("-", " ").strip().title()
        return f"{city_raw}, {st}, United States"

    # Normalize Indian ATS patterns like IN-Karnataka-Bangalore or IN-HR-Gurugram-418
    m_in = re.match(r"^IN-([A-Za-z0-9_-]+)", raw.strip(), re.IGNORECASE)
    if m_in:
        part = re.sub(r"-\d+$", "", m_in.group(1)).replace("-", ", ").strip().title()
        return f"{part}, India"

    # Replace bullet points and symbols
    cleaned = raw.replace("•", ",").replace("·", ",")
    # Strip parentheses like (Remote), (Hybrid)
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    # Strip brackets
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    # Replace slashes and pipes with commas
    cleaned = cleaned.replace("/", " ").replace("|", " ").replace(";", ",")
    # Normalize spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,-")
    return cleaned


def detect_international_country(text: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Checks if text points to an international (non-USA) country or city.
    Returns (CountryName, CityName) if matched, else None.
    """
    if not text:
        return None
    text_lower = text.lower()

    # Direct keyword search against known foreign locations
    for loc_key, country_name in INTERNATIONAL_LOCATIONS.items():
        if re.search(rf"\b{re.escape(loc_key)}\b", text_lower):
            city_name = loc_key.title() if loc_key != country_name.lower() else None
            return country_name, city_name

    for reg in INTERNATIONAL_REGIONAL_KEYWORDS:
        if re.search(rf"\b{re.escape(reg)}\b", text_lower):
            return reg.upper(), None

    return None


def is_usa_location(
    raw_location: str,
    title: str = "",
    description: str = "",
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
) -> bool:
    """
    Returns True ONLY if the job is physically in the United States or is US-Remote.
    Returns False for international locations (e.g. Bengaluru India, London UK, Canada, Paris, EMEA, etc.).
    """
    raw_lower = (raw_location or "").lower()
    title_lower = (title or "").lower()
    combined_header = f"{raw_lower} {title_lower}".replace("•", " ").replace("·", " ")
    desc_header = (description or "")[:1500].lower().replace("•", " ").replace("·", " ")

    # 1. Definite Non-USA check in raw location, title, parsed city, or JD header
    # If explicitly flagged with foreign city/country, immediately reject
    int_info = detect_international_country(combined_header)
    if not int_info:
        int_info = detect_international_country(desc_header)

    if int_info:
        # Check if it also explicitly mentions USA (e.g. "San Francisco, CA • London, UK")
        # If it specifically names non-US like London, England or Bengaluru, India alone:
        if not re.search(r"\b(?:united states|usa|u\.s\.|california|texas|new york|washington|florida)\b", combined_header):
            return False
        # If title or JD specifically targeted international (e.g. "Technical Quality Specialist (Bengaluru, India)"):
        if any(f"({k}" in title_lower or f" {k})" in title_lower for k in INTERNATIONAL_LOCATIONS.keys()):
            return False
        if any(k in desc_header[:300] for k in ["bengaluru", "hyderabad", "karnataka", "telangana", "pune", "maharashtra", "india", "london", "canada"]):
            return False

    if country and country != "United States":
        return False

    if city and city.lower() in INTERNATIONAL_LOCATIONS and city.lower() not in MAJOR_US_CITIES_TO_STATE:
        return False

    # 2. Definite Positive USA confirmation
    # State is valid US state code
    if state and state.upper() in US_STATE_CODES:
        return True

    # City matches a known major US city
    if city and city.lower() in MAJOR_US_CITIES_TO_STATE:
        return True

    # Explicit US Remote keywords
    if re.search(
        r"\b(?:remote\s*[-–—/,]?\s*(?:us|usa|united states)|(?:us|usa|united states)\s*[-–—/,]?\s*remote)\b|\bremote\s*\(\s*(?:us|usa|united states)\s*\)",
        combined_header,
    ):
        return True

    # Raw location contains "United States", "USA", or "U.S."
    if re.search(r"\b(?:united states|usa|u\.s\.|u\.s\.a\.)\b", raw_lower):
        # Ensure it doesn't also say "London, United Kingdom" or "India"
        if not int_info:
            return True

    # Check for City, ST in raw location (e.g. "San Francisco, CA" or "Austin, TX")
    if re.search(r"\b[A-Za-z\s.-]+,\s*[A-Z]{2}\b", raw_location or ""):
        m = re.findall(r"\b([A-Z]{2})\b", raw_location or "")
        if any(code in US_STATE_CODES for code in m):
            return True

    # Check for ATS pattern like US-CA-Campbell or USA-TX
    if re.search(r"\b(?:us|usa)-([a-z]{2})\b", raw_lower):
        m = re.search(r"\b(?:us|usa)-([a-z]{2})\b", raw_lower)
        if m and m.group(1).upper() in US_STATE_CODES:
            return True

    # Check description snippet for US state indicators
    desc_snippet = (description or "")[:2000].lower()
    if re.search(r"\b(?:location|office|based in):\s*[a-z\s.-]+,\s*([a-z]{2})\b", desc_snippet):
        m = re.search(r"\b(?:location|office|based in):\s*[a-z\s.-]+,\s*([a-z]{2})\b", desc_snippet)
        if m and m.group(1).upper() in US_STATE_CODES:
            return True

    # Check description snippet for strong US indicators (US work authorization, 401(k), United States)
    if not int_info:
        if re.search(r"\b(?:authorized to work in the (?:us|u\.s\.|united states)|work authorization in the (?:us|u\.s\.|united states)|401\(k\)|united states)\b", desc_snippet):
            if not detect_international_country(desc_snippet[:400]):
                return True

    # Default to False: Only scrape confirmed USA locations!
    return False


def _extract_from_text(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Scans text (e.g. JD snippet) for structured City, State or Location: patterns."""
    if not text:
        return None, None, None

    # Check for international indicator in text
    int_info = detect_international_country(text[:500])
    if int_info:
        country_name, city_name = int_info
        return city_name, None, country_name

    # Pattern 1: "Location: City, State" or "Based in City, State"
    prefix_rx = re.search(
        r"(?:location|based in|office in|located in|facility in|site):\s*([A-Za-z\s.-]+,\s*[A-Za-z]{2,})",
        text,
        re.IGNORECASE,
    )
    if prefix_rx:
        cand = prefix_rx.group(1).strip()
        parts = [p.strip() for p in cand.split(",") if p.strip()]
        if len(parts) >= 2:
            city_cand = parts[0]
            state_cand = parts[1].upper()
            if state_cand in US_STATE_CODES:
                return city_cand.title(), state_cand, "United States"
            if parts[1].lower() in US_STATE_NAMES_TO_CODE:
                return city_cand.title(), US_STATE_NAMES_TO_CODE[parts[1].lower()], "United States"

    # Pattern 2: "City, ST" (e.g. "San Francisco, CA" or "Hawthorne, CA")
    city_st_matches = re.findall(r"\b([A-Z][a-zA-Z\s.-]{2,25}),\s*([A-Z]{2})\b", text)
    for city_cand, st_cand in city_st_matches:
        city_clean = city_cand.strip().lower()
        if st_cand in US_STATE_CODES and city_clean not in NOISE_LOCATION_WORDS:
            return city_cand.strip().title(), st_cand, "United States"

    # Pattern 3: "City, StateName" (e.g. "San Francisco, California")
    state_names_pattern = "|".join(re.escape(s) for s in US_STATE_NAMES_TO_CODE.keys())
    state_name_rx = re.search(
        rf"\b([A-Z][a-zA-Z\s.-]{{2,25}}),\s*({state_names_pattern})\b",
        text,
        re.IGNORECASE,
    )
    if state_name_rx:
        city_cand = state_name_rx.group(1).strip().title()
        st_name = state_name_rx.group(2).strip().lower()
        st_code = US_STATE_NAMES_TO_CODE.get(st_name)
        if city_cand.lower() not in NOISE_LOCATION_WORDS and st_code:
            return city_cand, st_code, "United States"

    # Pattern 4: Check if any known major US city appears in the text
    text_lower = text[:3000].lower()
    for city_name, st_code in MAJOR_US_CITIES_TO_STATE.items():
        if re.search(rf"\b{re.escape(city_name)}\b", text_lower):
            return city_name.title(), st_code, "United States"

    return None, None, None


def parse_location(
    raw_location: str,
    title: str = "",
    description: str = "",
    default_country: str = "United States",
) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    """
    Parses location into (city, state, country, remote_type).
    Guarantees:
      - Accurately detects non-USA countries (India, UK, Canada, France, etc.) and does NOT falsely set them to 'United States'.
      - city is NEVER '/ Unspecified', 'Unspecified', 'Remote', or placeholder noise.
      - state is a valid 2-letter postal code (e.g. 'CA', 'TX', 'NY') or None.
      - remote_type is one of: 'REMOTE', 'HYBRID', 'ON_SITE', 'UNKNOWN'.
    """
    raw_str = (raw_location or "").strip()
    title_str = (title or "").strip()
    desc_str = (description or "").strip()

    combined_for_remote = f"{raw_str} {title_str} {desc_str[:1500]}".strip()

    # 1. Determine remote type
    remote_type = "UNKNOWN"
    if any(rx.search(combined_for_remote) for rx in HYBRID_RX):
        remote_type = "HYBRID"
    elif any(rx.search(combined_for_remote) for rx in REMOTE_RX):
        remote_type = "REMOTE"
    elif any(rx.search(combined_for_remote) for rx in ON_SITE_RX):
        remote_type = "ON_SITE"
    else:
        if "remote" in raw_str.lower():
            remote_type = "REMOTE"
        elif raw_str:
            remote_type = "ON_SITE"

    # 2. Check for International (Non-USA) Location FIRST
    int_info = detect_international_country(f"{raw_str} {title_str}")
    if int_info:
        country_detected, city_detected = int_info
        # If it's multi-location like "San Francisco, CA • London, England", check for US part
        if not re.search(r"\b(?:united states|usa|u\.s\.|california|texas|new york|washington)\b", raw_str.lower()):
            city = city_detected or raw_str.split(",")[0].strip()
            return city, None, country_detected, remote_type

    # 3. Clean location text
    cleaned = _clean_location_string(raw_str)
    # Remove words like remote, hybrid, onsite from location string
    cleaned = re.sub(r"(?i)\b(remote|hybrid|onsite|on-site|office|workplace)\b", "", cleaned).strip(" ,-")

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = default_country

    parts = [p.strip() for p in cleaned.split(",") if p.strip()]

    # Filter out empty or noise parts
    filtered_parts = []
    for p in parts:
        clean_p = p.strip(" /|-").strip()
        if clean_p.lower() not in NOISE_LOCATION_WORDS and len(clean_p) > 1:
            filtered_parts.append(clean_p)

    if len(filtered_parts) == 1:
        part = filtered_parts[0]
        part_upper = part.upper()
        part_lower = part.lower()

        if part_upper in ("USA", "US", "UNITED STATES"):
            country = "United States"
        elif part_upper in US_STATE_CODES:
            state = part_upper
            country = "United States"
        elif part_lower in US_STATE_NAMES_TO_CODE:
            state = US_STATE_NAMES_TO_CODE[part_lower]
            country = "United States"
        elif part_lower in MAJOR_US_CITIES_TO_STATE:
            city = part.title()
            state = MAJOR_US_CITIES_TO_STATE[part_lower]
            country = "United States"
        elif part_lower in INTERNATIONAL_LOCATIONS:
            country = INTERNATIONAL_LOCATIONS[part_lower]
            city = part.title() if part_lower != country.lower() else None
        else:
            m = re.match(r"^([A-Za-z\s.-]+)\s+([A-Z]{2})$", part)
            if m and m.group(2) in US_STATE_CODES:
                city = m.group(1).strip().title()
                state = m.group(2)
                country = "United States"
            else:
                city = part.title()

    elif len(filtered_parts) >= 2:
        cand_city = filtered_parts[0].strip().title()
        second = filtered_parts[1].strip()
        second_upper = second.upper()
        second_lower = second.lower()

        if second_upper in US_STATE_CODES:
            city = cand_city
            state = second_upper
            country = "United States"
        elif second_lower in US_STATE_NAMES_TO_CODE:
            city = cand_city
            state = US_STATE_NAMES_TO_CODE[second_lower]
            country = "United States"
        elif second_upper in ("USA", "US", "UNITED STATES"):
            city = cand_city
            country = "United States"
            if cand_city.lower() in MAJOR_US_CITIES_TO_STATE:
                state = MAJOR_US_CITIES_TO_STATE[cand_city.lower()]
        elif second_lower in INTERNATIONAL_LOCATIONS:
            country = INTERNATIONAL_LOCATIONS[second_lower]
            city = cand_city
        else:
            city = cand_city
            if len(filtered_parts) >= 3:
                third = filtered_parts[2].strip()
                if third.upper() in US_STATE_CODES:
                    state = third.upper()
                    country = "United States"
                elif third.lower() in US_STATE_NAMES_TO_CODE:
                    state = US_STATE_NAMES_TO_CODE[third.lower()]
                    country = "United States"
                elif third.upper() in ("USA", "US", "UNITED STATES"):
                    country = "United States"
                elif third.lower() in INTERNATIONAL_LOCATIONS:
                    country = INTERNATIONAL_LOCATIONS[third.lower()]

    # 4. If city or state could not be found from raw_location, extract from description & title
    if not city and not state:
        c_desc, s_desc, co_desc = _extract_from_text(f"{desc_str} {title_str}")
        if c_desc or s_desc:
            city = c_desc
            state = s_desc
            country = co_desc or default_country
    elif city and not state and city.lower() in MAJOR_US_CITIES_TO_STATE:
        state = MAJOR_US_CITIES_TO_STATE[city.lower()]

    # 5. Strict Sanitization: city must NEVER be a noise word, slash, or placeholder
    if city:
        city_clean = city.strip(" /|-,").strip()
        if (
            not city_clean
            or city_clean.lower() in NOISE_LOCATION_WORDS
            or "/" in city_clean
            or city_clean.lower().startswith("unspecified")
        ):
            city = None
        else:
            city = city_clean

    if state:
        state_clean = state.strip(" /|-,").strip().upper()
        if state_clean not in US_STATE_CODES:
            state = None
        else:
            state = state_clean

    if not country:
        country = default_country

    return city, state, country, remote_type
