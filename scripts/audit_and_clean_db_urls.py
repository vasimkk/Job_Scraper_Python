"""
Database URL Integrity Auditor and Cleaner:
Audits all job URLs in PostgreSQL.
Verifies:
1. No malformed 'boards.greenhouse.io/company/...' URLs.
2. All job URLs return HTTP 200 and do NOT contain 404/dead error pages.
3. Automatically repairs recoverable URLs or purges non-existent/expired jobs.
"""
import sys
import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ["TEMP"] = "D:\\Temp"
os.environ["TMP"] = "D:\\Temp"

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import psycopg
from scraper_agent.scrapers.base import BaseScraper

DEAD_INDICATORS = BaseScraper.DEAD_JOB_INDICATORS

def check_and_fix_url(item):
    jid, cname, title, url = item
    headers = {"User-Agent": "Mozilla/5.0"}

    # 1. Check for malformed greenhouse company URL
    if "boards.greenhouse.io/company/" in url:
        m = re.search(r"[-=](\d{6,})", url)
        if m:
            job_num = m.group(1)
            slug = cname.lower().replace(" ", "")
            candidate = f"https://boards.greenhouse.io/{slug}/jobs/{job_num}"
            try:
                req = urllib.request.Request(candidate, headers=headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        return (jid, "REPAIRED", candidate)
            except Exception:
                pass
        return (jid, "DELETE_MALFORMED", url)

    # 2. Test live HTTP status and body
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status != 200:
                return (jid, "DELETE_STATUS", f"HTTP {resp.status}")
            body = resp.read(8192).decode("utf-8", errors="ignore").lower()
            for dead in DEAD_INDICATORS:
                if dead in body:
                    return (jid, "DELETE_DEAD_TEXT", dead)
            return (jid, "VALID", url)
    except Exception as e:
        # If connection error / 404
        err_str = str(e)
        if "404" in err_str or "not found" in err_str.lower():
            return (jid, "DELETE_404", err_str)
        # Transient timeout or network drop - keep if unsure, or re-verify
        return (jid, "VALID_OR_TIMEOUT", err_str)


def main():
    conn = psycopg.connect("postgresql://postgres:root@localhost:5433/scraperAgent")
    cur = conn.cursor()
    cur.execute("""
        SELECT j.id, c.name, j.title, j.job_url
        FROM jobs j
        JOIN companies c ON c.id = j.company_id
        ORDER BY j.id;
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"Auditing {total} job URLs in PostgreSQL for active status & availability...")

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_and_fix_url, rows))

    repaired = 0
    deleted = 0
    valid = 0

    for jid, status, detail in results:
        if status == "REPAIRED":
            cur.execute("UPDATE jobs SET job_url = %s, application_url = %s WHERE id = %s", (detail, detail, jid))
            repaired += 1
            print(f"  [REPAIRED] ID {jid} -> {detail}")
        elif status.startswith("DELETE"):
            cur.execute("DELETE FROM jobs WHERE id = %s", (jid,))
            deleted += 1
            print(f"  [DELETED DEAD URL] ID {jid} ({status}): {detail}")
        else:
            valid += 1

    conn.commit()
    conn.close()

    print(f"\nAudit complete: {valid} valid active URLs, {repaired} repaired, {deleted} purged dead URLs.")


if __name__ == "__main__":
    main()

