import sys
sys.path.insert(0, ".")
import psycopg
from scraper_agent.classifiers.location_parser import is_usa_location, parse_location

conn = psycopg.connect('postgresql://postgres:root@localhost:5433/scraperAgent')
cur = conn.cursor()

cur.execute("SELECT id, title, description, location, city, state, country FROM jobs;")
rows = cur.fetchall()

usa_jobs = []
non_usa_jobs = []

for row in rows:
    jid, title, desc, loc, city, state, country = row
    is_us = is_usa_location(
        raw_location=loc,
        title=title,
        description=desc or "",
        city=city,
        state=state,
        country=country,
    )
    if is_us:
        usa_jobs.append(row)
    else:
        non_usa_jobs.append(row)

print(f"Total jobs evaluated: {len(rows)}")
print(f"USA jobs: {len(usa_jobs)}")
print(f"Non-USA jobs: {len(non_usa_jobs)}")

print("\nSample Non-USA jobs to be purged:")
for r in non_usa_jobs[:15]:
    print(f"ID {r[0]}: Title='{r[1][:40]}...', Loc='{r[3]}', City='{r[4]}', State='{r[5]}', Country='{r[6]}'")

conn.close()
