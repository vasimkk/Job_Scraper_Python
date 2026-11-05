from urllib.parse import urlparse
from scraper_agent.db.connection import get_dict_cursor
from collections import Counter

with get_dict_cursor() as cur:
    cur.execute("SELECT id, job_url, application_url, title, company_id FROM jobs")
    jobs = cur.fetchall()

domains = Counter()
for j in jobs:
    d = urlparse(j["job_url"]).netloc
    domains[d] += 1

print(f"Total jobs: {len(jobs)}")
print("Domains breakdown:")
for domain, count in domains.most_common():
    print(f"  {domain:<40} : {count}")

