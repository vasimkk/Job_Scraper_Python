import sys
sys.path.insert(0, ".")
import urllib.request
import json
import requests
from scraper_agent.scrapers.base import BaseScraper

slug = "scaleai"
url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    jobs = data.get("jobs", [])
    print("Job[0] data:", json.dumps(jobs[0], indent=2))
