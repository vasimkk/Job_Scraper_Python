import urllib.request
import json

host = "nvidia.wd5.myworkdayjobs.com"
tenant = "nvidia"
board = "NVIDIAExternalCareerSite"
api_url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"

for offset in [0, 20, 40, 60]:
    payload = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=8) as resp:
        d = json.loads(resp.read().decode())
        jobs = d.get("jobPostings", [])
        print(f"offset={offset}: got {len(jobs)} jobs. First: {jobs[0].get('title') if jobs else None}")

