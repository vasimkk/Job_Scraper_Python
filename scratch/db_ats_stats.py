import sys
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

# Setup path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scraper_agent.db.connection import get_db_connection

def detect_ats(url: str, ext_id: str = "") -> str:
    u = (url or "").lower()
    eid = (ext_id or "").lower()
    if "myworkdayjobs.com" in u or eid.startswith("wd_"):
        return "Workday"
    if "greenhouse.io" in u or eid.startswith("gh_") or "gh_jid" in u:
        return "Greenhouse"
    if "lever.co" in u or eid.startswith("lever_"):
        return "Lever"
    if "ashbyhq.com" in u or eid.startswith("ashby_"):
        return "Ashby"
    if "smartrecruiters.com" in u or eid.startswith("sr_"):
        return "SmartRecruiters"
    if "jobvite.com" in u or "jobvite" in eid:
        return "Jobvite"
    if "taleo.net" in u or "taleo" in eid:
        return "Taleo"
    if "bamboohr.com" in u or "bamboohr" in eid:
        return "BambooHR"
    if "icims.com" in u or "icims" in eid:
        return "iCIMS"
    return "Custom / Direct Career Site"

def run():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # 1. Total jobs count
            cur.execute("SELECT COUNT(*) FROM jobs;")
            total_jobs = cur.fetchone()[0]

            # 2. Query jobs with company and source info
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

            # Analyze ATS platforms
            ats_counts = defaultdict(int)
            company_stats = defaultdict(lambda: {
                "count": 0,
                "career_url": "",
                "industry": "",
                "ats": "",
                "source_url": ""
            })

            for row in rows:
                jid, ext_id, job_u, app_u, comp_name, career_u, industry, src_u = row
                
                # Detect ATS from all available URLs
                ats = detect_ats(job_u or app_u or src_u or career_u, ext_id)
                ats_counts[ats] += 1

                # Track per career website
                key = (comp_name, career_u or src_u or "Unknown")
                company_stats[key]["count"] += 1
                company_stats[key]["career_url"] = career_u or src_u or ""
                company_stats[key]["industry"] = industry or "General"
                company_stats[key]["ats"] = ats
                company_stats[key]["source_url"] = src_u or career_u or ""

            print(f"TOTAL_JOBS={total_jobs}")
            print("\n--- ATS PLATFORM BREAKDOWN ---")
            for ats, count in sorted(ats_counts.items(), key=lambda x: x[1], reverse=True):
                pct = (count / total_jobs * 100) if total_jobs else 0
                print(f"{ats}: {count} jobs ({pct:.1f}%)")

            print("\n--- CAREER WEBSITES BREAKDOWN (TOP 100) ---")
            sorted_companies = sorted(company_stats.items(), key=lambda x: x[1]["count"], reverse=True)
            for (cname, curl), data in sorted_companies:
                print(f"{cname} | {data['industry']} | {data['ats']} | {data['count']} jobs | {curl}")

if __name__ == "__main__":
    run()
