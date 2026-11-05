import sys
sys.path.insert(0, ".")
import psycopg
from scraper_agent.classifiers.location_parser import is_usa_location, parse_location

conn = psycopg.connect('postgresql://postgres:root@localhost:5433/scraperAgent')
cur = conn.cursor()

cur.execute("SELECT id, title, description, location, city, state, country FROM jobs;")
rows = cur.fetchall()

non_us_ids = []
updated_us_count = 0

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
    if not is_us:
        non_us_ids.append(jid)
    else:
        # Re-parse location to ensure clean city, state, country and no '/ Unspecified'
        clean_city, clean_state, clean_country, remote_type = parse_location(
            raw_location=loc,
            title=title,
            description=desc or "",
        )
        # Ensure country is United States
        clean_country = "United States"
        
        # Clean display location
        clean_loc = loc
        if not clean_loc or any(n in clean_loc.lower() for n in ["unspecified", "not specified", "n/a", "none"]):
            if clean_city and clean_state:
                clean_loc = f"{clean_city}, {clean_state}, United States"
            elif clean_state:
                clean_loc = f"{clean_state}, United States"
            elif remote_type == "REMOTE":
                clean_loc = "Remote, United States"
            else:
                clean_loc = "United States"

        cur.execute(
            """
            UPDATE jobs
            SET city = %s, state = %s, country = %s, location = %s, remote_type = %s
            WHERE id = %s
            """,
            (clean_city, clean_state, clean_country, clean_loc, remote_type, jid)
        )
        updated_us_count += 1

if non_us_ids:
    cur.execute("DELETE FROM jobs WHERE id = ANY(%s);", (non_us_ids,))
    conn.commit()

print(f"Purged {len(non_us_ids)} non-USA jobs.")
print(f"Normalized {updated_us_count} verified USA jobs.")

cur.execute("SELECT count(*) FROM jobs;")
remaining = cur.fetchone()[0]
print(f"Remaining verified USA jobs in DB: {remaining}")

# Check if any '/ Unspecified' remain
cur.execute("SELECT count(*) FROM jobs WHERE city LIKE '%Unspecified%' OR location LIKE '%Unspecified%';")
unspecified_cnt = cur.fetchone()[0]
print(f"Jobs with 'Unspecified': {unspecified_cnt}")

# Check country distribution
cur.execute("SELECT country, count(*) FROM jobs GROUP BY country;")
print("Country distribution:", cur.fetchall())

conn.close()

