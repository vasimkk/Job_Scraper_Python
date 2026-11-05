from scraper_agent.db.connection import get_dict_cursor

with get_dict_cursor() as cur:
    cur.execute("SELECT COUNT(*) as total FROM jobs")
    total = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as cnt FROM jobs WHERE job_url LIKE '%job-boards.greenhouse.io%'")
    jb_cnt = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM jobs WHERE job_url LIKE '%boards.greenhouse.io%'")
    b_cnt = cur.fetchone()["cnt"]
    print(f"Total jobs: {total}")
    print(f"job-boards.greenhouse.io: {jb_cnt}")
    print(f"boards.greenhouse.io: {b_cnt}")

    cur.execute("""
        SELECT c.name, c.career_url, COUNT(j.id) as job_count
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        WHERE j.job_url LIKE '%job-boards.greenhouse.io%'
        GROUP BY c.name, c.career_url
        ORDER BY job_count DESC
    """)
    rows = cur.fetchall()
    print(f"Distinct companies with job-boards.greenhouse.io: {len(rows)}")
    for r in rows:
        print(f"  {r['name']} ({r['job_count']} jobs) -> {r['career_url']}")

