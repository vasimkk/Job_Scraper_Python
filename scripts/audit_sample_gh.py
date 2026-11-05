import re
import requests
from scraper_agent.db.connection import get_dict_cursor

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/jxl,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-CH-UA": '"Not:A-Brand";v="8", "Chromium";v="124", "Google Chrome";v="124"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
}

with get_dict_cursor() as cur:
    cur.execute("""
        SELECT j.id, j.title, j.job_url, j.application_url, c.name as company_name, c.career_url
        FROM jobs j
        JOIN companies c ON j.company_id = c.id
        WHERE j.job_url LIKE '%job-boards.greenhouse.io%'
    """)
    jobs = cur.fetchall()

print(f"Auditing {len(jobs)} jobs with job-boards.greenhouse.io...")

working_as_is = 0
fixed_with_career = 0
fixed_with_boards = 0
unfixable = 0

for j in jobs[:30]:  # Test first 30
    url = j["job_url"]
    company = j["company_name"]
    career = j["career_url"]
    jid_m = re.search(r"/jobs/(\d+)", url)
    jid = jid_m.group(1) if jid_m else None

    # 1. Test existing
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=5)
        if r.status_code == 200 and "can't find that page" not in r.text.lower():
            working_as_is += 1
            print(f"[OK] {company[:15]:<15} | {url}")
            continue
    except Exception:
        pass

    # 2. Try company career_url + gh_jid
    fixed = False
    if jid and career and "greenhouse.io" not in career:
        sep = "&" if "?" in career else "?"
        cand1 = f"{career}{sep}gh_jid={jid}"
        try:
            r = requests.get(cand1, headers=BROWSER_HEADERS, timeout=5)
            if r.status_code == 200 and len(r.content) > 5000:
                fixed_with_career += 1
                fixed = True
                print(f"[FIXED -> CAREER] {company[:15]:<15} | {cand1}")
                continue
        except Exception:
            pass

    # 3. Try boards.greenhouse.io
    cand2 = url.replace("job-boards.greenhouse.io", "boards.greenhouse.io")
    try:
        r = requests.get(cand2, headers=BROWSER_HEADERS, timeout=5)
        if r.status_code == 200 and "can't find that page" not in r.text.lower():
            fixed_with_boards += 1
            fixed = True
            print(f"[FIXED -> BOARDS] {company[:15]:<15} | {cand2}")
            continue
    except Exception:
        pass

    if not fixed:
        unfixable += 1
        print(f"[UNFIXABLE] {company[:15]:<15} | {url}")

print(f"\nSummary (first 30): working_as_is={working_as_is}, fixed_with_career={fixed_with_career}, fixed_with_boards={fixed_with_boards}, unfixable={unfixable}")
