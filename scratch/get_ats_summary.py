import sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scraper_agent.db.connection import get_db_connection

def detect_ats(job_url, app_url, source_url, ext_id):
    combined = f"{job_url} {app_url} {source_url}".lower()
    eid = (ext_id or "").lower()
    if "greenhouse.io" in combined or "gh_jid" in combined or eid.startswith("gh_"):
        return "Greenhouse"
    if "ashbyhq.com" in combined or eid.startswith("ashby_"):
        return "Ashby"
    if "myworkdayjobs.com" in combined or eid.startswith("wd_") or "workday" in combined:
        return "Workday"
    if "smartrecruiters.com" in combined or eid.startswith("sr_"):
        return "SmartRecruiters"
    if "lever.co" in combined or eid.startswith("lever_"):
        return "Lever"
    if "jobvite.com" in combined:
        return "Jobvite"
    if "taleo.net" in combined:
        return "Taleo"
    if "bamboohr.com" in combined:
        return "BambooHR"
    if "icims.com" in combined:
        return "iCIMS"
    return "Direct Career Site / Custom ATS"

with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                j.id,
                j.external_job_id,
                j.job_url,
                j.application_url,
                c.name AS company_name,
                c.career_url,
                c.industry,
                s.source_url
            FROM jobs j
            JOIN companies c ON j.company_id = c.id
            LEFT JOIN job_sources s ON j.source_id = s.id;
        """)
        rows = cur.fetchall()

ats_counter = Counter()
company_counter = Counter()
company_details = {}
industry_counter = Counter()
ats_company_map = defaultdict(lambda: Counter())

for row in rows:
    jid, ext_id, jurl, aurl, cname, curl, ind, surl = row
    ats = detect_ats(jurl, aurl, surl, ext_id)
    ats_counter[ats] += 1
    company_counter[cname] += 1
    industry_counter[ind or "Other"] += 1
    ats_company_map[ats][cname] += 1
    if cname not in company_details:
        company_details[cname] = {
            "career_url": curl or surl or "",
            "industry": ind or "General",
            "ats": ats,
            "source_url": surl or curl or ""
        }

print("=== TOTAL METRICS ===")
print(f"Total Jobs: {len(rows)}")
print(f"Total Companies: {len(company_counter)}")

print("\n=== ATS PLATFORM COUNTS ===")
for ats, count in ats_counter.most_common():
    pct = count / len(rows) * 100
    comp_count = len(ats_company_map[ats])
    print(f"{ats:<30} | {count:>5} jobs ({pct:>5.1f}%) | {comp_count:>3} companies")

print("\n=== TOP 25 COMPANIES & CAREER WEBSITES ===")
for cname, count in company_counter.most_common(25):
    d = company_details[cname]
    print(f"{cname:<26} | {count:>4} jobs | {d['ats']:<15} | {d['industry']:<25} | {d['career_url']}")

print("\n=== ATS TOP COMPANY CONTRIBUTOR ===")
for ats, count in ats_counter.most_common():
    top_c, top_c_cnt = ats_company_map[ats].most_common(1)[0]
    print(f"{ats:<30}: Top company is {top_c} ({top_c_cnt} jobs)")

print("\n=== INDUSTRY BREAKDOWN ===")
for ind, count in industry_counter.most_common():
    pct = count / len(rows) * 100
    print(f"{ind:<30} | {count:>5} jobs ({pct:>5.1f}%)")

