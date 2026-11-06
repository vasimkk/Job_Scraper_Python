import sys
sys.path.insert(0, ".")
from scraper_agent.classifiers.location_parser import US_STATE_NAMES_TO_CODE, US_STATE_CODES

test_locs = [
    "Michigan, Portage",
    "Florida, Weston 3365 Enterprise Avenue",
    "Arizona, Phoenix",
    "California, San Jose",
    "Irvine, California",
    "Detroit, Michigan",
    "Portage, Michigan",
]

for loc in test_locs:
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    city, state, country = None, None, None
    if len(parts) >= 2:
        p0_low = parts[0].lower()
        p1_low = parts[1].lower()
        if p0_low in US_STATE_NAMES_TO_CODE:
            # Workday pattern: "State, City"
            state = US_STATE_NAMES_TO_CODE[p0_low]
            city = parts[1].title()
            country = "United States"
        elif p1_low in US_STATE_NAMES_TO_CODE:
            # Standard pattern: "City, State"
            state = US_STATE_NAMES_TO_CODE[p1_low]
            city = parts[0].title()
            country = "United States"
    print(f"'{loc}' -> City: {city}, State: {state}, Country: {country}")
