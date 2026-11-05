import urllib.request
import psycopg

conn = psycopg.connect("postgresql://postgres:root@localhost:5433/scraperAgent")
cur = conn.cursor()
cur.execute("""
    SELECT DISTINCT ON (c.name) c.name, j.job_url, c.career_url
    FROM jobs j
    JOIN companies c ON c.id = j.company_id
    WHERE j.job_url LIKE '%job-boards.greenhouse.io%';
""")
rows = cur.fetchall()
conn.close()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

print(f"Testing {len(rows)} companies with job-boards.greenhouse.io...")
for cname, url, career_url in rows:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            print(f"[OK 200] {cname}: {url}")
    except Exception as e:
        print(f"[FAILED {e}] {cname}: {url} (Company career: {career_url})")

