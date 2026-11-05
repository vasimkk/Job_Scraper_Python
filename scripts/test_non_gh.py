import requests
from urllib.parse import urlparse
from scraper_agent.db.connection import get_dict_cursor

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

with get_dict_cursor() as cur:
    cur.execute("""
        SELECT DISTINCT ON (split_part(job_url, '/', 3)) job_url, title
        FROM jobs
        WHERE job_url NOT LIKE '%greenhouse.io%'
    """)
    rows = cur.fetchall()

print(f"Testing non-greenhouse domains ({len(rows)} domains):")
for r in rows:
    try:
        resp = requests.get(r['job_url'], headers=headers, timeout=8)
        print(f"{urlparse(r['job_url']).netloc:<30} -> {resp.status_code} ({len(resp.content)} bytes)")
    except Exception as e:
        print(f"{urlparse(r['job_url']).netloc:<30} -> ERROR: {e}")

