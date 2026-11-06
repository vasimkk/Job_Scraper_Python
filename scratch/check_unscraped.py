import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scraper_agent.db.connection import get_db_connection
from scraper_agent.discovery.company_finder import VERIFIED_INDUSTRY_COMPANIES

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT c.name, COUNT(j.id) FROM companies c LEFT JOIN jobs j ON c.id = j.company_id GROUP BY c.name;")
        db_companies = dict(cur.fetchall())

print(f"Total companies in DB: {len(db_companies)}")

unscraped = []
low_jobs = []

for ind, comps in VERIFIED_INDUSTRY_COMPANIES.items():
    for c in comps:
        name = c["name"]
        cnt = db_companies.get(name, 0)
        if cnt == 0:
            unscraped.append((name, ind, c["career_url"]))
        elif cnt < 20:
            low_jobs.append((name, ind, cnt, c["career_url"]))

print(f"\nUnscraped companies ({len(unscraped)}):")
for name, ind, url in unscraped:
    print(f"  {name} ({ind}): {url}")

print(f"\nLow jobs (<20) companies ({len(low_jobs)}):")
for name, ind, cnt, url in low_jobs:
    print(f"  {name} ({ind}) - {cnt} jobs: {url}")

