import sys
sys.path.insert(0, ".")
import re
import requests
from scraper_agent.config import SCRAPER_CONFIG

job_url = "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/US-CA-Santa-Clara/Senior-Site-Reliability-Engineer_JR1985473"

wd_m = re.search(r"https://([^/]+)/(?:[a-zA-Z-]+/)?([^/?#]+)(/job/.+)", job_url)
if wd_m:
    host, board, ext_path = wd_m.group(1), wd_m.group(2), wd_m.group(3)
    tenant = host.split(".")[0]
    clean_path = ext_path.split("?")[0]
    api_u = f"https://{host}/wday/cxs/{tenant}/{board}{clean_path}"
    print(f"host: {host}, tenant: {tenant}, board: {board}, ext_path: {ext_path}")
    print(f"api_u: {api_u}")
    r = requests.get(api_u, headers={"User-Agent": SCRAPER_CONFIG.user_agent, "Accept": "application/json"}, timeout=6)
    print(f"status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("Keys:", data.keys())
        info = data.get("jobPostingInfo") or {}
        print("info keys:", info.keys())
        print("title:", info.get("title"))
        print("loc:", info.get("location"))
        print("jobDesc length:", len(info.get("jobDescription") or ""))
else:
    print("NO MATCH FOR REGEX!")
