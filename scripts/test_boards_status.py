import requests
from scraper_agent.db.connection import get_dict_cursor

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
with get_dict_cursor() as cur:
    cur.execute("""
        SELECT DISTINCT ON (c.name) c.name, j.job_url
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        WHERE j.job_url LIKE '%boards.greenhouse.io%'
          AND j.job_url NOT LIKE '%job-boards.greenhouse.io%'
    """)
    rows = cur.fetchall()
    print(f"Total boards.greenhouse.io non-job-boards companies: {len(rows)}")
    for r in rows[:15]:
        try:
            resp = requests.get(r['job_url'], headers=headers, timeout=5)
            print(f"{r['name'][:20]:<20} | status: {resp.status_code} | {r['job_url']}")
        except Exception as e:
            print(f"{r['name'][:20]:<20} | {e}")
