import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import urllib.request
import json
import re

from scraper_agent.classifiers.location_parser import is_usa_location, detect_international_country

def test_company_yield(name, host, tenant, board, max_fetch=200):
    url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"
    us_count = 0
    total_count = 0
    
    # We can fetch 50 at a time
    for offset in range(0, max_fetch, 20):
        payload = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                postings = data.get("jobPostings", [])
                if not postings:
                    break
                total_in_board = data.get("total", 0)
                for item in postings:
                    total_count += 1
                    path = item.get("externalPath", "")
                    loc = item.get("locationsText", "")
                    
                    # Check US indicators in path or loc
                    is_us = False
                    if "/job/US-" in path or "/job/United-States" in path:
                        is_us = True
                    elif "US," in loc or "United States" in loc or "USA" in loc:
                        is_us = True
                    elif not detect_international_country(f"{path} {loc}"):
                        # check US states
                        if any(f"-{st}-" in path for st in ["CA", "NY", "TX", "WA", "MA", "IL", "CO", "FL", "VA", "NC", "GA", "NJ"]):
                            is_us = True
                    if is_us:
                        us_count += 1
        except Exception as e:
            print(f"Error {name}: {e}")
            break
            
    print(f"{name}: Scanned {total_count} postings -> {us_count} US jobs (Est. total in board: {total_in_board})")

candidates = [
    ("NVIDIA", "nvidia.wd5.myworkdayjobs.com", "nvidia", "NVIDIAExternalCareerSite"),
    ("Adobe", "adobe.wd5.myworkdayjobs.com", "adobe", "external_experienced"),
    ("Salesforce", "salesforce.wd12.myworkdayjobs.com", "salesforce", "External_Career_Site"),
    ("Humana", "humana.wd5.myworkdayjobs.com", "humana", "Humana_External_Career_Site"),
    ("Medtronic", "medtronic.wd1.myworkdayjobs.com", "medtronic", "MedtronicCareers"),
    ("Stryker", "stryker.wd1.myworkdayjobs.com", "stryker", "StrykerCareers"),
    ("Danaher", "danaher.wd1.myworkdayjobs.com", "danaher", "DanaherJobs"),
    ("Pfizer", "pfizer.wd1.myworkdayjobs.com", "pfizer", "PfizerCareers"),
    ("Amgen", "amgen.wd1.myworkdayjobs.com", "amgen", "Careers"),
    ("Boeing", "boeing.wd1.myworkdayjobs.com", "boeing", "EXTERNAL_CAREERS"),
    ("Travelers", "travelers.wd5.myworkdayjobs.com", "travelers", "External"),
    ("US Bank", "usbank.wd1.myworkdayjobs.com", "usbank", "US_Bank_Careers"),
]

for name, host, tenant, board in candidates[:6]:
    test_company_yield(name, host, tenant, board, max_fetch=60)
