import urllib.request
import json

url = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"
payload = json.dumps({"appliedFacets": {}, "limit": 2, "offset": 0, "searchText": ""}).encode("utf-8")
req = urllib.request.Request(
    url,
    data=payload,
    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read().decode())
    for item in data.get("jobPostings", []):
        print(json.dumps(item, indent=2))

