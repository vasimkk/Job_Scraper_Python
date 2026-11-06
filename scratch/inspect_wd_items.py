import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import urllib.request
import json

def inspect_one(name, host, tenant, board):
    url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"
    payload = json.dumps({"appliedFacets": {}, "limit": 3, "offset": 0, "searchText": ""}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode())
        print(f"=== {name} ===")
        for item in data.get("jobPostings", []):
            print(f"Title: {item.get('title')}")
            print(f"Path: {item.get('externalPath')}")
            print(f"Loc: {item.get('locationsText')}")

inspect_one("Adobe", "adobe.wd5.myworkdayjobs.com", "adobe", "external_experienced")
inspect_one("Salesforce", "salesforce.wd12.myworkdayjobs.com", "salesforce", "External_Career_Site")
inspect_one("Humana", "humana.wd5.myworkdayjobs.com", "humana", "Humana_External_Career_Site")

