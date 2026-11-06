import urllib.request
import json

host = "nvidia.wd5.myworkdayjobs.com"
tenant = "nvidia"
board = "NVIDIAExternalCareerSite"
max_jobs = 100
limit = 20
offset = 0
posts = []
total_count = None

while len(posts) < max_jobs:
    api_url = f"https://{host}/wday/cxs/{tenant}/{board}/jobs"
    payload = json.dumps({"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": ""}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            job_list = data.get("jobPostings", [])
            print(f"offset {offset}: returned {len(job_list)} items, total in resp: {data.get('total')}")
            if not job_list:
                print("No more items, break")
                break
            for item in job_list:
                posts.append(item)
            if total_count is None and "total" in data:
                total_count = data["total"]
            offset += len(job_list)
            if (total_count and offset >= total_count) or len(job_list) < limit:
                print("Reached total or len < limit, break")
                break
    except Exception as e:
        print(f"Exception at offset {offset}: {e}")
        break

print(f"Final posts count: {len(posts)}")
