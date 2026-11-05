import requests
from scraper_agent.db.connection import get_dict_cursor

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

with get_dict_cursor() as cur:
    cur.execute("""
        SELECT DISTINCT ON (c.name) c.name, c.career_url, j.job_url, j.application_url
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        WHERE j.job_url LIKE '%job-boards.greenhouse.io%'
    """)
    samples = cur.fetchall()

print(f"Testing 1 job from each of the {len(samples)} companies:")
for s in samples:
    u = s["job_url"]
    # Test job-boards URL
    try:
        r1 = requests.get(u, headers=headers, timeout=6)
        code1 = r1.status_code
    except Exception as e:
        code1 = str(e)[:30]

    # Test boards.greenhouse.io replacement
    u_boards = u.replace("job-boards.greenhouse.io", "boards.greenhouse.io")
    try:
        r2 = requests.get(u_boards, headers=headers, timeout=6)
        code2 = r2.status_code
    except Exception as e:
        code2 = str(e)[:30]

    print(f"Company: {s['name'][:20]:<20} | job-boards: {code1} | boards: {code2} | {u}")

