import psycopg

conn = psycopg.connect('postgresql://postgres:root@localhost:5433/scraperAgent')
cur = conn.cursor()

cur.execute('SELECT count(*) FROM companies;')
companies_count = cur.fetchone()[0]

cur.execute('SELECT count(*) FROM job_sources;')
sources_count = cur.fetchone()[0]

cur.execute('SELECT count(*) FROM jobs;')
jobs_count = cur.fetchone()[0]

cur.execute('SELECT country, count(*) FROM jobs GROUP BY country ORDER BY count(*) DESC;')
country_breakdown = cur.fetchall()

cur.execute("SELECT employment_type, count(*) FROM jobs GROUP BY employment_type;")
emp_breakdown = cur.fetchall()

print(f"Companies: {companies_count}, Sources: {sources_count}, Jobs: {jobs_count}")
print("Country Breakdown:", country_breakdown)
print("Employment Types:", emp_breakdown)

# Check any non-US jobs
cur.execute("""
SELECT id, title, location, city, state, country 
FROM jobs 
WHERE country != 'United States' 
   OR LOWER(location) LIKE '%india%' 
   OR LOWER(location) LIKE '%bengaluru%' 
   OR LOWER(location) LIKE '%bangalore%'
   OR LOWER(location) LIKE '%london%'
   OR LOWER(location) LIKE '%united kingdom%'
   OR LOWER(location) LIKE '%canada%'
   OR LOWER(location) LIKE '%tokyo%'
   OR LOWER(location) LIKE '%paris%'
   OR LOWER(location) LIKE '%germany%'
LIMIT 20;
""")
non_us = cur.fetchall()
print(f"Sample Non-US Jobs found in DB ({len(non_us)}):")
for r in non_us:
    print(r)

conn.close()
