import re
import requests
from urllib.parse import urlparse, urljoin
from scraper_agent.db.connection import get_dict_cursor

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

with get_dict_cursor() as cur:
    cur.execute("""
        SELECT DISTINCT ON (c.name) c.name, c.career_url, j.job_url
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        WHERE j.job_url LIKE '%greenhouse.io%'
    """)
    samples = cur.fetchall()

print(f"Testing {len(samples)} companies with career_url?gh_jid=...")
for s in samples:
    m = re.search(r"/jobs/(\d+)", s["job_url"])
    if not m:
        continue
    jid = m.group(1)
    base_career = s["career_url"]
    sep = "&" if "?" in base_career else "?"
    candidate_url = f"{base_career}{sep}gh_jid={jid}"
    try:
        resp = requests.get(candidate_url, headers=headers, timeout=6)
        print(f"{s['name'][:20]:<20} | status: {resp.status_code} ({len(resp.content)} bytes) | {candidate_url}")
    except Exception as e:
        print(f"{s['name'][:20]:<20} | error: {e}")
